"""
Rate limiting middleware for AI Workflow Generator API.

This module implements rate limiting and throttling to protect the LLM service
and system resources from excessive requests. It provides:
- Per-session request throttling
- Request queuing for rate-limited scenarios
- User feedback for rate limit delays

Implements Requirements 9.2 and 9.3 from the AI Workflow Generator specification.
"""
import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.services.ai_workflow_generator.config import ai_workflow_config

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: int, message: str = "Rate limit exceeded"):
        self.retry_after = retry_after
        self.message = message
        super().__init__(self.message)


class SessionRateLimiter:
    """
    Per-session rate limiter with sliding window algorithm.
    
    Tracks requests per session and enforces rate limits to prevent
    excessive LLM API calls from individual sessions.
    """
    
    def __init__(
        self,
        max_requests: int,
        window_seconds: int
    ):
        """
        Initialize the session rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        
        # Track request timestamps per session
        # Key: session_id, Value: deque of request timestamps
        self.session_requests: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Track when sessions were last accessed for cleanup
        self.last_access: Dict[str, float] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        logger.info(
            f"Initialized SessionRateLimiter: "
            f"{max_requests} requests per {window_seconds}s"
        )
    
    async def check_rate_limit(self, session_id: str) -> Tuple[bool, Optional[int]]:
        """
        Check if a request from a session should be allowed.
        
        Uses a sliding window algorithm to track requests over time.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Tuple of (allowed: bool, retry_after: Optional[int])
            - allowed: True if request is allowed, False if rate limited
            - retry_after: Seconds to wait before retrying (if rate limited)
        """
        async with self._lock:
            current_time = time.time()
            window_start = current_time - self.window_seconds
            
            # Get request history for this session
            requests = self.session_requests[session_id]
            
            # Remove requests outside the current window
            while requests and requests[0] < window_start:
                requests.popleft()
            
            # Check if under limit
            if len(requests) < self.max_requests:
                # Allow request and record timestamp
                requests.append(current_time)
                self.last_access[session_id] = current_time
                return True, None
            
            # Rate limit exceeded - calculate retry_after
            oldest_request = requests[0]
            retry_after = int(oldest_request + self.window_seconds - current_time) + 1
            
            logger.warning(
                f"Rate limit exceeded for session {session_id}: "
                f"{len(requests)} requests in {self.window_seconds}s window. "
                f"Retry after {retry_after}s"
            )
            
            return False, retry_after
    
    async def cleanup_old_sessions(self, max_age_seconds: int = 3600):
        """
        Clean up tracking data for old sessions.
        
        Removes session data that hasn't been accessed recently to prevent
        memory leaks from abandoned sessions.
        
        Args:
            max_age_seconds: Maximum age for session data (default: 1 hour)
        """
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - max_age_seconds
            
            # Find sessions to remove
            sessions_to_remove = [
                session_id
                for session_id, last_time in self.last_access.items()
                if last_time < cutoff_time
            ]
            
            # Remove old sessions
            for session_id in sessions_to_remove:
                del self.session_requests[session_id]
                del self.last_access[session_id]
            
            if sessions_to_remove:
                logger.info(f"Cleaned up {len(sessions_to_remove)} old session(s)")


class RequestQueue:
    """
    Request queue for handling rate-limited requests.
    
    When rate limits are hit, requests can be queued and processed
    when capacity becomes available.
    """
    
    def __init__(self, max_queue_size: int = 100):
        """
        Initialize the request queue.
        
        Args:
            max_queue_size: Maximum number of queued requests
        """
        self.max_queue_size = max_queue_size
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._processing = False
        
        logger.info(f"Initialized RequestQueue with max size: {max_queue_size}")
    
    async def enqueue(self, request_data: Dict) -> bool:
        """
        Add a request to the queue.
        
        Args:
            request_data: Request data to queue
            
        Returns:
            True if enqueued successfully, False if queue is full
        """
        try:
            self.queue.put_nowait(request_data)
            logger.info(f"Request queued. Queue size: {self.queue.qsize()}")
            return True
        except asyncio.QueueFull:
            logger.warning("Request queue is full")
            return False
    
    async def dequeue(self) -> Optional[Dict]:
        """
        Get the next request from the queue.
        
        Returns:
            Request data or None if queue is empty
        """
        try:
            request_data = await asyncio.wait_for(
                self.queue.get(),
                timeout=0.1
            )
            return request_data
        except asyncio.TimeoutError:
            return None
    
    def size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting AI workflow generator endpoints.
    
    Implements per-session rate limiting with user feedback for delays.
    Only applies to AI workflow generator endpoints.
    """
    
    def __init__(self, app, enable_queueing: bool = False):
        """
        Initialize the rate limit middleware.
        
        Args:
            app: FastAPI application
            enable_queueing: Whether to enable request queueing (default: False)
        """
        super().__init__(app)
        
        # Initialize rate limiter with config values
        self.rate_limiter = SessionRateLimiter(
            max_requests=ai_workflow_config.max_requests_per_session,
            window_seconds=ai_workflow_config.rate_limit_window_seconds
        )
        
        # Optional request queue
        self.enable_queueing = enable_queueing
        self.request_queue = RequestQueue() if enable_queueing else None
        
        # Paths that should be rate limited
        self.rate_limited_paths = [
            "/api/v1/ai-workflows/generate",
            "/api/v1/ai-workflows/upload",
            "/api/v1/ai-workflows/chat/sessions",
        ]
        
        # Paths that should have per-session rate limiting
        self.session_rate_limited_paths = [
            "/api/v1/ai-workflows/chat/sessions/",
        ]
        
        logger.info("RateLimitMiddleware initialized")
    
    def _extract_session_id(self, request: Request) -> Optional[str]:
        """
        Extract session ID from request path or headers.
        
        Args:
            request: FastAPI request
            
        Returns:
            Session ID string or None
        """
        # Try to extract from path (for session-specific endpoints)
        path_parts = request.url.path.split('/')
        if 'sessions' in path_parts:
            try:
                session_idx = path_parts.index('sessions') + 1
                if session_idx < len(path_parts):
                    session_id = path_parts[session_idx]
                    # Validate it looks like a UUID
                    try:
                        UUID(session_id)
                        return session_id
                    except ValueError:
                        pass
            except (ValueError, IndexError):
                pass
        
        # Try to extract from headers
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            return session_id
        
        # Try to extract from query parameters
        session_id = request.query_params.get('session_id')
        if session_id:
            return session_id
        
        # For non-session endpoints, use client IP as identifier
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    def _should_rate_limit(self, path: str) -> bool:
        """
        Check if a path should be rate limited.
        
        Args:
            path: Request path
            
        Returns:
            True if path should be rate limited
        """
        # Check exact matches
        if path in self.rate_limited_paths:
            return True
        
        # Check prefix matches for session endpoints
        for prefix in self.session_rate_limited_paths:
            if path.startswith(prefix):
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        path = request.url.path
        
        # Skip rate limiting for non-AI workflow endpoints
        if not self._should_rate_limit(path):
            return await call_next(request)
        
        # Extract session/client identifier
        session_id = self._extract_session_id(request)
        
        if not session_id:
            logger.warning(f"Could not extract session ID for rate limiting: {path}")
            # Allow request but log warning
            return await call_next(request)
        
        # Check rate limit
        allowed, retry_after = await self.rate_limiter.check_rate_limit(session_id)
        
        if not allowed:
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for session {session_id} on {path}. "
                f"Retry after {retry_after}s"
            )
            
            # If queueing is enabled, try to queue the request
            if self.enable_queueing and self.request_queue:
                queued = await self.request_queue.enqueue({
                    'session_id': session_id,
                    'path': path,
                    'timestamp': time.time()
                })
                
                if queued:
                    queue_size = self.request_queue.size()
                    estimated_wait = queue_size * 2  # Rough estimate
                    
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "detail": (
                                f"Too many requests for this session. "
                                f"Your request has been queued."
                            ),
                            "retry_after": retry_after,
                            "queue_position": queue_size,
                            "estimated_wait_seconds": estimated_wait,
                            "session_id": session_id
                        },
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(self.rate_limiter.max_requests),
                            "X-RateLimit-Window": str(self.rate_limiter.window_seconds),
                            "X-RateLimit-Remaining": "0"
                        }
                    )
            
            # Return rate limit error with helpful information
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "detail": (
                        f"Too many requests for this session. "
                        f"Maximum {self.rate_limiter.max_requests} requests "
                        f"per {self.rate_limiter.window_seconds} seconds. "
                        f"Please wait {retry_after} seconds before retrying."
                    ),
                    "retry_after": retry_after,
                    "max_requests": self.rate_limiter.max_requests,
                    "window_seconds": self.rate_limiter.window_seconds,
                    "session_id": session_id
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.rate_limiter.max_requests),
                    "X-RateLimit-Window": str(self.rate_limiter.window_seconds),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Request allowed - add rate limit headers to response
        response = await call_next(request)
        
        # Calculate remaining requests
        async with self.rate_limiter._lock:
            requests = self.rate_limiter.session_requests[session_id]
            remaining = max(0, self.rate_limiter.max_requests - len(requests))
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.rate_limiter.window_seconds)
        
        return response


async def cleanup_rate_limiter_task(rate_limiter: SessionRateLimiter):
    """
    Background task to periodically clean up old session data.
    
    Args:
        rate_limiter: SessionRateLimiter instance to clean up
    """
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await rate_limiter.cleanup_old_sessions()
        except Exception as e:
            logger.error(f"Error in rate limiter cleanup task: {e}", exc_info=True)


def register_rate_limit_middleware(app, enable_queueing: bool = False):
    """
    Register rate limiting middleware with the FastAPI application.
    
    Args:
        app: FastAPI application instance
        enable_queueing: Whether to enable request queueing
    """
    middleware = RateLimitMiddleware(app, enable_queueing=enable_queueing)
    app.add_middleware(RateLimitMiddleware, enable_queueing=enable_queueing)
    
    logger.info(
        f"Rate limiting middleware registered "
        f"(queueing: {'enabled' if enable_queueing else 'disabled'})"
    )

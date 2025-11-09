"""
Request/response logging middleware for the Workflow Management API.

This middleware logs all API requests and responses with:
- HTTP method and path
- Response status code
- Request duration
- Correlation ID for request tracing
- Client information (IP, user agent)

The correlation ID is automatically propagated to all logs within the request context.
"""
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.logging import set_correlation_id, clear_correlation_id

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    This middleware:
    1. Generates a unique correlation ID for each request
    2. Sets the correlation ID in the context for all subsequent logs
    3. Logs request details (method, path, client info)
    4. Logs response details (status code, duration)
    5. Cleans up the correlation ID after request completion
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the logging middleware.
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response from the route handler
        """
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        # Set correlation ID in context for all logs in this request
        set_correlation_id(correlation_id)
        
        # Record start time
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        query_params = str(request.url.query) if request.url.query else None
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Log incoming request
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "event_type": "request_started",
                "method": method,
                "path": path,
                "query_params": query_params,
                "client_host": client_host,
                "user_agent": user_agent,
                "correlation_id": correlation_id
            }
        )
        
        # Process request and handle exceptions
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                f"Request completed: {method} {path} - {response.status_code} - {duration_ms:.2f}ms",
                extra={
                    "event_type": "request_completed",
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "correlation_id": correlation_id
                }
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as exc:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Request failed: {method} {path} - {duration_ms:.2f}ms - {str(exc)}",
                extra={
                    "event_type": "request_failed",
                    "method": method,
                    "path": path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(exc),
                    "correlation_id": correlation_id
                },
                exc_info=True
            )
            
            # Re-raise the exception to be handled by error handlers
            raise
            
        finally:
            # Clear correlation ID from context
            clear_correlation_id()


def register_logging_middleware(app) -> None:
    """
    Register the logging middleware with the FastAPI application.
    
    This function should be called during application initialization to enable
    request/response logging for all routes.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(LoggingMiddleware)
    logger.info("Logging middleware registered successfully")

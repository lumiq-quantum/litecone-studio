"""
Tests for rate limiting middleware.

Tests verify that rate limiting works correctly for AI workflow endpoints,
including per-session throttling and user feedback.
"""
import pytest
import asyncio
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from api.middleware.rate_limiter import (
    SessionRateLimiter,
    RateLimitMiddleware,
    RequestQueue
)


class TestSessionRateLimiter:
    """Test the SessionRateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self):
        """Test that requests under the limit are allowed."""
        limiter = SessionRateLimiter(max_requests=5, window_seconds=60)
        session_id = "test-session-1"
        
        # Make 5 requests (under limit)
        for i in range(5):
            allowed, retry_after = await limiter.check_rate_limit(session_id)
            assert allowed is True
            assert retry_after is None
    
    @pytest.mark.asyncio
    async def test_blocks_requests_over_limit(self):
        """Test that requests over the limit are blocked."""
        limiter = SessionRateLimiter(max_requests=3, window_seconds=60)
        session_id = "test-session-2"
        
        # Make 3 requests (at limit)
        for i in range(3):
            allowed, retry_after = await limiter.check_rate_limit(session_id)
            assert allowed is True
        
        # 4th request should be blocked
        allowed, retry_after = await limiter.check_rate_limit(session_id)
        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0
    
    @pytest.mark.asyncio
    async def test_sliding_window_allows_requests_after_window(self):
        """Test that requests are allowed after the window expires."""
        limiter = SessionRateLimiter(max_requests=2, window_seconds=1)
        session_id = "test-session-3"
        
        # Make 2 requests (at limit)
        for i in range(2):
            allowed, retry_after = await limiter.check_rate_limit(session_id)
            assert allowed is True
        
        # 3rd request should be blocked
        allowed, retry_after = await limiter.check_rate_limit(session_id)
        assert allowed is False
        
        # Wait for window to expire
        await asyncio.sleep(1.1)
        
        # Request should now be allowed
        allowed, retry_after = await limiter.check_rate_limit(session_id)
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_different_sessions_tracked_separately(self):
        """Test that different sessions have independent rate limits."""
        limiter = SessionRateLimiter(max_requests=2, window_seconds=60)
        
        # Session 1: make 2 requests (at limit)
        for i in range(2):
            allowed, _ = await limiter.check_rate_limit("session-1")
            assert allowed is True
        
        # Session 1: 3rd request blocked
        allowed, _ = await limiter.check_rate_limit("session-1")
        assert allowed is False
        
        # Session 2: should still be able to make requests
        allowed, _ = await limiter.check_rate_limit("session-2")
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_cleanup_removes_old_sessions(self):
        """Test that cleanup removes old session data."""
        limiter = SessionRateLimiter(max_requests=5, window_seconds=60)
        
        # Make requests for multiple sessions
        for i in range(3):
            await limiter.check_rate_limit(f"session-{i}")
        
        assert len(limiter.session_requests) == 3
        assert len(limiter.last_access) == 3
        
        # Manually set old access times
        for session_id in limiter.last_access:
            limiter.last_access[session_id] = time.time() - 7200  # 2 hours ago
        
        # Run cleanup (max age 1 hour)
        await limiter.cleanup_old_sessions(max_age_seconds=3600)
        
        # All sessions should be removed
        assert len(limiter.session_requests) == 0
        assert len(limiter.last_access) == 0


class TestRequestQueue:
    """Test the RequestQueue class."""
    
    @pytest.mark.asyncio
    async def test_enqueue_and_dequeue(self):
        """Test basic enqueue and dequeue operations."""
        queue = RequestQueue(max_queue_size=10)
        
        # Enqueue a request
        request_data = {"session_id": "test", "path": "/test"}
        result = await queue.enqueue(request_data)
        assert result is True
        assert queue.size() == 1
        
        # Dequeue the request
        dequeued = await queue.dequeue()
        assert dequeued == request_data
        assert queue.size() == 0
    
    @pytest.mark.asyncio
    async def test_queue_full_returns_false(self):
        """Test that enqueue returns False when queue is full."""
        queue = RequestQueue(max_queue_size=2)
        
        # Fill the queue
        assert await queue.enqueue({"id": 1}) is True
        assert await queue.enqueue({"id": 2}) is True
        
        # Queue is full
        assert await queue.enqueue({"id": 3}) is False
        assert queue.size() == 2
    
    @pytest.mark.asyncio
    async def test_dequeue_empty_returns_none(self):
        """Test that dequeue returns None when queue is empty."""
        queue = RequestQueue(max_queue_size=10)
        
        # Dequeue from empty queue
        result = await queue.dequeue()
        assert result is None


class TestRateLimitMiddleware:
    """Test the RateLimitMiddleware integration."""
    
    def test_middleware_allows_non_ai_workflow_endpoints(self):
        """Test that non-AI workflow endpoints are not rate limited."""
        app = FastAPI()
        
        @app.get("/api/v1/workflows")
        async def get_workflows():
            return {"workflows": []}
        
        app.add_middleware(RateLimitMiddleware, enable_queueing=False)
        
        client = TestClient(app)
        
        # Make multiple requests - should all succeed
        for i in range(10):
            response = client.get("/api/v1/workflows")
            assert response.status_code == 200
    
    def test_middleware_rate_limits_ai_workflow_endpoints(self):
        """Test that AI workflow endpoints are rate limited."""
        app = FastAPI()
        
        @app.post("/api/v1/ai-workflows/generate")
        async def generate_workflow():
            return {"workflow": {}}
        
        # Use very low limits for testing
        from api.services.ai_workflow_generator.config import ai_workflow_config
        original_max = ai_workflow_config.max_requests_per_session
        original_window = ai_workflow_config.rate_limit_window_seconds
        
        try:
            # Set low limits for testing
            ai_workflow_config.max_requests_per_session = 3
            ai_workflow_config.rate_limit_window_seconds = 60
            
            app.add_middleware(RateLimitMiddleware, enable_queueing=False)
            
            client = TestClient(app)
            
            # Make requests up to limit
            for i in range(3):
                response = client.post("/api/v1/ai-workflows/generate", json={})
                assert response.status_code == 200
            
            # Next request should be rate limited
            response = client.post("/api/v1/ai-workflows/generate", json={})
            assert response.status_code == 429
            assert "rate limit exceeded" in response.json()["error"].lower()
            assert "retry_after" in response.json()
            
        finally:
            # Restore original config
            ai_workflow_config.max_requests_per_session = original_max
            ai_workflow_config.rate_limit_window_seconds = original_window
    
    def test_middleware_adds_rate_limit_headers(self):
        """Test that rate limit headers are added to responses."""
        app = FastAPI()
        
        @app.post("/api/v1/ai-workflows/generate")
        async def generate_workflow():
            return {"workflow": {}}
        
        app.add_middleware(RateLimitMiddleware, enable_queueing=False)
        
        client = TestClient(app)
        
        response = client.post("/api/v1/ai-workflows/generate", json={})
        
        # Check rate limit headers are present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Window" in response.headers
    
    def test_middleware_extracts_session_id_from_path(self):
        """Test that session ID is extracted from URL path."""
        app = FastAPI()
        
        @app.post("/api/v1/ai-workflows/chat/sessions/{session_id}/messages")
        async def send_message(session_id: str):
            return {"message": "ok"}
        
        from api.services.ai_workflow_generator.config import ai_workflow_config
        original_max = ai_workflow_config.max_requests_per_session
        
        try:
            # Set low limit for testing
            ai_workflow_config.max_requests_per_session = 2
            
            app.add_middleware(RateLimitMiddleware, enable_queueing=False)
            
            client = TestClient(app)
            
            session_id = "550e8400-e29b-41d4-a716-446655440000"
            
            # Make requests up to limit for this session
            for i in range(2):
                response = client.post(
                    f"/api/v1/ai-workflows/chat/sessions/{session_id}/messages",
                    json={}
                )
                assert response.status_code == 200
            
            # Next request for same session should be rate limited
            response = client.post(
                f"/api/v1/ai-workflows/chat/sessions/{session_id}/messages",
                json={}
            )
            assert response.status_code == 429
            
            # Different session should still work
            other_session_id = "660e8400-e29b-41d4-a716-446655440000"
            response = client.post(
                f"/api/v1/ai-workflows/chat/sessions/{other_session_id}/messages",
                json={}
            )
            assert response.status_code == 200
            
        finally:
            # Restore original config
            ai_workflow_config.max_requests_per_session = original_max


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

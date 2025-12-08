# Rate Limiting for AI Workflow Generator

## Overview

The AI Workflow Generator implements rate limiting to protect the LLM service and system resources from excessive requests. This ensures fair usage and prevents individual sessions from overwhelming the system.

## Features

### 1. Per-Session Rate Limiting

Each chat session or client is tracked independently and has its own rate limit. This prevents one user from affecting others.

**Default Configuration:**
- Maximum requests: 50 per session
- Time window: 60 seconds

### 2. Sliding Window Algorithm

The rate limiter uses a sliding window algorithm that tracks requests over time. This provides more accurate rate limiting compared to fixed windows.

### 3. User Feedback

When rate limits are exceeded, users receive clear feedback including:
- Error message explaining the limit
- Retry-after time in seconds
- Current rate limit settings
- Session identifier

### 4. Rate Limit Headers

All responses include headers with rate limit information:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Window`: Time window in seconds
- `Retry-After`: Seconds to wait (when rate limited)

### 5. Request Queueing (Optional)

The system supports optional request queueing for rate-limited requests. When enabled:
- Requests that exceed the limit are queued
- Users receive queue position and estimated wait time
- Requests are processed when capacity becomes available

**Note:** Queueing is disabled by default for simplicity.

## Configuration

Rate limiting is configured via environment variables:

```bash
# Maximum requests per session
MAX_REQUESTS_PER_SESSION=50

# Rate limit window in seconds
RATE_LIMIT_WINDOW_SECONDS=60
```

## Protected Endpoints

The following AI workflow endpoints are rate limited:

1. `POST /api/v1/ai-workflows/generate` - Generate workflow from text
2. `POST /api/v1/ai-workflows/upload` - Generate workflow from document
3. `POST /api/v1/ai-workflows/chat/sessions` - Create chat session
4. `POST /api/v1/ai-workflows/chat/sessions/{session_id}/messages` - Send chat message

## Rate Limit Response

When a rate limit is exceeded, the API returns a 429 status code with details:

```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests for this session. Maximum 50 requests per 60 seconds. Please wait 45 seconds before retrying.",
  "retry_after": 45,
  "max_requests": 50,
  "window_seconds": 60,
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Session Identification

The rate limiter identifies sessions using:

1. **Session ID from URL path** - For session-specific endpoints
   - Example: `/api/v1/ai-workflows/chat/sessions/{session_id}/messages`

2. **X-Session-ID header** - Custom header for session tracking
   - Example: `X-Session-ID: 550e8400-e29b-41d4-a716-446655440000`

3. **Client IP address** - Fallback for non-session endpoints
   - Used when no session ID is available

## Best Practices

### For API Clients

1. **Monitor rate limit headers** - Check remaining requests before making calls
2. **Implement exponential backoff** - When rate limited, wait before retrying
3. **Respect Retry-After header** - Wait the specified time before retrying
4. **Use session IDs** - Provide session IDs for accurate tracking

### For Administrators

1. **Adjust limits based on usage** - Monitor and tune rate limits
2. **Enable queueing for high traffic** - Consider enabling queueing if needed
3. **Monitor rate limit metrics** - Track rate limit hits and adjust accordingly

## Implementation Details

### Sliding Window Algorithm

The rate limiter tracks request timestamps for each session:

```python
# Pseudo-code
def check_rate_limit(session_id):
    current_time = now()
    window_start = current_time - window_seconds
    
    # Remove old requests outside window
    remove_requests_before(window_start)
    
    # Check if under limit
    if request_count < max_requests:
        record_request(current_time)
        return ALLOWED
    else:
        retry_after = calculate_retry_time()
        return RATE_LIMITED, retry_after
```

### Cleanup

The rate limiter automatically cleans up old session data every hour to prevent memory leaks from abandoned sessions.

## Testing

The rate limiting implementation includes comprehensive tests:

```bash
# Run rate limiter tests
python -m pytest api/tests/test_rate_limiter.py -v
```

Tests cover:
- Basic rate limiting functionality
- Sliding window behavior
- Per-session tracking
- Request queueing
- Middleware integration

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 9.2**: Rate limit handling with user feedback
  - Returns clear error messages with retry times
  - Provides queue information when queueing is enabled

- **Requirement 9.3**: Per-session request throttling
  - Tracks requests independently per session
  - Enforces configurable limits per session

## Troubleshooting

### Rate Limits Too Strict

If users frequently hit rate limits:

1. Increase `MAX_REQUESTS_PER_SESSION`
2. Increase `RATE_LIMIT_WINDOW_SECONDS`
3. Enable request queueing

### Rate Limits Too Lenient

If system resources are strained:

1. Decrease `MAX_REQUESTS_PER_SESSION`
2. Decrease `RATE_LIMIT_WINDOW_SECONDS`
3. Monitor LLM API usage

### Session Tracking Issues

If rate limiting isn't working correctly:

1. Verify session IDs are being passed correctly
2. Check middleware is registered in correct order
3. Review logs for rate limiter warnings

## Future Enhancements

Potential improvements for the rate limiting system:

1. **Tiered rate limits** - Different limits for different user types
2. **Dynamic rate limiting** - Adjust limits based on system load
3. **Distributed rate limiting** - Share rate limit state across instances
4. **Rate limit analytics** - Dashboard for monitoring rate limit usage
5. **Burst allowance** - Allow short bursts above the limit

# AI Workflow Generator Configuration

This document describes the configuration system for the AI Workflow Generator service.

## Overview

The AI Workflow Generator uses a comprehensive configuration system that:
- Validates all settings on startup
- Provides sensible defaults for all non-required settings
- Supports environment variable overrides
- Implements rate limiting, timeouts, and retry logic as specified in requirements 9.1-9.4

## Configuration Files

### Main Configuration
- **File**: `api/services/ai_workflow_generator/config.py`
- **Class**: `AIWorkflowConfig`
- **Purpose**: Defines all configuration settings with validation

### Startup Validation
- **File**: `api/services/ai_workflow_generator/startup.py`
- **Functions**: `validate_environment()`, `initialize_service()`
- **Purpose**: Validates configuration on application startup

### Environment Variables
- **File**: `.env.api` (create from `.env.api.example`)
- **Purpose**: Store configuration values

## Required Settings

These settings **must** be configured before starting the service:

### Gemini API Configuration
```bash
GEMINI_API_KEY=your-gemini-api-key-here  # REQUIRED
```

### Integration Endpoints
```bash
AGENT_REGISTRY_URL=http://localhost:8000/api/v1/agents  # REQUIRED
WORKFLOW_API_URL=http://localhost:8000/api/v1/workflows  # REQUIRED
```

## Optional Settings

All optional settings have sensible defaults. Override them as needed:

### Gemini LLM Settings
```bash
GEMINI_MODEL=gemini-1.5-pro              # Default: gemini-1.5-pro
GEMINI_MAX_TOKENS=8192                   # Default: 8192 (range: 1024-32768)
GEMINI_TEMPERATURE=0.7                   # Default: 0.7 (range: 0.0-2.0)
GEMINI_TIMEOUT_SECONDS=60                # Default: 60 (range: 10-300)
```

### Session Configuration
```bash
SESSION_TIMEOUT_MINUTES=30               # Default: 30 (range: 5-1440)
SESSION_CLEANUP_INTERVAL_MINUTES=5       # Default: 5 (range: 1-60)
MAX_SESSION_HISTORY_SIZE=100             # Default: 100 (range: 10-1000)
```

### Document Processing (Requirement 9.4)
```bash
MAX_DOCUMENT_SIZE_MB=10                  # Default: 10 (range: 1-100)
SUPPORTED_DOCUMENT_FORMATS=pdf,docx,txt,md  # Default: pdf,docx,txt,md
DOCUMENT_CHUNK_SIZE_TOKENS=6000          # Default: 6000 (range: 1000-30000)
```

### Rate Limiting (Requirements 9.2, 9.3)
```bash
MAX_REQUESTS_PER_SESSION=50              # Default: 50 (range: 10-500)
RATE_LIMIT_WINDOW_SECONDS=60             # Default: 60 (range: 10-3600)
GLOBAL_RATE_LIMIT_PER_MINUTE=100         # Default: 100 (range: 10-1000)
RATE_LIMIT_QUEUE_SIZE=50                 # Default: 50 (range: 10-200)
```

### Retry Configuration (Requirement 9.1 - Exponential Backoff)
```bash
MAX_RETRIES=3                            # Default: 3 (range: 0-10)
INITIAL_RETRY_DELAY_MS=1000              # Default: 1000 (range: 100-5000)
MAX_RETRY_DELAY_MS=30000                 # Default: 30000 (range: 5000-60000)
RETRY_BACKOFF_MULTIPLIER=2.0             # Default: 2.0 (range: 1.0-5.0)
RETRIABLE_STATUS_CODES=429,500,502,503,504  # Default: 429,500,502,503,504
```

### Cache Configuration
```bash
AGENT_CACHE_TTL_SECONDS=300              # Default: 300 (range: 60-3600)
WORKFLOW_CACHE_TTL_SECONDS=60            # Default: 60 (range: 10-600)
```

### API Timeouts
```bash
API_TIMEOUT_SECONDS=30                   # Default: 30 (range: 5-120)
```

### Validation Configuration
```bash
ENABLE_STRICT_VALIDATION=true            # Default: true
ENABLE_AUTO_CORRECTION=true              # Default: true
```

### Logging Configuration
```bash
LOG_LLM_PROMPTS=false                    # Default: false (disable in production)
LOG_LLM_RESPONSES=false                  # Default: false (disable in production)
```

## Configuration Validation

The configuration system performs comprehensive validation on startup:

### 1. Required Settings Validation
- Ensures `GEMINI_API_KEY` is present and non-empty
- Validates API endpoint URLs are properly formatted

### 2. Rate Limiting Validation (Requirements 9.2, 9.3)
- Checks that rate limits are positive
- Warns if per-session rate exceeds global rate

### 3. Timeout Validation
- Ensures all timeouts are within reasonable ranges
- Warns if timeouts are unusually high

### 4. Document Processing Validation (Requirement 9.4)
- Validates document size limits
- Ensures chunk size is less than max tokens
- Validates supported formats list

### 5. Retry Configuration Validation (Requirement 9.1)
- Ensures max delay > initial delay
- Validates backoff multiplier
- Calculates total potential retry time

## Usage

### In Application Startup

```python
from api.services.ai_workflow_generator.startup import initialize_service

# Call during application startup
initialize_service()
```

This will:
1. Load configuration from environment variables
2. Validate all settings
3. Log configuration (excluding sensitive data)
4. Raise `StartupValidationError` if validation fails

### Accessing Configuration

```python
from api.services.ai_workflow_generator.config import ai_workflow_config

# Access configuration values
api_key = ai_workflow_config.gemini_api_key
max_tokens = ai_workflow_config.gemini_max_tokens
timeout = ai_workflow_config.session_timeout_minutes

# Use helper methods
retry_delay = ai_workflow_config.get_retry_delay_ms(attempt=2)
is_retriable = ai_workflow_config.is_retriable_error(status_code=429)
```

### Getting Service Info

```python
from api.services.ai_workflow_generator.startup import get_service_info

# Get service configuration info (for health checks, etc.)
info = get_service_info()
```

## Exponential Backoff (Requirement 9.1)

The retry configuration implements exponential backoff for LLM API calls:

```python
# Example: With default settings
# Attempt 0: 1000ms delay
# Attempt 1: 2000ms delay (1000 * 2^1)
# Attempt 2: 4000ms delay (1000 * 2^2)
# Attempt 3: 8000ms delay (1000 * 2^3)
# ...capped at MAX_RETRY_DELAY_MS (30000ms)

delay = ai_workflow_config.get_retry_delay_ms(attempt)
```

## Rate Limiting (Requirements 9.2, 9.3)

The configuration supports two levels of rate limiting:

1. **Per-Session Rate Limiting**: Limits requests per chat session
   - `MAX_REQUESTS_PER_SESSION`: Maximum requests allowed
   - `RATE_LIMIT_WINDOW_SECONDS`: Time window for counting requests

2. **Global Rate Limiting**: Limits total requests across all sessions
   - `GLOBAL_RATE_LIMIT_PER_MINUTE`: Total requests per minute
   - `RATE_LIMIT_QUEUE_SIZE`: Maximum queued requests

## Document Processing (Requirement 9.4)

Document processing is configured to handle large documents efficiently:

- **Size Limits**: `MAX_DOCUMENT_SIZE_MB` prevents memory issues
- **Chunking**: `DOCUMENT_CHUNK_SIZE_TOKENS` ensures content fits in LLM context
- **Format Support**: `SUPPORTED_DOCUMENT_FORMATS` defines accepted file types

## Testing

Run configuration tests:

```bash
pytest api/tests/ai_workflow_generator/test_config_validation.py -v
```

## Troubleshooting

### Configuration Validation Fails

If startup validation fails, check the error message for specific issues:

```
Configuration validation failed:
  - GEMINI_API_KEY is required. Please set it in your environment or .env.api file.
```

### Environment Variables Not Loading

1. Ensure `.env.api` file exists (copy from `.env.api.example`)
2. Check file permissions
3. Verify environment variable names match exactly

### Rate Limiting Issues

If you see warnings about rate limiting configuration:

```
max_requests_per_session (100) is greater than global_rate_limit_per_minute (50).
This may cause unexpected rate limiting behavior.
```

Adjust the values so global rate limit is higher than per-session rate.

### Retry Configuration Issues

If total retry time exceeds timeout:

```
Total retry time (45.0s) exceeds Gemini timeout (30s).
Retries may not complete before timeout.
```

Either increase `GEMINI_TIMEOUT_SECONDS` or reduce retry delays.

## Security Considerations

1. **API Keys**: Never commit `.env.api` to version control
2. **Logging**: Disable `LOG_LLM_PROMPTS` and `LOG_LLM_RESPONSES` in production
3. **Rate Limits**: Set appropriate limits to prevent abuse
4. **Timeouts**: Configure timeouts to prevent resource exhaustion

## References

- Requirements: See `.kiro/specs/ai-workflow-generator/requirements.md`
  - Requirement 9.1: Exponential backoff retry logic
  - Requirement 9.2: Rate limit handling
  - Requirement 9.3: Request throttling per session
  - Requirement 9.4: Document chunking for large files
- Design: See `.kiro/specs/ai-workflow-generator/design.md`

# Error Handling and Logging Implementation

This document describes the comprehensive error handling and logging system implemented for the AI Workflow Generator service.

## Overview

The error handling and logging system provides:

1. **Structured Error Models** - Categorized errors with severity levels and suggestions
2. **Comprehensive Logging** - Structured logging for all operations with performance metrics
3. **LLM Interaction Logging** - Sanitized logging of prompts and responses
4. **Performance Metrics** - Detailed tracking of operation durations and resource usage
5. **Error Categorization** - Systematic classification of errors for better handling

## Error Handling

### Error Categories

All errors are categorized into six types:

- **USER_INPUT** - Errors related to user input (invalid format, unsupported file types, etc.)
- **LLM_SERVICE** - Errors from LLM service interactions (rate limits, timeouts, API failures)
- **VALIDATION** - Errors from workflow validation (schema violations, circular references, etc.)
- **INTEGRATION** - Errors from external service integration (agent registry, workflow API)
- **RESOURCE** - Errors related to resource constraints (file size limits, token limits)
- **INTERNAL** - Internal system errors (unexpected exceptions, bugs)

### Error Severity Levels

- **LOW** - Minor issues that don't prevent operation (e.g., user input errors)
- **MEDIUM** - Moderate issues that may require attention (e.g., validation errors)
- **HIGH** - Serious issues that prevent operation (e.g., service unavailable)
- **CRITICAL** - Critical system failures (e.g., internal errors)

### Error Classes

#### Base Error: `AIWorkflowError`

All errors inherit from `AIWorkflowError`, which provides:

```python
AIWorkflowError(
    message: str,                    # Human-readable error message
    category: ErrorCategory,         # Error category
    severity: ErrorSeverity,         # Severity level
    details: Optional[Dict],         # Additional error details
    suggestions: Optional[List[str]], # Suggestions to resolve the error
    recoverable: bool,               # Whether the error is recoverable
    original_error: Optional[Exception] # Original exception if wrapping
)
```

#### Specific Error Types

1. **UserInputError** - For invalid user input
   - Severity: LOW
   - Recoverable: Yes
   - Includes suggestions for fixing input

2. **LLMServiceError** - For LLM service failures
   - Severity: MEDIUM (recoverable) or HIGH (non-recoverable)
   - Includes retry suggestions

3. **ValidationError** - For workflow validation failures
   - Severity: MEDIUM
   - Includes list of validation errors
   - Recoverable: Yes

4. **IntegrationError** - For external service failures
   - Severity: HIGH
   - Includes service name
   - Recoverable: Yes

5. **ResourceError** - For resource constraint violations
   - Severity: MEDIUM
   - Includes resource type and limits
   - Recoverable: Yes

6. **InternalError** - For unexpected system errors
   - Severity: CRITICAL
   - Recoverable: No
   - Includes original exception

### Error Response Model

All errors are converted to a standardized `ErrorResponse`:

```python
{
    "error_code": "category_severity",  # e.g., "user_input_low"
    "message": "Human-readable message",
    "details": {...},                   # Optional additional details
    "suggestions": [...],               # List of suggestions
    "recoverable": true/false           # Whether error is recoverable
}
```

### Usage Example

```python
from api.services.ai_workflow_generator.errors import UserInputError, handle_error

# Raise a specific error
raise UserInputError(
    message="Unsupported file format: xyz",
    details={"file_type": "xyz"},
    suggestions=["Use PDF, DOCX, TXT, or MD format"]
)

# Handle any error
try:
    # Some operation
    pass
except Exception as e:
    error_response = handle_error(e, context={"operation": "generate_workflow"})
    # error_response is an ErrorResponse object
```

## Logging System

### Structured Logging

All logging uses structured logging with consistent fields:

```python
{
    "timestamp": "2024-01-01T12:00:00Z",
    "level": "INFO",
    "logger": "api.services.ai_workflow_generator",
    "message": "Operation completed",
    "event_type": "operation_completed",
    "operation": "generate_workflow",
    "duration_ms": 1234.56,
    ...additional fields...
}
```

### Operation Logging

#### Using Context Manager

```python
from api.services.ai_workflow_generator.logging_utils import log_operation

with log_operation("generate_workflow", {"user_id": "123"}) as op_logger:
    # Do work
    op_logger.log("info", "Processing step 1")
    # More work
    # Automatically logs start, completion, and duration
```

#### Using Decorator

```python
from api.services.ai_workflow_generator.logging_utils import log_function_call

@log_function_call("my_operation")
async def my_function(arg1, arg2):
    # Function implementation
    pass
```

### LLM Interaction Logging

LLM calls are logged with sanitization to prevent logging sensitive data:

```python
from api.services.ai_workflow_generator.logging_utils import LLMLogger

LLMLogger.log_llm_call(
    model="gemini-1.5-pro",
    prompt=prompt_text,           # Automatically truncated
    response=response_text,       # Automatically truncated
    usage={"prompt_tokens": 100, "completion_tokens": 200},
    duration_ms=1500.0
)
```

Features:
- Automatic prompt/response truncation (default 500 chars)
- Token usage tracking
- Duration tracking
- Error logging for failed calls

### Performance Metrics

#### Individual Metrics

```python
from api.services.ai_workflow_generator.logging_utils import PerformanceLogger

PerformanceLogger.log_metric(
    metric_name="llm_call_duration",
    value=1234.56,
    unit="ms",
    context={"operation": "generate_workflow", "model": "gemini"}
)
```

#### Workflow Generation Metrics

Comprehensive metrics for workflow generation:

```python
PerformanceLogger.log_workflow_generation_metrics(
    total_duration_ms=2000.0,
    llm_duration_ms=1500.0,
    validation_duration_ms=300.0,
    agent_query_duration_ms=200.0,
    workflow_size_bytes=4096,
    num_steps=5,
    num_agents=3
)
```

This logs:
- Total generation time
- Time breakdown by component
- Workflow size and complexity
- LLM percentage of total time

## Integration with Services

### Document Processing Service

The document processing service uses error handling for:
- Unsupported file formats → `UserInputError`
- File size violations → `ResourceError`
- Extraction failures → Detailed error messages

### Gemini Service

The Gemini service includes:
- Exponential backoff retry with detailed logging
- LLM call logging with sanitization
- Performance metric tracking
- Error categorization for different failure types

### Workflow Generation Service

The workflow generation service provides:
- Comprehensive operation logging
- Performance metrics for all phases
- Error handling with context
- Detailed validation error reporting

## Configuration

### Logging Configuration

```python
from api.services.ai_workflow_generator.logging_utils import configure_logging

# Configure logging level and format
configure_logging(log_level="INFO", log_format="json")
```

Supported formats:
- `json` - Structured JSON logging (recommended for production)
- `text` - Human-readable text logging (for development)

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General informational messages
- `WARNING` - Warning messages (non-critical issues)
- `ERROR` - Error messages (operation failures)
- `CRITICAL` - Critical failures (system-level issues)

## Best Practices

### Error Handling

1. **Use Specific Error Types** - Use the most specific error type for the situation
2. **Provide Context** - Include relevant details in the `details` dict
3. **Add Suggestions** - Always provide actionable suggestions for users
4. **Log Errors** - Call `.log()` on errors to ensure they're logged
5. **Wrap Exceptions** - Wrap unexpected exceptions in `InternalError`

### Logging

1. **Use Structured Logging** - Always use the logging utilities for consistency
2. **Log Operations** - Use `log_operation` context manager for all major operations
3. **Track Performance** - Log performance metrics for optimization
4. **Sanitize Sensitive Data** - Use `LLMLogger` for LLM interactions
5. **Include Context** - Add relevant context to all log messages

### Performance Monitoring

1. **Track Durations** - Measure and log duration of all operations
2. **Monitor LLM Usage** - Track token usage and costs
3. **Identify Bottlenecks** - Use metrics to identify slow operations
4. **Set Baselines** - Establish performance baselines for monitoring

## Testing

Comprehensive tests are provided:

- `test_error_handling.py` - Tests for all error types and handling
- `test_logging_utils.py` - Tests for logging utilities

Run tests:
```bash
pytest api/tests/ai_workflow_generator/test_error_handling.py -v
pytest api/tests/ai_workflow_generator/test_logging_utils.py -v
```

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 2.3** - Document extraction errors include details ✓
- **Requirement 2.4** - Document extraction failures provide specific error details ✓
- **Requirement 6.5** - Workflow creation failures allow retry with error reporting ✓

### Task Completion

Task 14 implementation includes:

✓ Error response models with suggestions
✓ Structured logging for all operations
✓ Error categorization and handling strategies
✓ LLM prompt/response logging (sanitized)
✓ Performance metrics logging

All components are fully tested and integrated with existing services.

# Logging and Observability Implementation

## Overview

Implemented comprehensive structured logging with JSON formatting and correlation ID support for the Centralized Executor and HTTP-Kafka Bridge components.

## What Was Implemented

### 1. Structured Logging Utility (`src/utils/logging.py`)

Created a complete logging utility module with:

- **StructuredFormatter**: JSON formatter for structured logs
- **TextFormatter**: Human-readable text formatter with correlation IDs
- **setup_logging()**: Configure logging with format and level
- **set_correlation_id()**: Set correlation ID for current execution context
- **get_correlation_id()**: Retrieve current correlation ID
- **clear_correlation_id()**: Clear correlation ID from context
- **log_event()**: Convenience function for logging structured events

### 2. Integration with Centralized Executor

Updated `src/executor/centralized_executor.py` to:

- Import and use structured logging utilities
- Set correlation ID at workflow start (using run_id)
- Log key events with structured data:
  - `executor_start`: Executor initialization
  - `config_loaded`: Configuration loaded
  - `workflow_plan_loaded`: Workflow plan parsed
  - `step_start`: Step execution started
  - `agent_call`: Agent task published to Kafka
  - `step_complete`: Step completed successfully
  - `step_failed`: Step execution failed
  - `step_error`: Critical errors during execution

### 3. Integration with HTTP-Kafka Bridge

Updated `src/bridge/external_agent_executor.py` and `src/bridge/__main__.py` to:

- Import and use structured logging utilities
- Set correlation ID for each task (using task correlation_id)
- Log key events with structured data:
  - `bridge_start`: Bridge initialization
  - `task_received`: Task received from Kafka
  - `agent_metadata_fetch`: Fetching agent metadata
  - `agent_invoke_start`: Starting agent invocation
  - `http_call`: Making HTTP call to agent
  - `http_success`: HTTP call succeeded
  - `agent_success`: Agent completed successfully
  - `agent_error`: Agent invocation failed
  - `task_error`: Error handling task

### 4. Configuration

Added logging configuration to `.env.example`:

```bash
# Logging Configuration
LOG_LEVEL=INFO      # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json     # json or text
```

### 5. Documentation

Created comprehensive documentation:

- **src/utils/logging_README.md**: Detailed logging utility documentation
- **examples/logging_example.py**: Working example demonstrating logging features
- **README.md**: Updated with logging section and examples

## Key Features

### Structured JSON Logs

All logs are formatted as JSON objects with standard fields:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "src.executor.centralized_executor",
  "message": "Starting workflow step",
  "correlation_id": "run-123-correlation-456",
  "event_type": "step_start",
  "run_id": "run-123",
  "step_id": "step-1",
  "agent_name": "ResearchAgent"
}
```

### Correlation ID Tracking

- Automatically included in all log messages within an execution context
- Set once at the start of workflow/task processing
- Propagated through all operations
- Enables end-to-end tracing across services

### Event Types

Standardized event types for consistent logging:

- Executor: `executor_start`, `step_start`, `agent_call`, `step_complete`, `step_failed`, `step_error`
- Bridge: `bridge_start`, `task_received`, `http_call`, `agent_success`, `agent_error`

### Flexible Formatting

Two output formats supported:

1. **JSON Format** (default): Structured logs for production and log aggregation
2. **Text Format**: Human-readable logs for local development

## Requirements Satisfied

✅ **8.1**: Configured structured JSON logging  
✅ **8.2**: Added correlation ID to all log messages  
✅ **8.3**: Log key events (step start, step complete, agent call, errors)  
✅ **8.4**: Comprehensive observability with event types and metadata  

## Testing

Verified implementation with:

1. Unit test of logging utilities (JSON and text formats)
2. Import verification of all components
3. Example script demonstrating real-world usage
4. No diagnostic errors in any modified files

## Usage Example

```python
from src.utils.logging import setup_logging, set_correlation_id, log_event
import logging

# Configure logging
setup_logging(log_level='INFO', log_format='json')

# Set correlation ID
set_correlation_id('run-123')

# Log events
logger = logging.getLogger(__name__)
log_event(
    logger, 'info', 'step_start',
    'Starting workflow step',
    run_id='run-123',
    step_id='step-1',
    agent_name='ResearchAgent'
)
```

## Integration with Log Aggregation

The JSON format is designed to work with:

- Elasticsearch/Kibana
- CloudWatch Logs
- Datadog
- Splunk
- Any JSON-based log aggregation system

All fields are indexable and searchable for:

- Tracking workflow execution
- Debugging by correlation ID
- Performance analysis
- System health monitoring

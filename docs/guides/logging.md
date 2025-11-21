# Structured Logging Utility

This module provides structured logging capabilities with JSON formatting and correlation ID support for the Centralized Executor and HTTP-Kafka Bridge.

## Features

- **Structured JSON Logging**: All logs are formatted as JSON objects for easy parsing and analysis
- **Correlation ID Support**: Automatically includes correlation IDs in all log messages within an execution context
- **Text Format Option**: Human-readable text format for local development
- **Key Event Logging**: Convenience function for logging important events with consistent structure

## Configuration

Configure logging via environment variables:

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log format: json or text
LOG_FORMAT=json
```

## Usage

### Basic Setup

```python
from src.utils.logging import setup_logging

# Configure logging at application startup
setup_logging(log_level='INFO', log_format='json')
```

### Setting Correlation ID

```python
from src.utils.logging import set_correlation_id

# Set correlation ID for the current execution context
set_correlation_id('run-123-correlation-456')

# All subsequent logs in this context will include the correlation ID
```

### Logging Events

```python
from src.utils.logging import log_event
import logging

logger = logging.getLogger(__name__)

# Log a structured event
log_event(
    logger, 'info', 'step_start',
    "Starting workflow step",
    run_id='run-123',
    step_id='step-1',
    agent_name='ResearchAgent'
)
```

### Standard Logging

You can also use standard Python logging, and the correlation ID will be automatically included:

```python
import logging

logger = logging.getLogger(__name__)

# Standard logging calls work as expected
logger.info("Processing task", extra={'task_id': 'task-123'})
logger.error("Task failed", extra={'error': 'Connection timeout'})
```

## JSON Log Format

Each log entry is formatted as a JSON object with the following fields:

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

## Event Types

The following event types are used throughout the system:

### Executor Events
- `executor_start`: Executor initialization
- `config_loaded`: Configuration loaded
- `workflow_plan_loaded`: Workflow plan parsed and loaded
- `step_start`: Workflow step execution started
- `agent_call`: Agent task published to Kafka
- `step_complete`: Workflow step completed successfully
- `step_failed`: Workflow step failed
- `step_error`: Critical error during step execution

### Bridge Events
- `bridge_start`: Bridge initialization
- `task_received`: Task message received from Kafka
- `agent_metadata_fetch`: Fetching agent metadata from registry
- `agent_invoke_start`: Starting agent invocation
- `http_call`: Making HTTP call to agent
- `http_success`: HTTP call succeeded
- `agent_success`: Agent completed successfully
- `agent_error`: Agent invocation failed
- `task_error`: Error handling task message

## Text Format

When using text format (`LOG_FORMAT=text`), logs are formatted as:

```
2024-01-15 10:30:45 - src.executor.centralized_executor - INFO - [run-123-correlation-456] - Starting workflow step
```

## Best Practices

1. **Always set correlation ID**: Set the correlation ID at the start of each workflow run or task processing
2. **Use log_event for key events**: Use the `log_event` function for important events to ensure consistent structure
3. **Include relevant context**: Add extra fields to provide context for debugging and analysis
4. **Use appropriate log levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages for recoverable issues
   - ERROR: Error messages for failures
   - CRITICAL: Critical errors that may cause system failure

## Integration with Log Aggregation

The JSON format is designed to work seamlessly with log aggregation systems like:

- **Elasticsearch/Kibana**: Index logs for search and visualization
- **CloudWatch Logs**: AWS log aggregation and monitoring
- **Datadog**: Application performance monitoring
- **Splunk**: Log analysis and monitoring

All fields in the JSON logs can be indexed and searched, making it easy to:
- Track workflow execution across services
- Debug failures by correlation ID
- Analyze performance metrics
- Monitor system health

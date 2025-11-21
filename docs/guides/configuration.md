# Configuration Management

This module provides centralized configuration management using `pydantic-settings` for the Centralized Executor and HTTP-Kafka Bridge components.

## Features

- **Type-safe configuration**: All configuration values are validated using Pydantic models
- **Environment variable loading**: Automatically loads from environment variables
- **`.env` file support**: Can load from `.env` files for local development
- **Validation**: Comprehensive validation for all configuration values
- **Nested configuration**: Organized into logical sections (Kafka, Database, etc.)

## Usage

### Basic Usage

```python
from src.config import Config

# Load configuration from environment variables
config = Config()

# Access configuration values
kafka_brokers = config.kafka.brokers
database_url = config.database.url
agent_registry_url = config.agent_registry.url
```

### Loading from .env File

```python
from src.config import load_config

# Load from specific .env file
config = load_config(env_file='.env.local')
```

### Validating Executor Configuration

```python
from src.config import Config

config = Config()

# Validate that required executor config is present
try:
    config.validate_executor_config()
except ValueError as e:
    print(f"Missing required configuration: {e}")
```

## Configuration Sections

### Kafka Configuration

Environment variables:
- `KAFKA_BROKERS` (default: `localhost:9092`) - Comma-separated Kafka broker addresses
- `KAFKA_CLIENT_ID` (default: `executor-service`) - Kafka client identifier
- `KAFKA_GROUP_ID` (default: `executor-group`) - Kafka consumer group ID
- `KAFKA_TASKS_TOPIC` (default: `orchestrator.tasks.http`) - Topic for agent tasks
- `KAFKA_RESULTS_TOPIC` (default: `results.topic`) - Topic for agent results
- `KAFKA_MONITORING_TOPIC` (default: `workflow.monitoring.updates`) - Topic for monitoring

```python
config.kafka.brokers
config.kafka.client_id
config.kafka.tasks_topic
```

### Database Configuration

Environment variables:
- `DATABASE_URL` (required) - PostgreSQL connection URL (must start with `postgresql://` or `postgres://`)
- `DATABASE_POOL_SIZE` (default: `10`) - Connection pool size
- `DATABASE_MAX_OVERFLOW` (default: `20`) - Max connections beyond pool size

```python
config.database.url
config.database.pool_size
```

### Agent Registry Configuration

Environment variables:
- `AGENT_REGISTRY_URL` (required) - Base URL of Agent Registry service (must start with `http://` or `https://`)
- `AGENT_REGISTRY_CACHE_TTL` (default: `300`) - Cache TTL in seconds

```python
config.agent_registry.url
config.agent_registry.cache_ttl_seconds
```

### Executor Configuration

Environment variables:
- `RUN_ID` (optional) - Unique identifier for workflow run
- `WORKFLOW_PLAN` (optional) - JSON string or file path to workflow plan
- `WORKFLOW_INPUT` (optional) - JSON string or file path to initial input

```python
config.executor.run_id
config.executor.workflow_plan
config.executor.workflow_input
```

### Bridge Configuration

Environment variables:
- `HTTP_TIMEOUT_MS` (default: `30000`) - HTTP timeout in milliseconds
- `MAX_RETRIES` (default: `3`) - Maximum retry attempts
- `INITIAL_RETRY_DELAY_MS` (default: `1000`) - Initial retry delay in milliseconds
- `MAX_RETRY_DELAY_MS` (default: `30000`) - Maximum retry delay in milliseconds
- `BACKOFF_MULTIPLIER` (default: `2.0`) - Exponential backoff multiplier
- `WORKER_CONCURRENCY` (default: `10`) - Number of concurrent workers

```python
config.bridge.http_timeout_ms
config.bridge.max_retries
config.get_http_timeout_seconds()  # Helper to get timeout in seconds
```

### Logging Configuration

Environment variables:
- `LOG_LEVEL` (default: `INFO`) - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT` (default: `text`) - Log format (text or json)

```python
config.logging.level
config.logging.format
```

### S3 Configuration (Optional)

Environment variables:
- `S3_BUCKET` (optional) - S3 bucket name for large payloads
- `AWS_REGION` (default: `us-east-1`) - AWS region

```python
config.s3.bucket
config.s3.region
```

## Example: Centralized Executor

```python
from src.config import Config
from src.executor.centralized_executor import CentralizedExecutor

# Load configuration
config = Config()

# Validate executor-specific config
config.validate_executor_config()

# Create executor with config values
executor = CentralizedExecutor(
    run_id=config.executor.run_id,
    workflow_plan=workflow_plan,
    initial_input=initial_input,
    kafka_bootstrap_servers=config.kafka.brokers,
    database_url=config.database.url,
    agent_registry_url=config.agent_registry.url,
    kafka_client_id=config.kafka.client_id,
    kafka_group_id=config.kafka.group_id
)
```

## Example: External Agent Executor (Bridge)

```python
from src.config import Config
from src.bridge.external_agent_executor import ExternalAgentExecutor

# Load configuration
config = Config()

# Create bridge with config values
executor = ExternalAgentExecutor(
    kafka_bootstrap_servers=config.kafka.brokers,
    agent_registry_url=config.agent_registry.url,
    tasks_topic=config.kafka.tasks_topic,
    results_topic=config.kafka.results_topic,
    consumer_group_id=config.kafka.group_id,
    http_timeout_seconds=int(config.get_http_timeout_seconds()),
    max_retries=config.bridge.max_retries
)
```

## Validation

The configuration system provides comprehensive validation:

1. **Required fields**: `DATABASE_URL` and `AGENT_REGISTRY_URL` must be provided
2. **URL format**: Database and Agent Registry URLs must have correct prefixes
3. **Positive values**: Numeric values like timeouts and retries must be positive
4. **Valid enums**: Log level must be one of the valid logging levels
5. **Backoff multiplier**: Must be >= 1.0

If validation fails, a `ValidationError` will be raised with details about the invalid fields.

## Testing

```python
import os
from src.config import Config

# Set required environment variables
os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost:5432/testdb'
os.environ['AGENT_REGISTRY_URL'] = 'http://localhost:8080'

# Load and test configuration
config = Config()
assert config.database.url == 'postgresql://user:pass@localhost:5432/testdb'
assert config.kafka.brokers == 'localhost:9092'
assert config.get_http_timeout_seconds() == 30.0
```

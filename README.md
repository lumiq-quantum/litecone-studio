# Centralized Executor and HTTP-Kafka Bridge

Multi-agent orchestration platform components for executing workflows through asynchronous Kafka communication.

## Components

- **Centralized Executor**: Ephemeral orchestrator that manages workflow execution
- **External Agent Executor (HTTP-Kafka Bridge)**: Adapter service translating Kafka events to JSON-RPC 2.0 HTTP calls

## Project Structure

```
.
├── src/
│   ├── executor/          # Centralized Executor implementation
│   ├── bridge/            # HTTP-Kafka Bridge implementation
│   ├── models/            # Data models and schemas
│   ├── database/          # Database models and connection
│   ├── kafka_client/      # Kafka producer/consumer wrappers
│   ├── agent_registry/    # Agent Registry client
│   └── utils/             # Utility functions (including logging)
├── examples/              # Example scripts and configurations
├── docker-compose.yml     # Local development environment
├── requirements.txt       # Python dependencies
└── .env.example          # Configuration template

```

## Setup

1. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start local infrastructure (Kafka + PostgreSQL):
   ```bash
   docker-compose up -d zookeeper kafka postgres
   ```

## Running Services

### Centralized Executor
```bash
docker-compose --profile executor up
```

### HTTP-Kafka Bridge
```bash
docker-compose --profile bridge up
```

## Logging and Observability

The system uses structured JSON logging with correlation ID support for comprehensive observability.

### Configuration

Configure logging via environment variables:

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log format: json (structured) or text (human-readable)
LOG_FORMAT=json
```

### Features

- **Structured JSON Logs**: All logs formatted as JSON for easy parsing
- **Correlation IDs**: Automatic correlation ID tracking across all operations
- **Key Event Logging**: Standardized event types for workflow tracking
- **Text Format Option**: Human-readable format for local development

### Example JSON Log

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

### Event Types

Key events logged by the system:

**Executor Events:**
- `executor_start`: Executor initialization
- `step_start`: Step execution started
- `agent_call`: Agent task published
- `step_complete`: Step completed successfully
- `step_failed`: Step execution failed

**Bridge Events:**
- `bridge_start`: Bridge initialization
- `task_received`: Task received from Kafka
- `http_call`: HTTP call to agent
- `agent_success`: Agent completed successfully
- `agent_error`: Agent invocation failed

See [src/utils/logging_README.md](src/utils/logging_README.md) for detailed documentation.

### Example

Run the logging example to see structured logging in action:

```bash
PYTHONPATH=. python3 examples/logging_example.py
```

## Documentation

### Core Documentation
- **[Workflow JSON Format](WORKFLOW_FORMAT.md)** - Complete specification for defining workflows
- **[A2A Agent Interface](A2A_AGENT_INTERFACE.md)** - JSON-RPC 2.0 protocol specification for implementing agents
- **[Logging Guide](src/utils/logging_README.md)** - Structured logging and observability

### API Documentation
- **[API Documentation](API_DOCUMENTATION.md)** - Comprehensive REST API documentation
- **[OpenAPI Specification](openapi.yaml)** - Swagger/OpenAPI 3.0 spec
- **[Swagger Guide](SWAGGER_GUIDE.md)** - How to use Swagger UI with the API

### Migration and Deployment
- **[Migration Guide](MIGRATION_GUIDE.md)** - Migrate from CLI to API-based workflow execution
- **[Migration Quick Reference](MIGRATION_QUICK_REFERENCE.md)** - Quick commands for migration
- **[Migration Scripts](scripts/README.md)** - Automated migration tools

### Examples and Testing
- **[Quick Start Guide](QUICKSTART.md)** - Get started in 2 minutes
- **[Manual Testing Guide](MANUAL_TESTING_GUIDE.md)** - Step-by-step testing scenarios
- **[Testing Architecture](TESTING_ARCHITECTURE.md)** - How mock agents work
- **[Examples README](examples/README.md)** - Testing tools and example workflows

## Development

This project uses Python 3.11+ with async/await patterns for concurrent operations.

## License

MIT

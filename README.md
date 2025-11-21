# Centralized Executor and HTTP-Kafka Bridge

Multi-agent orchestration platform components for executing workflows through asynchronous Kafka communication.

## Components

- **Centralized Executor**: Ephemeral orchestrator that manages workflow execution
- **External Agent Executor (HTTP-Kafka Bridge)**: Adapter service translating Kafka events to JSON-RPC 2.0 HTTP calls
- **Parallel Executor**: Concurrent step execution with configurable parallelism limits

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

## Features

### Parallel Execution
Execute multiple workflow steps concurrently with configurable parallelism limits. See [docs/parallel_execution.md](docs/parallel_execution.md) for details.

- Concurrent execution using asyncio
- Configurable max parallelism
- Result aggregation from all parallel steps
- Partial failure handling

### Conditional Logic
Make dynamic decisions in workflows based on runtime data. See [docs/conditional_logic.md](docs/conditional_logic.md) for details.

- Comparison operators (==, !=, >, <, >=, <=)
- Logical operators (and, or, not)
- Membership tests (in, not in, contains)
- JSONPath support for nested data access
- Branch execution based on conditions

### Loop Execution
Iterate over collections with sequential or parallel execution. See [docs/loop_execution.md](docs/loop_execution.md) for details.

- Sequential and parallel execution modes
- Configurable parallelism limits
- Error handling policies (stop, continue, collect)
- Iteration context variables (item, index, total)
- Maximum iteration limits

### Fork-Join Pattern
Split execution into multiple named parallel branches with configurable join policies. See [docs/fork_join_pattern.md](docs/fork_join_pattern.md) for details.

- Named parallel branches with sequential steps
- Multiple join policies (ALL, ANY, MAJORITY, N_OF_M)
- Per-branch and global timeout configuration
- Branch result aggregation by name
- Complex parallel processing patterns

### Circuit Breaker
Prevent cascading failures with automatic circuit breaker pattern. See [docs/circuit_breaker.md](docs/circuit_breaker.md) and [usage guide](examples/CIRCUIT_BREAKER_USAGE_GUIDE.md) for details.

- Three-state circuit breaker (CLOSED, OPEN, HALF_OPEN)
- Dual threshold detection (consecutive failures and failure rate)
- Automatic recovery testing
- Distributed state management via Redis
- Per-agent configuration overrides
- Comprehensive monitoring and logging
- **Transparent to workflows** - Configure at agent level, works automatically

## Documentation

### Core Documentation
- **[Workflow JSON Format](WORKFLOW_FORMAT.md)** - Complete specification for defining workflows
- **[A2A Agent Interface](A2A_AGENT_INTERFACE.md)** - JSON-RPC 2.0 protocol specification for implementing agents
- **[Logging Guide](src/utils/logging_README.md)** - Structured logging and observability
- **[Parallel Execution](docs/parallel_execution.md)** - Concurrent step execution guide
- **[Conditional Logic](docs/conditional_logic.md)** - Dynamic workflow branching guide
- **[Loop Execution](docs/loop_execution.md)** - Iterate over collections guide
- **[Fork-Join Pattern](docs/fork_join_pattern.md)** - Advanced parallel branching guide
- **[Circuit Breaker](docs/circuit_breaker.md)** - Resilience pattern for failing agents
- **[Circuit Breaker Deployment](CIRCUIT_BREAKER_DEPLOYMENT.md)** - Deployment and configuration guide

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
- **[Circuit Breaker Usage Guide](examples/CIRCUIT_BREAKER_USAGE_GUIDE.md)** - How to use circuit breaker with workflows
- **[Circuit Breaker Testing](CIRCUIT_BREAKER_TEST_QUICK_START.md)** - Test circuit breaker functionality

## Development

This project uses Python 3.11+ with async/await patterns for concurrent operations.

## License

MIT

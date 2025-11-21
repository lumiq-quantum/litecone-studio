# Centralized Executor and HTTP-Kafka Bridge

Multi-agent orchestration platform components for executing workflows through asynchronous Kafka communication.

> 📌 **Quick Links:** [Quick Reference](QUICK_REFERENCE.md) | [Documentation Index](docs/README.md) | [Project Structure](PROJECT_STRUCTURE.md)

## Components

- **Centralized Executor**: Ephemeral orchestrator that manages workflow execution
- **External Agent Executor (HTTP-Kafka Bridge)**: Adapter service translating Kafka events to JSON-RPC 2.0 HTTP calls
- **Parallel Executor**: Concurrent step execution with configurable parallelism limits

## Project Structure

```
.
├── src/                   # Source code
│   ├── executor/          # Centralized Executor implementation
│   ├── bridge/            # HTTP-Kafka Bridge implementation
│   ├── models/            # Data models and schemas
│   ├── database/          # Database models and connection
│   ├── kafka_client/      # Kafka producer/consumer wrappers
│   ├── agent_registry/    # Agent Registry client
│   └── utils/             # Utility functions (including logging)
├── api/                   # REST API service
├── workflow-ui/           # React-based UI
├── docs/                  # All documentation
│   ├── api/               # API documentation
│   ├── deployment/        # Deployment guides
│   ├── testing/           # Testing documentation
│   ├── guides/            # User guides
│   ├── architecture/      # Architecture docs
│   ├── features/          # Feature documentation
│   └── ui/                # UI documentation
├── tests/                 # All test files
├── scripts/               # Shell scripts and utilities
├── examples/              # Example workflows and configurations
├── migrations/            # Database migrations
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

See [docs/guides/logging.md](docs/guides/logging.md) for detailed documentation.

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

All documentation is now organized in the [`docs/`](docs/) directory. See [docs/README.md](docs/README.md) for the complete documentation index.

### Quick Links

**Getting Started:**
- [Quick Start Guide](docs/guides/QUICKSTART.md) - Get started in 2 minutes
- [Development Guide](docs/guides/DEVELOPMENT.md) - Development setup and workflow
- [Workflow Format](docs/guides/WORKFLOW_FORMAT.md) - Complete workflow specification

**Features:**
- [Parallel Execution](docs/features/parallel_execution.md) - Concurrent step execution
- [Conditional Logic](docs/features/conditional_logic.md) - Dynamic workflow branching
- [Loop Execution](docs/features/loop_execution.md) - Iterate over collections
- [Fork-Join Pattern](docs/features/fork_join_pattern.md) - Advanced parallel branching
- [Circuit Breaker](docs/features/circuit_breaker.md) - Resilience pattern for failing agents

**API:**
- [API Documentation](docs/api/API_DOCUMENTATION.md) - Comprehensive REST API docs
- [A2A Agent Interface](docs/api/A2A_AGENT_INTERFACE.md) - JSON-RPC 2.0 protocol specification
- [Swagger Guide](docs/api/SWAGGER_GUIDE.md) - Using Swagger UI

**Deployment:**
- [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md) - Production deployment
- [Migration Guide](docs/deployment/MIGRATION_GUIDE.md) - Migration procedures
- [Circuit Breaker Deployment](docs/deployment/CIRCUIT_BREAKER_DEPLOYMENT.md) - Circuit breaker setup

**Testing:**
- [Testing Architecture](docs/testing/TESTING_ARCHITECTURE.md) - How testing works
- [Manual Testing Guide](docs/testing/MANUAL_TESTING_GUIDE.md) - Step-by-step testing
- [Test Files](tests/README.md) - All test files and how to run them

## Development

This project uses Python 3.11+ with async/await patterns for concurrent operations.

## License

MIT

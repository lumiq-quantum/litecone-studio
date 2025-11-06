# External Agent Executor (HTTP-Kafka Bridge)

The External Agent Executor is a service that bridges the gap between the asynchronous Kafka-based orchestration platform and synchronous HTTP-based external agents.

## Overview

This service:
- Consumes agent tasks from the `orchestrator.tasks.http` Kafka topic
- Queries the Agent Registry to get agent endpoint URLs and configuration
- Makes HTTP POST requests to external agents following the A2A protocol
- Implements retry logic with exponential backoff for transient failures
- Publishes agent results back to the `results.topic` Kafka topic

## Running the Bridge

### Using Python directly

```bash
# Set environment variables
export KAFKA_BROKERS=localhost:9092
export AGENT_REGISTRY_URL=http://localhost:8080
export TASKS_TOPIC=orchestrator.tasks.http
export RESULTS_TOPIC=results.topic
export CONSUMER_GROUP_ID=external-agent-executor-group
export HTTP_TIMEOUT_SECONDS=30
export MAX_RETRIES=3

# Run the bridge
python -m src.bridge
```

### Using Docker

```bash
docker build -f Dockerfile.bridge -t external-agent-executor .
docker run -e KAFKA_BROKERS=kafka:9092 \
           -e AGENT_REGISTRY_URL=http://agent-registry:8080 \
           external-agent-executor
```

### Using Docker Compose

```bash
docker-compose up bridge
```

## Configuration

The bridge is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_BROKERS` | Comma-separated list of Kafka broker addresses | `localhost:9092` |
| `AGENT_REGISTRY_URL` | Base URL of the Agent Registry service | `http://localhost:8080` |
| `TASKS_TOPIC` | Kafka topic to consume agent tasks from | `orchestrator.tasks.http` |
| `RESULTS_TOPIC` | Kafka topic to publish agent results to | `results.topic` |
| `CONSUMER_GROUP_ID` | Consumer group ID for Kafka consumer | `external-agent-executor-group` |
| `HTTP_TIMEOUT_SECONDS` | Default timeout for HTTP requests to agents | `30` |
| `MAX_RETRIES` | Default maximum number of retry attempts | `3` |

## A2A Protocol

The bridge communicates with external agents using the A2A (Agent-to-Agent) protocol over HTTP.

### Request Format

```json
{
  "task_id": "task-123",
  "input": {
    "query": "What is the weather?",
    "context": {...}
  }
}
```

### Response Format

```json
{
  "task_id": "task-123",
  "status": "success",
  "output": {
    "result": "The weather is sunny",
    "confidence": 0.95
  },
  "error": null
}
```

## Retry Logic

The bridge implements exponential backoff retry logic for:
- Network errors (connection failures, timeouts)
- 5xx server errors
- 429 Too Many Requests

Non-retriable errors (4xx client errors except 429) fail immediately.

## Graceful Shutdown

The bridge handles SIGINT and SIGTERM signals for graceful shutdown:
1. Stops consuming new tasks
2. Waits for in-flight tasks to complete (with timeout)
3. Closes all connections (Kafka, HTTP, Agent Registry)

## Architecture

```
[Kafka: orchestrator.tasks.http]
           ↓
    [Task Consumer]
           ↓
   [Agent Registry Query]
           ↓
    [HTTP POST to Agent]
           ↓
   [Retry with Backoff]
           ↓
   [Response Handler]
           ↓
[Kafka: results.topic]
```

## Logging

The bridge uses structured logging with the following log levels:
- `INFO`: Normal operation (task received, agent invoked, result published)
- `WARNING`: Retriable errors, retry attempts
- `ERROR`: Non-retriable errors, failures
- `DEBUG`: Detailed information (cache hits, authentication details)

All logs include contextual information:
- `run_id`: Workflow run identifier
- `task_id`: Task identifier
- `agent_name`: Name of the agent being invoked
- `correlation_id`: Request-response correlation ID

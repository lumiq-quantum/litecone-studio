# API-Executor Integration

This document describes the integration between the Workflow Management API and the Centralized Executor service.

## Overview

The integration enables the API to trigger workflow executions that are processed by the executor service. The communication happens through Kafka, with the database serving as the shared state store.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Management API                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/workflows/{id}/execute                 │  │
│  │  - Creates run record in database (PENDING)          │  │
│  │  - Publishes execution request to Kafka              │  │
│  │  - Returns run_id immediately                        │  │
│  └────────────────────┬─────────────────────────────────┘  │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        ▼ Kafka Topic: workflow.execution.requests
                        │
┌───────────────────────┼─────────────────────────────────────┐
│                       │      Execution Consumer Service     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │  Consumes execution requests from Kafka              │  │
│  │  - Validates and parses requests                     │  │
│  │  - Spawns CentralizedExecutor instances              │  │
│  │  - Manages executor lifecycle                        │  │
│  └────────────────────┬─────────────────────────────────┘  │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        ▼ Spawns
                        │
┌───────────────────────┼─────────────────────────────────────┐
│                       │      Centralized Executor           │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │  Executes workflow steps                             │  │
│  │  - Updates run status in database (RUNNING)          │  │
│  │  - Publishes tasks to agents via Kafka               │  │
│  │  - Consumes results from agents                      │  │
│  │  - Updates run status on completion (COMPLETED)      │  │
│  │  - Updates run status on failure (FAILED)            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼ Writes to
                        │
┌───────────────────────┼─────────────────────────────────────┐
│                  PostgreSQL Database                        │
│  - workflow_runs (shared state)                             │
│  - step_executions (execution history)                      │
└─────────────────────────────────────────────────────────────┘
```

## Message Flow

### 1. Execution Request (API → Executor)

**Topic:** `workflow.execution.requests`

**Message Format:**
```json
{
  "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
  "workflow_plan": {
    "workflow_id": "wf-data-pipeline-1",
    "name": "data-pipeline",
    "version": "1",
    "start_step": "extract",
    "steps": {
      "extract": {
        "id": "extract",
        "agent_name": "data-extractor",
        "next_step": "transform",
        "input_mapping": {
          "source": "$.workflow_input.source_url"
        }
      },
      "transform": {
        "id": "transform",
        "agent_name": "data-transformer",
        "next_step": null,
        "input_mapping": {
          "data": "$.extract.output_data"
        }
      }
    }
  },
  "input_data": {
    "source_url": "s3://bucket/data.csv"
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "message_type": "execution_request"
}
```

### 2. Cancellation Request (API → Executor)

**Topic:** `workflow.cancellation.requests`

**Message Format:**
```json
{
  "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
  "cancelled_by": "user@example.com",
  "reason": "User requested cancellation",
  "timestamp": "2024-01-15T10:35:00.000Z",
  "message_type": "cancellation_request"
}
```

## Database Schema

### workflow_runs Table

The `workflow_runs` table serves as the shared state between the API and executor:

```sql
CREATE TABLE workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    workflow_name VARCHAR(255) NOT NULL,
    workflow_definition_id VARCHAR(255),  -- UUID reference to workflow_definitions
    status VARCHAR(50) NOT NULL,  -- PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    input_data JSONB,
    error_message TEXT,
    triggered_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    cancelled_by VARCHAR(255)
);
```

**Status Flow:**
1. **PENDING**: Created by API when execution is triggered
2. **RUNNING**: Updated by executor when workflow starts
3. **COMPLETED**: Updated by executor when workflow finishes successfully
4. **FAILED**: Updated by executor when workflow fails
5. **CANCELLED**: Updated by API when user cancels, or by executor when cancellation is processed

### step_executions Table

The `step_executions` table tracks individual step executions:

```sql
CREATE TABLE step_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step_execution_id VARCHAR(255) UNIQUE NOT NULL,
    run_id VARCHAR(255) NOT NULL,
    step_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- RUNNING, COMPLETED, FAILED
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

## Components

### 1. Workflow Management API

**Location:** `api/`

**Responsibilities:**
- Expose REST endpoints for workflow management
- Create workflow run records in database
- Publish execution requests to Kafka
- Publish cancellation requests to Kafka
- Query run status from database

**Key Services:**
- `api/services/execution.py`: ExecutionService
- `api/services/kafka.py`: KafkaService

### 2. Execution Consumer Service

**Location:** `src/executor/execution_consumer.py`

**Responsibilities:**
- Consume execution requests from Kafka
- Validate and parse requests
- Spawn CentralizedExecutor instances
- Manage executor lifecycle
- Handle cancellation requests

**Key Features:**
- Asynchronous processing of multiple workflows
- Graceful shutdown handling
- Error recovery and logging

### 3. Centralized Executor

**Location:** `src/executor/centralized_executor.py`

**Responsibilities:**
- Execute workflow steps sequentially
- Update run status in database
- Publish tasks to agents via Kafka
- Consume results from agents
- Handle step failures and retries
- Support workflow resumption from last completed step

**Key Features:**
- Stateful execution with database persistence
- Retry logic with exponential backoff
- Monitoring updates via Kafka

## Deployment

### Docker Compose

The integration uses Docker Compose profiles for flexible deployment:

```bash
# Start core services (Kafka, PostgreSQL)
docker-compose up -d kafka postgres

# Start API service
docker-compose --profile api up -d api

# Start execution consumer service
docker-compose --profile consumer up -d execution-consumer

# Start bridge service (for HTTP agents)
docker-compose --profile bridge up -d bridge

# Start all services
docker-compose --profile api --profile consumer --profile bridge up -d
```

### Environment Variables

**API Service (.env.api):**
```bash
DATABASE_URL=postgresql://workflow_user:workflow_pass@postgres:5432/workflow_db
KAFKA_BROKERS=kafka:29092
KAFKA_EXECUTION_TOPIC=workflow.execution.requests
KAFKA_CANCELLATION_TOPIC=workflow.cancellation.requests
```

**Execution Consumer Service (.env):**
```bash
KAFKA_BROKERS=kafka:29092
DATABASE_URL=postgresql://workflow_user:workflow_pass@postgres:5432/workflow_db
AGENT_REGISTRY_URL=http://agent-registry:8080
KAFKA_GROUP_ID=execution-consumer-group
KAFKA_EXECUTION_TOPIC=workflow.execution.requests
KAFKA_CANCELLATION_TOPIC=workflow.cancellation.requests
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Testing

### Integration Test

Run the integration test to verify the complete flow:

```bash
# Ensure services are running
docker-compose up -d kafka postgres
docker-compose --profile consumer up -d execution-consumer

# Run integration test
python test_api_executor_integration.py
```

The test verifies:
1. Execution requests are consumed from Kafka
2. Executor processes workflows
3. Run status is written back to database
4. Step executions are recorded

### Manual Testing

1. **Create a workflow via API:**
```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-workflow",
    "description": "Test workflow",
    "start_step": "step1",
    "steps": {
      "step1": {
        "id": "step1",
        "agent_name": "test-agent",
        "next_step": null,
        "input_mapping": {
          "input": "$.workflow_input.value"
        }
      }
    }
  }'
```

2. **Trigger execution:**
```bash
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "value": "test"
    }
  }'
```

3. **Monitor execution:**
```bash
# Get run status
curl http://localhost:8000/api/v1/runs/{run_id}

# Get step executions
curl http://localhost:8000/api/v1/runs/{run_id}/steps
```

4. **Cancel execution:**
```bash
curl -X POST http://localhost:8000/api/v1/runs/{run_id}/cancel
```

## Error Handling

### Kafka Publishing Failures

If the API fails to publish to Kafka:
- Run record is created with PENDING status
- Error message is stored in `error_message` field
- Execution consumer can pick up PENDING runs on startup (future enhancement)

### Executor Failures

If the executor fails during execution:
- Run status is updated to FAILED
- Error message is stored in database
- Step executions show which step failed
- Workflow can be retried via API

### Database Connection Failures

If the executor loses database connection:
- Executor attempts to reconnect
- If reconnection fails, executor shuts down
- Run remains in RUNNING state
- Manual intervention required to mark as FAILED

## Monitoring

### Kafka Topics

Monitor these topics for execution flow:
- `workflow.execution.requests`: Execution requests from API
- `workflow.cancellation.requests`: Cancellation requests from API
- `workflow.monitoring.updates`: Real-time execution updates
- `orchestrator.tasks.http`: Tasks sent to agents
- `results.topic`: Results from agents

### Database Queries

Monitor execution status:

```sql
-- Active runs
SELECT run_id, workflow_name, status, created_at
FROM workflow_runs
WHERE status IN ('PENDING', 'RUNNING')
ORDER BY created_at DESC;

-- Failed runs
SELECT run_id, workflow_name, error_message, created_at
FROM workflow_runs
WHERE status = 'FAILED'
ORDER BY created_at DESC
LIMIT 10;

-- Step execution statistics
SELECT agent_name, status, COUNT(*) as count
FROM step_executions
GROUP BY agent_name, status
ORDER BY agent_name, status;
```

### Logs

Check logs for debugging:

```bash
# API logs
docker-compose logs -f api

# Execution consumer logs
docker-compose logs -f execution-consumer

# All logs
docker-compose logs -f
```

## Requirements Satisfied

This integration satisfies the following requirements:

- **11.1**: Executor consumes execution requests from API-published Kafka messages
  - ✓ ExecutionConsumer listens to `workflow.execution.requests` topic
  - ✓ Validates and parses execution requests
  - ✓ Spawns CentralizedExecutor instances

- **11.2**: Executor writes run status back to database
  - ✓ Updates status to RUNNING when execution starts
  - ✓ Updates status to COMPLETED when workflow finishes
  - ✓ Updates status to FAILED when workflow fails
  - ✓ Records step executions in database

- **11.3**: Executor records errors and marks run as failed
  - ✓ Captures error messages from failed steps
  - ✓ Updates run status to FAILED
  - ✓ Stores error_message in database

- **11.5**: Queue execution requests when executor is unavailable
  - ✓ Kafka provides message persistence
  - ✓ Messages are queued until consumer is available
  - ✓ Consumer processes messages in order

## Future Enhancements

1. **Automatic Retry of PENDING Runs**
   - Consumer checks for PENDING runs on startup
   - Republishes execution requests for stuck runs

2. **Executor Health Monitoring**
   - Periodic health checks for active executors
   - Automatic restart of failed executors

3. **Execution Metrics**
   - Prometheus metrics for execution rates
   - Success/failure rates by workflow
   - Execution duration histograms

4. **Distributed Execution**
   - Multiple consumer instances for scalability
   - Load balancing across executors
   - Partition-based workflow assignment

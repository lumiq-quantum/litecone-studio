# Orchestrator Architecture Summary

## Overview

Your workflow orchestration system consists of **4 main components** working together to execute multi-agent workflows:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Management API                       │
│                      (FastAPI Backend)                           │
│  - Agent Management                                              │
│  - Workflow Definition Management                                │
│  - Execution Triggering & Monitoring                             │
└────────────────────────┬────────────────────────────────────────┘
                         │ Publishes to Kafka
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Execution Consumer Service                     │
│  - Consumes execution requests from Kafka                        │
│  - Spawns CentralizedExecutor instances per workflow run         │
│  - Manages executor lifecycle                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ Spawns
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Centralized Executor (Ephemeral)                │
│  - One instance per workflow run                                 │
│  - Orchestrates step-by-step execution                           │
│  - Publishes tasks to Kafka                                      │
│  - Consumes results from Kafka                                   │
│  - Persists state to PostgreSQL                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ Tasks via Kafka
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              External Agent Executor (HTTP-Kafka Bridge)         │
│  - Stateless pool of workers                                     │
│  - Consumes tasks from Kafka                                     │
│  - Makes HTTP calls to external agents (JSON-RPC 2.0)            │
│  - Publishes results back to Kafka                               │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/JSON-RPC 2.0
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Agents                             │
│  - Implement JSON-RPC 2.0 protocol                               │
│  - Perform specific tasks (data fetching, processing, etc.)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Workflow Management API (`api/`)

**Purpose**: REST API for managing the entire workflow system

**Key Files**:
- `api/main.py` - FastAPI application
- `api/services/execution.py` - Execution service (trigger, retry, cancel)
- `api/routes/` - API endpoints
- `api/repositories/` - Database access layer

**Responsibilities**:
- Agent CRUD operations
- Workflow definition CRUD operations
- Trigger workflow execution → publishes to Kafka
- Retry failed workflows
- Cancel running workflows
- Query run status and step executions
- Audit logging

**Database Tables**:
- `agents` - Agent metadata (URL, auth, retry config, protocol)
- `workflow_definitions` - Workflow templates
- `workflow_runs` - Execution instances
- `step_executions` - Individual step results
- `audit_logs` - Action history

**Kafka Topics (Produces)**:
- `workflow.execution.requests` - Execution requests
- `workflow.cancellation.requests` - Cancellation requests

---

### 2. Execution Consumer Service (`src/executor/execution_consumer.py`)

**Purpose**: Bridge between API and executor instances

**Key Responsibilities**:
- Consumes execution requests from Kafka
- Spawns `CentralizedExecutor` instances (one per workflow run)
- Manages executor lifecycle (start, monitor, cleanup)
- Handles cancellation requests
- Graceful shutdown with active executor tracking

**Process Model**:
- Long-running service
- Maintains pool of active executors as asyncio tasks
- Each executor runs independently in its own task

**Configuration**:
```bash
KAFKA_BROKERS=localhost:9092
KAFKA_GROUP_ID=execution-consumer-group
DATABASE_URL=postgresql://...
AGENT_REGISTRY_URL=http://localhost:8000
KAFKA_EXECUTION_TOPIC=workflow.execution.requests
KAFKA_CANCELLATION_TOPIC=workflow.cancellation.requests
```

---

### 3. Centralized Executor (`src/executor/centralized_executor.py`)

**Purpose**: Ephemeral orchestrator for a single workflow run

**Lifecycle**:
1. **Spawned** by Execution Consumer per workflow run
2. **Initializes** Kafka connections, database, agent registry client
3. **Loads** existing execution state (for replay/resume)
4. **Executes** workflow steps sequentially
5. **Terminates** when workflow completes or fails

**Key Features**:

#### Sequential Execution
- Follows `start_step` → `next_step` linked list structure
- Executes one step at a time
- Waits for each step to complete before moving to next

#### State Persistence
- Saves step input/output to PostgreSQL after each step
- Enables resume from last completed step on failure
- Idempotent execution (skips already-completed steps)

#### Step Execution Flow
```
1. Resolve input data using input_mapping
2. Create step_execution record (status: RUNNING)
3. Publish monitoring update (RUNNING)
4. Publish AgentTask to orchestrator.tasks.http
5. Wait for AgentResult from results.topic (with correlation ID)
6. Update step_execution record (COMPLETED/FAILED)
7. Publish monitoring update (COMPLETED/FAILED)
8. Store output for next step's input mapping
```

#### Retry Logic
- Queries Agent Registry for retry configuration
- Implements exponential backoff
- Retries failed steps up to `max_retries`
- Marks workflow as FAILED if all retries exhausted

#### Input Mapping
- Resolves variables like `${workflow.input.field}` and `${step-1.output.result}`
- Uses `InputMappingResolver` to build step input from:
  - Initial workflow input
  - Previous step outputs

**Kafka Topics**:
- **Produces to**:
  - `orchestrator.tasks.http` - Agent tasks
  - `workflow.monitoring.updates` - Status updates
- **Consumes from**:
  - `results.topic` - Agent results (filtered by correlation_id)

**Database Operations**:
- Creates/updates `workflow_runs` record
- Creates/updates `step_executions` records
- Queries existing state for replay

---

### 4. External Agent Executor (Bridge) (`src/bridge/external_agent_executor.py`)

**Purpose**: Stateless HTTP-Kafka bridge for agent invocation

**Process Model**:
- Long-running service
- Pool of workers (horizontally scalable)
- Each worker processes tasks independently

**Key Responsibilities**:

#### Task Processing
1. Consume `AgentTask` from `orchestrator.tasks.http`
2. Query Agent Registry for agent metadata (URL, auth, timeout, retry config)
3. Build JSON-RPC 2.0 request
4. Make HTTP POST to agent endpoint
5. Parse JSON-RPC 2.0 response
6. Publish `AgentResult` to `results.topic`

#### JSON-RPC 2.0 Protocol
**Request Format**:
```json
{
  "jsonrpc": "2.0",
  "id": "task-123",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-task-123",
      "parts": [
        {"kind": "text", "text": "input data here"}
      ]
    }
  }
}
```

**Response Format**:
```json
{
  "jsonrpc": "2.0",
  "id": "task-123",
  "result": {
    "status": {"state": "completed"},
    "artifacts": [...],
    "history": [...]
  }
}
```

#### Output Extraction
- Extracts text from `artifacts[].parts[]` where `kind == "text"`
- Extracts text from `history[]` (last agent message)
- Falls back to full result if extraction fails

#### Retry Logic
- Exponential backoff for retriable errors:
  - Network errors (connection failures, timeouts)
  - 5xx server errors
  - 429 Too Many Requests
- Non-retriable errors:
  - 4xx client errors (except 429)
  - Invalid response format

**Configuration**:
```bash
KAFKA_BROKERS=localhost:9092
AGENT_REGISTRY_URL=http://localhost:8000
HTTP_TIMEOUT_MS=30000
MAX_RETRIES=3
WORKER_CONCURRENCY=10
```

---

## Data Flow Example

### Workflow Execution Flow

```
1. User triggers workflow via API:
   POST /api/v1/workflows/{id}/execute
   Body: {"input_data": {"topic": "AI"}}

2. API creates workflow_run record (status: PENDING)

3. API publishes to Kafka:
   Topic: workflow.execution.requests
   Message: {
     "run_id": "run-abc123",
     "workflow_plan": {...},
     "input_data": {"topic": "AI"}
   }

4. Execution Consumer receives message
   - Spawns CentralizedExecutor instance

5. CentralizedExecutor initializes
   - Connects to Kafka, database
   - Loads existing state (if any)
   - Updates workflow_run status to RUNNING

6. Executor executes Step 1 (ResearchAgent):
   a. Resolves input: {"topic": "AI"} from workflow.input
   b. Creates step_execution record (RUNNING)
   c. Publishes to orchestrator.tasks.http:
      {
        "run_id": "run-abc123",
        "task_id": "task-step1-xyz",
        "agent_name": "ResearchAgent",
        "input_data": {"topic": "AI"},
        "correlation_id": "corr-abc123-step1"
      }
   d. Waits for result with correlation_id

7. Bridge consumes task:
   a. Queries Agent Registry for ResearchAgent URL
   b. Builds JSON-RPC 2.0 request
   c. POST to http://research-agent:8001
   d. Receives JSON-RPC 2.0 response
   e. Extracts output from artifacts/history
   f. Publishes to results.topic:
      {
        "run_id": "run-abc123",
        "task_id": "task-step1-xyz",
        "status": "SUCCESS",
        "output_data": {"result": "AI research data..."},
        "correlation_id": "corr-abc123-step1"
      }

8. Executor receives result:
   a. Updates step_execution (COMPLETED, output_data)
   b. Stores output for next step
   c. Publishes monitoring update (COMPLETED)
   d. Moves to next_step

9. Executor executes Step 2 (WriterAgent):
   a. Resolves input: {"research": "${step-1.output.result}"}
   b. Repeats steps 6-8

10. Workflow completes:
    a. No more next_step (null)
    b. Updates workflow_run status to COMPLETED
    c. Executor terminates

11. User queries run status:
    GET /api/v1/runs/run-abc123
    Response: {
      "run_id": "run-abc123",
      "status": "COMPLETED",
      "created_at": "...",
      "completed_at": "..."
    }
```

---

## Key Design Patterns

### 1. Claim Check Pattern (Planned, Not Implemented)
- Large payloads stored in S3
- Only URI references passed through Kafka
- Reduces Kafka message size

### 2. Correlation ID Pattern
- Each task has unique correlation_id
- Executor filters results by correlation_id
- Enables request-response matching in async system

### 3. State Machine Pattern
```
PENDING → RUNNING → COMPLETED
                 ↘ FAILED
```

### 4. Retry with Exponential Backoff
- Initial delay: 1s
- Backoff multiplier: 2.0
- Max delay: 30s
- Max retries: 3 (configurable per agent)

### 5. Adapter Pattern (JSON-RPC Protocol)
- `ProtocolAdapter` interface
- `JsonRpc2Adapter` implementation
- `SimpleA2AAdapter` for legacy support
- Factory pattern for adapter creation

---

## Current Limitations & Known Issues

### 1. Sequential Execution Only
- No parallel step execution
- No conditional branching (if/else)
- No loops or iterations

### 2. No Streaming Support
- Agents must return complete responses
- No SSE (Server-Sent Events) handling
- No real-time progress updates from agents

### 3. Limited Error Recovery
- Retry logic is basic (exponential backoff only)
- No fallback agents
- No circuit breaker pattern

### 4. No Workflow Versioning
- Workflow definitions are not versioned
- No rollback capability
- No A/B testing support

### 5. No Rate Limiting
- No throttling of agent calls
- No queue management
- Can overwhelm agents with concurrent requests

### 6. No Caching
- No response caching for idempotent operations
- Every execution calls agents fresh

### 7. Single Database Transaction
- No distributed transaction support
- No saga pattern for long-running workflows

---

## Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** - REST API framework
- **SQLAlchemy 2.0** - ORM
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation
- **httpx** - Async HTTP client
- **kafka-python** - Kafka client

### Infrastructure
- **PostgreSQL 15+** - Metadata storage
- **Apache Kafka** - Message broker
- **Docker** - Containerization
- **Docker Compose** - Local orchestration

### Frontend (Workflow UI)
- **React 18+** with TypeScript
- **Vite** - Build tool
- **TanStack Query** - Server state management
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **React Flow** - Workflow visualization

---

## Configuration Files

### Environment Variables

**API** (`.env.api`):
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/workflow_db
KAFKA_BROKERS=localhost:9092
AGENT_REGISTRY_URL=http://localhost:8000
JWT_SECRET=your-secret-key
```

**Executor** (`.env`):
```bash
KAFKA_BROKERS=localhost:9092
DATABASE_URL=postgresql://user:pass@localhost:5432/workflow_db
AGENT_REGISTRY_URL=http://localhost:8000
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Bridge** (`.env`):
```bash
KAFKA_BROKERS=localhost:9092
AGENT_REGISTRY_URL=http://localhost:8000
HTTP_TIMEOUT_MS=30000
MAX_RETRIES=3
WORKER_CONCURRENCY=10
```

### Docker Compose

**Services**:
- `postgres` - Database
- `kafka` - Message broker
- `zookeeper` - Kafka coordination
- `api` - Management API
- `executor-consumer` - Execution consumer
- `bridge` - HTTP-Kafka bridge
- `workflow-ui` - React frontend

---

## Deployment Architecture

### Local Development
```
docker-compose up
```

### Production (Planned)
- **API**: Multiple instances behind load balancer
- **Executor Consumer**: Single instance (Kafka consumer group)
- **Bridge**: Horizontal scaling (multiple workers)
- **Database**: PostgreSQL with replication
- **Kafka**: Multi-broker cluster

---

## Monitoring & Observability

### Logging
- Structured JSON logging
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Metrics (Planned)
- Prometheus metrics endpoint
- Workflow execution duration
- Step execution duration
- Agent call success/failure rates
- Kafka consumer lag

### Tracing (Planned)
- OpenTelemetry integration
- Distributed tracing across components
- Correlation ID propagation

---

## Next Steps for Enhancement

Based on the current implementation, here are potential areas for improvement:

1. **Parallel Execution** - Execute independent steps concurrently
2. **Conditional Logic** - Support if/else branches in workflows
3. **Loops** - Iterate over collections
4. **Streaming Support** - Handle SSE responses from agents
5. **Workflow Versioning** - Track and manage workflow versions
6. **Circuit Breaker** - Prevent cascading failures
7. **Rate Limiting** - Throttle agent calls
8. **Caching** - Cache idempotent agent responses
9. **Saga Pattern** - Distributed transaction support
10. **Advanced Monitoring** - Metrics, tracing, alerting

---

This summary provides a complete picture of your orchestrator architecture. Ready to discuss enhancements?

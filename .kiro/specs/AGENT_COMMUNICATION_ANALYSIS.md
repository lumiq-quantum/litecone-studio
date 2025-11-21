# Agent Communication Architecture Analysis

## Overview
This document provides a comprehensive analysis of how the orchestrator system initiates and communicates with external agents. The system uses a **Kafka-based asynchronous messaging architecture** with an HTTP-Kafka bridge pattern.

---

## Architecture Components

### 1. **Workflow Execution Initiation (API Layer)**
**Location**: `api/services/execution.py`

**Flow**:
1. User triggers workflow via REST API: `POST /api/v1/workflows/{workflow_id}/execute`
2. `ExecutionService.execute_workflow()` creates a `WorkflowRun` record with `PENDING` status
3. Publishes execution request to Kafka topic via `KafkaService.publish_execution_request()`
4. Returns `run_id` immediately (non-blocking)

**Key Data**:
```python
{
    "run_id": "run-uuid",
    "workflow_plan": {...},  # Complete workflow definition
    "input_data": {...},     # User-provided input
    "workflow_name": "..."
}
```

---

### 2. **Centralized Executor (Orchestration Engine)**
**Location**: `src/executor/centralized_executor.py`

**Responsibilities**:
- Consumes execution requests from Kafka
- Manages workflow state and step sequencing
- Resolves input mappings between steps
- Publishes agent tasks to Kafka
- Waits for agent results
- Updates database with execution status

**Key Methods**:

#### `execute_workflow()`
Main orchestration loop:
1. Creates/updates workflow run record in database
2. Determines starting step (supports resume from failure)
3. Iterates through workflow steps using `next_step` references
4. Calls `execute_step()` for each step
5. Stores outputs for input mapping to subsequent steps
6. Marks workflow as COMPLETED or FAILED

#### `_execute_agent_step(step)`
Executes a single agent step:
1. **Resolves input data** using `InputMappingResolver`:
   - Maps from workflow input
   - Maps from previous step outputs
   - Supports loop context
   
2. **Creates step execution record** in database with `RUNNING` status

3. **Publishes monitoring update** to track progress

4. **Publishes AgentTask** to Kafka topic `orchestrator.tasks.http`:
```python
AgentTask(
    run_id="run-uuid",
    task_id="task-uuid",
    agent_name="agent-name",
    input_data={...},  # Resolved input
    correlation_id="corr-uuid"  # For response matching
)
```

5. **Waits for AgentResult** from `results.topic` using correlation ID (5 min timeout)

6. **Updates step execution** with output data and final status

7. **Publishes final monitoring update**

---

### 3. **HTTP-Kafka Bridge (External Agent Executor)**
**Location**: `src/bridge/external_agent_executor.py`

**Purpose**: Translates between Kafka messages and HTTP calls to external agents

**Flow**:

#### Initialization
```python
ExternalAgentExecutor(
    kafka_bootstrap_servers="...",
    agent_registry_url="...",
    redis_url="...",  # For circuit breaker
    tasks_topic="orchestrator.tasks.http",
    results_topic="results.topic"
)
```

#### Main Processing Loop (`process_task`)
1. **Consumes AgentTask** from `orchestrator.tasks.http` topic

2. **Fetches agent metadata** from Agent Registry:
   - Agent URL
   - Authentication config
   - Timeout settings
   - Retry configuration
   - Circuit breaker settings

3. **Invokes agent via HTTP** with retry logic and circuit breaker:
   - Builds JSON-RPC 2.0 request
   - Adds authentication headers (Bearer token, API key)
   - Makes HTTP POST request
   - Handles timeouts and errors

4. **Parses JSON-RPC response** and converts to internal format

5. **Publishes AgentResult** to `results.topic`:
```python
AgentResult(
    run_id="run-uuid",
    task_id="task-uuid",
    status="SUCCESS" | "FAILURE",
    output_data={...},  # Extracted from response
    correlation_id="corr-uuid",  # Matches request
    error_message="..."  # If failed
)
```

---

### 4. **Agent Registry Client**
**Location**: `src/agent_registry/client.py`

**Features**:
- Fetches agent metadata from API database or fallback registry
- In-memory caching with TTL (5 minutes default)
- Retry logic with exponential backoff
- Validates agent availability

**Agent Metadata**:
```python
AgentMetadata(
    name="agent-name",
    url="http://agent-service:8080",
    auth_config={
        "type": "bearer",  # or "apikey"
        "token": "..."
    },
    timeout=30000,  # milliseconds
    retry_config={
        "max_retries": 3,
        "initial_delay_ms": 1000,
        "max_delay_ms": 30000,
        "backoff_multiplier": 2.0
    },
    circuit_breaker_config={...}
)
```

---

### 5. **Circuit Breaker (Resilience)**
**Location**: `src/bridge/circuit_breaker.py`

**Purpose**: Prevents cascading failures by failing fast when agents are unhealthy

**States**:
- **CLOSED**: Normal operation, all calls go through
- **OPEN**: Agent is failing, reject calls immediately
- **HALF_OPEN**: Testing recovery, allow limited test calls

**Configuration**:
```python
CircuitBreakerConfig(
    enabled=True,
    failure_threshold=5,           # Consecutive failures to open
    failure_rate_threshold=0.5,    # 50% failure rate to open
    timeout_seconds=60,            # Time before attempting reset
    half_open_max_calls=3,         # Test calls in half-open state
    window_size_seconds=120        # Sliding window for failure rate
)
```

**Storage**: Uses Redis for shared state across multiple executor instances

---

## Communication Protocol: JSON-RPC 2.0

### Request Format
```json
{
  "jsonrpc": "2.0",
  "id": "task-uuid",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-task-uuid",
      "parts": [
        {
          "kind": "text",
          "text": "Input data as text or JSON string"
        }
      ]
    }
  }
}
```

### Response Format
```json
{
  "jsonrpc": "2.0",
  "id": "task-uuid",
  "result": {
    "status": {
      "state": "completed"
    },
    "artifacts": [...],
    "history": [
      {
        "role": "agent",
        "parts": [
          {
            "kind": "text",
            "text": "Agent response"
          }
        ]
      }
    ],
    "metadata": {...},
    "contextId": "...",
    "id": "..."
  }
}
```

### Error Response
```json
{
  "jsonrpc": "2.0",
  "id": "task-uuid",
  "error": {
    "code": -32000,
    "message": "Error description",
    "data": {...}
  }
}
```

---

## Retry and Error Handling

### Retry Logic (`retry_with_backoff`)
- **Retriable Errors**:
  - Network errors (connection failures, timeouts)
  - HTTP 5xx server errors
  - HTTP 429 Too Many Requests
  
- **Non-Retriable Errors**:
  - HTTP 4xx client errors (except 429)
  - Invalid response format
  - Circuit breaker open

- **Exponential Backoff**:
  - Initial delay: 1 second
  - Max delay: 30 seconds
  - Multiplier: 2.0
  - Max retries: 3 (configurable per agent)

### Error Propagation
1. Agent invocation fails → `AgentResult` with `FAILURE` status
2. Executor receives failure → Updates step execution as `FAILED`
3. Workflow marked as `FAILED` → Stops execution
4. User can retry workflow via API → Resumes from last incomplete step

---

## Kafka Topics

### `orchestrator.tasks.http`
- **Producer**: Centralized Executor
- **Consumer**: External Agent Executor (Bridge)
- **Message**: `AgentTask`
- **Purpose**: Queue agent invocation requests

### `results.topic`
- **Producer**: External Agent Executor (Bridge)
- **Consumer**: Centralized Executor
- **Message**: `AgentResult`
- **Purpose**: Return agent execution results

### `workflow.monitoring.updates`
- **Producer**: Centralized Executor
- **Consumer**: Monitoring/UI services
- **Message**: `MonitoringUpdate`
- **Purpose**: Real-time workflow progress tracking

---

## Database Persistence

### `workflow_runs` Table
- Stores workflow execution metadata
- Status: PENDING → RUNNING → COMPLETED/FAILED/CANCELLED
- Tracks input data, error messages, timestamps

### `step_executions` Table
- Stores individual step execution details
- Links to workflow run via `run_id`
- Stores input/output data for each step
- Enables resume from failure

---

## Key Features

### 1. **Asynchronous Execution**
- Non-blocking API responses
- Kafka-based message passing
- Scalable to multiple executor instances

### 2. **Fault Tolerance**
- Circuit breaker prevents cascading failures
- Retry logic with exponential backoff
- Resume from last incomplete step
- Database persistence for state recovery

### 3. **Observability**
- Correlation IDs for request tracing
- Monitoring updates for real-time progress
- Comprehensive logging at each stage
- Audit trail in database

### 4. **Flexibility**
- Pluggable authentication (Bearer, API Key)
- Configurable timeouts and retries per agent
- Support for parallel, conditional, loop, and fork-join patterns
- Input mapping between workflow steps

---

## Sequence Diagram

```
User → API → Kafka → Executor → Kafka → Bridge → Agent
                                   ↓
                              Database
                                   ↓
                              Monitoring

1. User: POST /workflows/{id}/execute
2. API: Create run, publish to Kafka
3. Executor: Consume request, start workflow
4. Executor: Resolve inputs, publish AgentTask
5. Bridge: Consume task, fetch agent metadata
6. Bridge: HTTP POST to agent (JSON-RPC)
7. Agent: Process request, return response
8. Bridge: Parse response, publish AgentResult
9. Executor: Consume result, update database
10. Executor: Move to next step or complete workflow
```

---

## Enhancement Opportunities

Based on this analysis, potential enhancements could include:

1. **Protocol Support**: Add support for gRPC, WebSocket, or other protocols
2. **Agent Discovery**: Dynamic agent registration and health checking
3. **Load Balancing**: Distribute requests across multiple agent instances
4. **Caching**: Cache agent responses for idempotent operations
5. **Streaming**: Support streaming responses for long-running agents
6. **Webhooks**: Allow agents to push results instead of polling
7. **Rate Limiting**: Protect agents from overload
8. **Metrics**: Detailed performance metrics per agent
9. **Tracing**: Distributed tracing integration (OpenTelemetry)
10. **Security**: mTLS, request signing, encryption at rest

---

## Summary

The orchestrator uses a **robust, scalable, and fault-tolerant architecture** for agent communication:

- **Kafka** provides asynchronous, decoupled messaging
- **HTTP-Kafka Bridge** translates between protocols
- **JSON-RPC 2.0** standardizes agent communication
- **Circuit Breaker** prevents cascading failures
- **Retry Logic** handles transient errors
- **Database Persistence** enables recovery and audit
- **Correlation IDs** enable end-to-end tracing

This architecture supports high-throughput workflow execution with strong reliability guarantees.

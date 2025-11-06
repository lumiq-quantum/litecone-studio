# Design Document: Centralized Executor and HTTP-Kafka Bridge

## Overview

This design implements the core execution engine for a multi-agent orchestration platform. The system consists of two primary components:

1. **Centralized Executor**: An ephemeral, per-run orchestrator that manages workflow execution through asynchronous Kafka communication
2. **External Agent Executor (HTTP-Kafka Bridge)**: An adapter service that translates between Kafka events and HTTP calls to external agents

The design prioritizes horizontal scalability, fault tolerance, and deterministic execution while maintaining a clean separation between the asynchronous platform core and synchronous external agent communication.

## Architecture

### High-Level Component Interaction

```
[Workflow API] 
    |
    | (spawns)
    v
[Centralized Executor Instance]
    |
    | (publishes tasks)
    v
[Kafka: orchestrator.tasks.http]
    |
    | (consumes)
    v
[External Agent Executor Pool]
    |
    | (HTTP A2A calls)
    v
[External Agent URLs]
    |
    | (responses/streams)
    v
[External Agent Executor Pool]
    |
    | (publishes results)
    v
[Kafka: results.topic / stream.{agent}]
    |
    | (consumes)
    v
[Centralized Executor Instance]
```

### Technology Stack

- **Runtime**: Python 3.11+ for both executor and bridge
- **Message Broker**: Apache Kafka (kafka-python or confluent-kafka-python)
- **Storage**: 
  - PostgreSQL for Workflow Database (SQLAlchemy ORM)
  - AWS S3 for large payload storage (optional, for future use)
- **HTTP Client**: httpx (async HTTP client)
- **Process Management**: Docker containers with orchestration via Kubernetes or ECS

## Components and Interfaces

### 1. Centralized Executor

#### Responsibilities
- Parse and validate workflow plan JSON
- Manage step execution state machine
- Publish tasks to Kafka
- Consume results from Kafka
- Persist execution state to database
- Publish monitoring updates
- Handle workflow completion and cleanup

#### Core Classes

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class ExecutionStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class WorkflowStep:
    id: str
    agent_name: str
    next_step: Optional[str]  # ID of next step in sequence
    input_mapping: Dict[str, str]  # How to map previous outputs to this agent's input

@dataclass
class WorkflowPlan:
    workflow_id: str
    name: str
    version: str
    start_step: str  # ID of first step
    steps: Dict[str, WorkflowStep]  # Map of step_id -> WorkflowStep

@dataclass
class StepResult:
    step_id: str
    status: ExecutionStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    timestamp: datetime
    error_message: Optional[str] = None

class CentralizedExecutor:
    def __init__(self, run_id: str, workflow_plan: WorkflowPlan):
        self.run_id = run_id
        self.workflow_plan = workflow_plan
        self.kafka_producer = None
        self.kafka_consumer = None
        self.database = None
        self.execution_state: Dict[str, StepResult] = {}
    
    async def initialize(self) -> None:
        """Initialize Kafka connections and database"""
        pass
    
    async def load_execution_state(self) -> None:
        """Load any existing execution state from database for replay"""
        pass
    
    async def execute_workflow(self, initial_input: Dict[str, Any]) -> None:
        """Execute workflow from start to finish"""
        pass
    
    async def execute_step(self, step: WorkflowStep, input_data: Dict[str, Any]) -> StepResult:
        """Execute a single workflow step"""
        pass
    
    async def publish_task(self, task: Dict[str, Any]) -> None:
        """Publish agent task to Kafka"""
        pass
    
    async def wait_for_result(self, correlation_id: str) -> Dict[str, Any]:
        """Wait for and return agent result from Kafka"""
        pass
    
    async def persist_step_execution(self, step_result: StepResult) -> None:
        """Save step input/output to database"""
        pass
    
    async def publish_monitoring_update(self, update: Dict[str, Any]) -> None:
        """Publish status update to monitoring topic"""
        pass
    
    async def shutdown(self) -> None:
        """Clean up resources"""
        pass
```

#### State Machine

The executor follows this state progression for each step:

```
PENDING → READY → RUNNING → COMPLETED/FAILED
```

- **PENDING**: Step has unmet dependencies
- **READY**: All dependencies satisfied, ready to execute
- **RUNNING**: Task published to Kafka, awaiting result
- **COMPLETED**: Result received and persisted
- **FAILED**: Error received or timeout occurred

#### Kafka Topics

**Produces to:**
- `orchestrator.tasks.http`: Agent invocation tasks
- `workflow.monitoring.updates`: Real-time status updates

**Consumes from:**
- `results.topic`: Agent execution results

#### Message Schemas

```python
# Task message published to orchestrator.tasks.http
@dataclass
class AgentTask:
    run_id: str
    task_id: str
    agent_name: str
    input_data: Dict[str, Any]  # Full input payload (not S3 reference)
    correlation_id: str
    timestamp: str

# Result message published to results.topic
@dataclass
class AgentResult:
    run_id: str
    task_id: str
    status: str  # 'SUCCESS' or 'FAILURE'
    output_data: Optional[Dict[str, Any]]  # Full output payload
    correlation_id: str
    error_message: Optional[str]
    timestamp: str

# Monitoring update published to workflow.monitoring.updates
@dataclass
class MonitoringUpdate:
    run_id: str
    step_id: str
    step_name: str
    status: str  # 'RUNNING', 'COMPLETED', 'FAILED'
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
```

### 2. External Agent Executor (HTTP-Kafka Bridge)

#### Responsibilities
- Consume tasks from Kafka
- Query Agent Registry for endpoint URLs
- Make HTTP calls to agents (A2A protocol)
- Handle both streaming (SSE) and non-streaming responses
- Implement retry logic with exponential backoff
- Store response payloads in S3
- Publish results and stream events to Kafka

#### Core Classes

```python
import httpx
from kafka import KafkaConsumer, KafkaProducer
from typing import Dict, Any

@dataclass
class AgentMetadata:
    name: str
    url: str
    auth_config: Optional[Dict[str, str]]
    timeout: int
    retry_config: 'RetryConfig'

@dataclass
class RetryConfig:
    max_retries: int
    initial_delay_ms: int
    max_delay_ms: int
    backoff_multiplier: float

class AgentRegistryClient:
    def __init__(self, registry_url: str):
        self.registry_url = registry_url
        self.http_client = httpx.AsyncClient()
    
    async def get_agent_endpoint(self, agent_name: str) -> AgentMetadata:
        """Fetch agent metadata from registry"""
        pass

class ExternalAgentExecutor:
    def __init__(self):
        self.kafka_consumer: KafkaConsumer = None
        self.kafka_producer: KafkaProducer = None
        self.agent_registry: AgentRegistryClient = None
        self.http_client: httpx.AsyncClient = None
    
    async def start(self) -> None:
        """Start consuming tasks from Kafka"""
        pass
    
    async def process_task(self, task: AgentTask) -> None:
        """Process a single agent task"""
        pass
    
    async def invoke_agent(self, agent_url: str, payload: Dict[str, Any], 
                          auth_config: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Make HTTP call to agent endpoint"""
        pass
    
    async def handle_response(self, response: httpx.Response, task: AgentTask) -> None:
        """Process HTTP response and publish result"""
        pass
    
    async def publish_result(self, result: AgentResult) -> None:
        """Publish result to Kafka results topic"""
        pass
    
    async def retry_with_backoff(self, operation, retry_config: RetryConfig):
        """Execute operation with exponential backoff retry logic"""
        pass
```

#### HTTP Request Flow

1. **Receive Task**: Consume from `orchestrator.tasks.http`
2. **Lookup Agent**: Query Agent Registry for URL and config
3. **Prepare Request**: 
   - Extract input data from task message
   - Construct A2A-compliant HTTP POST request
   - Add authentication headers (if configured)
4. **Execute Request**: Make HTTP call with timeout and retry logic
5. **Process Response**:
   - Parse JSON response body
   - Extract output data
6. **Publish Result**: Send complete result to `results.topic`

#### A2A HTTP Request Format

```python
# POST request to agent endpoint
{
    "task_id": "task-123",
    "input": {
        # Agent-specific input data
        "query": "What is the weather?",
        "context": {...}
    }
}

# Expected response format
{
    "task_id": "task-123",
    "status": "success",  # or "error"
    "output": {
        # Agent-specific output data
        "result": "The weather is sunny",
        "confidence": 0.95
    },
    "error": None  # or error message if status is "error"
}
```

#### Retry Logic

Implements exponential backoff for transient failures:

```python
import asyncio
from typing import Callable, TypeVar, Any

T = TypeVar('T')

async def retry_with_backoff(
    operation: Callable[[], Any],
    config: RetryConfig
) -> Any:
    """Execute operation with exponential backoff retry logic"""
    attempt = 0
    delay = config.initial_delay_ms / 1000.0  # Convert to seconds
    
    while attempt < config.max_retries:
        try:
            return await operation()
        except Exception as error:
            if not is_retriable_error(error) or attempt == config.max_retries - 1:
                raise error
            
            await asyncio.sleep(delay)
            delay = min(delay * config.backoff_multiplier, config.max_delay_ms / 1000.0)
            attempt += 1

def is_retriable_error(error: Exception) -> bool:
    """Determine if error is retriable"""
    # Retry on network errors and 5xx status codes
    if isinstance(error, httpx.NetworkError):
        return True
    if isinstance(error, httpx.TimeoutException):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        return 500 <= error.response.status_code < 600
    return False
```

### 3. Workflow Database Schema

```sql
CREATE TABLE workflow_runs (
  run_id VARCHAR(255) PRIMARY KEY,
  workflow_id VARCHAR(255) NOT NULL,
  workflow_name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  error_message TEXT
);

CREATE TABLE step_executions (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(255) NOT NULL REFERENCES workflow_runs(run_id),
  step_id VARCHAR(255) NOT NULL,
  step_name VARCHAR(255) NOT NULL,
  agent_name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL,
  input_data JSONB NOT NULL,  -- Store full input as JSON
  output_data JSONB,           -- Store full output as JSON
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  error_message TEXT,
  UNIQUE(run_id, step_id)
);

CREATE INDEX idx_run_status ON workflow_runs(status);
CREATE INDEX idx_step_run_id ON step_executions(run_id);
CREATE INDEX idx_step_status ON step_executions(status);
```

#### SQLAlchemy Models

```python
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class WorkflowRun(Base):
    __tablename__ = 'workflow_runs'
    
    run_id = Column(String(255), primary_key=True)
    workflow_id = Column(String(255), nullable=False)
    workflow_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

class StepExecution(Base):
    __tablename__ = 'step_executions'
    
    id = Column(String(255), primary_key=True)
    run_id = Column(String(255), ForeignKey('workflow_runs.run_id'), nullable=False)
    step_id = Column(String(255), nullable=False)
    step_name = Column(String(255), nullable=False)
    agent_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB, nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
```

### 4. Agent Registry Interface

The executor and bridge interact with the Agent Registry via HTTP API:

```python
class AgentRegistryAPI:
    """Client for Agent Registry HTTP API"""
    
    async def get_agent(self, agent_name: str) -> AgentMetadata:
        """GET /agents/{agentName}"""
        pass
    
    async def get_recovery_logic(self, agent_name: str) -> RecoveryConfig:
        """GET /agents/{agentName}/recovery"""
        pass

@dataclass
class RecoveryConfig:
    on_failure: str  # 'RETRY', 'FALLBACK', or 'FAIL'
    fallback_agent: Optional[str]
    max_retries: Optional[int]
```

## Data Models

### Workflow Plan JSON

The workflow is defined as a single JSON document that specifies the sequential flow of agent executions:

```json
{
  "workflow_id": "wf-001",
  "name": "research-and-write",
  "version": "1.0.0",
  "start_step": "step-1",
  "steps": {
    "step-1": {
      "id": "step-1",
      "agent_name": "ResearchAgent",
      "next_step": "step-2",
      "input_mapping": {
        "topic": "${workflow.input.topic}"
      }
    },
    "step-2": {
      "id": "step-2",
      "agent_name": "WriterAgent",
      "next_step": null,
      "input_mapping": {
        "research_data": "${step-1.output.result}",
        "style": "${workflow.input.style}"
      }
    }
  }
}
```

**Key Design Points:**
- `start_step`: Identifies the first step to execute
- `next_step`: Creates a linked list structure for sequential execution
- `input_mapping`: Defines how to construct input from workflow input and previous step outputs
- Variable substitution syntax: `${step-id.output.field}` or `${workflow.input.field}`

## Error Handling

### Executor Error Scenarios

1. **Invalid Workflow Plan**: Validate JSON schema on initialization, fail fast
2. **Database Connection Failure**: Retry with exponential backoff, fail after max attempts
3. **Kafka Connection Failure**: Retry connection, buffer messages in memory
4. **Result Timeout**: Configurable timeout per step, publish FAILED status
5. **Unrecoverable Agent Failure**: Check recovery logic, execute or fail workflow

### Bridge Error Scenarios

1. **Agent Registry Unavailable**: Retry with backoff, publish failure result after max attempts
2. **Agent HTTP Timeout**: Respect agent-specific timeout, publish failure result
3. **Agent Returns 4xx**: Non-retriable, publish failure result immediately
4. **Agent Returns 5xx**: Retriable, apply exponential backoff
5. **SSE Stream Interrupted**: Publish partial stream + error marker
6. **S3 Upload Failure**: Retry with backoff, fail task if persistent

### Error Message Format

```typescript
interface ErrorDetails {
  code: string;
  message: string;
  retriable: boolean;
  context: Record<string, any>;
}
```

## Testing Strategy

### Unit Tests

**Centralized Executor:**
- Workflow plan parsing and validation
- Step dependency resolution
- State machine transitions
- Message schema validation
- Database persistence logic

**External Agent Executor:**
- HTTP request construction
- SSE stream parsing
- Retry logic with various error types
- S3 Claim Check generation
- Message publishing

### Integration Tests

1. **End-to-End Workflow Execution**:
   - Spawn executor with test workflow
   - Mock Kafka and verify message flow
   - Verify database state after completion

2. **Bridge with Mock Agents**:
   - Start bridge with test Kafka
   - Publish test tasks
   - Mock HTTP responses (streaming and non-streaming)
   - Verify result messages

3. **Stateful Resume**:
   - Execute workflow partially
   - Simulate failure
   - Restart executor with same run_id
   - Verify skipped completed steps

### Performance Tests

- **Executor Spawn Time**: Target < 500ms from API call to first task published
- **Message Processing Latency**: Target < 50ms from result received to state persisted
- **Bridge Throughput**: Target 100+ concurrent agent calls
- **Streaming Latency**: Target < 100ms from SSE event to Kafka publish

## Deployment Architecture

### Containerization

Both components run as Docker containers:

```dockerfile
# Centralized Executor
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
CMD ["python", "-m", "src.executor"]
```

### Scaling Strategy

**Centralized Executor:**
- Ephemeral: One container per workflow run
- Spawned by Workflow API via Kubernetes Job or ECS Task
- Auto-terminates on completion
- No persistent state (reads from DB on startup)

**External Agent Executor:**
- Stateless pool of workers
- Horizontal scaling based on Kafka consumer lag
- Kubernetes HPA or ECS Auto Scaling
- Target: Keep consumer lag < 100 messages

### Configuration

Environment variables for both services:

```bash
# Kafka
KAFKA_BROKERS=kafka-1:9092,kafka-2:9092
KAFKA_CLIENT_ID=executor-service
KAFKA_GROUP_ID=executor-group

# Database
DATABASE_URL=postgresql://user:pass@host:5432/workflows

# S3
S3_BUCKET=workflow-data
AWS_REGION=us-east-1

# Agent Registry
AGENT_REGISTRY_URL=http://agent-registry:8080

# Executor-specific
RUN_ID=<injected-by-spawner>
WORKFLOW_PLAN=<injected-by-spawner>

# Bridge-specific
HTTP_TIMEOUT_MS=30000
MAX_RETRIES=3
WORKER_CONCURRENCY=10
```

## Observability

### Logging

Structured JSON logs with correlation IDs:

```python
import logging
import json

logger = logging.getLogger(__name__)

logger.info(json.dumps({
    'message': 'Step execution started',
    'run_id': self.run_id,
    'step_id': step.id,
    'agent_name': step.agent_name,
    'timestamp': datetime.utcnow().isoformat()
}))
```

### Metrics

Key metrics to track:

**Executor:**
- `executor.workflow.duration` (histogram)
- `executor.step.duration` (histogram, labeled by agent)
- `executor.step.failures` (counter, labeled by agent)
- `executor.active.runs` (gauge)

**Bridge:**
- `bridge.http.request.duration` (histogram, labeled by agent)
- `bridge.http.request.failures` (counter, labeled by status code)
- `bridge.kafka.publish.latency` (histogram)
- `bridge.active.requests` (gauge)

### Tracing

Implement distributed tracing with correlation IDs:
- Generate trace ID at workflow start
- Propagate through all Kafka messages
- Include in HTTP headers to agents
- Use OpenTelemetry for instrumentation

## Security Considerations

1. **Agent Authentication**: Support multiple auth schemes (Bearer token, API key, mTLS)
2. **Kafka Security**: Use SASL/SSL for broker connections
3. **S3 Access**: Use IAM roles, not access keys
4. **Database**: Use connection pooling with encrypted connections
5. **Secrets Management**: Load auth credentials from AWS Secrets Manager or Vault
6. **Input Validation**: Sanitize all workflow plan inputs to prevent injection attacks

## Execution Flow Example

Here's how a complete workflow execution flows through the system:

1. **Workflow API** receives request to execute workflow with `initial_input`
2. **Workflow API** spawns **Centralized Executor** with `run_id`, `workflow_plan`, and `initial_input`
3. **Centralized Executor** initializes:
   - Connects to Kafka
   - Connects to database
   - Loads any existing execution state (for replay)
   - Identifies `start_step` from workflow plan
4. **Execute Step 1** (ResearchAgent):
   - Build input using `input_mapping` and `initial_input`
   - Save step execution record to database (status: RUNNING, input_data: {...})
   - Publish monitoring update (status: RUNNING)
   - Publish task to `orchestrator.tasks.http` topic
   - Wait for result on `results.topic`
5. **External Agent Executor** (running as consumer pool):
   - Consumes task from `orchestrator.tasks.http`
   - Queries Agent Registry for ResearchAgent URL
   - Makes HTTP POST to ResearchAgent with input data
   - Receives JSON response
   - Publishes result to `results.topic`
6. **Centralized Executor** receives result:
   - Updates database (status: COMPLETED, output_data: {...})
   - Publishes monitoring update (status: COMPLETED)
   - Looks up `next_step` from workflow plan
7. **Execute Step 2** (WriterAgent):
   - Build input using `input_mapping` and Step 1's output
   - Repeat steps 4-6
8. **Workflow Complete**:
   - No more `next_step` (null)
   - Update workflow_runs table (status: COMPLETED)
   - Publish final monitoring update
   - Shutdown executor

## Future Enhancements

1. **SSE Streaming Support**: Add streaming response handling for real-time agent outputs
2. **Parallel Execution**: Execute independent branches concurrently
3. **Conditional Logic**: Support if/else branches in workflow plans
4. **Loop Support**: Enable iteration over collections
5. **Workflow Versioning**: Support multiple versions of same workflow
6. **Circuit Breaker**: Prevent cascading failures from problematic agents
7. **Rate Limiting**: Throttle requests to specific agents
8. **Caching**: Cache agent responses for idempotent operations
9. **S3 Claim Check**: Move large payloads to S3 for efficiency

# Design Document: Workflow Management API

## Overview

This design implements a FastAPI-based REST API for managing the Centralized Executor system. The API provides endpoints for agent registration, workflow definition management, execution triggering, and run monitoring. The system follows a modular architecture with clear separation between models, services, routes, and database layers.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web UI / Client                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Management API                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routes (API Endpoints)                              │  │
│  │  - /api/v1/agents                                    │  │
│  │  - /api/v1/workflows                                 │  │
│  │  - /api/v1/runs                                      │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │  Services (Business Logic)                           │  │
│  │  - AgentService                                      │  │
│  │  - WorkflowService                                   │  │
│  │  - ExecutionService                                  │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │  Repositories (Data Access)                          │  │
│  │  - AgentRepository                                   │  │
│  │  - WorkflowRepository                                │  │
│  │  - RunRepository                                     │  │
│  └────────────────────┬─────────────────────────────────┘  │
└───────────────────────┼─────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│   PostgreSQL     │          │      Kafka       │
│   (Metadata)     │          │   (Execution)    │
└──────────────────┘          └──────────────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ Executor Service │
                              │  (Existing)      │
                              └──────────────────┘
```

### Technology Stack

- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Database**: PostgreSQL 15+
- **Message Queue**: Kafka (existing)
- **Authentication**: JWT + API Keys
- **Documentation**: OpenAPI 3.0 (auto-generated)
- **Testing**: pytest + httpx

## Database Schema

### New Tables

#### 1. agents

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    url VARCHAR(512) NOT NULL,
    description TEXT,
    auth_type VARCHAR(50),  -- 'none', 'bearer', 'apikey'
    auth_config JSONB,
    timeout_ms INTEGER DEFAULT 30000,
    retry_config JSONB,
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'inactive', 'deleted'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

CREATE INDEX idx_agents_name ON agents(name);
CREATE INDEX idx_agents_status ON agents(status);
```

#### 2. workflow_definitions

```sql
CREATE TABLE workflow_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version INTEGER DEFAULT 1,
    workflow_data JSONB NOT NULL,  -- Complete workflow JSON
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'inactive', 'deleted'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    UNIQUE(name, version)
);

CREATE INDEX idx_workflow_definitions_name ON workflow_definitions(name);
CREATE INDEX idx_workflow_definitions_status ON workflow_definitions(status);
```

#### 3. workflow_steps

```sql
CREATE TABLE workflow_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflow_definitions(id) ON DELETE CASCADE,
    step_id VARCHAR(255) NOT NULL,
    agent_id UUID REFERENCES agents(id),
    next_step_id VARCHAR(255),
    input_mapping JSONB,
    step_order INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(workflow_id, step_id)
);

CREATE INDEX idx_workflow_steps_workflow_id ON workflow_steps(workflow_id);
```

#### 4. audit_logs

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,  -- 'agent', 'workflow', 'run'
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,  -- 'create', 'update', 'delete', 'execute'
    user_id VARCHAR(255),
    changes JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

### Updated Tables

#### workflow_runs (enhanced)

```sql
ALTER TABLE workflow_runs ADD COLUMN workflow_definition_id UUID REFERENCES workflow_definitions(id);
ALTER TABLE workflow_runs ADD COLUMN input_data JSONB;
ALTER TABLE workflow_runs ADD COLUMN triggered_by VARCHAR(255);
ALTER TABLE workflow_runs ADD COLUMN cancelled_at TIMESTAMP;
ALTER TABLE workflow_runs ADD COLUMN cancelled_by VARCHAR(255);
```

## API Design

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

All endpoints (except health checks) require authentication via:
- **JWT Token**: `Authorization: Bearer <token>`
- **API Key**: `X-API-Key: <key>`

### Endpoints

#### Agent Management

```
POST   /api/v1/agents                    - Create agent
GET    /api/v1/agents                    - List agents (paginated)
GET    /api/v1/agents/{agent_id}         - Get agent details
PUT    /api/v1/agents/{agent_id}         - Update agent
DELETE /api/v1/agents/{agent_id}         - Delete agent
GET    /api/v1/agents/{agent_id}/health  - Check agent health
```

#### Workflow Management

```
POST   /api/v1/workflows                      - Create workflow
GET    /api/v1/workflows                      - List workflows (paginated)
GET    /api/v1/workflows/{workflow_id}        - Get workflow details
PUT    /api/v1/workflows/{workflow_id}        - Update workflow
DELETE /api/v1/workflows/{workflow_id}        - Delete workflow
GET    /api/v1/workflows/{workflow_id}/versions - Get workflow versions
POST   /api/v1/workflows/{workflow_id}/execute - Execute workflow
```

#### Run Management

```
GET    /api/v1/runs                     - List runs (paginated)
GET    /api/v1/runs/{run_id}            - Get run details
GET    /api/v1/runs/{run_id}/steps      - Get run steps
POST   /api/v1/runs/{run_id}/retry      - Retry failed run
POST   /api/v1/runs/{run_id}/cancel     - Cancel running workflow
GET    /api/v1/runs/{run_id}/logs       - Get run logs
```

#### System

```
GET    /health                          - Health check
GET    /health/ready                    - Readiness check
GET    /metrics                         - Prometheus metrics
GET    /docs                            - Swagger UI
GET    /redoc                           - ReDoc UI
GET    /openapi.json                    - OpenAPI spec
```

## Project Structure

```
api/
├── __init__.py
├── main.py                      # FastAPI app initialization
├── config.py                    # Configuration management
├── dependencies.py              # Dependency injection
│
├── models/                      # SQLAlchemy models
│   ├── __init__.py
│   ├── agent.py
│   ├── workflow.py
│   ├── run.py
│   └── audit.py
│
├── schemas/                     # Pydantic schemas
│   ├── __init__.py
│   ├── agent.py
│   ├── workflow.py
│   ├── run.py
│   ├── common.py               # Shared schemas (pagination, etc.)
│   └── responses.py            # API response schemas
│
├── repositories/                # Data access layer
│   ├── __init__.py
│   ├── base.py                 # Base repository
│   ├── agent.py
│   ├── workflow.py
│   ├── run.py
│   └── audit.py
│
├── services/                    # Business logic
│   ├── __init__.py
│   ├── agent.py
│   ├── workflow.py
│   ├── execution.py
│   ├── audit.py
│   └── kafka.py                # Kafka integration
│
├── routes/                      # API endpoints
│   ├── __init__.py
│   ├── agents.py
│   ├── workflows.py
│   ├── runs.py
│   └── system.py
│
├── middleware/                  # Custom middleware
│   ├── __init__.py
│   ├── auth.py
│   ├── logging.py
│   └── error_handler.py
│
├── utils/                       # Utilities
│   ├── __init__.py
│   ├── pagination.py
│   ├── validators.py
│   └── exceptions.py
│
└── migrations/                  # Alembic migrations
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── 001_initial_schema.py
```

## Data Models

### Pydantic Schemas

#### Agent Schemas

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict
from datetime import datetime
from uuid import UUID

class RetryConfigSchema(BaseModel):
    max_retries: int = Field(default=3, ge=0, le=10)
    initial_delay_ms: int = Field(default=1000, ge=100)
    max_delay_ms: int = Field(default=30000, ge=1000)
    backoff_multiplier: float = Field(default=2.0, ge=1.0)

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    description: Optional[str] = None
    auth_type: Optional[str] = Field(default="none", pattern="^(none|bearer|apikey)$")
    auth_config: Optional[Dict] = None
    timeout_ms: int = Field(default=30000, ge=1000, le=300000)
    retry_config: RetryConfigSchema = Field(default_factory=RetryConfigSchema)

class AgentUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    description: Optional[str] = None
    auth_type: Optional[str] = Field(None, pattern="^(none|bearer|apikey)$")
    auth_config: Optional[Dict] = None
    timeout_ms: Optional[int] = Field(None, ge=1000, le=300000)
    retry_config: Optional[RetryConfigSchema] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")

class AgentResponse(BaseModel):
    id: UUID
    name: str
    url: str
    description: Optional[str]
    auth_type: str
    timeout_ms: int
    retry_config: RetryConfigSchema
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### Workflow Schemas

```python
class WorkflowStepSchema(BaseModel):
    id: str
    agent_name: str
    next_step: Optional[str] = None
    input_mapping: Dict[str, str]

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_step: str
    steps: Dict[str, WorkflowStepSchema]

class WorkflowUpdate(BaseModel):
    description: Optional[str] = None
    start_step: Optional[str] = None
    steps: Optional[Dict[str, WorkflowStepSchema]] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")

class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    version: int
    workflow_data: Dict
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### Run Schemas

```python
class WorkflowExecuteRequest(BaseModel):
    input_data: Dict[str, Any]
    
class RunResponse(BaseModel):
    id: UUID
    run_id: str
    workflow_id: UUID
    workflow_name: str
    status: str
    input_data: Dict
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    triggered_by: str
    
    class Config:
        from_attributes = True

class StepExecutionResponse(BaseModel):
    id: str
    step_id: str
    agent_name: str
    status: str
    input_data: Dict
    output_data: Optional[Dict]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True
```

## Services Layer

### AgentService

```python
class AgentService:
    def __init__(self, repository: AgentRepository, audit_service: AuditService):
        self.repository = repository
        self.audit_service = audit_service
    
    async def create_agent(self, agent_data: AgentCreate, user_id: str) -> Agent:
        """Create a new agent and log the action"""
        agent = await self.repository.create(agent_data)
        await self.audit_service.log_action(
            entity_type="agent",
            entity_id=agent.id,
            action="create",
            user_id=user_id,
            changes=agent_data.dict()
        )
        return agent
    
    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        """Get agent by ID"""
        return await self.repository.get_by_id(agent_id)
    
    async def list_agents(self, skip: int, limit: int, status: Optional[str]) -> List[Agent]:
        """List agents with pagination and filtering"""
        return await self.repository.list(skip=skip, limit=limit, status=status)
    
    async def update_agent(self, agent_id: UUID, agent_data: AgentUpdate, user_id: str) -> Agent:
        """Update agent and log the action"""
        agent = await self.repository.update(agent_id, agent_data)
        await self.audit_service.log_action(
            entity_type="agent",
            entity_id=agent_id,
            action="update",
            user_id=user_id,
            changes=agent_data.dict(exclude_unset=True)
        )
        return agent
    
    async def delete_agent(self, agent_id: UUID, user_id: str) -> None:
        """Soft delete agent and log the action"""
        await self.repository.soft_delete(agent_id)
        await self.audit_service.log_action(
            entity_type="agent",
            entity_id=agent_id,
            action="delete",
            user_id=user_id
        )
```

### WorkflowService

```python
class WorkflowService:
    def __init__(
        self,
        repository: WorkflowRepository,
        agent_repository: AgentRepository,
        audit_service: AuditService
    ):
        self.repository = repository
        self.agent_repository = agent_repository
        self.audit_service = audit_service
    
    async def create_workflow(self, workflow_data: WorkflowCreate, user_id: str) -> Workflow:
        """Create workflow and validate agent references"""
        # Validate that all agents exist
        await self._validate_agents(workflow_data.steps)
        
        # Validate workflow structure
        self._validate_workflow_structure(workflow_data)
        
        workflow = await self.repository.create(workflow_data)
        await self.audit_service.log_action(
            entity_type="workflow",
            entity_id=workflow.id,
            action="create",
            user_id=user_id,
            changes=workflow_data.dict()
        )
        return workflow
    
    async def _validate_agents(self, steps: Dict[str, WorkflowStepSchema]) -> None:
        """Validate that all referenced agents exist"""
        agent_names = {step.agent_name for step in steps.values()}
        for agent_name in agent_names:
            agent = await self.agent_repository.get_by_name(agent_name)
            if not agent or agent.status != 'active':
                raise ValueError(f"Agent '{agent_name}' not found or inactive")
    
    def _validate_workflow_structure(self, workflow_data: WorkflowCreate) -> None:
        """Validate workflow structure (no cycles, valid references)"""
        # Check start_step exists
        if workflow_data.start_step not in workflow_data.steps:
            raise ValueError(f"start_step '{workflow_data.start_step}' not found in steps")
        
        # Check for cycles
        visited = set()
        current = workflow_data.start_step
        while current:
            if current in visited:
                raise ValueError(f"Circular reference detected at step '{current}'")
            visited.add(current)
            current = workflow_data.steps[current].next_step
```

### ExecutionService

```python
class ExecutionService:
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        run_repository: RunRepository,
        kafka_service: KafkaService,
        audit_service: AuditService
    ):
        self.workflow_repository = workflow_repository
        self.run_repository = run_repository
        self.kafka_service = kafka_service
        self.audit_service = audit_service
    
    async def execute_workflow(
        self,
        workflow_id: UUID,
        input_data: Dict,
        user_id: str
    ) -> WorkflowRun:
        """Trigger workflow execution"""
        # Get workflow definition
        workflow = await self.workflow_repository.get_by_id(workflow_id)
        if not workflow or workflow.status != 'active':
            raise ValueError("Workflow not found or inactive")
        
        # Create run record
        run_id = f"run-{uuid.uuid4()}"
        run = await self.run_repository.create(
            run_id=run_id,
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            input_data=input_data,
            triggered_by=user_id
        )
        
        # Publish to Kafka for executor
        await self.kafka_service.publish_execution_request(
            run_id=run_id,
            workflow_plan=workflow.workflow_data,
            input_data=input_data
        )
        
        # Log action
        await self.audit_service.log_action(
            entity_type="run",
            entity_id=run.id,
            action="execute",
            user_id=user_id,
            changes={"input_data": input_data}
        )
        
        return run
    
    async def retry_workflow(self, run_id: str, user_id: str) -> WorkflowRun:
        """Retry a failed workflow from last incomplete step"""
        run = await self.run_repository.get_by_run_id(run_id)
        if not run:
            raise ValueError("Run not found")
        
        if run.status not in ['FAILED', 'CANCELLED']:
            raise ValueError("Can only retry failed or cancelled runs")
        
        # Update run status
        await self.run_repository.update_status(run_id, 'PENDING')
        
        # Republish to Kafka (executor will resume from last step)
        workflow = await self.workflow_repository.get_by_id(run.workflow_definition_id)
        await self.kafka_service.publish_execution_request(
            run_id=run_id,
            workflow_plan=workflow.workflow_data,
            input_data=run.input_data
        )
        
        # Log action
        await self.audit_service.log_action(
            entity_type="run",
            entity_id=run.id,
            action="retry",
            user_id=user_id
        )
        
        return run
```

## Error Handling

### Custom Exceptions

```python
class APIException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

class NotFoundException(APIException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)

class ValidationException(APIException):
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)

class ConflictException(APIException):
    def __init__(self, detail: str):
        super().__init__(status_code=409, detail=detail)
```

### Error Handler Middleware

```python
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
```

## Testing Strategy

### Unit Tests
- Test services with mocked repositories
- Test repositories with in-memory database
- Test validators and utilities

### Integration Tests
- Test API endpoints with test database
- Test Kafka integration
- Test database migrations

### E2E Tests
- Test complete workflow execution flow
- Test retry and cancellation
- Test authentication and authorization

## Deployment

### Docker Compose

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/workflow_db
      - KAFKA_BROKERS=kafka:29092
      - JWT_SECRET=secret
    depends_on:
      - postgres
      - kafka
```

### Environment Variables

```
DATABASE_URL=postgresql://user:pass@host:5432/db
KAFKA_BROKERS=localhost:9092
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
API_KEY_HEADER=X-API-Key
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

## Security Considerations

1. **Authentication**: JWT tokens with expiration
2. **Authorization**: Role-based access control
3. **Input Validation**: Pydantic models with strict validation
4. **SQL Injection**: SQLAlchemy ORM prevents SQL injection
5. **Rate Limiting**: Implement rate limiting middleware
6. **CORS**: Configure allowed origins
7. **Secrets**: Store secrets in environment variables or secret manager

## Performance Considerations

1. **Database Indexing**: Index frequently queried columns
2. **Connection Pooling**: Use SQLAlchemy connection pool
3. **Caching**: Cache agent and workflow definitions
4. **Pagination**: Limit result set sizes
5. **Async Operations**: Use async/await for I/O operations
6. **Background Tasks**: Use FastAPI BackgroundTasks for non-blocking operations

## Monitoring and Observability

1. **Logging**: Structured JSON logging
2. **Metrics**: Prometheus metrics endpoint
3. **Tracing**: OpenTelemetry integration
4. **Health Checks**: Liveness and readiness probes
5. **Alerts**: Alert on error rates and latency

# Workflow Management API - Specification Summary

## Overview

This specification defines a FastAPI-based REST API that transforms the current CLI-driven Centralized Executor system into a fully-featured web application with database-backed agent and workflow management.

## Key Features

### 1. **Agent Management API**
- Register agents via REST API instead of editing Python files
- Store agent configurations in PostgreSQL
- Update, delete, and query agents dynamically
- Health check endpoints for agent monitoring

### 2. **Workflow Definition Management**
- Create workflows via REST API instead of JSON files
- Store workflow definitions in database with versioning
- Update workflows and automatically increment versions
- Query workflow history and versions

### 3. **Workflow Execution API**
- Trigger workflow executions via REST API
- Automatic run ID generation
- Immediate response with run tracking
- Integration with existing executor service via Kafka

### 4. **Run Monitoring and Management**
- Query workflow runs with filtering and pagination
- View step-by-step execution details
- Retry failed workflows from last incomplete step
- Cancel running workflows

### 5. **Database-Backed Storage**
- All configurations stored in PostgreSQL
- Alembic migrations for schema versioning
- Audit logging for all changes
- Soft deletes for data retention

### 6. **Auto-Generated API Documentation**
- Swagger UI at `/docs`
- ReDoc at `/redoc`
- OpenAPI 3.0 specification
- Interactive API testing

## Architecture

```
┌─────────────┐
│   Web UI    │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────────────────────────┐
│   FastAPI Management API        │
│  ┌──────────────────────────┐  │
│  │ Routes → Services →      │  │
│  │ Repositories → Database  │  │
│  └──────────────────────────┘  │
└────────┬────────────────┬───────┘
         │                │
         ▼                ▼
   ┌──────────┐    ┌──────────┐
   │PostgreSQL│    │  Kafka   │
   └──────────┘    └────┬─────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   Executor   │
                 │  (Existing)  │
                 └──────────────┘
```

## Technology Stack

- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+ (async)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Database**: PostgreSQL 15+
- **Message Queue**: Kafka (existing)
- **Authentication**: JWT + API Keys
- **Testing**: pytest + httpx
- **Documentation**: OpenAPI 3.0 (auto-generated)

## Project Structure

```
api/
├── main.py                 # FastAPI app
├── config.py              # Configuration
├── dependencies.py        # DI
├── models/                # SQLAlchemy models
│   ├── agent.py
│   ├── workflow.py
│   ├── run.py
│   └── audit.py
├── schemas/               # Pydantic schemas
│   ├── agent.py
│   ├── workflow.py
│   ├── run.py
│   └── common.py
├── repositories/          # Data access
│   ├── base.py
│   ├── agent.py
│   ├── workflow.py
│   └── run.py
├── services/              # Business logic
│   ├── agent.py
│   ├── workflow.py
│   ├── execution.py
│   └── kafka.py
├── routes/                # API endpoints
│   ├── agents.py
│   ├── workflows.py
│   ├── runs.py
│   └── system.py
├── middleware/            # Middleware
│   ├── auth.py
│   ├── logging.py
│   └── error_handler.py
└── migrations/            # Alembic migrations
    └── versions/
```

## API Endpoints

### Agent Management
```
POST   /api/v1/agents                    - Create agent
GET    /api/v1/agents                    - List agents
GET    /api/v1/agents/{id}               - Get agent
PUT    /api/v1/agents/{id}               - Update agent
DELETE /api/v1/agents/{id}               - Delete agent
GET    /api/v1/agents/{id}/health        - Check health
```

### Workflow Management
```
POST   /api/v1/workflows                 - Create workflow
GET    /api/v1/workflows                 - List workflows
GET    /api/v1/workflows/{id}            - Get workflow
PUT    /api/v1/workflows/{id}            - Update workflow
DELETE /api/v1/workflows/{id}            - Delete workflow
GET    /api/v1/workflows/{id}/versions   - Get versions
POST   /api/v1/workflows/{id}/execute    - Execute workflow
```

### Run Management
```
GET    /api/v1/runs                      - List runs
GET    /api/v1/runs/{id}                 - Get run details
GET    /api/v1/runs/{id}/steps           - Get run steps
POST   /api/v1/runs/{id}/retry           - Retry failed run
POST   /api/v1/runs/{id}/cancel          - Cancel run
```

### System
```
GET    /health                           - Health check
GET    /health/ready                     - Readiness check
GET    /metrics                          - Prometheus metrics
GET    /docs                             - Swagger UI
GET    /redoc                            - ReDoc
```

## Database Schema

### New Tables

1. **agents** - Agent configurations
2. **workflow_definitions** - Workflow templates
3. **workflow_steps** - Individual workflow steps
4. **audit_logs** - Change tracking

### Enhanced Tables

- **workflow_runs** - Add workflow_definition_id, input_data, triggered_by
- **step_executions** - No changes needed

## Implementation Phases

### Phase 1: Foundation (Tasks 1-3)
- Project setup
- Database configuration
- Development environment

### Phase 2: Database (Tasks 4-8)
- Create models
- Generate migrations
- Test migrations

### Phase 3: Schemas (Tasks 9-12)
- Pydantic models
- Validation logic
- Common schemas

### Phase 4: Repositories (Tasks 13-17)
- Data access layer
- CRUD operations
- Filtering and pagination

### Phase 5: Services (Tasks 18-22)
- Business logic
- Validation
- Kafka integration

### Phase 6: Routes (Tasks 23-26)
- API endpoints
- Request/response handling
- Error handling

### Phase 7: Auth & Middleware (Tasks 27-29)
- Authentication
- Error handling
- Logging

### Phase 8: Integration (Tasks 30-34)
- Executor integration
- Documentation
- Testing

### Phase 9: Deployment (Tasks 35-37)
- Docker configuration
- Documentation
- Migration guide

### Phase 10: Monitoring (Tasks 38-40)
- Metrics
- Logging
- Health checks

## Key Benefits

### For Administrators
- ✅ No code changes needed to add agents
- ✅ Web-based workflow management
- ✅ Audit trail of all changes
- ✅ Easy monitoring and debugging

### For Developers
- ✅ RESTful API for integrations
- ✅ Auto-generated documentation
- ✅ Type-safe with Pydantic
- ✅ Testable architecture

### For Operations
- ✅ Database-backed reliability
- ✅ Version-controlled migrations
- ✅ Health checks and metrics
- ✅ Structured logging

## Migration Path

### Current State
```bash
# Edit Python file
vim examples/mock_agent_registry.py

# Edit JSON file
vim my_workflow.json

# Run CLI command
docker compose run executor ...
```

### Future State
```bash
# Register agent via API
curl -X POST /api/v1/agents -d '{...}'

# Create workflow via API
curl -X POST /api/v1/workflows -d '{...}'

# Execute workflow via API
curl -X POST /api/v1/workflows/{id}/execute -d '{...}'
```

## Security Features

- JWT token authentication
- API key support
- Role-based access control (RBAC)
- Input validation
- SQL injection prevention (ORM)
- Rate limiting
- CORS configuration
- Audit logging

## Testing Strategy

- **Unit Tests**: Services, repositories, validators
- **Integration Tests**: API endpoints, database, Kafka
- **E2E Tests**: Complete workflow execution flows
- **Load Tests**: Performance under load

## Documentation Deliverables

1. **API Documentation** - Auto-generated Swagger/ReDoc
2. **Usage Guide** - How to use the API
3. **Migration Guide** - Moving from CLI to API
4. **Development Guide** - How to extend the API
5. **Deployment Guide** - Production deployment

## Success Criteria

- ✅ All agents manageable via API
- ✅ All workflows manageable via API
- ✅ Workflow execution via API
- ✅ Run monitoring via API
- ✅ Retry failed workflows
- ✅ Cancel running workflows
- ✅ Comprehensive API documentation
- ✅ Database migrations working
- ✅ Authentication implemented
- ✅ Integration with existing executor

## Timeline Estimate

- **Phase 1-2**: 2-3 days (Setup + Database)
- **Phase 3-4**: 2-3 days (Schemas + Repositories)
- **Phase 5-6**: 3-4 days (Services + Routes)
- **Phase 7-8**: 2-3 days (Auth + Integration)
- **Phase 9-10**: 1-2 days (Deployment + Monitoring)

**Total**: ~10-15 days for core implementation

## Next Steps

1. Review requirements, design, and tasks
2. Confirm approach and architecture
3. Begin Phase 1 implementation
4. Iterate with feedback

## Questions for Review

1. Does the API design meet your requirements?
2. Is the database schema appropriate?
3. Should we add any additional endpoints?
4. Are there specific authentication requirements?
5. Any specific UI framework preferences for future frontend?

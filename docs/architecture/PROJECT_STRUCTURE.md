# Project Structure Guide

This document provides a comprehensive overview of the project's directory structure and organization.

## Root Directory

```
.
├── README.md                    # Main project documentation
├── CLEANUP_SUMMARY.md           # Summary of organizational cleanup
├── PROJECT_STRUCTURE.md         # This file
├── quick-start.sh               # Quick setup and test script
├── cleanup.sh                   # Cleanup Docker containers/volumes
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker services configuration
├── .env.example                 # Environment variables template
└── openapi.yaml                 # OpenAPI specification
```

## Source Code (`src/`)

```
src/
├── executor/                    # Centralized Executor
│   ├── centralized_executor.py  # Main executor logic
│   ├── parallel_executor.py     # Parallel execution
│   ├── conditional_executor.py  # Conditional logic
│   ├── loop_executor.py         # Loop execution
│   ├── fork_join_executor.py    # Fork-join pattern
│   └── condition_evaluator.py   # Condition evaluation
├── bridge/                      # HTTP-Kafka Bridge
│   ├── external_agent_executor.py
│   └── circuit_breaker.py       # Circuit breaker implementation
├── models/                      # Data models
│   └── workflow.py              # Workflow definitions
├── database/                    # Database layer
│   ├── models.py                # SQLAlchemy models
│   └── connection.py            # Database connection
├── kafka_client/                # Kafka integration
│   ├── producer.py
│   └── consumer.py
├── agent_registry/              # Agent registry client
│   └── client.py
└── utils/                       # Utilities
    └── logging.py               # Structured logging
```

## API Service (`api/`)

```
api/
├── main.py                      # FastAPI application
├── routes/                      # API endpoints
│   ├── agents.py
│   ├── workflows.py
│   ├── runs.py
│   └── health.py
├── services/                    # Business logic
│   ├── workflow_service.py
│   └── execution_service.py
├── models/                      # API models
│   └── workflow.py
├── migrations/                  # Alembic migrations
│   └── versions/
└── README.md                    # API documentation
```

## UI Application (`workflow-ui/`)

```
workflow-ui/
├── src/
│   ├── components/              # React components
│   │   ├── workflows/           # Workflow management
│   │   ├── runs/                # Run monitoring
│   │   └── common/              # Shared components
│   ├── services/                # API clients
│   ├── types/                   # TypeScript types
│   └── App.tsx                  # Main application
├── public/                      # Static assets
├── package.json                 # Node dependencies
└── README.md                    # UI documentation
```

## Documentation (`docs/`)

```
docs/
├── README.md                    # Documentation index
├── api/                         # API documentation
│   ├── API_DOCUMENTATION.md
│   ├── A2A_AGENT_INTERFACE.md
│   ├── SWAGGER_GUIDE.md
│   └── ...
├── deployment/                  # Deployment guides
│   ├── DEPLOYMENT_GUIDE.md
│   ├── MIGRATION_GUIDE.md
│   └── ...
├── testing/                     # Testing documentation
│   ├── TESTING_ARCHITECTURE.md
│   ├── MANUAL_TESTING_GUIDE.md
│   └── ...
├── guides/                      # User guides
│   ├── QUICKSTART.md
│   ├── DEVELOPMENT.md
│   ├── WORKFLOW_FORMAT.md
│   └── ...
├── architecture/                # Architecture docs
│   ├── ORCHESTRATOR_ARCHITECTURE_SUMMARY.md
│   └── ...
├── features/                    # Feature documentation
│   ├── parallel_execution.md
│   ├── conditional_logic.md
│   ├── loop_execution.md
│   ├── fork_join_pattern.md
│   ├── circuit_breaker.md
│   └── ...
└── ui/                          # UI documentation
    ├── CONDITIONAL_LOGIC_UI.md
    ├── WORKFLOW_VISUALIZER_IMPLEMENTATION.md
    └── ...
```

## Tests (`tests/`)

```
tests/
├── README.md                    # Testing guide
├── test_api_executor_integration.py
├── test_circuit_breaker.py
├── test_conditional_logic.py
├── test_error_scenarios.py
├── test_jsonrpc_deployment.py
├── test_workflow_jsonrpc.py
├── test_database_setup.py
├── e2e_test.py
└── simple_e2e_test.py
```

## Scripts (`scripts/`)

```
scripts/
├── README.md                    # Scripts documentation
├── start_api.sh                 # Start API server
├── restart-api.sh               # Restart API
├── deploy-api.sh                # Deploy API
├── run-migrations.sh            # Run database migrations
├── test_circuit_breaker_live.sh # Test circuit breaker
├── ui-build.sh                  # Build UI
├── ui-deploy.sh                 # Deploy UI
├── migrate_workflows.py         # Migrate workflows
├── register_agents.py           # Register agents
└── ...
```

## Examples (`examples/`)

```
examples/
├── README.md                    # Examples documentation
├── TESTING.md                   # Testing guide
├── sample_workflow.json         # Basic workflow
├── parallel_workflow_example.json
├── conditional_workflow_example.json
├── loop_sequential_example.json
├── fork_join_example.json
├── circuit_breaker_example.json
├── mock_agent.py                # Mock agent for testing
└── mock_failing_agent.py        # Failing agent for testing
```

## Migrations (`migrations/`)

```
migrations/
├── README.md                    # Migration documentation
├── 001_add_parallel_execution_columns.sql
├── 002_add_conditional_execution_columns.sql
├── 003_add_loop_execution_columns.sql
└── *_rollback.sql               # Rollback scripts
```

## Configuration Files

### Environment Configuration
- `.env.example` - Template for environment variables
- `.env` - Local environment variables (not in git)
- `.env.api` - API-specific environment variables

### Docker Configuration
- `docker-compose.yml` - Main services (Kafka, PostgreSQL, Redis)
- `docker-compose.test.yml` - Test services (mock agents)
- `Dockerfile` - Container image definitions

### Python Configuration
- `requirements.txt` - Python dependencies
- `setup.py` - Package setup (if applicable)

### Node Configuration
- `workflow-ui/package.json` - Node dependencies
- `workflow-ui/tsconfig.json` - TypeScript configuration

## Key Files by Purpose

### Getting Started
1. `README.md` - Start here
2. `docs/guides/QUICKSTART.md` - Quick setup
3. `quick-start.sh` - Automated setup

### Development
1. `docs/guides/DEVELOPMENT.md` - Development guide
2. `docs/guides/configuration.md` - Configuration guide
3. `docker-compose.yml` - Local environment

### API Development
1. `docs/api/API_DOCUMENTATION.md` - API reference
2. `api/README.md` - API setup
3. `openapi.yaml` - API specification

### Testing
1. `tests/README.md` - Testing guide
2. `docs/testing/TESTING_ARCHITECTURE.md` - Test architecture
3. `docs/testing/MANUAL_TESTING_GUIDE.md` - Manual testing

### Deployment
1. `docs/deployment/DEPLOYMENT_GUIDE.md` - Deployment procedures
2. `docs/deployment/MIGRATION_GUIDE.md` - Migration guide
3. `scripts/deploy-api.sh` - Deployment script

### Features
1. `docs/features/parallel_execution.md` - Parallel execution
2. `docs/features/conditional_logic.md` - Conditional logic
3. `docs/features/loop_execution.md` - Loop execution
4. `docs/features/fork_join_pattern.md` - Fork-join pattern
5. `docs/features/circuit_breaker.md` - Circuit breaker

## Navigation Tips

### Finding Documentation
1. Check `docs/README.md` for the complete index
2. Use subdirectories to narrow down: api/, deployment/, testing/, etc.
3. README files in each directory provide context

### Finding Scripts
1. Check `scripts/README.md` for all available scripts
2. Scripts are organized by purpose (API, testing, deployment, etc.)
3. Use descriptive names to find what you need

### Finding Tests
1. Check `tests/README.md` for testing guide
2. Test files are named by what they test: `test_<feature>.py`
3. E2E tests are clearly marked

### Finding Examples
1. Check `examples/README.md` for available examples
2. Example workflows are named by feature: `<feature>_example.json`
3. Mock agents for testing are also in examples/

## Common Tasks

### Start Development Environment
```bash
./quick-start.sh
```

### Run Tests
```bash
pytest tests/
```

### Deploy to Production
```bash
./scripts/deploy-api.sh
```

### View API Documentation
```bash
# Start API and visit http://localhost:8000/docs
./scripts/start_api.sh
```

### Create New Workflow
See `docs/guides/WORKFLOW_FORMAT.md` and `examples/`

## Maintenance

### Adding New Documentation
1. Place in appropriate `docs/` subdirectory
2. Update `docs/README.md` with link
3. Use clear, descriptive filename

### Adding New Scripts
1. Place in `scripts/` directory
2. Make executable: `chmod +x script.sh`
3. Update `scripts/README.md`
4. Add usage comments in script

### Adding New Tests
1. Place in `tests/` directory
2. Name clearly: `test_<feature>.py`
3. Update `tests/README.md` if needed
4. Follow existing test patterns

## Questions?

- General: See `README.md`
- Documentation: See `docs/README.md`
- Scripts: See `scripts/README.md`
- Tests: See `tests/README.md`
- Examples: See `examples/README.md`

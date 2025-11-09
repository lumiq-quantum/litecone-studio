# Implementation Plan: Workflow Management API

## Overview

This implementation plan breaks down the development of the FastAPI-based Workflow Management API into discrete, manageable tasks. Each task builds incrementally on previous work.

---

## Phase 1: Project Setup and Foundation

- [x] 1. Set up FastAPI project structure
  - Create `api/` directory with modular structure (models, schemas, routes, services, repositories)
  - Set up `pyproject.toml` or `requirements.txt` with dependencies
  - Create `api/main.py` with FastAPI app initialization
  - Set up `api/config.py` for configuration management using pydantic-settings
  - _Requirements: All_

- [x] 2. Configure database connection and Alembic
  - Install SQLAlchemy 2.0+ and Alembic
  - Create `api/database.py` with async database engine and session factory
  - Initialize Alembic with `alembic init api/migrations`
  - Configure `alembic.ini` and `env.py` for async migrations
  - Create base model class with common fields (id, created_at, updated_at)
  - _Requirements: 5.1, 5.2_

- [x] 3. Set up development environment
  - Create `Dockerfile.api` for the FastAPI application
  - Update `docker-compose.yml` to include the API service
  - Create `.env.api` with development configuration
  - Add API service to orchestrator network
  - _Requirements: All_

---

## Phase 2: Database Models and Migrations

- [x] 4. Create Agent database model
  - Create `api/models/agent.py` with Agent SQLAlchemy model
  - Include fields: id, name, url, description, auth_type, auth_config, timeout_ms, retry_config, status, timestamps
  - Add indexes for name and status
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 5. Create Workflow database models
  - Create `api/models/workflow.py` with WorkflowDefinition model
  - Create WorkflowStep model with relationship to WorkflowDefinition
  - Include JSONB field for complete workflow data
  - Add indexes for name, status, and version
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 6. Enhance existing Run models
  - Update `src/database/models.py` to add workflow_definition_id, input_data, triggered_by fields
  - Add cancelled_at and cancelled_by fields
  - Create migration to alter existing tables
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3_

- [x] 7. Create Audit Log model
  - Create `api/models/audit.py` with AuditLog model
  - Include fields: entity_type, entity_id, action, user_id, changes, timestamp
  - Add indexes for entity lookups and timestamp
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 8. Generate initial database migration
  - Create Alembic migration for all new tables
  - Test migration up and down
  - Document migration in migration file
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

---

## Phase 3: Pydantic Schemas

- [x] 9. Create Agent schemas
  - Create `api/schemas/agent.py` with AgentCreate, AgentUpdate, AgentResponse schemas
  - Create RetryConfigSchema for nested retry configuration
  - Add validation for auth_type, timeout ranges, and URL format
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 8.1, 8.2, 8.4_

- [x] 10. Create Workflow schemas
  - Create `api/schemas/workflow.py` with WorkflowCreate, WorkflowUpdate, WorkflowResponse schemas
  - Create WorkflowStepSchema for step definitions
  - Add validation for workflow structure (no cycles, valid references)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.4, 8.5_

- [x] 11. Create Run schemas
  - Create `api/schemas/run.py` with WorkflowExecuteRequest, RunResponse, StepExecutionResponse schemas
  - Add schemas for retry and cancel operations
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3_

- [x] 12. Create common schemas
  - Create `api/schemas/common.py` with PaginationParams, PaginatedResponse schemas
  - Create ErrorResponse schema for consistent error formatting
  - Create HealthResponse schema
  - _Requirements: 6.1, 6.2, 6.3, 9.1, 9.2, 10.1, 10.2_

---

## Phase 4: Repository Layer

- [x] 13. Create base repository
  - Create `api/repositories/base.py` with BaseRepository class
  - Implement common CRUD operations (create, get_by_id, list, update, delete)
  - Add pagination support
  - Add soft delete functionality
  - _Requirements: 9.1, 9.2_

- [x] 14. Create Agent repository
  - Create `api/repositories/agent.py` extending BaseRepository
  - Implement get_by_name method
  - Implement list with status filtering
  - Implement soft delete
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.4_

- [x] 15. Create Workflow repository
  - Create `api/repositories/workflow.py` extending BaseRepository
  - Implement get_by_name_and_version method
  - Implement list_versions method
  - Implement list with filtering and sorting
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 9.3, 9.5_

- [x] 16. Create Run repository
  - Create `api/repositories/run.py` extending BaseRepository
  - Implement get_by_run_id method
  - Implement list with filtering by status, workflow_id, date range
  - Implement get_steps method
  - _Requirements: 4.1, 4.2, 4.3, 9.3_

- [x] 17. Create Audit repository
  - Create `api/repositories/audit.py` extending BaseRepository
  - Implement list with filtering by entity_type, entity_id, user_id, date range
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

---

## Phase 5: Service Layer

- [x] 18. Create Audit service
  - Create `api/services/audit.py` with AuditService class
  - Implement log_action method
  - Implement query_logs method with filtering
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [x] 19. Create Agent service
  - Create `api/services/agent.py` with AgentService class
  - Implement create_agent with audit logging
  - Implement get_agent, list_agents, update_agent, delete_agent
  - Implement check_agent_health method (HTTP call to agent)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 20. Create Workflow service
  - Create `api/services/workflow.py` with WorkflowService class
  - Implement create_workflow with validation and audit logging
  - Implement validate_agents method
  - Implement validate_workflow_structure method
  - Implement get_workflow, list_workflows, update_workflow, delete_workflow
  - Implement get_versions method
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.5_

- [x] 21. Create Kafka service
  - Create `api/services/kafka.py` with KafkaService class
  - Implement publish_execution_request method
  - Implement publish_cancellation_request method
  - Reuse existing KafkaProducerClient
  - _Requirements: 3.1, 3.3, 11.1, 11.2, 11.4_

- [x] 22. Create Execution service
  - Create `api/services/execution.py` with ExecutionService class
  - Implement execute_workflow method (create run, publish to Kafka)
  - Implement retry_workflow method (resume from last step)
  - Implement cancel_workflow method
  - Implement get_run, list_runs, get_run_steps methods
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 11.1, 11.3, 11.5_

---

## Phase 6: API Routes

- [x] 23. Create Agent routes
  - Create `api/routes/agents.py` with agent endpoints
  - Implement POST /api/v1/agents (create)
  - Implement GET /api/v1/agents (list with pagination)
  - Implement GET /api/v1/agents/{agent_id} (get details)
  - Implement PUT /api/v1/agents/{agent_id} (update)
  - Implement DELETE /api/v1/agents/{agent_id} (delete)
  - Implement GET /api/v1/agents/{agent_id}/health (health check)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 24. Create Workflow routes
  - Create `api/routes/workflows.py` with workflow endpoints
  - Implement POST /api/v1/workflows (create)
  - Implement GET /api/v1/workflows (list with pagination and filtering)
  - Implement GET /api/v1/workflows/{workflow_id} (get details)
  - Implement PUT /api/v1/workflows/{workflow_id} (update)
  - Implement DELETE /api/v1/workflows/{workflow_id} (delete)
  - Implement GET /api/v1/workflows/{workflow_id}/versions (list versions)
  - Implement POST /api/v1/workflows/{workflow_id}/execute (trigger execution)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1_

- [x] 25. Create Run routes
  - Create `api/routes/runs.py` with run endpoints
  - Implement GET /api/v1/runs (list with pagination and filtering)
  - Implement GET /api/v1/runs/{run_id} (get details)
  - Implement GET /api/v1/runs/{run_id}/steps (get step executions)
  - Implement POST /api/v1/runs/{run_id}/retry (retry failed run)
  - Implement POST /api/v1/runs/{run_id}/cancel (cancel running workflow)
  - Implement GET /api/v1/runs/{run_id}/logs (get logs - placeholder)
  - _Requirements: 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4_

- [x] 26. Create System routes
  - Create `api/routes/system.py` with system endpoints
  - Implement GET /health (basic health check)
  - Implement GET /health/ready (readiness check with DB connectivity)
  - Implement GET /metrics (Prometheus metrics - placeholder)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

---

## Phase 7: Middleware (Authentication Skipped)

- [ ]* 27. Implement authentication (OPTIONAL - Not needed for initial version)
  - Create `api/middleware/auth.py` with JWT and API key authentication
  - Implement get_current_user dependency
  - Implement API key validation
  - Add authentication to protected endpoints
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - _Note: APIs will be exposed directly without authentication for now_

- [x] 28. Implement error handling middleware
  - Create `api/middleware/error_handler.py` with global error handlers
  - Handle APIException, ValidationError, SQLAlchemyError
  - Return consistent error response format
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 29. Implement logging middleware
  - Create `api/middleware/logging.py` with request/response logging
  - Log all API requests with method, path, status, duration
  - Add correlation ID to logs
  - _Requirements: 12.1, 12.2, 12.3_

---

## Phase 8: Integration and Testing

- [x] 30. Integrate API with existing executor
  - Update executor to consume execution requests from API-published Kafka messages
  - Update executor to write run status back to database
  - Test end-to-end workflow execution flow
  - _Requirements: 11.1, 11.2, 11.3, 11.5_

- [x] 31. Create API documentation
  - Configure FastAPI to generate OpenAPI spec
  - Add descriptions and examples to all endpoints
  - Add tags for endpoint grouping
  - Test Swagger UI at /docs
  - Test ReDoc at /redoc
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 32. Write unit tests
  - Write tests for services with mocked repositories
  - Write tests for repositories with test database
  - Write tests for validators and utilities
  - Aim for >80% code coverage
  - _Requirements: All_

- [ ]* 33. Write integration tests
  - Write tests for API endpoints with test database
  - Write tests for Kafka integration
  - Write tests for database migrations
  - _Requirements: All_

- [ ]* 34. Write E2E tests
  - Test complete workflow creation and execution flow
  - Test retry and cancellation scenarios
  - Test error handling and validation
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

---

## Phase 9: Deployment and Documentation

- [x] 35. Create deployment configuration
  - Create `Dockerfile.api` for production
  - Update `docker-compose.yml` with API service
  - Create environment variable documentation
  - Add health check configuration
  - _Requirements: All_

- [x] 36. Create API usage documentation
  - Write comprehensive API documentation in Markdown
  - Include example requests for all endpoints
  - Document error codes and responses
  - Note: Authentication can be added later if needed
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 37. Create migration guide
  - Document how to migrate from CLI-based to API-based workflow execution
  - Provide scripts to import existing workflows into database
  - Document backward compatibility considerations
  - _Requirements: All_

---

## Phase 10: Monitoring and Observability

- [ ]* 38. Implement Prometheus metrics
  - Add prometheus-fastapi-instrumentator
  - Expose metrics at /metrics endpoint
  - Track request count, latency, error rate
  - Track workflow execution metrics
  - _Requirements: 10.3, 10.5_

- [ ]* 39. Implement structured logging
  - Configure JSON logging for production
  - Add correlation IDs to all logs
  - Log all database queries in debug mode
  - Integrate with existing logging utilities
  - _Requirements: 12.1, 12.2, 12.3_

- [ ]* 40. Add health checks and monitoring
  - Implement liveness probe (basic health)
  - Implement readiness probe (DB + Kafka connectivity)
  - Add alerting for error rates
  - Document monitoring setup
  - _Requirements: 10.1, 10.2, 10.4_

---

## Notes

- Tasks marked with `*` are optional but recommended for production readiness
- Each task should be completed and tested before moving to the next
- Database migrations should be tested both up and down
- All endpoints should have proper error handling and validation
- **Authentication is currently skipped** - APIs are exposed directly without auth
- Authentication (Task 27) can be implemented later when needed

## Dependencies

- **Phase 1** must be completed before any other phase
- **Phase 2** must be completed before Phase 4
- **Phase 3** can be done in parallel with Phase 2
- **Phase 4** must be completed before Phase 5
- **Phase 5** must be completed before Phase 6
- **Phase 6** can have tasks done in parallel
- **Phase 7** - Task 27 (authentication) is optional and can be skipped; Tasks 28-29 should be completed
- **Phase 8** integrates everything
- **Phase 9** and **Phase 10** can be done in parallel after Phase 8

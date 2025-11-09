# Requirements Document: Workflow Management API

## Introduction

This document specifies the requirements for a FastAPI-based management API that provides a web interface for the Centralized Executor and HTTP-Kafka Bridge system. The API will enable users to register agents, create workflows, trigger executions, and monitor runs through RESTful endpoints, replacing the current file-based and CLI-driven approach.

## Glossary

- **Management API**: FastAPI application providing REST endpoints for system management
- **Agent**: External service that executes tasks via the A2A protocol
- **Workflow**: A directed acyclic graph of steps executed sequentially
- **Workflow Definition**: The template/blueprint for a workflow stored in the database
- **Workflow Run**: A specific execution instance of a workflow definition
- **Step Execution**: The execution of a single step within a workflow run
- **Executor Service**: Background service that processes workflow runs
- **Database Migration**: Version-controlled database schema changes using Alembic

## Requirements

### Requirement 1: Agent Management

**User Story:** As a system administrator, I want to register and manage agents through a REST API, so that I can dynamically configure the system without modifying code.

#### Acceptance Criteria

1. WHEN I send a POST request to `/api/v1/agents`, THE Management API SHALL create a new agent record in the database
2. WHEN I send a GET request to `/api/v1/agents`, THE Management API SHALL return a paginated list of all registered agents
3. WHEN I send a GET request to `/api/v1/agents/{agent_id}`, THE Management API SHALL return the details of a specific agent
4. WHEN I send a PUT request to `/api/v1/agents/{agent_id}`, THE Management API SHALL update the agent configuration
5. WHEN I send a DELETE request to `/api/v1/agents/{agent_id}`, THE Management API SHALL soft-delete the agent and prevent it from being used in new workflows

### Requirement 2: Workflow Definition Management

**User Story:** As a workflow designer, I want to create and manage workflow definitions through a REST API, so that I can build and version workflows without manual file editing.

#### Acceptance Criteria

1. WHEN I send a POST request to `/api/v1/workflows`, THE Management API SHALL create a new workflow definition in the database
2. WHEN I send a GET request to `/api/v1/workflows`, THE Management API SHALL return a paginated list of all workflow definitions with filtering and sorting
3. WHEN I send a GET request to `/api/v1/workflows/{workflow_id}`, THE Management API SHALL return the complete workflow definition including all steps
4. WHEN I send a PUT request to `/api/v1/workflows/{workflow_id}`, THE Management API SHALL update the workflow definition and increment the version
5. WHEN I send a DELETE request to `/api/v1/workflows/{workflow_id}`, THE Management API SHALL soft-delete the workflow definition
6. WHEN I send a GET request to `/api/v1/workflows/{workflow_id}/versions`, THE Management API SHALL return all versions of the workflow definition

### Requirement 3: Workflow Execution

**User Story:** As a workflow operator, I want to trigger workflow executions through a REST API, so that I can run workflows programmatically without CLI commands.

#### Acceptance Criteria

1. WHEN I send a POST request to `/api/v1/workflows/{workflow_id}/execute`, THE Management API SHALL create a workflow run record and trigger the executor service
2. WHEN the workflow execution is triggered, THE Management API SHALL return the run_id immediately without waiting for completion
3. WHEN I send a POST request to `/api/v1/runs/{run_id}/retry`, THE Management API SHALL resume a failed workflow from the last incomplete step
4. WHEN I send a POST request to `/api/v1/runs/{run_id}/cancel`, THE Management API SHALL mark the run as cancelled and stop further step execution
5. WHEN a workflow run is created, THE Management API SHALL validate the input data against the workflow definition schema

### Requirement 4: Workflow Run Monitoring

**User Story:** As a workflow operator, I want to monitor workflow executions through a REST API, so that I can track progress and debug failures.

#### Acceptance Criteria

1. WHEN I send a GET request to `/api/v1/runs`, THE Management API SHALL return a paginated list of all workflow runs with filtering by status, workflow_id, and date range
2. WHEN I send a GET request to `/api/v1/runs/{run_id}`, THE Management API SHALL return the complete run details including status, timestamps, and error messages
3. WHEN I send a GET request to `/api/v1/runs/{run_id}/steps`, THE Management API SHALL return all step executions for the run with their status and output data
4. WHEN I send a GET request to `/api/v1/runs/{run_id}/logs`, THE Management API SHALL return the execution logs for the run
5. WHEN a workflow run status changes, THE Management API SHALL emit a webhook event to configured endpoints

### Requirement 5: Database Schema and Migrations

**User Story:** As a developer, I want database schema changes to be version-controlled through migrations, so that I can safely evolve the database structure.

#### Acceptance Criteria

1. WHEN the application starts, THE Management API SHALL apply pending database migrations automatically
2. WHEN I create a new migration, THE Management API SHALL use Alembic to generate migration scripts
3. WHEN a migration is applied, THE Management API SHALL record the migration version in the database
4. WHEN I need to rollback, THE Management API SHALL support downgrade migrations
5. WHEN the database schema changes, THE Management API SHALL maintain backward compatibility for at least one version

### Requirement 6: API Documentation

**User Story:** As an API consumer, I want comprehensive API documentation, so that I can integrate with the system easily.

#### Acceptance Criteria

1. WHEN I access `/docs`, THE Management API SHALL display interactive Swagger UI documentation
2. WHEN I access `/redoc`, THE Management API SHALL display ReDoc documentation
3. WHEN I access `/openapi.json`, THE Management API SHALL return the OpenAPI 3.0 specification
4. WHEN viewing the documentation, THE Management API SHALL include request/response examples for all endpoints
5. WHEN viewing the documentation, THE Management API SHALL include authentication requirements for protected endpoints

### Requirement 7: Authentication and Authorization

**User Story:** As a security administrator, I want API endpoints to be protected with authentication, so that only authorized users can manage workflows.

#### Acceptance Criteria

1. WHEN I access protected endpoints without authentication, THE Management API SHALL return 401 Unauthorized
2. WHEN I provide valid API key or JWT token, THE Management API SHALL authenticate the request
3. WHEN I attempt to perform an action without sufficient permissions, THE Management API SHALL return 403 Forbidden
4. WHEN authentication is enabled, THE Management API SHALL support role-based access control (RBAC)
5. WHEN an API key is compromised, THE Management API SHALL allow administrators to revoke it

### Requirement 8: Error Handling and Validation

**User Story:** As an API consumer, I want clear error messages and validation, so that I can quickly identify and fix issues.

#### Acceptance Criteria

1. WHEN I send invalid request data, THE Management API SHALL return 422 Unprocessable Entity with detailed validation errors
2. WHEN a resource is not found, THE Management API SHALL return 404 Not Found with a descriptive message
3. WHEN a server error occurs, THE Management API SHALL return 500 Internal Server Error and log the error details
4. WHEN validation fails, THE Management API SHALL return field-level error messages
5. WHEN a workflow definition is invalid, THE Management API SHALL validate the structure before saving

### Requirement 9: Pagination and Filtering

**User Story:** As an API consumer, I want to paginate and filter large result sets, so that I can efficiently retrieve data.

#### Acceptance Criteria

1. WHEN I request a list endpoint, THE Management API SHALL support pagination with `page` and `page_size` parameters
2. WHEN I request a list endpoint, THE Management API SHALL return pagination metadata (total, page, page_size, total_pages)
3. WHEN I request workflow runs, THE Management API SHALL support filtering by status, workflow_id, created_date_range
4. WHEN I request agents, THE Management API SHALL support filtering by name and status
5. WHEN I request workflows, THE Management API SHALL support sorting by name, created_at, updated_at

### Requirement 10: Health and Metrics

**User Story:** As a DevOps engineer, I want health check and metrics endpoints, so that I can monitor the API service.

#### Acceptance Criteria

1. WHEN I send a GET request to `/health`, THE Management API SHALL return the service health status
2. WHEN I send a GET request to `/health/ready`, THE Management API SHALL return readiness status including database connectivity
3. WHEN I send a GET request to `/metrics`, THE Management API SHALL return Prometheus-compatible metrics
4. WHEN the database is unavailable, THE Management API SHALL return unhealthy status
5. WHEN monitoring the API, THE Management API SHALL expose metrics for request count, latency, and error rate

### Requirement 11: Workflow Execution Service Integration

**User Story:** As a system architect, I want the API to integrate with the existing executor service, so that workflows are executed reliably.

#### Acceptance Criteria

1. WHEN a workflow execution is triggered, THE Management API SHALL publish a message to Kafka for the executor service
2. WHEN the executor service completes a run, THE Management API SHALL update the run status in the database
3. WHEN the executor service fails, THE Management API SHALL record the error and mark the run as failed
4. WHEN a workflow is cancelled, THE Management API SHALL notify the executor service via Kafka
5. WHEN the executor service is unavailable, THE Management API SHALL queue execution requests for later processing

### Requirement 12: Audit Logging

**User Story:** As a compliance officer, I want all API actions to be logged, so that I can audit system changes.

#### Acceptance Criteria

1. WHEN an agent is created, updated, or deleted, THE Management API SHALL log the action with user, timestamp, and changes
2. WHEN a workflow is created, updated, or deleted, THE Management API SHALL log the action with user, timestamp, and changes
3. WHEN a workflow execution is triggered, THE Management API SHALL log the action with user, timestamp, and input data
4. WHEN I query audit logs, THE Management API SHALL support filtering by user, action type, and date range
5. WHEN audit logs are stored, THE Management API SHALL retain them for at least 90 days

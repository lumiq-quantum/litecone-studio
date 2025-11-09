# Workflow Management API - Complete Usage Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [Agent Management](#agent-management)
5. [Workflow Management](#workflow-management)
6. [Workflow Execution](#workflow-execution)
7. [Run Monitoring](#run-monitoring)
8. [System & Health](#system--health)
9. [Error Handling](#error-handling)
10. [Common Workflows](#common-workflows)
11. [Best Practices](#best-practices)

---

## Introduction

The Workflow Management API is a RESTful API for managing multi-agent workflow orchestration. It provides comprehensive endpoints for:

- **Agent Registration**: Register and manage external agents that execute workflow steps
- **Workflow Definitions**: Create, version, and manage workflow templates
- **Workflow Execution**: Trigger asynchronous workflow executions
- **Run Monitoring**: Track execution status, view step details, retry failures, and cancel runs
- **System Health**: Monitor API health and metrics

**Base URL**: `http://localhost:8000`  
**API Version**: `v1`  
**API Prefix**: `/api/v1`

### Key Features

- Asynchronous workflow execution via Kafka
- Automatic workflow versioning
- Retry and cancellation support
- Comprehensive filtering and pagination
- Interactive API documentation (Swagger UI & ReDoc)
- Prometheus metrics endpoint

---

## Getting Started

### Prerequisites

- API server running on `http://localhost:8000`
- PostgreSQL database configured
- Kafka broker accessible


### Quick Start

1. **Verify API is running**:
```bash
curl http://localhost:8000/health
```

2. **Access interactive documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

3. **Create your first agent**:
```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-agent",
    "url": "http://my-agent:8080"
  }'
```

---

## Authentication

**Current Status**: Authentication is **not currently enforced**. All endpoints are publicly accessible.

**Future Implementation**: When authentication is enabled, the API will support:
- **JWT Tokens**: `Authorization: Bearer <token>`
- **API Keys**: `X-API-Key: <key>`

For now, you can make requests without authentication headers.

---

## Agent Management

Agents are external services that execute workflow steps via the A2A (Agent-to-Agent) protocol.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/agents` | Create a new agent |
| GET | `/api/v1/agents` | List all agents |
| GET | `/api/v1/agents/{agent_id}` | Get agent details |
| PUT | `/api/v1/agents/{agent_id}` | Update an agent |
| DELETE | `/api/v1/agents/{agent_id}` | Delete an agent |
| GET | `/api/v1/agents/{agent_id}/health` | Check agent health |


### Create Agent

**Endpoint**: `POST /api/v1/agents`  
**Status Code**: `201 Created`

Creates a new agent in the system. Agent names must be unique.

**Request Body**:
```json
{
  "name": "data-processor",
  "url": "http://data-processor:8080",
  "description": "Processes data transformations",
  "auth_type": "bearer",
  "auth_config": {
    "token": "secret-token-123"
  },
  "timeout_ms": 30000,
  "retry_config": {
    "max_retries": 3,
    "initial_delay_ms": 1000,
    "max_delay_ms": 30000,
    "backoff_multiplier": 2.0
  }
}
```

**Field Descriptions**:
- `name` (required): Unique agent name (1-255 characters)
- `url` (required): HTTP endpoint URL for the agent
- `description` (optional): Human-readable description
- `auth_type` (optional): Authentication type - `none`, `bearer`, or `apikey` (default: `none`)
- `auth_config` (optional): Authentication configuration object
- `timeout_ms` (optional): Request timeout in milliseconds (1000-300000, default: 30000)
- `retry_config` (optional): Retry configuration object

**Retry Config Fields**:
- `max_retries`: Maximum retry attempts (0-10, default: 3)
- `initial_delay_ms`: Initial delay before first retry (min: 100, default: 1000)
- `max_delay_ms`: Maximum delay between retries (min: 1000, default: 30000)
- `backoff_multiplier`: Exponential backoff multiplier (min: 1.0, default: 2.0)

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data-processor",
    "url": "http://data-processor:8080",
    "description": "Processes data transformations",
    "timeout_ms": 60000
  }'
```

**Success Response** (201):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "data-processor",
  "url": "http://data-processor:8080",
  "description": "Processes data transformations",
  "auth_type": "none",
  "timeout_ms": 60000,
  "retry_config": {
    "max_retries": 3,
    "initial_delay_ms": 1000,
    "max_delay_ms": 30000,
    "backoff_multiplier": 2.0
  },
  "status": "active",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Agent name already exists
- `422 Unprocessable Entity`: Validation error (invalid field values)


### List Agents

**Endpoint**: `GET /api/v1/agents`  
**Status Code**: `200 OK`

Retrieves a paginated list of agents with optional filtering.

**Query Parameters**:
- `page` (optional): Page number, 1-indexed (default: 1)
- `page_size` (optional): Items per page, 1-100 (default: 20)
- `status` (optional): Filter by status - `active`, `inactive`, or `deleted`

**Example Request**:
```bash
curl "http://localhost:8000/api/v1/agents?page=1&page_size=20&status=active"
```

**Success Response** (200):
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "data-processor",
      "url": "http://data-processor:8080",
      "description": "Processes data transformations",
      "auth_type": "none",
      "timeout_ms": 30000,
      "retry_config": {
        "max_retries": 3,
        "initial_delay_ms": 1000,
        "max_delay_ms": 30000,
        "backoff_multiplier": 2.0
      },
      "status": "active",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Get Agent

**Endpoint**: `GET /api/v1/agents/{agent_id}`  
**Status Code**: `200 OK`

Retrieves detailed information about a specific agent.

**Path Parameters**:
- `agent_id` (required): UUID of the agent

**Example Request**:
```bash
curl http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000
```

**Success Response** (200): Same structure as Create Agent response

**Error Responses**:
- `404 Not Found`: Agent does not exist


### Update Agent

**Endpoint**: `PUT /api/v1/agents/{agent_id}`  
**Status Code**: `200 OK`

Updates an existing agent. Only provided fields are updated (partial update).

**Path Parameters**:
- `agent_id` (required): UUID of the agent

**Request Body** (all fields optional):
```json
{
  "url": "http://new-url:8080",
  "description": "Updated description",
  "auth_type": "apikey",
  "auth_config": {
    "key": "new-api-key"
  },
  "timeout_ms": 60000,
  "retry_config": {
    "max_retries": 5
  },
  "status": "inactive"
}
```

**Example Request**:
```bash
curl -X PUT http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "timeout_ms": 60000
  }'
```

**Success Response** (200): Updated agent object

**Error Responses**:
- `404 Not Found`: Agent does not exist
- `422 Unprocessable Entity`: Validation error

### Delete Agent

**Endpoint**: `DELETE /api/v1/agents/{agent_id}`  
**Status Code**: `200 OK`

Soft deletes an agent. The agent is marked as deleted and cannot be used in new workflows.

**Path Parameters**:
- `agent_id` (required): UUID of the agent

**Example Request**:
```bash
curl -X DELETE http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000
```

**Success Response** (200):
```json
{
  "message": "Agent '123e4567-e89b-12d3-a456-426614174000' deleted successfully"
}
```

**Error Responses**:
- `404 Not Found`: Agent does not exist

### Check Agent Health

**Endpoint**: `GET /api/v1/agents/{agent_id}/health`  
**Status Code**: `200 OK`

Performs a health check on an agent by calling its `/health` endpoint.

**Path Parameters**:
- `agent_id` (required): UUID of the agent

**Example Request**:
```bash
curl http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/health
```

**Success Response** (200):
```json
{
  "healthy": true,
  "status_code": 200,
  "response_time_ms": 45.23,
  "error": null
}
```

**Unhealthy Response** (200):
```json
{
  "healthy": false,
  "status_code": null,
  "response_time_ms": null,
  "error": "Connection timeout after 30000ms"
}
```

**Error Responses**:
- `404 Not Found`: Agent does not exist

---

## Workflow Management

Workflows define directed acyclic graphs (DAGs) of steps executed sequentially by agents.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/workflows` | Create a new workflow |
| GET | `/api/v1/workflows` | List all workflows |
| GET | `/api/v1/workflows/{workflow_id}` | Get workflow details |
| PUT | `/api/v1/workflows/{workflow_id}` | Update a workflow |
| DELETE | `/api/v1/workflows/{workflow_id}` | Delete a workflow |
| GET | `/api/v1/workflows/{workflow_id}/versions` | Get workflow versions |
| POST | `/api/v1/workflows/{workflow_id}/execute` | Execute a workflow |

### Create Workflow

**Endpoint**: `POST /api/v1/workflows`  
**Status Code**: `201 Created`

Creates a new workflow definition. The workflow structure is validated to ensure:
- All referenced agents exist and are active
- No circular references exist
- All steps are reachable from the start_step

**Request Body**:
```json
{
  "name": "data-processing-pipeline",
  "description": "ETL pipeline for data processing",
  "start_step": "extract",
  "steps": {
    "extract": {
      "id": "extract",
      "agent_name": "DataExtractorAgent",
      "next_step": "transform",
      "input_mapping": {
        "source_url": "${workflow.input.data_source}",
        "format": "${workflow.input.format}"
      }
    },
    "transform": {
      "id": "transform",
      "agent_name": "DataTransformerAgent",
      "next_step": "load",
      "input_mapping": {
        "raw_data": "${extract.output.data}",
        "schema": "${workflow.input.schema}"
      }
    },
    "load": {
      "id": "load",
      "agent_name": "DataLoaderAgent",
      "next_step": null,
      "input_mapping": {
        "transformed_data": "${transform.output.data}",
        "destination": "${workflow.input.destination}"
      }
    }
  }
}
```

**Field Descriptions**:
- `name` (required): Unique workflow name (1-255 characters)
- `description` (optional): Human-readable description
- `start_step` (required): ID of the first step to execute
- `steps` (required): Dictionary of step definitions keyed by step ID

**Step Definition Fields**:
- `id` (required): Unique step identifier within the workflow
- `agent_name` (required): Name of the agent to execute this step
- `next_step` (optional): ID of the next step (null for final step)
- `input_mapping` (required): Dictionary mapping input variables to values

**Input Mapping Syntax**:
- `${workflow.input.field}`: Reference workflow input data
- `${step_id.output.field}`: Reference output from a previous step
- Static values: Use plain strings or numbers


**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data-processing-pipeline",
    "description": "ETL pipeline for data processing",
    "start_step": "extract",
    "steps": {
      "extract": {
        "id": "extract",
        "agent_name": "DataExtractorAgent",
        "next_step": "transform",
        "input_mapping": {
          "source_url": "${workflow.input.data_source}"
        }
      },
      "transform": {
        "id": "transform",
        "agent_name": "DataTransformerAgent",
        "next_step": null,
        "input_mapping": {
          "raw_data": "${extract.output.data}"
        }
      }
    }
  }'
```

**Success Response** (201):
```json
{
  "id": "456e7890-e89b-12d3-a456-426614174000",
  "name": "data-processing-pipeline",
  "description": "ETL pipeline for data processing",
  "version": 1,
  "workflow_data": {
    "start_step": "extract",
    "steps": {
      "extract": { ... },
      "transform": { ... }
    }
  },
  "status": "active",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Validation failed (agent not found, circular reference, invalid structure)
- `422 Unprocessable Entity`: Validation error (invalid field values)

### List Workflows

**Endpoint**: `GET /api/v1/workflows`  
**Status Code**: `200 OK`

Retrieves a paginated list of workflows with filtering and sorting.

**Query Parameters**:
- `page` (optional): Page number, 1-indexed (default: 1)
- `page_size` (optional): Items per page, 1-100 (default: 20)
- `status` (optional): Filter by status - `active`, `inactive`, or `deleted`
- `name` (optional): Filter by exact name match
- `sort_by` (optional): Sort field - `name`, `created_at`, `updated_at`, `version` (default: `created_at`)
- `sort_order` (optional): Sort order - `asc` or `desc` (default: `desc`)

**Example Request**:
```bash
curl "http://localhost:8000/api/v1/workflows?page=1&page_size=20&status=active&sort_by=name&sort_order=asc"
```

**Success Response** (200):
```json
{
  "items": [
    {
      "id": "456e7890-e89b-12d3-a456-426614174000",
      "name": "data-processing-pipeline",
      "description": "ETL pipeline for data processing",
      "version": 1,
      "workflow_data": { ... },
      "status": "active",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```


### Get Workflow

**Endpoint**: `GET /api/v1/workflows/{workflow_id}`  
**Status Code**: `200 OK`

Retrieves detailed information about a specific workflow.

**Path Parameters**:
- `workflow_id` (required): UUID of the workflow

**Example Request**:
```bash
curl http://localhost:8000/api/v1/workflows/456e7890-e89b-12d3-a456-426614174000
```

**Success Response** (200): Same structure as Create Workflow response

**Error Responses**:
- `404 Not Found`: Workflow does not exist

### Update Workflow

**Endpoint**: `PUT /api/v1/workflows/{workflow_id}`  
**Status Code**: `200 OK`

Updates an existing workflow. If `steps` or `start_step` are modified, the version is automatically incremented.

**Path Parameters**:
- `workflow_id` (required): UUID of the workflow

**Request Body** (all fields optional):
```json
{
  "description": "Updated description",
  "start_step": "new_start",
  "steps": { ... },
  "status": "inactive"
}
```

**Example Request**:
```bash
curl -X PUT http://localhost:8000/api/v1/workflows/456e7890-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated ETL pipeline with validation",
    "status": "active"
  }'
```

**Success Response** (200): Updated workflow object with incremented version if structure changed

**Error Responses**:
- `404 Not Found`: Workflow does not exist
- `400 Bad Request`: Validation failed
- `422 Unprocessable Entity`: Validation error

### Delete Workflow

**Endpoint**: `DELETE /api/v1/workflows/{workflow_id}`  
**Status Code**: `200 OK`

Soft deletes a workflow. The workflow is marked as deleted and cannot be used for new executions.

**Path Parameters**:
- `workflow_id` (required): UUID of the workflow

**Example Request**:
```bash
curl -X DELETE http://localhost:8000/api/v1/workflows/456e7890-e89b-12d3-a456-426614174000
```

**Success Response** (200):
```json
{
  "message": "Workflow '456e7890-e89b-12d3-a456-426614174000' deleted successfully"
}
```

**Error Responses**:
- `404 Not Found`: Workflow does not exist


### Get Workflow Versions

**Endpoint**: `GET /api/v1/workflows/{workflow_id}/versions`  
**Status Code**: `200 OK`

Retrieves all versions of a workflow, ordered by version number (newest first).

**Path Parameters**:
- `workflow_id` (required): UUID of any version of the workflow

**Query Parameters**:
- `page` (optional): Page number, 1-indexed (default: 1)
- `page_size` (optional): Items per page, 1-100 (default: 20)

**Example Request**:
```bash
curl "http://localhost:8000/api/v1/workflows/456e7890-e89b-12d3-a456-426614174000/versions?page=1&page_size=10"
```

**Success Response** (200):
```json
{
  "items": [
    {
      "id": "456e7890-e89b-12d3-a456-426614174000",
      "name": "data-processing-pipeline",
      "version": 3,
      "workflow_data": { ... },
      "status": "active",
      "created_at": "2024-01-03T10:00:00Z",
      "updated_at": "2024-01-03T10:00:00Z"
    },
    {
      "id": "456e7890-e89b-12d3-a456-426614174001",
      "name": "data-processing-pipeline",
      "version": 2,
      "workflow_data": { ... },
      "status": "inactive",
      "created_at": "2024-01-02T10:00:00Z",
      "updated_at": "2024-01-02T10:00:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

**Error Responses**:
- `404 Not Found`: Workflow does not exist

---

## Workflow Execution

### Execute Workflow

**Endpoint**: `POST /api/v1/workflows/{workflow_id}/execute`  
**Status Code**: `202 Accepted`

Triggers asynchronous execution of a workflow. Returns immediately with run details.

**Path Parameters**:
- `workflow_id` (required): UUID of the workflow to execute

**Request Body**:
```json
{
  "input_data": {
    "data_source": "https://api.example.com/data",
    "format": "json",
    "schema": "v2",
    "destination": "s3://bucket/output/"
  }
}
```

**Field Descriptions**:
- `input_data` (required): Dictionary of input data for the workflow. Keys should match the variables referenced in step input_mappings (e.g., `${workflow.input.data_source}`)

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/workflows/456e7890-e89b-12d3-a456-426614174000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "data_source": "https://api.example.com/data",
      "format": "json"
    }
  }'
```


**Success Response** (202):
```json
{
  "id": "run-789e0123-e89b-12d3-a456-426614174000",
  "run_id": "run-789e0123-e89b-12d3-a456-426614174000",
  "workflow_id": "wf-data-pipeline-001",
  "workflow_name": "data-processing-pipeline",
  "workflow_definition_id": "456e7890-e89b-12d3-a456-426614174000",
  "status": "PENDING",
  "input_data": {
    "data_source": "https://api.example.com/data",
    "format": "json"
  },
  "triggered_by": "system",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "completed_at": null,
  "cancelled_at": null,
  "cancelled_by": null,
  "error_message": null
}
```

**Error Responses**:
- `404 Not Found`: Workflow does not exist
- `400 Bad Request`: Workflow is not active or validation failed
- `422 Unprocessable Entity`: Validation error

**Notes**:
- The workflow executes asynchronously via Kafka
- Use the returned `run_id` to monitor progress
- Poll `/api/v1/runs/{run_id}` to check status

---

## Run Monitoring

Monitor and control workflow executions.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/runs` | List all runs |
| GET | `/api/v1/runs/{run_id}` | Get run details |
| GET | `/api/v1/runs/{run_id}/steps` | Get step executions |
| POST | `/api/v1/runs/{run_id}/retry` | Retry a failed run |
| POST | `/api/v1/runs/{run_id}/cancel` | Cancel a running workflow |
| GET | `/api/v1/runs/{run_id}/logs` | Get run logs (placeholder) |

### List Runs

**Endpoint**: `GET /api/v1/runs`  
**Status Code**: `200 OK`

Retrieves a paginated list of workflow runs with filtering and sorting.

**Query Parameters**:
- `page` (optional): Page number, 1-indexed (default: 1)
- `page_size` (optional): Items per page, 1-100 (default: 20)
- `status` (optional): Filter by status - `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`
- `workflow_id` (optional): Filter by workflow_id (e.g., `wf-data-pipeline-001`)
- `workflow_definition_id` (optional): Filter by workflow_definition_id (UUID)
- `created_after` (optional): Filter runs created after timestamp (ISO 8601 format)
- `created_before` (optional): Filter runs created before timestamp (ISO 8601 format)
- `sort_by` (optional): Sort field - `created_at`, `updated_at`, `completed_at`, `status` (default: `created_at`)
- `sort_order` (optional): Sort order - `asc` or `desc` (default: `desc`)

**Example Request**:
```bash
curl "http://localhost:8000/api/v1/runs?status=FAILED&created_after=2024-01-01T00:00:00Z&sort_by=created_at&sort_order=desc"
```


**Success Response** (200):
```json
{
  "items": [
    {
      "id": "run-789e0123-e89b-12d3-a456-426614174000",
      "run_id": "run-789e0123-e89b-12d3-a456-426614174000",
      "workflow_id": "wf-data-pipeline-001",
      "workflow_name": "data-processing-pipeline",
      "workflow_definition_id": "456e7890-e89b-12d3-a456-426614174000",
      "status": "FAILED",
      "input_data": { ... },
      "triggered_by": "system",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:05:00Z",
      "completed_at": "2024-01-01T10:05:00Z",
      "cancelled_at": null,
      "cancelled_by": null,
      "error_message": "Step 'transform' failed: Connection timeout"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Get Run

**Endpoint**: `GET /api/v1/runs/{run_id}`  
**Status Code**: `200 OK`

Retrieves detailed information about a specific workflow run.

**Path Parameters**:
- `run_id` (required): Run identifier

**Example Request**:
```bash
curl http://localhost:8000/api/v1/runs/run-789e0123-e89b-12d3-a456-426614174000
```

**Success Response** (200):
```json
{
  "id": "run-789e0123-e89b-12d3-a456-426614174000",
  "run_id": "run-789e0123-e89b-12d3-a456-426614174000",
  "workflow_id": "wf-data-pipeline-001",
  "workflow_name": "data-processing-pipeline",
  "workflow_definition_id": "456e7890-e89b-12d3-a456-426614174000",
  "status": "COMPLETED",
  "input_data": {
    "data_source": "https://api.example.com/data",
    "format": "json"
  },
  "triggered_by": "system",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:05:00Z",
  "completed_at": "2024-01-01T10:05:00Z",
  "cancelled_at": null,
  "cancelled_by": null,
  "error_message": null
}
```

**Error Responses**:
- `404 Not Found`: Run does not exist

**Run Status Values**:
- `PENDING`: Run created, waiting to start
- `RUNNING`: Run is currently executing
- `COMPLETED`: Run finished successfully
- `FAILED`: Run failed with an error
- `CANCELLED`: Run was cancelled by user


### Get Run Steps

**Endpoint**: `GET /api/v1/runs/{run_id}/steps`  
**Status Code**: `200 OK`

Retrieves all step executions for a workflow run, ordered by start time.

**Path Parameters**:
- `run_id` (required): Run identifier

**Example Request**:
```bash
curl http://localhost:8000/api/v1/runs/run-789e0123-e89b-12d3-a456-426614174000/steps
```

**Success Response** (200):
```json
[
  {
    "id": "step-exec-123e4567-e89b-12d3-a456-426614174000",
    "run_id": "run-789e0123-e89b-12d3-a456-426614174000",
    "step_id": "extract",
    "step_name": "extract",
    "agent_name": "DataExtractorAgent",
    "status": "COMPLETED",
    "input_data": {
      "source_url": "https://api.example.com/data",
      "format": "json"
    },
    "output_data": {
      "data": [...],
      "record_count": 100
    },
    "started_at": "2024-01-01T10:00:00Z",
    "completed_at": "2024-01-01T10:01:00Z",
    "error_message": null
  },
  {
    "id": "step-exec-456e7890-e89b-12d3-a456-426614174000",
    "run_id": "run-789e0123-e89b-12d3-a456-426614174000",
    "step_id": "transform",
    "step_name": "transform",
    "agent_name": "DataTransformerAgent",
    "status": "COMPLETED",
    "input_data": {
      "raw_data": [...]
    },
    "output_data": {
      "transformed_data": [...]
    },
    "started_at": "2024-01-01T10:01:00Z",
    "completed_at": "2024-01-01T10:03:00Z",
    "error_message": null
  }
]
```

**Error Responses**:
- `404 Not Found`: Run does not exist

**Step Status Values**:
- `PENDING`: Step waiting to execute
- `RUNNING`: Step is currently executing
- `COMPLETED`: Step finished successfully
- `FAILED`: Step failed with an error
- `SKIPPED`: Step was skipped (conditional execution)

### Retry Run

**Endpoint**: `POST /api/v1/runs/{run_id}/retry`  
**Status Code**: `202 Accepted`

Retries a failed or cancelled workflow run. The executor resumes from the last incomplete step.

**Path Parameters**:
- `run_id` (required): Run identifier

**Request Body** (optional):
```json
{}
```

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/runs/run-789e0123-e89b-12d3-a456-426614174000/retry \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Success Response** (202): Updated run object with `PENDING` status

**Error Responses**:
- `404 Not Found`: Run does not exist
- `400 Bad Request`: Run cannot be retried (not in FAILED or CANCELLED status)


### Cancel Run

**Endpoint**: `POST /api/v1/runs/{run_id}/cancel`  
**Status Code**: `200 OK`

Cancels a pending or running workflow. The executor stops processing further steps.

**Path Parameters**:
- `run_id` (required): Run identifier

**Request Body** (optional):
```json
{
  "reason": "User requested cancellation due to incorrect input data"
}
```

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/runs/run-789e0123-e89b-12d3-a456-426614174000/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Incorrect input data provided"
  }'
```

**Success Response** (200):
```json
{
  "id": "run-789e0123-e89b-12d3-a456-426614174000",
  "run_id": "run-789e0123-e89b-12d3-a456-426614174000",
  "workflow_id": "wf-data-pipeline-001",
  "workflow_name": "data-processing-pipeline",
  "workflow_definition_id": "456e7890-e89b-12d3-a456-426614174000",
  "status": "CANCELLED",
  "input_data": { ... },
  "triggered_by": "system",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:02:00Z",
  "completed_at": null,
  "cancelled_at": "2024-01-01T10:02:00Z",
  "cancelled_by": "system",
  "error_message": "Cancelled: Incorrect input data provided"
}
```

**Error Responses**:
- `404 Not Found`: Run does not exist
- `400 Bad Request`: Run cannot be cancelled (not in PENDING or RUNNING status)

### Get Run Logs

**Endpoint**: `GET /api/v1/runs/{run_id}/logs`  
**Status Code**: `501 Not Implemented`

Placeholder endpoint for future log retrieval functionality.

**Path Parameters**:
- `run_id` (required): Run identifier

**Example Request**:
```bash
curl http://localhost:8000/api/v1/runs/run-789e0123-e89b-12d3-a456-426614174000/logs
```

**Response** (501):
```json
{
  "detail": {
    "message": "Log retrieval not yet implemented",
    "run_id": "run-789e0123-e89b-12d3-a456-426614174000",
    "note": "This endpoint will be implemented in a future release to integrate with a logging system"
  }
}
```

---

## System & Health

Health check and monitoring endpoints.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/ready` | Readiness check with dependencies |
| GET | `/metrics` | Prometheus metrics |

### Basic Health Check

**Endpoint**: `GET /health`  
**Status Code**: `200 OK`

Returns basic health status without checking dependencies. Useful for liveness probes.

**Example Request**:
```bash
curl http://localhost:8000/health
```

**Success Response** (200):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "services": null
}
```

### Readiness Check

**Endpoint**: `GET /health/ready`  
**Status Code**: `200 OK` or `503 Service Unavailable`

Returns readiness status including database and Kafka connectivity checks. Useful for readiness probes.

**Example Request**:
```bash
curl http://localhost:8000/health/ready
```

**Success Response** (200):
```json
{
  "ready": true,
  "timestamp": "2024-01-01T10:00:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection active",
      "response_time_ms": 12.5
    },
    "kafka": {
      "status": "unknown",
      "message": "Kafka health check not yet implemented",
      "response_time_ms": null
    }
  }
}
```

**Unhealthy Response** (503):
```json
{
  "ready": false,
  "timestamp": "2024-01-01T10:00:00Z",
  "checks": {
    "database": {
      "status": "unhealthy",
      "message": "Database connection failed: Connection refused",
      "response_time_ms": null
    },
    "kafka": {
      "status": "unknown",
      "message": "Kafka health check not yet implemented",
      "response_time_ms": null
    }
  }
}
```

### Prometheus Metrics

**Endpoint**: `GET /metrics`  
**Status Code**: `200 OK`

Returns Prometheus-compatible metrics in text format. Currently a placeholder.

**Example Request**:
```bash
curl http://localhost:8000/metrics
```

**Success Response** (200):
```
# HELP api_info API information
# TYPE api_info gauge
api_info{version="1.0.0"} 1

# HELP api_uptime_seconds API uptime in seconds
# TYPE api_uptime_seconds gauge
api_uptime_seconds 3600.50

# HELP api_requests_total Total number of API requests (placeholder)
# TYPE api_requests_total counter
api_requests_total 0
```

---

## Error Handling

The API uses standard HTTP status codes and returns consistent error responses.

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created successfully |
| 202 | Accepted - Request accepted for async processing |
| 400 | Bad Request - Invalid input or business logic error |
| 404 | Not Found - Resource does not exist |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Unexpected server error |
| 501 | Not Implemented - Feature not yet implemented |
| 503 | Service Unavailable - Service or dependencies unavailable |

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": "Error Type",
  "detail": "Detailed error message",
  "errors": [
    {
      "field": "field_name",
      "message": "Field-specific error message",
      "type": "error_type"
    }
  ],
  "status_code": 422,
  "timestamp": "2024-01-01T10:00:00Z",
  "path": "/api/v1/agents",
  "request_id": "req-123e4567-e89b-12d3-a456-426614174000"
}
```

### Common Error Examples

**Validation Error (422)**:
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": {}
    },
    {
      "type": "string_too_short",
      "loc": ["body", "url"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

**Not Found Error (404)**:
```json
{
  "detail": "Agent with id '123e4567-e89b-12d3-a456-426614174000' not found"
}
```

**Bad Request Error (400)**:
```json
{
  "detail": "Agent name 'data-processor' already exists"
}
```

**Business Logic Error (400)**:
```json
{
  "detail": "Agent 'NonExistentAgent' not found or inactive"
}
```

**Internal Server Error (500)**:
```json
{
  "detail": "An unexpected error occurred"
}
```

### Error Handling Best Practices

1. **Always check status codes**: Don't assume success
2. **Parse error details**: Use the `detail` field for user-friendly messages
3. **Handle validation errors**: The `errors` array provides field-level details
4. **Implement retries**: For 500 and 503 errors with exponential backoff
5. **Log errors**: Include `request_id` for debugging

---

## Common Workflows

### Workflow 1: Complete Setup and Execution

This workflow demonstrates the complete process from agent registration to workflow execution.

```bash
# Step 1: Create agents
EXTRACTOR_ID=$(curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DataExtractorAgent",
    "url": "http://extractor:8080",
    "description": "Extracts data from external sources"
  }' | jq -r '.id')

TRANSFORMER_ID=$(curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DataTransformerAgent",
    "url": "http://transformer:8080",
    "description": "Transforms raw data"
  }' | jq -r '.id')

echo "Created agents: $EXTRACTOR_ID, $TRANSFORMER_ID"

# Step 2: Create workflow
WORKFLOW_ID=$(curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data-pipeline",
    "description": "ETL pipeline",
    "start_step": "extract",
    "steps": {
      "extract": {
        "id": "extract",
        "agent_name": "DataExtractorAgent",
        "next_step": "transform",
        "input_mapping": {
          "source": "${workflow.input.source}"
        }
      },
      "transform": {
        "id": "transform",
        "agent_name": "DataTransformerAgent",
        "next_step": null,
        "input_mapping": {
          "data": "${extract.output.data}"
        }
      }
    }
  }' | jq -r '.id')

echo "Created workflow: $WORKFLOW_ID"

# Step 3: Execute workflow
RUN_ID=$(curl -X POST http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "source": "https://api.example.com/data"
    }
  }' | jq -r '.run_id')

echo "Started run: $RUN_ID"

# Step 4: Monitor execution
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/runs/$RUN_ID | jq -r '.status')
  echo "Run status: $STATUS"
  
  if [[ "$STATUS" == "COMPLETED" || "$STATUS" == "FAILED" || "$STATUS" == "CANCELLED" ]]; then
    break
  fi
  
  sleep 5
done

# Step 5: Get step details
curl http://localhost:8000/api/v1/runs/$RUN_ID/steps | jq '.'
```


### Workflow 2: Monitor and Retry Failed Runs

This workflow demonstrates how to find and retry failed runs.

```bash
# Step 1: List failed runs
echo "Finding failed runs..."
curl -s "http://localhost:8000/api/v1/runs?status=FAILED&sort_by=created_at&sort_order=desc" \
  | jq '.items[] | {run_id, workflow_name, error_message, created_at}'

# Step 2: Get details of a specific failed run
RUN_ID="run-789e0123-e89b-12d3-a456-426614174000"
echo "Getting details for run: $RUN_ID"
curl -s http://localhost:8000/api/v1/runs/$RUN_ID | jq '.'

# Step 3: Get step executions to identify failure point
echo "Getting step executions..."
curl -s http://localhost:8000/api/v1/runs/$RUN_ID/steps \
  | jq '.[] | {step_id, status, error_message}'

# Step 4: Retry the failed run
echo "Retrying run..."
curl -X POST http://localhost:8000/api/v1/runs/$RUN_ID/retry \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.'

# Step 5: Monitor retry progress
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/runs/$RUN_ID | jq -r '.status')
  echo "Retry status: $STATUS"
  
  if [[ "$STATUS" == "COMPLETED" || "$STATUS" == "FAILED" ]]; then
    break
  fi
  
  sleep 5
done
```

### Workflow 3: Update Workflow Version

This workflow demonstrates how to update a workflow and track versions.

```bash
# Step 1: Get current workflow
WORKFLOW_ID="456e7890-e89b-12d3-a456-426614174000"
echo "Current workflow:"
curl -s http://localhost:8000/api/v1/workflows/$WORKFLOW_ID | jq '{name, version, status}'

# Step 2: Update workflow (increments version)
echo "Updating workflow..."
curl -X PUT http://localhost:8000/api/v1/workflows/$WORKFLOW_ID \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated ETL pipeline with validation step",
    "steps": {
      "extract": {
        "id": "extract",
        "agent_name": "DataExtractorAgent",
        "next_step": "validate",
        "input_mapping": {
          "source": "${workflow.input.source}"
        }
      },
      "validate": {
        "id": "validate",
        "agent_name": "DataValidatorAgent",
        "next_step": "transform",
        "input_mapping": {
          "data": "${extract.output.data}"
        }
      },
      "transform": {
        "id": "transform",
        "agent_name": "DataTransformerAgent",
        "next_step": null,
        "input_mapping": {
          "data": "${validate.output.validated_data}"
        }
      }
    }
  }' | jq '{name, version, status}'

# Step 3: View all versions
echo "All versions:"
curl -s "http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/versions" \
  | jq '.items[] | {version, status, created_at}'
```


### Workflow 4: Cancel Long-Running Workflow

This workflow demonstrates how to cancel a running workflow.

```bash
# Step 1: Execute workflow
WORKFLOW_ID="456e7890-e89b-12d3-a456-426614174000"
RUN_ID=$(curl -X POST http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "source": "https://api.example.com/large-dataset"
    }
  }' | jq -r '.run_id')

echo "Started run: $RUN_ID"

# Step 2: Wait a bit, then check status
sleep 10
STATUS=$(curl -s http://localhost:8000/api/v1/runs/$RUN_ID | jq -r '.status')
echo "Current status: $STATUS"

# Step 3: Cancel the run
if [[ "$STATUS" == "RUNNING" || "$STATUS" == "PENDING" ]]; then
  echo "Cancelling run..."
  curl -X POST http://localhost:8000/api/v1/runs/$RUN_ID/cancel \
    -H "Content-Type: application/json" \
    -d '{
      "reason": "Dataset too large, need to optimize first"
    }' | jq '{status, cancelled_at, error_message}'
fi

# Step 4: Verify cancellation
curl -s http://localhost:8000/api/v1/runs/$RUN_ID \
  | jq '{status, cancelled_at, cancelled_by, error_message}'
```

### Workflow 5: Health Check All Agents

This workflow demonstrates how to check the health of all registered agents.

```bash
# Step 1: Get all active agents
echo "Checking health of all active agents..."
AGENTS=$(curl -s "http://localhost:8000/api/v1/agents?status=active" | jq -r '.items[] | .id')

# Step 2: Check health of each agent
for AGENT_ID in $AGENTS; do
  echo "Checking agent: $AGENT_ID"
  
  AGENT_NAME=$(curl -s http://localhost:8000/api/v1/agents/$AGENT_ID | jq -r '.name')
  HEALTH=$(curl -s http://localhost:8000/api/v1/agents/$AGENT_ID/health)
  
  HEALTHY=$(echo $HEALTH | jq -r '.healthy')
  RESPONSE_TIME=$(echo $HEALTH | jq -r '.response_time_ms')
  
  if [[ "$HEALTHY" == "true" ]]; then
    echo "  ✓ $AGENT_NAME is healthy (${RESPONSE_TIME}ms)"
  else
    ERROR=$(echo $HEALTH | jq -r '.error')
    echo "  ✗ $AGENT_NAME is unhealthy: $ERROR"
  fi
done
```

---

## Best Practices

### 1. Always Check Health Before Operations

Before performing critical operations, verify the API and its dependencies are healthy:

```bash
# Check basic health
curl http://localhost:8000/health

# Check readiness (includes DB and Kafka)
curl http://localhost:8000/health/ready
```

### 2. Use Pagination for Large Result Sets

Always use pagination when listing resources to avoid performance issues:

```bash
# Good: Use pagination
curl "http://localhost:8000/api/v1/runs?page=1&page_size=50"

# Bad: Don't request all results at once
# (API enforces max page_size of 100)
```

### 3. Filter Results to Reduce Response Size

Use filtering to get only the data you need:

```bash
# Filter by status and date range
curl "http://localhost:8000/api/v1/runs?status=FAILED&created_after=2024-01-01T00:00:00Z"

# Filter by workflow
curl "http://localhost:8000/api/v1/runs?workflow_id=wf-data-pipeline-001"
```

### 4. Monitor Workflow Execution Asynchronously

Don't block waiting for workflow completion. Poll the status endpoint:

```bash
# Trigger execution
RUN_ID=$(curl -X POST http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/execute \
  -H "Content-Type: application/json" \
  -d '{"input_data": {...}}' | jq -r '.run_id')

# Poll status with exponential backoff
DELAY=1
MAX_DELAY=60

while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/runs/$RUN_ID | jq -r '.status')
  
  if [[ "$STATUS" == "COMPLETED" || "$STATUS" == "FAILED" || "$STATUS" == "CANCELLED" ]]; then
    break
  fi
  
  sleep $DELAY
  DELAY=$((DELAY * 2))
  if [ $DELAY -gt $MAX_DELAY ]; then
    DELAY=$MAX_DELAY
  fi
done
```

### 5. Handle Errors Gracefully

Always check status codes and handle errors appropriately:

```bash
# Example with error handling
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "test-agent", "url": "http://test:8080"}')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ $HTTP_CODE -eq 201 ]; then
  echo "Success: Agent created"
  echo $BODY | jq '.'
elif [ $HTTP_CODE -eq 400 ]; then
  echo "Error: Bad request"
  echo $BODY | jq '.detail'
elif [ $HTTP_CODE -eq 422 ]; then
  echo "Error: Validation failed"
  echo $BODY | jq '.detail'
else
  echo "Error: Unexpected status code $HTTP_CODE"
  echo $BODY
fi
```

### 6. Use Descriptive Names and Descriptions

Make your agents and workflows easy to identify:

```json
{
  "name": "customer-data-etl-pipeline",
  "description": "Extracts customer data from CRM, transforms to standard format, and loads to data warehouse. Runs daily at 2 AM UTC."
}
```

### 7. Validate Workflow Structure Before Creation

Ensure all referenced agents exist before creating a workflow:

```bash
# Check if agent exists
AGENT_EXISTS=$(curl -s "http://localhost:8000/api/v1/agents?name=DataExtractorAgent" \
  | jq '.items | length')

if [ $AGENT_EXISTS -eq 0 ]; then
  echo "Error: Agent 'DataExtractorAgent' does not exist"
  exit 1
fi

# Now create workflow
curl -X POST http://localhost:8000/api/v1/workflows ...
```

### 8. Use Workflow Versions for Change Tracking

Track workflow changes by viewing version history:

```bash
# View all versions before making changes
curl "http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/versions" \
  | jq '.items[] | {version, created_at, status}'

# Update workflow (creates new version)
curl -X PUT http://localhost:8000/api/v1/workflows/$WORKFLOW_ID ...
```

### 9. Review Step Executions for Debugging

When a workflow fails, examine step executions to identify the failure point:

```bash
# Get failed run details
curl http://localhost:8000/api/v1/runs/$RUN_ID | jq '.'

# Get step executions
curl http://localhost:8000/api/v1/runs/$RUN_ID/steps \
  | jq '.[] | {step_id, status, error_message, started_at, completed_at}'
```

### 10. Use Consistent Input Data Structure

Maintain consistent input data structure across workflow executions:

```json
{
  "input_data": {
    "source": "https://api.example.com/data",
    "format": "json",
    "schema_version": "v2",
    "options": {
      "validate": true,
      "transform": true
    }
  }
}
```

---

## Additional Resources

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API explorer
  - Try endpoints directly in browser
  - View request/response schemas

- **ReDoc**: http://localhost:8000/redoc
  - Clean, readable documentation
  - Three-panel layout
  - Search functionality

### OpenAPI Specification

- **URL**: http://localhost:8000/openapi.json
- **Format**: OpenAPI 3.1.0 (JSON)
- **Use Cases**:
  - Generate client SDKs
  - Import into Postman/Insomnia
  - Integrate with API gateways

### Client SDK Generation

Generate client SDKs using the OpenAPI specification:

```bash
# Download OpenAPI spec
curl http://localhost:8000/openapi.json > openapi.json

# Generate Python client
openapi-generator-cli generate -i openapi.json -g python -o ./client-python

# Generate TypeScript client
openapi-generator-cli generate -i openapi.json -g typescript-axios -o ./client-typescript

# Generate Java client
openapi-generator-cli generate -i openapi.json -g java -o ./client-java
```

### Testing Tools

**cURL**:
```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d @agent.json
```

**HTTPie**:
```bash
http POST http://localhost:8000/api/v1/agents < agent.json
```

**Postman**:
1. Import OpenAPI spec: http://localhost:8000/openapi.json
2. Postman creates collection with all endpoints

**Python**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/agents",
    json={
        "name": "test-agent",
        "url": "http://test:8080"
    }
)
print(response.json())
```

---

## Support and Feedback

For issues, questions, or contributions:
- **Documentation**: See README.md and other docs in the repository
- **GitHub Issues**: Report bugs or request features
- **API Status**: Check `/health` and `/health/ready` endpoints

---

**Last Updated**: 2024-01-01  
**API Version**: 1.0.0

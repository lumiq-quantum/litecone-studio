# Workflow Management API Documentation

## Overview

The Workflow Management API is a comprehensive REST API for managing workflow orchestration in the Centralized Executor system. It provides endpoints for agent management, workflow definition management, workflow execution, and run monitoring.

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000` (development) or `http://api.example.com` (production)  
**API Prefix:** `/api/v1`

## Features

- **Agent Management**: Register and manage external agents that execute workflow steps
- **Workflow Definitions**: Create, version, and manage workflow templates
- **Workflow Execution**: Trigger and monitor workflow runs asynchronously
- **Run Management**: Track execution status, retry failed runs, and cancel active workflows
- **Health & Monitoring**: Built-in health checks and Prometheus metrics

## Interactive Documentation

The API provides interactive documentation through multiple interfaces:

### Swagger UI (Recommended for Testing)
- **URL:** `http://localhost:8000/docs`
- **Features:**
  - Interactive API explorer
  - Try out endpoints directly from the browser
  - View request/response schemas
  - See example requests and responses
  - Test authentication (when enabled)

### ReDoc (Recommended for Reading)
- **URL:** `http://localhost:8000/redoc`
- **Features:**
  - Clean, readable documentation
  - Three-panel layout
  - Search functionality
  - Code samples in multiple languages
  - Downloadable OpenAPI spec

### OpenAPI Specification
- **URL:** `http://localhost:8000/openapi.json`
- **Format:** OpenAPI 3.1.0 (JSON)
- **Use Cases:**
  - Generate client SDKs
  - Import into API testing tools (Postman, Insomnia)
  - Integrate with API gateways
  - Generate documentation in other formats

## Quick Start

### 1. Start the API Server

```bash
# Development mode with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Verify the API is Running

```bash
# Check basic health
curl http://localhost:8000/health

# Check readiness (includes dependency checks)
curl http://localhost:8000/health/ready

# Get API information
curl http://localhost:8000/
```

### 3. Access Interactive Documentation

Open your browser and navigate to:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Agent Management

Manage external agents that execute workflow steps.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/agents` | Create a new agent |
| GET | `/api/v1/agents` | List all agents (paginated) |
| GET | `/api/v1/agents/{agent_id}` | Get agent details |
| PUT | `/api/v1/agents/{agent_id}` | Update an agent |
| DELETE | `/api/v1/agents/{agent_id}` | Delete an agent (soft delete) |
| GET | `/api/v1/agents/{agent_id}/health` | Check agent health |

### Workflow Management

Create and manage workflow definitions.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/workflows` | Create a new workflow |
| GET | `/api/v1/workflows` | List all workflows (paginated, filterable) |
| GET | `/api/v1/workflows/{workflow_id}` | Get workflow details |
| PUT | `/api/v1/workflows/{workflow_id}` | Update a workflow |
| DELETE | `/api/v1/workflows/{workflow_id}` | Delete a workflow (soft delete) |
| GET | `/api/v1/workflows/{workflow_id}/versions` | Get all versions of a workflow |
| POST | `/api/v1/workflows/{workflow_id}/execute` | Execute a workflow |

### Run Management

Monitor and control workflow executions.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/runs` | List all runs (paginated, filterable) |
| GET | `/api/v1/runs/{run_id}` | Get run details |
| GET | `/api/v1/runs/{run_id}/steps` | Get step executions for a run |
| POST | `/api/v1/runs/{run_id}/retry` | Retry a failed run |
| POST | `/api/v1/runs/{run_id}/cancel` | Cancel a running workflow |
| GET | `/api/v1/runs/{run_id}/logs` | Get run logs (placeholder) |

### System & Monitoring

Health checks and monitoring endpoints.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and links |
| GET | `/health` | Basic health check (liveness probe) |
| GET | `/health/ready` | Readiness check with dependency validation |
| GET | `/metrics` | Prometheus metrics (placeholder) |

## Example Usage

### Creating an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data-processor",
    "url": "http://data-processor:8080",
    "description": "Processes data transformations",
    "auth_type": "bearer",
    "auth_config": {
      "token": "secret-token"
    },
    "timeout_ms": 30000,
    "retry_config": {
      "max_retries": 3,
      "initial_delay_ms": 1000,
      "max_delay_ms": 30000,
      "backoff_multiplier": 2.0
    }
  }'
```

### Creating a Workflow

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

### Executing a Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "data_source": "https://api.example.com/data",
      "output_format": "json"
    }
  }'
```

### Monitoring a Run

```bash
# Get run details
curl http://localhost:8000/api/v1/runs/{run_id}

# Get step executions
curl http://localhost:8000/api/v1/runs/{run_id}/steps

# List all runs with filtering
curl "http://localhost:8000/api/v1/runs?status=FAILED&page=1&page_size=20"
```

## Response Formats

### Success Response

All successful responses follow a consistent format:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "example-resource",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Paginated Response

List endpoints return paginated responses:

```json
{
  "items": [
    { "id": "...", "name": "..." }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### Error Response

All errors follow a consistent format:

```json
{
  "error": "Validation Error",
  "detail": "Request validation failed",
  "errors": [
    {
      "field": "name",
      "message": "Field required",
      "type": "missing"
    }
  ],
  "status_code": 422,
  "timestamp": "2024-01-01T10:00:00Z",
  "path": "/api/v1/agents",
  "request_id": "req-123e4567-e89b-12d3-a456-426614174000"
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created successfully |
| 202 | Accepted - Request accepted for processing |
| 400 | Bad Request - Invalid input or validation failed |
| 404 | Not Found - Resource does not exist |
| 422 | Unprocessable Entity - Request validation failed |
| 500 | Internal Server Error - Unexpected server error |
| 503 | Service Unavailable - Service or dependencies unavailable |

## Pagination

All list endpoints support pagination with the following query parameters:

- `page` (integer, default: 1): Page number (1-indexed)
- `page_size` (integer, default: 20, max: 100): Number of items per page

Example:
```
GET /api/v1/agents?page=2&page_size=50
```

## Filtering and Sorting

Many list endpoints support filtering and sorting:

### Agents
- `status`: Filter by status (active, inactive, deleted)

### Workflows
- `status`: Filter by status (active, inactive, deleted)
- `name`: Filter by exact name match
- `sort_by`: Sort field (name, created_at, updated_at, version)
- `sort_order`: Sort order (asc, desc)

### Runs
- `status`: Filter by status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
- `workflow_id`: Filter by workflow identifier
- `workflow_definition_id`: Filter by workflow definition UUID
- `created_after`: Filter runs created after timestamp (ISO 8601)
- `created_before`: Filter runs created before timestamp (ISO 8601)
- `sort_by`: Sort field (created_at, updated_at, completed_at, status)
- `sort_order`: Sort order (asc, desc)

Example:
```
GET /api/v1/runs?status=FAILED&created_after=2024-01-01T00:00:00Z&sort_by=created_at&sort_order=desc
```

## Authentication

**Note:** Authentication is currently not enforced. This will be added in a future release.

When authentication is enabled, the API will support:
- JWT tokens via `Authorization: Bearer <token>` header
- API keys via `X-API-Key: <key>` header

## Rate Limiting

Rate limiting is not currently implemented but will be added in a future release.

## Versioning

The API uses URL-based versioning with the prefix `/api/v1`. Future versions will use `/api/v2`, etc.

## Client SDK Generation

You can generate client SDKs in various languages using the OpenAPI specification:

```bash
# Download the OpenAPI spec
curl http://localhost:8000/openapi.json > openapi.json

# Generate Python client using openapi-generator
openapi-generator-cli generate -i openapi.json -g python -o ./client-python

# Generate TypeScript client
openapi-generator-cli generate -i openapi.json -g typescript-axios -o ./client-typescript

# Generate Java client
openapi-generator-cli generate -i openapi.json -g java -o ./client-java
```

## Testing with Postman

1. Import the OpenAPI specification into Postman:
   - Open Postman
   - Click "Import"
   - Select "Link" and enter: `http://localhost:8000/openapi.json`
   - Click "Import"

2. Postman will create a collection with all endpoints pre-configured

## Best Practices

### 1. Always Check Health Before Operations
```bash
curl http://localhost:8000/health/ready
```

### 2. Use Pagination for Large Result Sets
```bash
curl "http://localhost:8000/api/v1/runs?page=1&page_size=100"
```

### 3. Handle Errors Gracefully
Always check the `status_code` and `error` fields in error responses.

### 4. Use Filtering to Reduce Response Size
```bash
curl "http://localhost:8000/api/v1/runs?status=FAILED&workflow_id=wf-001"
```

### 5. Monitor Workflow Execution Asynchronously
After triggering execution, poll the run status endpoint:
```bash
# Trigger execution
RUN_ID=$(curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d '{"input_data": {...}}' | jq -r '.run_id')

# Poll status
while true; do
  STATUS=$(curl http://localhost:8000/api/v1/runs/$RUN_ID | jq -r '.status')
  echo "Status: $STATUS"
  if [[ "$STATUS" == "COMPLETED" || "$STATUS" == "FAILED" ]]; then
    break
  fi
  sleep 5
done
```

## Troubleshooting

### API Not Starting
- Check database connection in `.env.api`
- Verify Kafka brokers are accessible
- Check logs for detailed error messages

### 503 Service Unavailable
- Check `/health/ready` endpoint for dependency status
- Verify database and Kafka are running
- Check network connectivity

### 422 Validation Error
- Review the `errors` array in the response
- Check field-level validation messages
- Refer to schema examples in Swagger UI

### Workflow Execution Not Starting
- Verify workflow status is "active"
- Check that all referenced agents exist and are active
- Review workflow structure for circular references

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/your-org/workflow-management-api
- Email: support@example.com

## License

MIT License - See LICENSE file for details

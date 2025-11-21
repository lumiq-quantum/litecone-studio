# Workflow Management API - Quick Reference

## Documentation URLs

| Resource | URL |
|----------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI Spec | http://localhost:8000/openapi.json |
| API Info | http://localhost:8000/ |

## Common Endpoints

### Health & Status
```bash
# Liveness probe
GET /health

# Readiness probe (checks dependencies)
GET /health/ready

# Metrics (Prometheus format)
GET /metrics
```

### Agents
```bash
# Create agent
POST /api/v1/agents

# List agents
GET /api/v1/agents?page=1&page_size=20&status=active

# Get agent
GET /api/v1/agents/{agent_id}

# Update agent
PUT /api/v1/agents/{agent_id}

# Delete agent
DELETE /api/v1/agents/{agent_id}

# Health check
GET /api/v1/agents/{agent_id}/health
```

### Workflows
```bash
# Create workflow
POST /api/v1/workflows

# List workflows
GET /api/v1/workflows?page=1&page_size=20&status=active&sort_by=name

# Get workflow
GET /api/v1/workflows/{workflow_id}

# Update workflow
PUT /api/v1/workflows/{workflow_id}

# Delete workflow
DELETE /api/v1/workflows/{workflow_id}

# Get versions
GET /api/v1/workflows/{workflow_id}/versions

# Execute workflow
POST /api/v1/workflows/{workflow_id}/execute
```

### Runs
```bash
# List runs
GET /api/v1/runs?status=FAILED&page=1&page_size=20

# Get run
GET /api/v1/runs/{run_id}

# Get steps
GET /api/v1/runs/{run_id}/steps

# Retry run
POST /api/v1/runs/{run_id}/retry

# Cancel run
POST /api/v1/runs/{run_id}/cancel

# Get logs (placeholder)
GET /api/v1/runs/{run_id}/logs
```

## Request Examples

### Create Agent
```json
POST /api/v1/agents
{
  "name": "data-processor",
  "url": "http://data-processor:8080",
  "description": "Processes data transformations",
  "auth_type": "bearer",
  "auth_config": {"token": "secret"},
  "timeout_ms": 30000,
  "retry_config": {
    "max_retries": 3,
    "initial_delay_ms": 1000,
    "max_delay_ms": 30000,
    "backoff_multiplier": 2.0
  }
}
```

### Create Workflow
```json
POST /api/v1/workflows
{
  "name": "data-pipeline",
  "description": "ETL pipeline",
  "start_step": "extract",
  "steps": {
    "extract": {
      "id": "extract",
      "agent_name": "DataExtractor",
      "next_step": "transform",
      "input_mapping": {
        "source": "${workflow.input.source}"
      }
    },
    "transform": {
      "id": "transform",
      "agent_name": "DataTransformer",
      "next_step": null,
      "input_mapping": {
        "data": "${extract.output.data}"
      }
    }
  }
}
```

### Execute Workflow
```json
POST /api/v1/workflows/{workflow_id}/execute
{
  "input_data": {
    "source": "https://api.example.com/data",
    "format": "json"
  }
}
```

### Cancel Run
```json
POST /api/v1/runs/{run_id}/cancel
{
  "reason": "User requested cancellation"
}
```

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async operation) |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |
| 503 | Service Unavailable |

## Query Parameters

### Pagination
- `page` (default: 1, min: 1)
- `page_size` (default: 20, min: 1, max: 100)

### Filtering (Agents)
- `status`: active, inactive, deleted

### Filtering (Workflows)
- `status`: active, inactive, deleted
- `name`: exact match
- `sort_by`: name, created_at, updated_at, version
- `sort_order`: asc, desc

### Filtering (Runs)
- `status`: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
- `workflow_id`: workflow identifier
- `workflow_definition_id`: UUID
- `created_after`: ISO 8601 timestamp
- `created_before`: ISO 8601 timestamp
- `sort_by`: created_at, updated_at, completed_at, status
- `sort_order`: asc, desc

## Common Workflows

### 1. Register Agent and Create Workflow
```bash
# 1. Create agent
AGENT_ID=$(curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name":"processor","url":"http://processor:8080"}' \
  | jq -r '.id')

# 2. Create workflow
WORKFLOW_ID=$(curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{"name":"pipeline","start_step":"step1","steps":{...}}' \
  | jq -r '.id')

# 3. Execute workflow
RUN_ID=$(curl -X POST http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/execute \
  -H "Content-Type: application/json" \
  -d '{"input_data":{...}}' \
  | jq -r '.run_id')

# 4. Monitor execution
curl http://localhost:8000/api/v1/runs/$RUN_ID
```

### 2. Monitor Failed Runs
```bash
# List failed runs
curl "http://localhost:8000/api/v1/runs?status=FAILED&sort_by=created_at&sort_order=desc"

# Get run details
curl http://localhost:8000/api/v1/runs/{run_id}

# Get step executions to identify failure
curl http://localhost:8000/api/v1/runs/{run_id}/steps

# Retry the run
curl -X POST http://localhost:8000/api/v1/runs/{run_id}/retry
```

### 3. Update Workflow Version
```bash
# Get current workflow
curl http://localhost:8000/api/v1/workflows/{workflow_id}

# Update workflow (increments version)
curl -X PUT http://localhost:8000/api/v1/workflows/{workflow_id} \
  -H "Content-Type: application/json" \
  -d '{"steps":{...}}'

# View all versions
curl http://localhost:8000/api/v1/workflows/{workflow_id}/versions
```

## Error Handling

### Validation Error (422)
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
  "status_code": 422
}
```

### Not Found (404)
```json
{
  "error": "Not Found",
  "detail": "Agent with id '...' not found",
  "status_code": 404
}
```

### Server Error (500)
```json
{
  "error": "Internal Server Error",
  "detail": "An unexpected error occurred",
  "status_code": 500
}
```

## Tips

1. **Use Swagger UI for exploration**: http://localhost:8000/docs
2. **Check health before operations**: `GET /health/ready`
3. **Use pagination for large lists**: `?page=1&page_size=100`
4. **Filter to reduce response size**: `?status=FAILED`
5. **Poll run status asynchronously**: Check `/api/v1/runs/{run_id}` periodically
6. **Review step executions for debugging**: `GET /api/v1/runs/{run_id}/steps`
7. **Use ReDoc for readable docs**: http://localhost:8000/redoc

## Testing Tools

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d @agent.json
```

### HTTPie
```bash
http POST http://localhost:8000/api/v1/agents < agent.json
```

### Postman
Import OpenAPI spec: http://localhost:8000/openapi.json

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/agents",
    json={"name": "processor", "url": "http://processor:8080"}
)
print(response.json())
```

## Start Server

```bash
# Development (with auto-reload)
uvicorn api.main:app --reload

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

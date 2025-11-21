# Workflow Management API - Testing Guide

## 🚀 Services Running

All services are now running and ready for testing!

| Service | URL | Status |
|---------|-----|--------|
| **API Documentation (Swagger)** | http://localhost:8000/docs | ✓ Running |
| **API Documentation (ReDoc)** | http://localhost:8000/redoc | ✓ Running |
| **API Root** | http://localhost:8000/ | ✓ Running |
| **Health Check** | http://localhost:8000/health | ✓ Running |
| ResearchAgent | http://localhost:8081 | ✓ Running |
| WriterAgent | http://localhost:8082 | ✓ Running |
| Agent Registry | http://localhost:8080 | ✓ Running |
| Bridge Service | (internal) | ✓ Running |

## 📚 Interactive API Documentation

### Swagger UI (Recommended for Testing)
**URL**: http://localhost:8000/docs

Features:
- Interactive API explorer
- Try out endpoints directly in the browser
- See request/response examples
- View all available endpoints and parameters
- Test authentication (when implemented)

### ReDoc (Recommended for Reading)
**URL**: http://localhost:8000/redoc

Features:
- Clean, readable documentation
- Better for understanding API structure
- Detailed descriptions and examples
- Downloadable OpenAPI spec

## 🎯 Quick Start Testing

### 1. Open the API Documentation
```bash
# Open Swagger UI in your browser
open http://localhost:8000/docs

# Or use ReDoc
open http://localhost:8000/redoc
```

### 2. Test the Health Endpoint
```bash
curl http://localhost:8000/health | python3 -m json.tool
```

### 3. Register an Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ResearchAgent",
    "url": "http://research-agent:8080",
    "protocol": "jsonrpc-2.0",
    "timeout_ms": 30000,
    "retry_config": {
      "max_retries": 3,
      "initial_delay_ms": 100,
      "max_delay_ms": 5000,
      "backoff_multiplier": 2.0
    }
  }' | python3 -m json.tool
```

### 4. Create a Workflow
```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "research-workflow",
    "name": "Research Workflow",
    "version": "1.0.0",
    "description": "A simple research workflow",
    "steps": [
      {
        "step_id": "step-1",
        "agent_name": "ResearchAgent",
        "input_mapping": {
          "topic": "${workflow.input.topic}"
        },
        "next_step_id": null
      }
    ]
  }' | python3 -m json.tool
```

### 5. Execute a Workflow
```bash
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "research-workflow",
    "workflow_version": "1.0.0",
    "input_data": {
      "topic": "Artificial Intelligence"
    }
  }' | python3 -m json.tool
```

### 6. Check Run Status
```bash
# Replace {run_id} with the ID from step 5
curl http://localhost:8000/api/v1/runs/{run_id} | python3 -m json.tool
```

## 📋 Available Endpoints

### Agents
- `GET /api/v1/agents` - List all agents
- `POST /api/v1/agents` - Register a new agent
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `PUT /api/v1/agents/{agent_id}` - Update agent
- `DELETE /api/v1/agents/{agent_id}` - Delete agent
- `GET /api/v1/agents/{agent_id}/health` - Check agent health

### Workflows
- `GET /api/v1/workflows` - List all workflows
- `POST /api/v1/workflows` - Create a new workflow
- `GET /api/v1/workflows/{workflow_id}` - Get workflow details
- `GET /api/v1/workflows/{workflow_id}/versions` - List workflow versions
- `PUT /api/v1/workflows/{workflow_id}` - Update workflow
- `DELETE /api/v1/workflows/{workflow_id}` - Delete workflow

### Runs
- `GET /api/v1/runs` - List all runs
- `POST /api/v1/runs` - Execute a workflow
- `GET /api/v1/runs/{run_id}` - Get run details
- `GET /api/v1/runs/{run_id}/steps` - Get step executions
- `POST /api/v1/runs/{run_id}/retry` - Retry a failed run
- `POST /api/v1/runs/{run_id}/cancel` - Cancel a running workflow

### System
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check with dependencies
- `GET /metrics` - Prometheus metrics

## 🧪 Testing Scenarios

### Scenario 1: Simple Agent Registration and Health Check
1. Open http://localhost:8000/docs
2. Navigate to "Agents" section
3. Try `POST /api/v1/agents` to register ResearchAgent
4. Try `GET /api/v1/agents/{agent_id}/health` to check health

### Scenario 2: Create and Execute Workflow
1. Register agents (ResearchAgent, WriterAgent)
2. Create a workflow with multiple steps
3. Execute the workflow with input data
4. Monitor the run status
5. View step executions

### Scenario 3: Error Handling
1. Try to execute a workflow with invalid input
2. Try to get a non-existent run
3. Try to register an agent with invalid URL
4. Observe error responses and status codes

### Scenario 4: Workflow Versioning
1. Create a workflow (version 1.0.0)
2. Update the workflow (version 1.1.0)
3. List all versions
4. Execute different versions

## 🔍 Monitoring and Debugging

### View API Logs
```bash
docker compose logs api -f
```

### View Bridge Logs
```bash
docker compose logs bridge -f
```

### View Agent Logs
```bash
docker compose -f docker-compose.test.yml logs research-agent -f
```

### Check Database
```bash
docker exec -it postgres psql -U workflow_user -d workflow_db
```

### View Kafka Messages
```bash
# View tasks
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orchestrator.tasks.http \
  --from-beginning

# View results
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic results.topic \
  --from-beginning
```

## 🎨 Swagger UI Features

### Try It Out
1. Click on any endpoint
2. Click "Try it out" button
3. Fill in the parameters
4. Click "Execute"
5. View the response

### Request Examples
- Each endpoint shows example requests
- Copy and modify for your needs
- See all required and optional fields

### Response Examples
- View example responses for each status code
- Understand the response structure
- See error response formats

### Authentication
- Currently no authentication required
- Will be added in future releases

## 📊 API Response Formats

### Success Response
```json
{
  "id": "123",
  "status": "success",
  "data": {...}
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status_code": 400,
  "timestamp": "2025-11-09T13:00:00Z"
}
```

### Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 🛠️ Troubleshooting

### API Not Responding
```bash
# Check if API is running
docker compose ps api

# View logs
docker compose logs api --tail 50

# Restart API
docker compose restart api
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Test connection
docker exec postgres pg_isready -U workflow_user
```

### Kafka Connection Issues
```bash
# Check if Kafka is running
docker compose ps kafka

# List topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

## 🎉 Next Steps

1. **Explore the API**: Open http://localhost:8000/docs and try different endpoints
2. **Create Workflows**: Design your own workflow definitions
3. **Test Error Scenarios**: Try invalid inputs and see error handling
4. **Monitor Execution**: Watch logs and Kafka messages
5. **Check Metrics**: View Prometheus metrics at /metrics

## 📝 Notes

- All services are running with JSON-RPC 2.0 protocol
- Mock agents are configured for testing
- Database migrations have been applied
- Health checks are enabled
- CORS is configured for local development

Enjoy testing the API! 🚀

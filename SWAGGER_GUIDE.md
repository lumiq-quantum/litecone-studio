# Swagger/OpenAPI Documentation Guide

This guide explains how to view and use the Swagger/OpenAPI documentation for the Centralized Executor and HTTP-Kafka Bridge system.

## Available Documentation

1. **[openapi.yaml](openapi.yaml)** - OpenAPI 3.0 specification
2. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Comprehensive API documentation
3. **[A2A_AGENT_INTERFACE.md](A2A_AGENT_INTERFACE.md)** - Detailed A2A protocol specification

## Viewing Swagger UI

### Option 1: Swagger Editor (Online)

1. Go to [Swagger Editor](https://editor.swagger.io/)
2. Click **File** → **Import file**
3. Select `openapi.yaml` from this repository
4. The Swagger UI will render the documentation

### Option 2: Swagger UI (Docker)

Run Swagger UI locally:

```bash
docker run -p 8888:8080 \
  -e SWAGGER_JSON=/openapi.yaml \
  -v $(pwd)/openapi.yaml:/openapi.yaml \
  swaggerapi/swagger-ui
```

Then open: http://localhost:8888

### Option 3: VS Code Extension

1. Install the **Swagger Viewer** extension
2. Open `openapi.yaml`
3. Press `Shift+Alt+P` (Windows/Linux) or `Shift+Option+P` (Mac)
4. Select "Preview Swagger"

### Option 4: Redoc (Alternative UI)

Run Redoc for a different documentation view:

```bash
docker run -p 8888:80 \
  -e SPEC_URL=https://raw.githubusercontent.com/your-org/orchestrator/main/openapi.yaml \
  redocly/redoc
```

Then open: http://localhost:8888

## API Overview

### 1. Agent Registry API

**Base URL:** `http://localhost:8080`

**Endpoints:**
- `GET /health` - Health check
- `GET /agents/{agentName}` - Get agent metadata
- `GET /agents/{agentName}/recovery` - Get recovery configuration

**Example:**
```bash
# Get agent metadata
curl http://localhost:8080/agents/ResearchAgent

# Response
{
  "name": "ResearchAgent",
  "url": "http://research-agent:8080",
  "auth_config": null,
  "timeout": 30000,
  "retry_config": {
    "max_retries": 3,
    "initial_delay_ms": 1000,
    "max_delay_ms": 30000,
    "backoff_multiplier": 2.0
  }
}
```

### 2. A2A Agent Interface

**Base URL:** Agent-specific (e.g., `http://localhost:8081`)

**Endpoints:**
- `GET /health` - Health check
- `POST /` - Execute agent task

**Example:**
```bash
# Execute task
curl -X POST http://localhost:8081 \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-123",
    "input": {
      "topic": "AI",
      "depth": "basic"
    }
  }'

# Response
{
  "task_id": "test-123",
  "status": "success",
  "output": {
    "findings": [...],
    "summary": "..."
  },
  "error": null
}
```

## Testing with Swagger UI

### 1. Start the Services

```bash
# Start infrastructure
docker-compose up -d zookeeper kafka postgres

# Start mock agents
docker-compose -f docker-compose.test.yml up -d

# Start bridge
docker-compose --profile bridge up -d
```

### 2. Test Agent Registry

In Swagger UI:
1. Expand **Agent Registry** section
2. Click **GET /agents/{agentName}**
3. Click **Try it out**
4. Enter `ResearchAgent` as the agent name
5. Click **Execute**
6. View the response

### 3. Test A2A Agent

In Swagger UI:
1. Change the server to `http://localhost:8081` (ResearchAgent)
2. Expand **A2A Agent Interface** section
3. Click **POST /**
4. Click **Try it out**
5. Use the example request body:
   ```json
   {
     "task_id": "test-123",
     "input": {
       "topic": "AI",
       "depth": "basic"
     }
   }
   ```
6. Click **Execute**
7. View the response

## Authentication

### Bearer Token

If an agent requires Bearer token authentication:

1. In Swagger UI, click **Authorize** button
2. Select **BearerAuth**
3. Enter your token
4. Click **Authorize**
5. All subsequent requests will include the token

### API Key

If an agent requires API key authentication:

1. In Swagger UI, click **Authorize** button
2. Select **ApiKeyAuth**
3. Enter your API key
4. Click **Authorize**
5. All subsequent requests will include the key in `X-API-Key` header

## Generating Client Code

Swagger UI can generate client code in multiple languages:

1. Open Swagger UI with `openapi.yaml`
2. Click **Generate Client**
3. Select your language (Python, JavaScript, Java, etc.)
4. Download the generated client library

### Example: Python Client

```python
# Generated client usage
from swagger_client import ApiClient, AgentRegistryApi

# Create API client
api_client = ApiClient(host='http://localhost:8080')
api = AgentRegistryApi(api_client)

# Get agent metadata
agent = api.get_agent('ResearchAgent')
print(f"Agent URL: {agent.url}")
print(f"Timeout: {agent.timeout}ms")
```

## Validating API Requests

Use the OpenAPI spec to validate requests:

### Using openapi-spec-validator (Python)

```bash
pip install openapi-spec-validator

# Validate the spec
openapi-spec-validator openapi.yaml
```

### Using Spectral (Node.js)

```bash
npm install -g @stoplight/spectral-cli

# Validate the spec
spectral lint openapi.yaml
```

## Extending the API Documentation

### Adding a New Endpoint

1. Open `openapi.yaml`
2. Add the endpoint under `paths:`
   ```yaml
   /agents/{agentName}/metrics:
     get:
       tags:
         - Agent Registry
       summary: Get Agent Metrics
       operationId: getAgentMetrics
       parameters:
         - name: agentName
           in: path
           required: true
           schema:
             type: string
       responses:
         '200':
           description: Agent metrics
           content:
             application/json:
               schema:
                 $ref: '#/components/schemas/AgentMetrics'
   ```

3. Add the schema under `components/schemas:`
   ```yaml
   AgentMetrics:
     type: object
     properties:
       total_requests:
         type: integer
       success_rate:
         type: number
       avg_response_time_ms:
         type: number
   ```

4. Validate the updated spec
5. Commit the changes

### Adding Examples

Add more examples to help users understand the API:

```yaml
examples:
  researchAgent:
    summary: Research Agent Task
    value:
      task_id: task-123
      input:
        topic: Climate Change
        depth: comprehensive
  writerAgent:
    summary: Writer Agent Task
    value:
      task_id: task-456
      input:
        research_data: [...]
        style: academic
```

## API Versioning

Currently, the API is version 1.0.0. When making breaking changes:

1. Update the version in `openapi.yaml`:
   ```yaml
   info:
     version: 2.0.0
   ```

2. Consider adding version to the base path:
   ```yaml
   servers:
     - url: http://localhost:8080/v2
       description: Version 2 API
   ```

3. Document breaking changes in the description

## Troubleshooting

### Swagger UI Not Loading

**Issue:** Swagger UI shows "Failed to load API definition"

**Solution:**
- Check that `openapi.yaml` is valid YAML
- Validate with `openapi-spec-validator openapi.yaml`
- Check for syntax errors (indentation, quotes)

### CORS Errors

**Issue:** Browser shows CORS errors when testing

**Solution:**
- Add CORS headers to your API responses
- Use Swagger UI's built-in proxy
- Run Swagger UI with `--cors` flag

### Authentication Not Working

**Issue:** Requests fail with 401 Unauthorized

**Solution:**
- Click **Authorize** button in Swagger UI
- Enter valid credentials
- Check that the agent requires the authentication type you're using

## Additional Resources

- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI Documentation](https://swagger.io/tools/swagger-ui/)
- [Swagger Editor](https://editor.swagger.io/)
- [Redoc Documentation](https://redocly.com/docs/redoc/)

## Quick Reference

### View Documentation
```bash
# Swagger UI
docker run -p 8888:8080 -v $(pwd)/openapi.yaml:/openapi.yaml -e SWAGGER_JSON=/openapi.yaml swaggerapi/swagger-ui

# Redoc
docker run -p 8888:80 -e SPEC_URL=file:///openapi.yaml -v $(pwd)/openapi.yaml:/openapi.yaml redocly/redoc
```

### Validate Spec
```bash
# Python
openapi-spec-validator openapi.yaml

# Node.js
spectral lint openapi.yaml
```

### Generate Client
```bash
# Using openapi-generator
docker run --rm -v $(pwd):/local openapitools/openapi-generator-cli generate \
  -i /local/openapi.yaml \
  -g python \
  -o /local/python-client
```

## See Also

- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Comprehensive API documentation
- [A2A_AGENT_INTERFACE.md](A2A_AGENT_INTERFACE.md) - A2A protocol specification
- [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md) - Testing guide
- [README.md](README.md) - Project overview

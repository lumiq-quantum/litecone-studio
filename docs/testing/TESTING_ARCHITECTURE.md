# Testing Architecture - Mock Agents & A2A Protocol

## Overview

This document explains how the mock agents work for testing and how they implement the A2A (Agent-to-Agent) protocol.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Centralized Executor                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Reads workflow plan                                    │  │
│  │ 2. Resolves input data                                    │  │
│  │ 3. Publishes AgentTask to Kafka                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Kafka Topic: orchestrator.tasks.http
                             │ Message: {task_id, agent_name, input_data, correlation_id}
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              HTTP-Kafka Bridge (External Agent Executor)        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Consumes AgentTask from Kafka                         │  │
│  │ 2. Queries Agent Registry for agent URL                  │  │
│  │ 3. Makes HTTP POST to agent (A2A protocol)              │  │
│  │ 4. Receives HTTP response                                │  │
│  │ 5. Publishes AgentResult to Kafka                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP POST (A2A Protocol)
                             │ Request: {task_id, input: {...}}
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Registry                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Returns agent metadata:                                   │  │
│  │ - URL: http://research-agent:8080                        │  │
│  │ - Auth config                                            │  │
│  │ - Timeout: 30000ms                                       │  │
│  │ - Retry config                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ HTTP POST to agent URL
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Mock Agent (ResearchAgent)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ HTTP Server (Python)                                      │  │
│  │                                                           │  │
│  │ POST / endpoint:                                          │  │
│  │   1. Receives A2A request                                │  │
│  │   2. Validates input                                     │  │
│  │   3. Generates mock output                               │  │
│  │   4. Returns A2A response                                │  │
│  │                                                           │  │
│  │ GET /health endpoint:                                     │  │
│  │   Returns: {status: "healthy"}                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ HTTP Response (A2A Protocol)
                             │ Response: {task_id, status: "success", output: {...}}
                             ▼
                    Back to Bridge → Kafka → Executor
```

## Mock Agent Implementation

### 1. **Simple HTTP Server**

The mock agents are built using Python's built-in `HTTPServer`:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler

class MockAgentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Handle A2A requests
        pass
    
    def do_GET(self):
        # Handle health checks
        pass

httpd = HTTPServer(('', 8080), MockAgentHandler)
httpd.serve_forever()
```

### 2. **A2A Protocol Implementation**

The mock agents implement the A2A protocol exactly as specified:

#### **Request Handling:**
```python
def do_POST(self):
    # 1. Read request body
    content_length = int(self.headers.get('Content-Length', 0))
    body = self.rfile.read(content_length)
    request_data = json.loads(body.decode('utf-8'))
    
    # 2. Extract A2A fields
    task_id = request_data.get('task_id')
    input_data = request_data.get('input')
    
    # 3. Process the task
    output_data = self._generate_mock_output(input_data)
    
    # 4. Return A2A response
    response = {
        'task_id': task_id,
        'status': 'success',
        'output': output_data,
        'error': None
    }
    
    self.send_response(200)
    self.send_header('Content-Type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(response).encode('utf-8'))
```

### 3. **Agent-Specific Logic**

Each mock agent generates different output based on its name:

```python
def _generate_mock_output(self, input_data):
    if AGENT_NAME == 'ResearchAgent':
        return {
            'findings': [
                {'source': 'Mock Source 1', 'content': '...'},
                {'source': 'Mock Source 2', 'content': '...'}
            ],
            'summary': f"Summary of research on {input_data.get('topic')}",
            'confidence': 0.85,
            'sources_count': 2
        }
    elif AGENT_NAME == 'WriterAgent':
        return {
            'article': f"This is a {input_data.get('style')} article...",
            'word_count': input_data.get('word_count', 500),
            'style': input_data.get('style'),
            'quality_score': 0.92
        }
```

## A2A Protocol Flow

### Step-by-Step Request/Response

**1. Bridge sends HTTP POST request:**
```http
POST / HTTP/1.1
Host: research-agent:8080
Content-Type: application/json
X-Correlation-ID: corr-test-123-step-1-abc

{
  "task_id": "task-step-1-xyz",
  "input": {
    "topic": "Climate Change Impact on Agriculture",
    "depth": "comprehensive",
    "sources": ["scientific journals", "government reports"]
  }
}
```

**2. Mock agent processes and responds:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "task_id": "task-step-1-xyz",
  "status": "success",
  "output": {
    "findings": [
      {
        "source": "Mock Source 1",
        "content": "Research finding about Climate Change Impact on Agriculture"
      },
      {
        "source": "Mock Source 2",
        "content": "Additional research on Climate Change Impact on Agriculture"
      }
    ],
    "summary": "Summary of research on Climate Change Impact on Agriculture",
    "confidence": 0.85,
    "sources_count": 2
  },
  "error": null
}
```

**3. Bridge publishes result to Kafka:**
```json
{
  "run_id": "test-123",
  "task_id": "task-step-1-xyz",
  "status": "SUCCESS",
  "output_data": {
    "findings": [...],
    "summary": "...",
    "confidence": 0.85,
    "sources_count": 2
  },
  "correlation_id": "corr-test-123-step-1-abc",
  "error_message": null
}
```

## Docker Compose Configuration

### Mock Agents Setup

```yaml
services:
  # Mock Research Agent
  research-agent:
    build:
      context: .
      dockerfile: Dockerfile.mock-agent
    ports:
      - "8081:8080"
    environment:
      - AGENT_NAME=ResearchAgent
      - AGENT_PORT=8080
      - AGENT_DELAY_MS=100
      - AGENT_ERROR_MODE=none
      - AGENT_ERROR_RATE=0.0
    networks:
      - orchestrator-network

  # Mock Writer Agent
  writer-agent:
    build:
      context: .
      dockerfile: Dockerfile.mock-agent
    ports:
      - "8082:8080"
    environment:
      - AGENT_NAME=WriterAgent
      - AGENT_PORT=8080
      - AGENT_DELAY_MS=200
      - AGENT_ERROR_MODE=none
      - AGENT_ERROR_RATE=0.0
    networks:
      - orchestrator-network
```

### Agent Registry Setup

```yaml
  agent-registry:
    image: python:3.11-slim
    ports:
      - "8080:8080"
    volumes:
      - ./examples/mock_agent_registry.py:/app/mock_agent_registry.py:ro
    working_dir: /app
    command: python mock_agent_registry.py
    environment:
      - PORT=8080
    networks:
      - orchestrator-network
```

The Agent Registry returns metadata for each agent:

```json
{
  "ResearchAgent": {
    "name": "ResearchAgent",
    "url": "http://research-agent:8080",
    "auth_config": null,
    "timeout": 30000,
    "retry_config": {
      "max_retries": 3,
      "initial_delay_ms": 100,
      "max_delay_ms": 5000,
      "backoff_multiplier": 2.0
    }
  }
}
```

## Testing Features

### 1. **Configurable Delays**

Simulate slow agents:
```bash
AGENT_DELAY_MS=2000 python examples/mock_agent.py
```

### 2. **Error Simulation**

Test error handling:
```bash
# Simulate 50% failure rate with 5xx errors
AGENT_ERROR_MODE=5xx AGENT_ERROR_RATE=0.5 python examples/mock_agent.py

# Simulate timeouts
AGENT_ERROR_MODE=timeout python examples/mock_agent.py

# Simulate 4xx client errors
AGENT_ERROR_MODE=4xx AGENT_ERROR_RATE=1.0 python examples/mock_agent.py
```

### 3. **Health Checks**

Test agent availability:
```bash
curl http://localhost:8081/health
# Response: {"status": "healthy", "agent_name": "ResearchAgent", "error_mode": "none"}
```

### 4. **Direct Testing**

Test agents directly without the full system:
```bash
curl -X POST http://localhost:8081 \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-123",
    "input": {
      "topic": "AI",
      "depth": "basic",
      "sources": ["web"]
    }
  }'
```

## Building Real Agents

To build a real agent that works with the system:

### 1. **Implement A2A Protocol**

Your agent must:
- Accept HTTP POST requests
- Parse JSON with `task_id` and `input` fields
- Return JSON with `task_id`, `status`, `output`, and `error` fields
- Return 200 OK for both success and business logic errors

### 2. **Register in Agent Registry**

Add your agent to the registry with:
- Name
- URL (must be accessible from the bridge)
- Authentication config (if needed)
- Timeout (in milliseconds)
- Retry configuration

### 3. **Handle Errors Properly**

- Use `status: "error"` for business logic errors
- Use HTTP 4xx for client errors (bad request, auth)
- Use HTTP 5xx for server errors (crashes, dependencies down)

### 4. **Implement Health Check**

Provide a `/health` endpoint that returns:
```json
{"status": "healthy"}
```

## Example: Converting Mock to Real Agent

**Mock Agent (Testing):**
```python
def _generate_mock_output(self, input_data):
    return {
        'findings': ['Mock finding 1', 'Mock finding 2'],
        'summary': 'Mock summary'
    }
```

**Real Agent (Production):**
```python
def _generate_real_output(self, input_data):
    # Call actual research APIs
    topic = input_data['topic']
    sources = input_data['sources']
    
    findings = []
    for source in sources:
        results = research_api.search(topic, source)
        findings.extend(results)
    
    summary = summarization_api.summarize(findings)
    
    return {
        'findings': findings,
        'summary': summary,
        'confidence': calculate_confidence(findings),
        'sources_count': len(findings)
    }
```

## Key Takeaways

1. **Mock agents are simple HTTP servers** that implement the A2A protocol
2. **A2A protocol is straightforward**: POST with `{task_id, input}`, respond with `{task_id, status, output, error}`
3. **Bridge handles all Kafka communication** - agents only need HTTP
4. **Mock agents are configurable** for testing different scenarios (delays, errors)
5. **Real agents follow the same interface** - just replace mock logic with real implementation

## See Also

- [A2A_AGENT_INTERFACE.md](A2A_AGENT_INTERFACE.md) - Complete A2A protocol specification
- [examples/mock_agent.py](examples/mock_agent.py) - Mock agent implementation
- [examples/mock_agent_registry.py](examples/mock_agent_registry.py) - Mock registry implementation
- [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md) - Testing guide

# A2A Agent Interface Specification

This document defines the Agent-to-Agent (A2A) HTTP protocol used by the External Agent Executor (HTTP-Kafka Bridge) to communicate with external agents.

## Overview

The A2A protocol is a simple, synchronous HTTP-based interface that allows agents to receive task requests and return results. All agents must implement this interface to be compatible with the orchestration platform.

## Protocol Requirements

### HTTP Method
All agent invocations use **HTTP POST**

### Content Type
- Request: `application/json`
- Response: `application/json`

### Endpoint
Agents must expose a single HTTP endpoint (path configurable in Agent Registry, typically `/` or `/invoke`)

### Authentication
Agents may require authentication via:
- **Bearer Token**: `Authorization: Bearer <token>`
- **API Key**: `X-API-Key: <key>`
- **Custom Headers**: As configured in Agent Registry

## Request Format

### Request Schema

```json
{
  "task_id": "string",
  "input": {
    // Agent-specific input fields
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | string | Yes | Unique identifier for this task invocation |
| `input` | object | Yes | Agent-specific input data (structure varies by agent) |

### Example Request

```json
{
  "task_id": "task-abc123-def456",
  "input": {
    "topic": "Climate Change Impact on Agriculture",
    "depth": "comprehensive",
    "sources": ["scientific journals", "government reports"]
  }
}
```

### HTTP Headers

**Required:**
```
Content-Type: application/json
```

**Optional (based on agent configuration):**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-API-Key: sk-1234567890abcdef
X-Correlation-ID: run-123-correlation-456
```

## Response Format

### Success Response

**HTTP Status Code:** `200 OK`

**Response Schema:**

```json
{
  "task_id": "string",
  "status": "success",
  "output": {
    // Agent-specific output fields
  },
  "error": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | string | Yes | Must match the request task_id |
| `status` | string | Yes | Must be "success" for successful execution |
| `output` | object | Yes | Agent-specific output data |
| `error` | null | Yes | Must be null for successful execution |

**Example Success Response:**

```json
{
  "task_id": "task-abc123-def456",
  "status": "success",
  "output": {
    "findings": [
      "Rising temperatures affect crop yields by 10-25%",
      "Changing precipitation patterns impact irrigation needs"
    ],
    "summary": "Climate change significantly impacts agricultural productivity through temperature increases and altered precipitation patterns.",
    "confidence": 0.92,
    "sources_used": 15
  },
  "error": null
}
```

### Error Response

**HTTP Status Code:** `200 OK` (with error in body) or `4xx/5xx` (HTTP error)

**Response Schema (200 with error):**

```json
{
  "task_id": "string",
  "status": "error",
  "output": null,
  "error": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | string | Yes | Must match the request task_id |
| `status` | string | Yes | Must be "error" for failed execution |
| `output` | null | Yes | Must be null for failed execution |
| `error` | string | Yes | Human-readable error message |

**Example Error Response (200 OK):**

```json
{
  "task_id": "task-abc123-def456",
  "status": "error",
  "output": null,
  "error": "Invalid input: 'depth' must be one of: basic, intermediate, comprehensive"
}
```

**Example HTTP Error Response (4xx/5xx):**

```
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Missing required field: topic",
  "details": {
    "field": "topic",
    "message": "This field is required"
  }
}
```

## HTTP Status Codes

### Success Codes

| Code | Meaning | Bridge Behavior |
|------|---------|-----------------|
| 200 OK | Task completed (check status field) | Parse response, publish result |

### Client Error Codes (4xx)

| Code | Meaning | Bridge Behavior |
|------|---------|-----------------|
| 400 Bad Request | Invalid input data | Non-retriable, publish failure immediately |
| 401 Unauthorized | Missing or invalid authentication | Non-retriable, publish failure immediately |
| 403 Forbidden | Insufficient permissions | Non-retriable, publish failure immediately |
| 404 Not Found | Agent endpoint not found | Non-retriable, publish failure immediately |
| 422 Unprocessable Entity | Validation error | Non-retriable, publish failure immediately |
| 429 Too Many Requests | Rate limit exceeded | Retriable with exponential backoff |

### Server Error Codes (5xx)

| Code | Meaning | Bridge Behavior |
|------|---------|-----------------|
| 500 Internal Server Error | Agent internal error | Retriable with exponential backoff |
| 502 Bad Gateway | Upstream service error | Retriable with exponential backoff |
| 503 Service Unavailable | Agent temporarily unavailable | Retriable with exponential backoff |
| 504 Gateway Timeout | Agent timeout | Retriable with exponential backoff |

## Retry Logic

The External Agent Executor implements automatic retry with exponential backoff for retriable errors.

### Retriable Errors
- Network errors (connection refused, timeout)
- HTTP 5xx status codes
- HTTP 429 (rate limit)

### Non-Retriable Errors
- HTTP 4xx status codes (except 429)
- Invalid response format
- Response with `status: "error"`

### Retry Configuration

Default retry behavior (configurable per agent in Agent Registry):

```json
{
  "max_retries": 3,
  "initial_delay_ms": 1000,
  "max_delay_ms": 30000,
  "backoff_multiplier": 2.0
}
```

**Retry Schedule Example:**
- Attempt 1: Immediate
- Attempt 2: Wait 1 second
- Attempt 3: Wait 2 seconds
- Attempt 4: Wait 4 seconds

## Timeout Configuration

Agents must respond within the configured timeout period (default: 30 seconds).

**Timeout Behavior:**
- Bridge waits for configured timeout
- If no response, connection is closed
- Timeout is treated as a retriable error
- Bridge retries according to retry configuration

## Agent Implementation Examples

### Python (Flask)

```python
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_task():
    data = request.get_json()
    
    # Validate request
    if not data or 'task_id' not in data or 'input' not in data:
        return jsonify({
            'error': 'Invalid request format'
        }), 400
    
    task_id = data['task_id']
    input_data = data['input']
    
    try:
        # Process the task
        result = process_task(input_data)
        
        # Return success response
        return jsonify({
            'task_id': task_id,
            'status': 'success',
            'output': result,
            'error': None
        }), 200
        
    except ValueError as e:
        # Return error response (200 with error status)
        return jsonify({
            'task_id': task_id,
            'status': 'error',
            'output': None,
            'error': str(e)
        }), 200
    
    except Exception as e:
        # Return HTTP error for unexpected failures
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

def process_task(input_data):
    # Agent-specific logic
    topic = input_data.get('topic')
    if not topic:
        raise ValueError('Missing required field: topic')
    
    # Simulate processing
    time.sleep(1)
    
    return {
        'findings': [f'Finding about {topic}'],
        'summary': f'Summary of research on {topic}'
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### Node.js (Express)

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/', async (req, res) => {
  const { task_id, input } = req.body;
  
  // Validate request
  if (!task_id || !input) {
    return res.status(400).json({
      error: 'Invalid request format'
    });
  }
  
  try {
    // Process the task
    const result = await processTask(input);
    
    // Return success response
    res.json({
      task_id,
      status: 'success',
      output: result,
      error: null
    });
    
  } catch (error) {
    if (error.name === 'ValidationError') {
      // Return error response (200 with error status)
      res.json({
        task_id,
        status: 'error',
        output: null,
        error: error.message
      });
    } else {
      // Return HTTP error for unexpected failures
      res.status(500).json({
        error: 'Internal server error',
        details: error.message
      });
    }
  }
});

async function processTask(input) {
  const { topic } = input;
  
  if (!topic) {
    const error = new Error('Missing required field: topic');
    error.name = 'ValidationError';
    throw error;
  }
  
  // Simulate processing
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  return {
    findings: [`Finding about ${topic}`],
    summary: `Summary of research on ${topic}`
  };
}

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`Agent listening on port ${PORT}`);
});
```

### Go (net/http)

```go
package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "time"
)

type TaskRequest struct {
    TaskID string                 `json:"task_id"`
    Input  map[string]interface{} `json:"input"`
}

type TaskResponse struct {
    TaskID string                 `json:"task_id"`
    Status string                 `json:"status"`
    Output map[string]interface{} `json:"output,omitempty"`
    Error  *string                `json:"error"`
}

func handleTask(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }
    
    var req TaskRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request format", http.StatusBadRequest)
        return
    }
    
    // Process the task
    result, err := processTask(req.Input)
    
    w.Header().Set("Content-Type", "application/json")
    
    if err != nil {
        // Return error response (200 with error status)
        errMsg := err.Error()
        json.NewEncoder(w).Encode(TaskResponse{
            TaskID: req.TaskID,
            Status: "error",
            Error:  &errMsg,
        })
        return
    }
    
    // Return success response
    json.NewEncoder(w).Encode(TaskResponse{
        TaskID: req.TaskID,
        Status: "success",
        Output: result,
        Error:  nil,
    })
}

func processTask(input map[string]interface{}) (map[string]interface{}, error) {
    topic, ok := input["topic"].(string)
    if !ok || topic == "" {
        return nil, fmt.Errorf("Missing required field: topic")
    }
    
    // Simulate processing
    time.Sleep(1 * time.Second)
    
    return map[string]interface{}{
        "findings": []string{fmt.Sprintf("Finding about %s", topic)},
        "summary":  fmt.Sprintf("Summary of research on %s", topic),
    }, nil
}

func main() {
    http.HandleFunc("/", handleTask)
    fmt.Println("Agent listening on port 8080")
    http.ListenAndServe(":8080", nil)
}
```

## Testing Your Agent

### Using curl

```bash
# Test successful request
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-123",
    "input": {
      "topic": "AI",
      "depth": "basic"
    }
  }'

# Test with authentication
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token-here" \
  -d '{
    "task_id": "test-456",
    "input": {
      "query": "What is machine learning?"
    }
  }'

# Test error handling
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-789",
    "input": {}
  }'
```

### Using Python

```python
import requests

# Test successful request
response = requests.post(
    'http://localhost:8080',
    json={
        'task_id': 'test-123',
        'input': {
            'topic': 'AI',
            'depth': 'basic'
        }
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Expected output:
# Status: 200
# Response: {
#   'task_id': 'test-123',
#   'status': 'success',
#   'output': { ... },
#   'error': None
# }
```

## Agent Registry Configuration

Agents must be registered in the Agent Registry with their endpoint URL and configuration:

```json
{
  "name": "ResearchAgent",
  "url": "http://research-agent:8080",
  "auth_config": {
    "type": "bearer",
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

## Best Practices

### 1. Validate Input Early
Return 400 or error response immediately for invalid input rather than processing and failing later.

### 2. Use Appropriate Status Codes
- Use 200 with `status: "error"` for business logic errors
- Use 4xx for client errors (bad request, auth)
- Use 5xx for server errors (crashes, dependencies down)

### 3. Include Detailed Error Messages
Help developers debug issues by providing clear, actionable error messages.

```json
{
  "status": "error",
  "error": "Invalid depth value: 'very-deep'. Must be one of: basic, intermediate, comprehensive"
}
```

### 4. Implement Health Checks
Provide a health check endpoint for monitoring:

```python
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200
```

### 5. Log All Requests
Log incoming requests and responses for debugging and monitoring.

### 6. Handle Timeouts Gracefully
If your agent performs long-running operations, ensure they respect the timeout configuration.

### 7. Return Consistent Output Structure
Define a clear output schema for your agent and document it.

### 8. Support Idempotency
If possible, make your agent idempotent so retries don't cause duplicate side effects.

## Security Considerations

### 1. Validate Authentication
Always verify authentication tokens/keys before processing requests.

### 2. Sanitize Input
Validate and sanitize all input data to prevent injection attacks.

### 3. Rate Limiting
Implement rate limiting to prevent abuse:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.headers.get('X-API-Key'))

@app.route('/', methods=['POST'])
@limiter.limit("100 per minute")
def handle_task():
    # ...
```

### 4. Use HTTPS
In production, always use HTTPS to encrypt data in transit.

### 5. Don't Log Sensitive Data
Avoid logging sensitive information from input or output.

## Troubleshooting

### Agent Not Receiving Requests

1. Check agent is registered in Agent Registry
2. Verify agent URL is correct and accessible
3. Check network connectivity from bridge to agent
4. Review bridge logs for connection errors

### Requests Timing Out

1. Check agent timeout configuration
2. Verify agent is responding within timeout period
3. Optimize agent processing time
4. Consider increasing timeout in Agent Registry

### Authentication Failures

1. Verify auth configuration in Agent Registry
2. Check agent is validating credentials correctly
3. Ensure credentials haven't expired
4. Review agent logs for auth errors

### Unexpected Retries

1. Check agent is returning correct status codes
2. Verify response format matches specification
3. Review bridge logs for retry reasons
4. Ensure agent isn't returning 5xx for business logic errors

## See Also

- [Workflow JSON Format Specification](WORKFLOW_FORMAT.md)
- [README.md](README.md) - Project overview
- [examples/mock_agent.py](examples/mock_agent.py) - Reference implementation

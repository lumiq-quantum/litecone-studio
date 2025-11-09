# A2A Agent Interface Specification

This document defines the Agent-to-Agent (A2A) HTTP protocol used by the External Agent Executor (HTTP-Kafka Bridge) to communicate with external agents.

## Overview

The A2A protocol uses JSON-RPC 2.0, a stateless, lightweight remote procedure call (RPC) protocol. This provides a standardized, synchronous HTTP-based interface that allows agents to receive task requests and return results. All agents must implement this interface to be compatible with the orchestration platform.

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

### JSON-RPC 2.0 Request Schema

```json
{
  "jsonrpc": "2.0",
  "id": "string",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "string",
      "parts": [
        {
          "kind": "text",
          "text": "string"
        }
      ]
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jsonrpc` | string | Yes | JSON-RPC version, must be "2.0" |
| `id` | string | Yes | Unique identifier for this request (task_id) |
| `method` | string | Yes | RPC method name, must be "message/send" |
| `params` | object | Yes | Parameters object containing the message |
| `params.message` | object | Yes | Message object with role, messageId, and parts |
| `params.message.role` | string | Yes | Message role, must be "user" |
| `params.message.messageId` | string | Yes | Unique message identifier |
| `params.message.parts` | array | Yes | Array of message parts (content) |
| `params.message.parts[].kind` | string | Yes | Part type (e.g., "text") |
| `params.message.parts[].text` | string | Yes | Text content of the part |

### Example Request

```json
{
  "jsonrpc": "2.0",
  "id": "task-abc123-def456",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-task-abc123-def456",
      "parts": [
        {
          "kind": "text",
          "text": "{\"topic\": \"Climate Change Impact on Agriculture\", \"depth\": \"comprehensive\", \"sources\": [\"scientific journals\", \"government reports\"]}"
        }
      ]
    }
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

### JSON-RPC 2.0 Success Response

**HTTP Status Code:** `200 OK`

**Response Schema:**

```json
{
  "jsonrpc": "2.0",
  "id": "string",
  "result": {
    "status": {
      "state": "completed"
    },
    "artifacts": [
      {
        "parts": [
          {
            "kind": "text",
            "text": "string"
          }
        ]
      }
    ],
    "history": [
      {
        "role": "agent",
        "parts": [
          {
            "kind": "text",
            "text": "string"
          }
        ]
      }
    ]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jsonrpc` | string | Yes | JSON-RPC version, must be "2.0" |
| `id` | string | Yes | Must match the request id |
| `result` | object | Yes | Result object containing task output |
| `result.status` | object | Yes | Status object with state information |
| `result.status.state` | string | Yes | Task state (e.g., "completed", "failed") |
| `result.artifacts` | array | No | Array of output artifacts |
| `result.artifacts[].parts` | array | Yes | Array of artifact parts |
| `result.artifacts[].parts[].kind` | string | Yes | Part type (e.g., "text") |
| `result.artifacts[].parts[].text` | string | Yes | Text content of the artifact |
| `result.history` | array | No | Conversation history |
| `result.history[].role` | string | Yes | Message role ("agent" or "user") |
| `result.history[].parts` | array | Yes | Array of message parts |

**Example Success Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "task-abc123-def456",
  "result": {
    "status": {
      "state": "completed"
    },
    "artifacts": [
      {
        "parts": [
          {
            "kind": "text",
            "text": "Climate change significantly impacts agricultural productivity through temperature increases and altered precipitation patterns."
          }
        ]
      }
    ],
    "history": [
      {
        "role": "user",
        "parts": [
          {
            "kind": "text",
            "text": "{\"topic\": \"Climate Change Impact on Agriculture\", \"depth\": \"comprehensive\"}"
          }
        ]
      },
      {
        "role": "agent",
        "parts": [
          {
            "kind": "text",
            "text": "Based on my research, I found that:\n\n1. Rising temperatures affect crop yields by 10-25%\n2. Changing precipitation patterns impact irrigation needs\n\nConfidence: 92% (based on 15 sources)"
          }
        ]
      }
    ]
  }
}
```

### JSON-RPC 2.0 Error Response

**HTTP Status Code:** `200 OK`

**Response Schema:**

```json
{
  "jsonrpc": "2.0",
  "id": "string",
  "error": {
    "code": -32600,
    "message": "string",
    "data": {}
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jsonrpc` | string | Yes | JSON-RPC version, must be "2.0" |
| `id` | string | Yes | Must match the request id (or null if id couldn't be determined) |
| `error` | object | Yes | Error object |
| `error.code` | integer | Yes | Error code (see JSON-RPC 2.0 error codes) |
| `error.message` | string | Yes | Human-readable error message |
| `error.data` | any | No | Additional error information |

**Standard JSON-RPC 2.0 Error Codes:**

| Code | Message | Meaning |
|------|---------|---------|
| -32700 | Parse error | Invalid JSON received |
| -32600 | Invalid Request | JSON-RPC request is not valid |
| -32601 | Method not found | Method does not exist |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Internal JSON-RPC error |
| -32000 to -32099 | Server error | Implementation-defined server errors |

**Example Error Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "task-abc123-def456",
  "error": {
    "code": -32602,
    "message": "Invalid params: 'depth' must be one of: basic, intermediate, comprehensive",
    "data": {
      "field": "depth",
      "provided": "very-deep",
      "allowed": ["basic", "intermediate", "comprehensive"]
    }
  }
}
```

**Example HTTP Error Response (4xx/5xx):**

For non-JSON-RPC errors (e.g., authentication, server errors), standard HTTP status codes may be used:

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32000,
    "message": "Authentication required"
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
import json
import time

app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_task():
    data = request.get_json()
    
    # Validate JSON-RPC request
    if not data or data.get('jsonrpc') != '2.0':
        return jsonify({
            'jsonrpc': '2.0',
            'id': data.get('id') if data else None,
            'error': {
                'code': -32600,
                'message': 'Invalid Request: missing or invalid jsonrpc field'
            }
        }), 200
    
    request_id = data.get('id')
    method = data.get('method')
    params = data.get('params', {})
    
    # Validate method
    if method != 'message/send':
        return jsonify({
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': -32601,
                'message': f'Method not found: {method}'
            }
        }), 200
    
    # Extract message from params
    message = params.get('message', {})
    parts = message.get('parts', [])
    
    try:
        # Extract input from message parts
        input_text = ''
        for part in parts:
            if part.get('kind') == 'text':
                input_text = part.get('text', '')
                break
        
        # Parse input if it's JSON
        try:
            input_data = json.loads(input_text)
        except:
            input_data = {'text': input_text}
        
        # Process the task
        result = process_task(input_data)
        
        # Return JSON-RPC success response
        return jsonify({
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'status': {'state': 'completed'},
                'artifacts': [
                    {
                        'parts': [
                            {
                                'kind': 'text',
                                'text': result.get('summary', '')
                            }
                        ]
                    }
                ],
                'history': [
                    {
                        'role': 'user',
                        'parts': parts
                    },
                    {
                        'role': 'agent',
                        'parts': [
                            {
                                'kind': 'text',
                                'text': json.dumps(result)
                            }
                        ]
                    }
                ]
            }
        }), 200
        
    except ValueError as e:
        # Return JSON-RPC error response
        return jsonify({
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': -32602,
                'message': str(e)
            }
        }), 200
    
    except Exception as e:
        # Return JSON-RPC internal error
        return jsonify({
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': -32603,
                'message': 'Internal error',
                'data': {'details': str(e)}
            }
        }), 200

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
  const { jsonrpc, id, method, params } = req.body;
  
  // Validate JSON-RPC request
  if (jsonrpc !== '2.0') {
    return res.json({
      jsonrpc: '2.0',
      id: id || null,
      error: {
        code: -32600,
        message: 'Invalid Request: missing or invalid jsonrpc field'
      }
    });
  }
  
  // Validate method
  if (method !== 'message/send') {
    return res.json({
      jsonrpc: '2.0',
      id,
      error: {
        code: -32601,
        message: `Method not found: ${method}`
      }
    });
  }
  
  // Extract message from params
  const message = params?.message || {};
  const parts = message.parts || [];
  
  try {
    // Extract input from message parts
    let inputText = '';
    for (const part of parts) {
      if (part.kind === 'text') {
        inputText = part.text || '';
        break;
      }
    }
    
    // Parse input if it's JSON
    let inputData;
    try {
      inputData = JSON.parse(inputText);
    } catch {
      inputData = { text: inputText };
    }
    
    // Process the task
    const result = await processTask(inputData);
    
    // Return JSON-RPC success response
    res.json({
      jsonrpc: '2.0',
      id,
      result: {
        status: { state: 'completed' },
        artifacts: [
          {
            parts: [
              {
                kind: 'text',
                text: result.summary || ''
              }
            ]
          }
        ],
        history: [
          {
            role: 'user',
            parts
          },
          {
            role: 'agent',
            parts: [
              {
                kind: 'text',
                text: JSON.stringify(result)
              }
            ]
          }
        ]
      }
    });
    
  } catch (error) {
    if (error.name === 'ValidationError') {
      // Return JSON-RPC error response
      res.json({
        jsonrpc: '2.0',
        id,
        error: {
          code: -32602,
          message: error.message
        }
      });
    } else {
      // Return JSON-RPC internal error
      res.json({
        jsonrpc: '2.0',
        id,
        error: {
          code: -32603,
          message: 'Internal error',
          data: { details: error.message }
        }
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

type JsonRpcRequest struct {
    Jsonrpc string                 `json:"jsonrpc"`
    ID      string                 `json:"id"`
    Method  string                 `json:"method"`
    Params  map[string]interface{} `json:"params"`
}

type JsonRpcResponse struct {
    Jsonrpc string      `json:"jsonrpc"`
    ID      string      `json:"id"`
    Result  interface{} `json:"result,omitempty"`
    Error   *RpcError   `json:"error,omitempty"`
}

type RpcError struct {
    Code    int         `json:"code"`
    Message string      `json:"message"`
    Data    interface{} `json:"data,omitempty"`
}

type MessagePart struct {
    Kind string `json:"kind"`
    Text string `json:"text"`
}

type HistoryItem struct {
    Role  string        `json:"role"`
    Parts []MessagePart `json:"parts"`
}

func handleTask(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }
    
    var req JsonRpcRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        sendJsonRpcError(w, "", -32700, "Parse error", nil)
        return
    }
    
    // Validate JSON-RPC request
    if req.Jsonrpc != "2.0" {
        sendJsonRpcError(w, req.ID, -32600, "Invalid Request: missing or invalid jsonrpc field", nil)
        return
    }
    
    // Validate method
    if req.Method != "message/send" {
        sendJsonRpcError(w, req.ID, -32601, fmt.Sprintf("Method not found: %s", req.Method), nil)
        return
    }
    
    // Extract message from params
    message, ok := req.Params["message"].(map[string]interface{})
    if !ok {
        sendJsonRpcError(w, req.ID, -32602, "Invalid params: missing message", nil)
        return
    }
    
    parts, ok := message["parts"].([]interface{})
    if !ok {
        sendJsonRpcError(w, req.ID, -32602, "Invalid params: missing parts", nil)
        return
    }
    
    // Extract input from message parts
    var inputText string
    for _, p := range parts {
        part, ok := p.(map[string]interface{})
        if !ok {
            continue
        }
        if part["kind"] == "text" {
            inputText = part["text"].(string)
            break
        }
    }
    
    // Parse input if it's JSON
    var inputData map[string]interface{}
    if err := json.Unmarshal([]byte(inputText), &inputData); err != nil {
        inputData = map[string]interface{}{"text": inputText}
    }
    
    // Process the task
    result, err := processTask(inputData)
    
    w.Header().Set("Content-Type", "application/json")
    
    if err != nil {
        sendJsonRpcError(w, req.ID, -32602, err.Error(), nil)
        return
    }
    
    // Build message parts for response
    userParts := make([]MessagePart, len(parts))
    for i, p := range parts {
        part := p.(map[string]interface{})
        userParts[i] = MessagePart{
            Kind: part["kind"].(string),
            Text: part["text"].(string),
        }
    }
    
    resultJSON, _ := json.Marshal(result)
    
    // Return JSON-RPC success response
    response := JsonRpcResponse{
        Jsonrpc: "2.0",
        ID:      req.ID,
        Result: map[string]interface{}{
            "status": map[string]string{"state": "completed"},
            "artifacts": []map[string]interface{}{
                {
                    "parts": []MessagePart{
                        {Kind: "text", Text: result["summary"].(string)},
                    },
                },
            },
            "history": []HistoryItem{
                {Role: "user", Parts: userParts},
                {
                    Role: "agent",
                    Parts: []MessagePart{
                        {Kind: "text", Text: string(resultJSON)},
                    },
                },
            },
        },
    }
    
    json.NewEncoder(w).Encode(response)
}

func sendJsonRpcError(w http.ResponseWriter, id string, code int, message string, data interface{}) {
    w.Header().Set("Content-Type", "application/json")
    response := JsonRpcResponse{
        Jsonrpc: "2.0",
        ID:      id,
        Error: &RpcError{
            Code:    code,
            Message: message,
            Data:    data,
        },
    }
    json.NewEncoder(w).Encode(response)
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
    "jsonrpc": "2.0",
    "id": "test-123",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "messageId": "msg-test-123",
        "parts": [
          {
            "kind": "text",
            "text": "{\"topic\": \"AI\", \"depth\": \"basic\"}"
          }
        ]
      }
    }
  }'

# Test with authentication
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token-here" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-456",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "messageId": "msg-test-456",
        "parts": [
          {
            "kind": "text",
            "text": "{\"query\": \"What is machine learning?\"}"
          }
        ]
      }
    }
  }'

# Test error handling
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-789",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "messageId": "msg-test-789",
        "parts": [
          {
            "kind": "text",
            "text": "{}"
          }
        ]
      }
    }
  }'
```

### Using Python

```python
import requests

# Test successful request
response = requests.post(
    'http://localhost:8080',
    json={
        'jsonrpc': '2.0',
        'id': 'test-123',
        'method': 'message/send',
        'params': {
            'message': {
                'role': 'user',
                'messageId': 'msg-test-123',
                'parts': [
                    {
                        'kind': 'text',
                        'text': '{"topic": "AI", "depth": "basic"}'
                    }
                ]
            }
        }
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Expected output:
# Status: 200
# Response: {
#   'jsonrpc': '2.0',
#   'id': 'test-123',
#   'result': {
#     'status': {'state': 'completed'},
#     'artifacts': [...],
#     'history': [...]
#   }
# }
```

## Agent Registry Configuration

Agents must be registered in the Agent Registry with their endpoint URL and configuration. The protocol field should be set to "jsonrpc-2.0":

```json
{
  "name": "ResearchAgent",
  "url": "http://research-agent:8080",
  "protocol": "jsonrpc-2.0",
  "protocol_config": {
    "method": "message/send",
    "version": "2.0"
  },
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
Return JSON-RPC error response immediately for invalid input rather than processing and failing later.

### 2. Use Appropriate Error Codes
- Use JSON-RPC error codes (-32602) for invalid parameters
- Use -32600 for malformed requests
- Use -32603 for internal errors
- Use custom codes (-32000 to -32099) for application-specific errors

### 3. Include Detailed Error Messages
Help developers debug issues by providing clear, actionable error messages with the `data` field.

```json
{
  "jsonrpc": "2.0",
  "id": "task-123",
  "error": {
    "code": -32602,
    "message": "Invalid depth value: 'very-deep'. Must be one of: basic, intermediate, comprehensive",
    "data": {
      "field": "depth",
      "provided": "very-deep",
      "allowed": ["basic", "intermediate", "comprehensive"]
    }
  }
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
Always return results with `status.state`, `artifacts`, and `history` fields for consistency.

### 8. Support Idempotency
If possible, make your agent idempotent so retries don't cause duplicate side effects.

### 9. Use Artifacts for Primary Output
Place the main task output in the `artifacts` array with appropriate `parts`.

### 10. Include Conversation History
Populate the `history` array with both user and agent messages for context and debugging.

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

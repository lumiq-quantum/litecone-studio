# JSON-RPC 2.0 Migration Guide

## Overview

This guide helps you migrate your existing Simple A2A agents to the JSON-RPC 2.0 protocol. The migration is straightforward and involves updating your request/response handling to match the JSON-RPC 2.0 specification.

**Migration Timeline**: All agents must be updated before the bridge service is deployed with JSON-RPC support.

---

## Table of Contents

1. [Protocol Comparison](#protocol-comparison)
2. [Request Format Changes](#request-format-changes)
3. [Response Format Changes](#response-format-changes)
4. [Code Examples by Language](#code-examples-by-language)
5. [Testing Your Migration](#testing-your-migration)
6. [Common Migration Issues](#common-migration-issues)
7. [Validation Checklist](#validation-checklist)

---

## Protocol Comparison

### Simple A2A (Old Format)

**Request:**
```json
{
  "task_id": "task-123",
  "input": {
    "query": "What is the weather?",
    "context": "user location"
  }
}
```

**Response:**
```json
{
  "task_id": "task-123",
  "status": "success",
  "output": {
    "result": "The weather is sunny"
  },
  "error": null
}
```

### JSON-RPC 2.0 (New Format)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "task-123",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-task-123",
      "parts": [
        {
          "kind": "text",
          "text": "{\"query\": \"What is the weather?\", \"context\": \"user location\"}"
        }
      ]
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "task-123",
  "result": {
    "status": {
      "state": "completed"
    },
    "artifacts": [
      {
        "parts": [
          {
            "kind": "text",
            "text": "The weather is sunny"
          }
        ]
      }
    ],
    "history": [
      {
        "role": "user",
        "parts": [{"kind": "text", "text": "What is the weather?"}]
      },
      {
        "role": "agent",
        "parts": [{"kind": "text", "text": "The weather is sunny"}]
      }
    ]
  }
}
```

---

## Request Format Changes

### Key Differences

1. **Top-level structure**: Add `jsonrpc`, `method`, and `params` fields
2. **ID field**: `task_id` becomes `id`
3. **Input wrapping**: Input data is wrapped in `params.message.parts[]`
4. **Message structure**: Input is structured as a message with role and parts

### Field Mapping

| Simple A2A | JSON-RPC 2.0 | Notes |
|------------|--------------|-------|
| `task_id` | `id` | Direct mapping |
| `input` | `params.message.parts[].text` | Input serialized to text |
| N/A | `jsonrpc` | Always "2.0" |
| N/A | `method` | Always "message/send" |
| N/A | `params.message.role` | Always "user" |
| N/A | `params.message.messageId` | Generated from task_id |

### Extracting Input Data

The bridge converts your input data to JSON-RPC format. To extract it:

```python
# Extract from JSON-RPC request
def extract_input(jsonrpc_request):
    message = jsonrpc_request['params']['message']
    parts = message['parts']
    
    # Get text from first part
    if parts and parts[0]['kind'] == 'text':
        text = parts[0]['text']
        
        # Try to parse as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {'text': text}
    
    return {}
```

---

## Response Format Changes

### Key Differences

1. **Top-level structure**: Add `jsonrpc` and wrap output in `result`
2. **Status format**: Change from `status: "success"` to `result.status.state: "completed"`
3. **Output structure**: Output goes in `artifacts` and/or `history`
4. **Error handling**: Errors use JSON-RPC error object

### Success Response Structure

```json
{
  "jsonrpc": "2.0",
  "id": "<task_id>",
  "result": {
    "status": {
      "state": "completed"
    },
    "artifacts": [
      {
        "parts": [
          {
            "kind": "text",
            "text": "<your output here>"
          }
        ]
      }
    ],
    "history": [
      {
        "role": "user",
        "parts": [{"kind": "text", "text": "<user input>"}]
      },
      {
        "role": "agent",
        "parts": [{"kind": "text", "text": "<agent response>"}]
      }
    ]
  }
}
```

### Error Response Structure

```json
{
  "jsonrpc": "2.0",
  "id": "<task_id>",
  "error": {
    "code": -32603,
    "message": "Internal error: <error description>"
  }
}
```

### Common Error Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON received |
| -32600 | Invalid Request | Missing required fields |
| -32601 | Method not found | Unsupported method |
| -32602 | Invalid params | Invalid parameters |
| -32603 | Internal error | Agent processing error |

---

## Code Examples by Language

### Python (Flask)

#### Before (Simple A2A)

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/agent', methods=['POST'])
def handle_task():
    data = request.json
    task_id = data['task_id']
    input_data = data['input']
    
    try:
        # Process the task
        result = process_task(input_data)
        
        return jsonify({
            'task_id': task_id,
            'status': 'success',
            'output': result,
            'error': None
        })
    except Exception as e:
        return jsonify({
            'task_id': task_id,
            'status': 'error',
            'output': None,
            'error': str(e)
        }), 500

def process_task(input_data):
    query = input_data.get('query', '')
    # Your processing logic here
    return {'result': f'Processed: {query}'}

if __name__ == '__main__':
    app.run(port=8080)
```

#### After (JSON-RPC 2.0)

```python
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/agent', methods=['POST'])
def handle_jsonrpc():
    data = request.json
    
    # Validate JSON-RPC structure
    if data.get('jsonrpc') != '2.0':
        return jsonify({
            'jsonrpc': '2.0',
            'id': data.get('id'),
            'error': {
                'code': -32600,
                'message': 'Invalid Request: jsonrpc must be 2.0'
            }
        }), 400
    
    if data.get('method') != 'message/send':
        return jsonify({
            'jsonrpc': '2.0',
            'id': data.get('id'),
            'error': {
                'code': -32601,
                'message': f'Method not found: {data.get("method")}'
            }
        }), 400
    
    task_id = data['id']
    
    try:
        # Extract input from message parts
        message = data['params']['message']
        parts = message['parts']
        
        # Get text from first part and parse as JSON
        input_text = parts[0]['text']
        try:
            input_data = json.loads(input_text)
        except json.JSONDecodeError:
            input_data = {'text': input_text}
        
        # Process the task
        result = process_task(input_data)
        
        # Build JSON-RPC response
        return jsonify({
            'jsonrpc': '2.0',
            'id': task_id,
            'result': {
                'status': {
                    'state': 'completed'
                },
                'artifacts': [
                    {
                        'parts': [
                            {
                                'kind': 'text',
                                'text': json.dumps(result) if isinstance(result, dict) else str(result)
                            }
                        ]
                    }
                ],
                'history': [
                    {
                        'role': 'user',
                        'parts': [{'kind': 'text', 'text': input_text}]
                    },
                    {
                        'role': 'agent',
                        'parts': [{'kind': 'text', 'text': json.dumps(result)}]
                    }
                ]
            }
        })
    
    except Exception as e:
        return jsonify({
            'jsonrpc': '2.0',
            'id': task_id,
            'error': {
                'code': -32603,
                'message': f'Internal error: {str(e)}'
            }
        }), 500

def process_task(input_data):
    query = input_data.get('query', '')
    # Your processing logic here
    return {'result': f'Processed: {query}'}

if __name__ == '__main__':
    app.run(port=8080)
```

### Node.js (Express)

#### Before (Simple A2A)

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/agent', async (req, res) => {
  const { task_id, input } = req.body;
  
  try {
    const result = await processTask(input);
    
    res.json({
      task_id,
      status: 'success',
      output: result,
      error: null
    });
  } catch (error) {
    res.status(500).json({
      task_id,
      status: 'error',
      output: null,
      error: error.message
    });
  }
});

async function processTask(input) {
  const query = input.query || '';
  // Your processing logic here
  return { result: `Processed: ${query}` };
}

app.listen(8080, () => {
  console.log('Agent listening on port 8080');
});
```

#### After (JSON-RPC 2.0)

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/agent', async (req, res) => {
  const { jsonrpc, id, method, params } = req.body;
  
  // Validate JSON-RPC structure
  if (jsonrpc !== '2.0') {
    return res.status(400).json({
      jsonrpc: '2.0',
      id,
      error: {
        code: -32600,
        message: 'Invalid Request: jsonrpc must be 2.0'
      }
    });
  }
  
  if (method !== 'message/send') {
    return res.status(400).json({
      jsonrpc: '2.0',
      id,
      error: {
        code: -32601,
        message: `Method not found: ${method}`
      }
    });
  }
  
  try {
    // Extract input from message parts
    const message = params.message;
    const parts = message.parts;
    const inputText = parts[0].text;
    
    // Parse input
    let inputData;
    try {
      inputData = JSON.parse(inputText);
    } catch (e) {
      inputData = { text: inputText };
    }
    
    // Process the task
    const result = await processTask(inputData);
    const resultText = typeof result === 'object' ? JSON.stringify(result) : String(result);
    
    // Build JSON-RPC response
    res.json({
      jsonrpc: '2.0',
      id,
      result: {
        status: {
          state: 'completed'
        },
        artifacts: [
          {
            parts: [
              {
                kind: 'text',
                text: resultText
              }
            ]
          }
        ],
        history: [
          {
            role: 'user',
            parts: [{ kind: 'text', text: inputText }]
          },
          {
            role: 'agent',
            parts: [{ kind: 'text', text: resultText }]
          }
        ]
      }
    });
  } catch (error) {
    res.status(500).json({
      jsonrpc: '2.0',
      id,
      error: {
        code: -32603,
        message: `Internal error: ${error.message}`
      }
    });
  }
});

async function processTask(input) {
  const query = input.query || '';
  // Your processing logic here
  return { result: `Processed: ${query}` };
}

app.listen(8080, () => {
  console.log('Agent listening on port 8080');
});
```

### Go (net/http)

#### Before (Simple A2A)

```go
package main

import (
    "encoding/json"
    "log"
    "net/http"
)

type SimpleRequest struct {
    TaskID string                 `json:"task_id"`
    Input  map[string]interface{} `json:"input"`
}

type SimpleResponse struct {
    TaskID string                 `json:"task_id"`
    Status string                 `json:"status"`
    Output map[string]interface{} `json:"output"`
    Error  *string                `json:"error"`
}

func handleTask(w http.ResponseWriter, r *http.Request) {
    var req SimpleRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    result, err := processTask(req.Input)
    
    w.Header().Set("Content-Type", "application/json")
    
    if err != nil {
        errMsg := err.Error()
        json.NewEncoder(w).Encode(SimpleResponse{
            TaskID: req.TaskID,
            Status: "error",
            Output: nil,
            Error:  &errMsg,
        })
        return
    }
    
    json.NewEncoder(w).Encode(SimpleResponse{
        TaskID: req.TaskID,
        Status: "success",
        Output: result,
        Error:  nil,
    })
}

func processTask(input map[string]interface{}) (map[string]interface{}, error) {
    query := input["query"].(string)
    return map[string]interface{}{
        "result": "Processed: " + query,
    }, nil
}

func main() {
    http.HandleFunc("/agent", handleTask)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

#### After (JSON-RPC 2.0)

```go
package main

import (
    "encoding/json"
    "log"
    "net/http"
)

type JsonRpcRequest struct {
    Jsonrpc string                 `json:"jsonrpc"`
    ID      string                 `json:"id"`
    Method  string                 `json:"method"`
    Params  map[string]interface{} `json:"params"`
}

type JsonRpcResponse struct {
    Jsonrpc string                 `json:"jsonrpc"`
    ID      string                 `json:"id"`
    Result  *JsonRpcResult         `json:"result,omitempty"`
    Error   *JsonRpcError          `json:"error,omitempty"`
}

type JsonRpcResult struct {
    Status    map[string]string        `json:"status"`
    Artifacts []map[string]interface{} `json:"artifacts"`
    History   []map[string]interface{} `json:"history"`
}

type JsonRpcError struct {
    Code    int    `json:"code"`
    Message string `json:"message"`
}

func handleJsonRpc(w http.ResponseWriter, r *http.Request) {
    var req JsonRpcRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    
    // Validate JSON-RPC structure
    if req.Jsonrpc != "2.0" {
        json.NewEncoder(w).Encode(JsonRpcResponse{
            Jsonrpc: "2.0",
            ID:      req.ID,
            Error: &JsonRpcError{
                Code:    -32600,
                Message: "Invalid Request: jsonrpc must be 2.0",
            },
        })
        return
    }
    
    if req.Method != "message/send" {
        json.NewEncoder(w).Encode(JsonRpcResponse{
            Jsonrpc: "2.0",
            ID:      req.ID,
            Error: &JsonRpcError{
                Code:    -32601,
                Message: "Method not found: " + req.Method,
            },
        })
        return
    }
    
    // Extract input from message parts
    message := req.Params["message"].(map[string]interface{})
    parts := message["parts"].([]interface{})
    firstPart := parts[0].(map[string]interface{})
    inputText := firstPart["text"].(string)
    
    // Parse input
    var inputData map[string]interface{}
    if err := json.Unmarshal([]byte(inputText), &inputData); err != nil {
        inputData = map[string]interface{}{"text": inputText}
    }
    
    // Process the task
    result, err := processTask(inputData)
    
    if err != nil {
        json.NewEncoder(w).Encode(JsonRpcResponse{
            Jsonrpc: "2.0",
            ID:      req.ID,
            Error: &JsonRpcError{
                Code:    -32603,
                Message: "Internal error: " + err.Error(),
            },
        })
        return
    }
    
    // Convert result to JSON string
    resultBytes, _ := json.Marshal(result)
    resultText := string(resultBytes)
    
    // Build JSON-RPC response
    json.NewEncoder(w).Encode(JsonRpcResponse{
        Jsonrpc: "2.0",
        ID:      req.ID,
        Result: &JsonRpcResult{
            Status: map[string]string{
                "state": "completed",
            },
            Artifacts: []map[string]interface{}{
                {
                    "parts": []map[string]interface{}{
                        {
                            "kind": "text",
                            "text": resultText,
                        },
                    },
                },
            },
            History: []map[string]interface{}{
                {
                    "role": "user",
                    "parts": []map[string]interface{}{
                        {"kind": "text", "text": inputText},
                    },
                },
                {
                    "role": "agent",
                    "parts": []map[string]interface{}{
                        {"kind": "text", "text": resultText},
                    },
                },
            },
        },
    })
}

func processTask(input map[string]interface{}) (map[string]interface{}, error) {
    query := input["query"].(string)
    return map[string]interface{}{
        "result": "Processed: " + query,
    }, nil
}

func main() {
    http.HandleFunc("/agent", handleJsonRpc)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

---

## Testing Your Migration

### 1. Manual Testing with curl

#### Test JSON-RPC Request

```bash
curl -X POST http://localhost:8080/agent \
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
            "text": "{\"query\": \"test query\"}"
          }
        ]
      }
    }
  }'
```

#### Expected Response

```json
{
  "jsonrpc": "2.0",
  "id": "test-123",
  "result": {
    "status": {
      "state": "completed"
    },
    "artifacts": [
      {
        "parts": [
          {
            "kind": "text",
            "text": "{\"result\": \"Processed: test query\"}"
          }
        ]
      }
    ],
    "history": [
      {
        "role": "user",
        "parts": [{"kind": "text", "text": "{\"query\": \"test query\"}"}]
      },
      {
        "role": "agent",
        "parts": [{"kind": "text", "text": "{\"result\": \"Processed: test query\"}"}]
      }
    ]
  }
}
```

### 2. Automated Testing

Create a test script to validate your agent:

```python
import requests
import json

def test_jsonrpc_agent(url):
    """Test agent with JSON-RPC 2.0 format."""
    
    # Test 1: Valid request
    request = {
        "jsonrpc": "2.0",
        "id": "test-1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "msg-test-1",
                "parts": [
                    {
                        "kind": "text",
                        "text": json.dumps({"query": "test"})
                    }
                ]
            }
        }
    }
    
    response = requests.post(url, json=request)
    assert response.status_code == 200
    
    data = response.json()
    assert data['jsonrpc'] == '2.0'
    assert data['id'] == 'test-1'
    assert 'result' in data
    assert data['result']['status']['state'] == 'completed'
    assert 'artifacts' in data['result']
    
    print("✓ Valid request test passed")
    
    # Test 2: Invalid jsonrpc version
    request['jsonrpc'] = '1.0'
    response = requests.post(url, json=request)
    data = response.json()
    assert 'error' in data
    assert data['error']['code'] == -32600
    
    print("✓ Invalid version test passed")
    
    # Test 3: Invalid method
    request['jsonrpc'] = '2.0'
    request['method'] = 'invalid/method'
    response = requests.post(url, json=request)
    data = response.json()
    assert 'error' in data
    assert data['error']['code'] == -32601
    
    print("✓ Invalid method test passed")
    
    print("\n✅ All tests passed!")

if __name__ == '__main__':
    test_jsonrpc_agent('http://localhost:8080/agent')
```

### 3. Integration Testing

Once your agent is updated, test it with the workflow system:

1. Register your agent with the API
2. Create a simple workflow that uses your agent
3. Execute the workflow
4. Verify the results

---

## Common Migration Issues

### Issue 1: Input Extraction Fails

**Symptom**: Agent receives request but can't parse input data

**Cause**: Not properly extracting text from `params.message.parts[]`

**Solution**:
```python
# Correct way to extract input
message = request['params']['message']
parts = message['parts']
input_text = parts[0]['text']

# Parse as JSON if possible
try:
    input_data = json.loads(input_text)
except json.JSONDecodeError:
    input_data = {'text': input_text}
```

### Issue 2: Response Missing Required Fields

**Symptom**: Bridge logs "malformed JSON-RPC response"

**Cause**: Response missing `jsonrpc`, `id`, or `result`/`error`

**Solution**:
```python
# Always include these fields
response = {
    'jsonrpc': '2.0',  # Required
    'id': task_id,      # Required - must match request
    'result': {         # Required for success (or 'error' for failure)
        'status': {'state': 'completed'},
        'artifacts': [...],
        'history': [...]
    }
}
```

### Issue 3: Empty Artifacts Array

**Symptom**: Bridge extracts no output from response

**Cause**: Artifacts array is empty or missing `parts`

**Solution**:
```python
# Always include at least one artifact with parts
'artifacts': [
    {
        'parts': [
            {
                'kind': 'text',
                'text': 'Your output here'
            }
        ]
    }
]
```

### Issue 4: Status State Not Recognized

**Symptom**: Task marked as failed even though agent succeeded

**Cause**: `status.state` is not set to "completed"

**Solution**:
```python
# Use exact string "completed"
'status': {
    'state': 'completed'  # Not "success", "done", etc.
}
```

### Issue 5: Error Responses Not Formatted Correctly

**Symptom**: Errors not properly reported to workflow system

**Cause**: Using `result` instead of `error` for failures

**Solution**:
```python
# For errors, use error object instead of result
{
    'jsonrpc': '2.0',
    'id': task_id,
    'error': {
        'code': -32603,
        'message': 'Description of error'
    }
}
```

### Issue 6: History Array Format Issues

**Symptom**: Bridge can't extract output from history

**Cause**: History items missing `role` or `parts` fields

**Solution**:
```python
# Correct history format
'history': [
    {
        'role': 'user',
        'parts': [{'kind': 'text', 'text': 'user input'}]
    },
    {
        'role': 'agent',
        'parts': [{'kind': 'text', 'text': 'agent response'}]
    }
]
```

### Issue 7: Content-Type Header Issues

**Symptom**: Agent receives request but can't parse it

**Cause**: Not setting proper Content-Type header

**Solution**:
```python
# In your agent, ensure you're accepting JSON
@app.route('/agent', methods=['POST'])
def handle_request():
    if request.content_type != 'application/json':
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    # ... rest of handler
```

### Issue 8: ID Mismatch

**Symptom**: Bridge logs "Response ID mismatch"

**Cause**: Response `id` doesn't match request `id`

**Solution**:
```python
# Always use the same ID from the request
request_id = request_data['id']

response = {
    'jsonrpc': '2.0',
    'id': request_id,  # Must match exactly
    'result': {...}
}
```

---

## Validation Checklist

Use this checklist to ensure your agent is fully migrated:

### Request Handling

- [ ] Agent accepts JSON-RPC 2.0 requests
- [ ] Agent validates `jsonrpc` field equals "2.0"
- [ ] Agent validates `method` field equals "message/send"
- [ ] Agent extracts input from `params.message.parts[]`
- [ ] Agent handles JSON-serialized input data
- [ ] Agent handles plain text input data

### Response Format

- [ ] Response includes `jsonrpc: "2.0"`
- [ ] Response includes `id` matching request
- [ ] Success responses include `result` object
- [ ] Result includes `status.state: "completed"`
- [ ] Result includes `artifacts` array with parts
- [ ] Result includes `history` array with user and agent messages
- [ ] Each part has `kind` and `text` fields
- [ ] Error responses use `error` object instead of `result`
- [ ] Error object includes `code` and `message`

### Error Handling

- [ ] Invalid `jsonrpc` version returns error code -32600
- [ ] Invalid `method` returns error code -32601
- [ ] Invalid `params` returns error code -32602
- [ ] Internal errors return error code -32603
- [ ] All errors include descriptive messages

### Testing

- [ ] Manual curl test passes
- [ ] Automated test script passes
- [ ] Agent works in workflow system
- [ ] Error scenarios handled correctly
- [ ] Logs show proper JSON-RPC format

### Documentation

- [ ] Agent documentation updated
- [ ] API examples updated to JSON-RPC 2.0
- [ ] Team notified of migration

---

## Migration Support

### Getting Help

If you encounter issues during migration:

1. **Check the logs**: Bridge logs show detailed JSON-RPC communication
2. **Use curl**: Test your agent directly with curl commands
3. **Review examples**: Compare your code to the examples in this guide
4. **Check common issues**: Review the Common Migration Issues section

### Deployment Coordination

Before the bridge service is deployed:

1. Update your agent code
2. Test with curl and automated tests
3. Deploy your updated agent
4. Notify the platform team that your agent is ready
5. Verify in development environment before production

### Rollback Plan

If issues arise after deployment:

1. The bridge service can be rolled back to Simple A2A
2. Your agent should continue working with JSON-RPC 2.0
3. No data loss will occur during rollback

---

## Summary

The migration from Simple A2A to JSON-RPC 2.0 involves:

1. **Request changes**: Extract input from `params.message.parts[]`
2. **Response changes**: Wrap output in `result.artifacts` and `result.history`
3. **Error handling**: Use JSON-RPC error format
4. **Testing**: Validate with curl and automated tests

The protocol change is straightforward and provides better structure for agent communication. Follow the code examples for your language, test thoroughly, and coordinate deployment with the platform team.

**Questions?** Contact the platform team or refer to the [A2A Agent Interface Documentation](A2A_AGENT_INTERFACE.md).

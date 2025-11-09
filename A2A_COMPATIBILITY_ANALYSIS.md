# A2A Protocol Compatibility Analysis

## Summary

**Current Status:** ❌ **NOT COMPATIBLE**

Our system uses a **simple A2A HTTP protocol**, while your agents use **JSON-RPC 2.0 A2A protocol**. These are two different standards and are not directly compatible.

## Current System Format (Simple A2A)

### Request
```json
{
  "task_id": "task-abc123-def456",
  "input": {
    "topic": "Climate Change",
    "depth": "comprehensive"
  }
}
```

### Response
```json
{
  "task_id": "task-abc123-def456",
  "status": "success",
  "output": {
    "findings": ["Finding 1", "Finding 2"],
    "summary": "Summary text"
  },
  "error": null
}
```

### Characteristics
- Simple key-value structure
- Direct input/output mapping
- Status field for success/error
- No protocol versioning
- No method specification

## Your Agent Format (JSON-RPC 2.0 A2A)

### Request
```json
{
  "jsonrpc": "2.0",
  "id": "req-004",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-user-005",
      "parts": [
        {
          "kind": "text",
          "text": "What can you do?"
        }
      ]
    }
  }
}
```

### Response
```json
{
  "id": "req-004",
  "jsonrpc": "2.0",
  "result": {
    "artifacts": [...],
    "contextId": "...",
    "history": [...],
    "id": "...",
    "kind": "task",
    "metadata": {...},
    "status": {
      "state": "completed",
      "timestamp": "2025-11-08T10:40:34.322759+00:00"
    }
  }
}
```

### Characteristics
- JSON-RPC 2.0 protocol
- Method-based invocation
- Structured message format with parts
- Context and history tracking
- Rich metadata
- Artifacts support
- Conversation-style interaction

## Key Differences

| Aspect | Our System | Your Agents |
|--------|-----------|-------------|
| **Protocol** | Simple HTTP/JSON | JSON-RPC 2.0 |
| **Request ID** | `task_id` | `id` + `jsonrpc` |
| **Method** | Implicit (POST to endpoint) | Explicit (`method: "message/send"`) |
| **Input** | Direct `input` object | Nested in `params.message` |
| **Message Structure** | Flat key-value | Structured with `parts`, `role`, `messageId` |
| **Output** | Direct `output` object | Nested in `result` with artifacts |
| **Status** | `status: "success"/"error"` | `result.status.state: "completed"` |
| **Context** | None | `contextId`, `history` |
| **Conversation** | Single request/response | Multi-turn with history |
| **Metadata** | Minimal | Rich (`adk_*` fields, usage) |

## Compatibility Issues

### 1. Protocol Mismatch
- Our system doesn't send `jsonrpc` or `method` fields
- Your agents expect JSON-RPC 2.0 structure

### 2. Request Structure
- We send: `{"task_id": "...", "input": {...}}`
- You expect: `{"jsonrpc": "2.0", "id": "...", "method": "...", "params": {...}}`

### 3. Message Format
- We send flat input data
- You expect structured messages with `role`, `parts`, `messageId`

### 4. Response Structure
- We expect: `{"task_id": "...", "status": "...", "output": {...}}`
- You return: `{"id": "...", "jsonrpc": "2.0", "result": {...}}`

### 5. Conversation Context
- Our system is stateless (single request/response)
- Your agents maintain context and history

## Solutions

### Option 1: Add JSON-RPC 2.0 Adapter (Recommended)

Create an adapter layer in the bridge that translates between formats:

**Pros:**
- Supports both protocols
- No changes to existing agents
- Backward compatible
- Can be toggled per agent

**Cons:**
- Additional complexity
- Translation overhead
- May lose some features (context, history)

**Implementation:**
```python
# In bridge: src/bridge/adapters/jsonrpc_adapter.py

class JsonRpcAdapter:
    """Adapter to translate between simple A2A and JSON-RPC 2.0 A2A"""
    
    def to_jsonrpc_request(self, task: AgentTask) -> dict:
        """Convert simple A2A request to JSON-RPC 2.0"""
        return {
            "jsonrpc": "2.0",
            "id": task.task_id,
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "messageId": f"msg-{task.task_id}",
                    "parts": self._convert_input_to_parts(task.input_data)
                }
            }
        }
    
    def from_jsonrpc_response(self, response: dict) -> dict:
        """Convert JSON-RPC 2.0 response to simple A2A"""
        result = response.get("result", {})
        
        # Extract output from artifacts or history
        output = self._extract_output(result)
        
        return {
            "task_id": response.get("id"),
            "status": "success" if result.get("status", {}).get("state") == "completed" else "error",
            "output": output,
            "error": None
        }
    
    def _convert_input_to_parts(self, input_data: dict) -> list:
        """Convert flat input to message parts"""
        # Simple conversion: treat all input as text
        text = json.dumps(input_data) if isinstance(input_data, dict) else str(input_data)
        return [{"kind": "text", "text": text}]
    
    def _extract_output(self, result: dict) -> dict:
        """Extract output from JSON-RPC result"""
        # Extract from artifacts or history
        artifacts = result.get("artifacts", [])
        if artifacts:
            # Get text from first artifact
            parts = artifacts[0].get("parts", [])
            if parts:
                return {"text": parts[0].get("text", "")}
        
        # Fallback: return full result
        return result
```

### Option 2: Update All Agents to Simple A2A

Modify your agents to support the simple A2A format.

**Pros:**
- Simpler system
- No translation overhead
- Direct compatibility

**Cons:**
- Requires changing all agents
- Loses JSON-RPC features
- Not backward compatible with existing agents

### Option 3: Dual Protocol Support

Support both protocols in the bridge, configured per agent.

**Pros:**
- Maximum flexibility
- Supports both agent types
- Can migrate gradually

**Cons:**
- Most complex implementation
- Two code paths to maintain
- Configuration overhead

**Implementation:**
```python
# In agent registry, add protocol field:
{
  "name": "JsonRpcAgent",
  "url": "http://agent:8001",
  "protocol": "jsonrpc-2.0",  # or "simple-a2a"
  "protocol_config": {
    "method": "message/send"
  }
}

# In bridge, check protocol and use appropriate adapter:
if agent_metadata.protocol == "jsonrpc-2.0":
    request = jsonrpc_adapter.to_jsonrpc_request(task)
    response = await http_client.post(url, json=request)
    result = jsonrpc_adapter.from_jsonrpc_response(response.json())
else:
    # Use simple A2A format
    request = {"task_id": task.task_id, "input": task.input_data}
    response = await http_client.post(url, json=request)
    result = response.json()
```

## Recommended Approach

**Implement Option 3: Dual Protocol Support**

This provides the best balance of:
1. **Compatibility** - Works with both agent types
2. **Flexibility** - Can add more protocols in future
3. **Migration Path** - Can gradually migrate agents
4. **Feature Preservation** - Doesn't lose JSON-RPC features

### Implementation Steps

1. **Add Protocol Field to Agent Registry**
   - Update agent model to include `protocol` field
   - Add `protocol_config` for protocol-specific settings

2. **Create Protocol Adapters**
   - `SimpleA2AAdapter` (current format)
   - `JsonRpc2Adapter` (your format)
   - `ProtocolAdapterFactory` to select adapter

3. **Update Bridge**
   - Detect agent protocol from metadata
   - Use appropriate adapter for request/response
   - Handle protocol-specific errors

4. **Update Documentation**
   - Document both protocols
   - Provide examples for each
   - Migration guide

5. **Add Tests**
   - Test both protocols
   - Test adapter translations
   - Test error handling

## Example Configuration

### Simple A2A Agent (Current)
```json
{
  "name": "ResearchAgent",
  "url": "http://research-agent:8080",
  "protocol": "simple-a2a",
  "auth_type": "none",
  "timeout_ms": 30000
}
```

### JSON-RPC 2.0 Agent (Your Format)
```json
{
  "name": "HelloWorldAgent",
  "url": "http://hello-world-agent:8001",
  "protocol": "jsonrpc-2.0",
  "protocol_config": {
    "method": "message/send",
    "version": "2.0"
  },
  "auth_type": "none",
  "timeout_ms": 30000
}
```

## Testing Strategy

### 1. Unit Tests
```python
def test_jsonrpc_adapter_request():
    adapter = JsonRpc2Adapter()
    task = AgentTask(
        task_id="test-123",
        input_data={"query": "What can you do?"}
    )
    
    request = adapter.to_jsonrpc_request(task)
    
    assert request["jsonrpc"] == "2.0"
    assert request["id"] == "test-123"
    assert request["method"] == "message/send"
    assert "params" in request

def test_jsonrpc_adapter_response():
    adapter = JsonRpc2Adapter()
    response = {
        "id": "test-123",
        "jsonrpc": "2.0",
        "result": {
            "status": {"state": "completed"},
            "artifacts": [{"parts": [{"kind": "text", "text": "I can help"}]}]
        }
    }
    
    result = adapter.from_jsonrpc_response(response)
    
    assert result["task_id"] == "test-123"
    assert result["status"] == "success"
    assert "output" in result
```

### 2. Integration Tests
```python
async def test_jsonrpc_agent_invocation():
    # Start mock JSON-RPC agent
    agent = MockJsonRpcAgent(port=8001)
    
    # Register agent with JSON-RPC protocol
    await register_agent({
        "name": "TestAgent",
        "url": "http://localhost:8001",
        "protocol": "jsonrpc-2.0"
    })
    
    # Execute workflow with JSON-RPC agent
    result = await execute_workflow(workflow_with_jsonrpc_agent)
    
    assert result.status == "COMPLETED"
```

### 3. End-to-End Tests
```bash
# Test with real JSON-RPC agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "HelloWorldAgent",
    "url": "http://hello-world-agent:8001",
    "protocol": "jsonrpc-2.0"
  }'

# Execute workflow
curl -X POST http://localhost:8000/api/v1/workflows/{id}/execute \
  -d '{"query": "What can you do?"}'
```

## Migration Timeline

### Phase 1: Design & Planning (1-2 days)
- Finalize adapter design
- Update data models
- Plan database migrations

### Phase 2: Implementation (3-5 days)
- Implement protocol adapters
- Update bridge code
- Add protocol detection
- Update agent registry

### Phase 3: Testing (2-3 days)
- Unit tests
- Integration tests
- End-to-end tests
- Performance testing

### Phase 4: Documentation (1-2 days)
- Update A2A specification
- Add JSON-RPC examples
- Migration guide
- API documentation

### Phase 5: Deployment (1 day)
- Deploy to dev environment
- Test with real agents
- Deploy to production

**Total Estimated Time: 7-13 days**

## Next Steps

1. **Confirm Approach**: Agree on Option 3 (Dual Protocol Support)
2. **Review Design**: Review adapter design and implementation plan
3. **Create Tasks**: Break down into implementation tasks
4. **Start Implementation**: Begin with protocol adapter
5. **Test Incrementally**: Test each component as it's built

## Questions to Answer

1. Do all your agents use JSON-RPC 2.0, or are there variations?
2. What JSON-RPC methods do your agents support besides `message/send`?
3. Do you need context/history preservation across workflow steps?
4. Are there other protocol features we need to support?
5. What's the priority timeline for this compatibility?

## References

- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Current A2A Specification](A2A_AGENT_INTERFACE.md)
- [Bridge Implementation](src/bridge/external_agent_executor.py)

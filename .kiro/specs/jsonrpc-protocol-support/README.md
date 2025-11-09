# JSON-RPC 2.0 Protocol Migration

## Overview

Migrate the workflow orchestration system from Simple A2A HTTP protocol to JSON-RPC 2.0 protocol for all agent communication.

## Problem Statement

The current system uses a custom Simple A2A format, but all agents now use JSON-RPC 2.0 standard. We need to update the bridge to send JSON-RPC 2.0 requests instead.

**Current Format (to be replaced):**
```json
Request:  {"task_id": "...", "input": {...}}
Response: {"task_id": "...", "status": "success", "output": {...}}
```

**New Format (JSON-RPC 2.0):**
```json
Request:  {
  "jsonrpc": "2.0",
  "id": "task-123",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-123",
      "parts": [{"kind": "text", "text": "..."}]
    }
  }
}

Response: {
  "jsonrpc": "2.0",
  "id": "task-123",
  "result": {
    "status": {"state": "completed"},
    "artifacts": [...],
    "history": [...]
  }
}
```

## Solution

**Simple replacement** - Update the bridge to:
1. Send JSON-RPC 2.0 formatted requests
2. Parse JSON-RPC 2.0 formatted responses
3. Extract output from artifacts/history

**No dual protocol support needed** - All agents use JSON-RPC 2.0.

## Key Changes

1. **Bridge Request Format** - Change `invoke_agent()` to send JSON-RPC 2.0
2. **Bridge Response Parsing** - Parse JSON-RPC 2.0 responses
3. **Input Conversion** - Convert task input to message parts
4. **Output Extraction** - Extract text from artifacts/history
5. **Error Handling** - Handle JSON-RPC error responses

## Implementation

**Simple 3-step process:**

1. **Update Bridge** (1 day)
   - Modify request construction
   - Modify response parsing
   - Add helper functions

2. **Update Tests** (1 day)
   - Update mock agents to use JSON-RPC
   - Update test expectations
   - Add JSON-RPC validation

3. **Update Documentation** (0.5 day)
   - Update A2A spec
   - Update examples
   - Update agent implementation guide

**Total: 2-3 days**

## Files

- **requirements.md** - Updated requirements (simplified)
- **design.md** - Technical design (simplified)
- **tasks.md** - Implementation tasks (simplified)

## Success Criteria

- ✅ Bridge sends JSON-RPC 2.0 requests
- ✅ Bridge parses JSON-RPC 2.0 responses
- ✅ Workflows execute successfully
- ✅ Tests pass
- ✅ Documentation updated

## Next Steps

Start with the bridge update - it's a straightforward code change!

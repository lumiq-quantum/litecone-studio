# Implementation Plan: JSON-RPC 2.0 Protocol Migration

## Overview

Replace Simple A2A protocol with JSON-RPC 2.0 protocol for all agent communication. This is a straightforward migration - no dual protocol support needed.

---

## Phase 1: Bridge Updates

- [x] 1. Update bridge request format
  - [x] 1.1 Modify `invoke_agent()` in `src/bridge/external_agent_executor.py` to construct JSON-RPC 2.0 request
  - [x] 1.2 Create helper function `_build_jsonrpc_request(task: AgentTask)` to build request structure
  - [x] 1.3 Create helper function `_convert_input_to_message_parts(input_data: dict)` to convert input to message parts
  - [x] 1.4 Update request to include `jsonrpc`, `id`, `method`, and `params` fields
  - [x] 1.5 Set `method` to "message/send"
  - [x] 1.6 Use task_id as JSON-RPC `id`
  - _Requirements: Send JSON-RPC 2.0 formatted requests_

- [x] 2. Update bridge response parsing
  - [x] 2.1 Create helper function `_parse_jsonrpc_response(response: dict, task_id: str)` to parse JSON-RPC responses
  - [x] 2.2 Validate response contains `jsonrpc`, `id`, and either `result` or `error`
  - [x] 2.3 Handle JSON-RPC error responses (extract error code and message)
  - [x] 2.4 Create helper function `_extract_output_from_result(result: dict)` to extract output
  - [x] 2.5 Extract text from `artifacts[].parts[]` where `kind == "text"`
  - [x] 2.6 Extract text from `history[]` where `role == "agent"`
  - [x] 2.7 Map `result.status.state == "completed"` to success
  - [x] 2.8 Return output in format expected by executor: `{"task_id": "...", "status": "...", "output": {...}}`
  - _Requirements: Parse JSON-RPC 2.0 responses and extract output_

- [x] 3. Update error handling
  - [x] 3.1 Add specific error handling for malformed JSON-RPC responses
  - [x] 3.2 Log JSON-RPC error responses with code and message
  - [x] 3.3 Handle missing `result` or `error` fields
  - [x] 3.4 Handle invalid `jsonrpc` version
  - [x] 3.5 Add detailed logging for debugging JSON-RPC issues
  - _Requirements: Proper error handling for JSON-RPC protocol_

---

## Phase 2: Testing Updates

- [x] 4. Update mock agents
  - [x] 4.1 Update `examples/mock_agent.py` to return JSON-RPC 2.0 responses
  - [x] 4.2 Update mock agent to accept JSON-RPC 2.0 requests
  - [x] 4.3 Update mock agent to validate JSON-RPC request structure
  - [x] 4.4 Update mock agent to return proper `artifacts` and `history` in response
  - _Requirements: Mock agents use JSON-RPC 2.0 format_

- [ ] 5. Update unit tests
  - [ ] 5.1 Update bridge unit tests to expect JSON-RPC 2.0 request format
  - [ ] 5.2 Update bridge unit tests to provide JSON-RPC 2.0 response format
  - [ ] 5.3 Add test for `_build_jsonrpc_request()` helper
  - [ ] 5.4 Add test for `_convert_input_to_message_parts()` helper
  - [ ] 5.5 Add test for `_parse_jsonrpc_response()` helper
  - [ ] 5.6 Add test for `_extract_output_from_result()` helper
  - [ ] 5.7 Add test for JSON-RPC error response handling
  - _Requirements: Unit tests validate JSON-RPC format_

- [ ] 6. Update integration tests
  - [ ] 6.1 Update integration tests to use JSON-RPC mock agents
  - [ ] 6.2 Test end-to-end workflow with JSON-RPC agents
  - [ ] 6.3 Test error scenarios with JSON-RPC error responses
  - [ ] 6.4 Test timeout handling with JSON-RPC agents
  - _Requirements: Integration tests work with JSON-RPC_

---

## Phase 3: Documentation Updates

- [x] 7. Update A2A documentation
  - [x] 7.1 Update `A2A_AGENT_INTERFACE.md` to document JSON-RPC 2.0 format
  - [x] 7.2 Replace Simple A2A examples with JSON-RPC 2.0 examples
  - [x] 7.3 Document JSON-RPC request structure with all fields
  - [x] 7.4 Document JSON-RPC response structure with artifacts and history
  - [x] 7.5 Document JSON-RPC error response format
  - [x] 7.6 Update agent implementation examples (Python, Node.js, Go) to use JSON-RPC 2.0
  - _Requirements: Documentation reflects JSON-RPC 2.0 protocol_

- [x] 8. Update workflow documentation
  - [x] 8.1 Update `WORKFLOW_FORMAT.md` if needed
  - [x] 8.2 Update `QUICKSTART.md` with JSON-RPC examples
  - [x] 8.3 Update `MANUAL_TESTING_GUIDE.md` with JSON-RPC curl examples
  - [x] 8.4 Update README.md if needed
  - _Requirements: All documentation uses JSON-RPC 2.0_

- [x] 9. Create migration guide
  - [x] 9.1 Create `JSONRPC_MIGRATION_GUIDE.md` for existing agent developers
  - [x] 9.2 Document how to convert Simple A2A agents to JSON-RPC 2.0
  - [x] 9.3 Provide before/after code examples
  - [x] 9.4 Document common migration issues and solutions
  - _Requirements: Help developers migrate their agents_

---

## Phase 4: Deployment

- [x] 10. Deploy to development
  - [x] 10.1 Deploy updated bridge service
  - [x] 10.2 Update mock agents to JSON-RPC 2.0
  - [x] 10.3 Test with sample workflow
  - [x] 10.4 Verify logs show correct JSON-RPC format
  - [x] 10.5 Test error scenarios
  - _Requirements: Dev environment works with JSON-RPC_

- [ ] 11. Validate and deploy to production
  - [ ] 11.1 Coordinate with agent developers to update their agents
  - [ ] 11.2 Schedule deployment window
  - [ ] 11.3 Deploy bridge service
  - [ ] 11.4 Monitor logs for errors
  - [ ] 11.5 Verify workflows execute successfully
  - [ ] 11.6 Have rollback plan ready
  - _Requirements: Production deployment successful_

---

## Summary

**Total Tasks:** 11 main tasks, 60+ sub-tasks

**Estimated Timeline:**
- Phase 1 (Bridge): 1 day
- Phase 2 (Testing): 1 day  
- Phase 3 (Documentation): 0.5 day
- Phase 4 (Deployment): 0.5 day

**Total: 2-3 days**

**Key Changes:**
- Bridge sends JSON-RPC 2.0 requests
- Bridge parses JSON-RPC 2.0 responses
- Tests updated for new format
- Documentation updated

**No Database Changes Needed** - This is purely a protocol format change in the bridge.

**No API Changes Needed** - Agent registry stays the same.

**Breaking Change** - All agents must be updated to JSON-RPC 2.0 format before deployment.

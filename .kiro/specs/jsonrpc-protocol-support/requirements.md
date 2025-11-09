# Requirements Document: JSON-RPC 2.0 Protocol Migration

## Introduction

Migrate the workflow orchestration system from Simple A2A HTTP protocol to JSON-RPC 2.0 protocol for all agent communication. All agents will use the JSON-RPC 2.0 standard format.

## Glossary

- **System**: The workflow orchestration platform (Centralized Executor + HTTP-Kafka Bridge)
- **Agent**: An external service that performs tasks as part of a workflow
- **Bridge**: The HTTP-Kafka Bridge service that translates between Kafka messages and HTTP calls
- **JSON-RPC 2.0**: A stateless, light-weight remote procedure call (RPC) protocol
- **Message Parts**: Structured content in JSON-RPC messages (text, images, etc.)
- **Artifacts**: Output content returned by JSON-RPC agents
- **Workflow**: A sequence of steps executed by different agents

---

## Requirements

### Requirement 1: JSON-RPC Request Format

**User Story:** As the Bridge service, I want to send JSON-RPC 2.0 formatted requests to agents, so that agents receive requests in the standard format.

#### Acceptance Criteria

1. WHEN the Bridge invokes an agent, THE Bridge SHALL construct a JSON-RPC 2.0 request with `jsonrpc`, `id`, `method`, and `params` fields
2. WHEN constructing a JSON-RPC request, THE Bridge SHALL set `jsonrpc` field to "2.0"
3. WHEN constructing a JSON-RPC request, THE Bridge SHALL use the task_id as the `id` field
4. WHEN constructing a JSON-RPC request, THE Bridge SHALL set `method` field to "message/send"
5. WHEN constructing a JSON-RPC request, THE Bridge SHALL include a `params` object containing a `message` object
6. WHEN constructing the message object, THE Bridge SHALL include `role`, `messageId`, and `parts` fields
7. WHEN constructing the message object, THE Bridge SHALL set `role` to "user"
8. WHEN constructing the message object, THE Bridge SHALL set `messageId` to a unique identifier based on task_id
9. WHEN constructing message parts, THE Bridge SHALL convert task input data into an array of parts with `kind` and `text` fields
10. WHEN the input data contains text or string content, THE Bridge SHALL create parts with `kind: "text"`

### Requirement 2: JSON-RPC Response Parsing

**User Story:** As the Bridge service, I want to parse JSON-RPC 2.0 responses from agents, so that I can extract task results and return them to the executor.

#### Acceptance Criteria

1. WHEN the Bridge receives a response, THE Bridge SHALL validate it contains `jsonrpc` and `id` fields
2. WHEN the Bridge receives a response, THE Bridge SHALL validate `jsonrpc` field equals "2.0"
3. WHEN the Bridge receives a response, THE Bridge SHALL validate it contains either `result` or `error` field
4. WHEN a response contains a `result` field, THE Bridge SHALL extract the task output from the result
5. WHEN a response contains an `error` field, THE Bridge SHALL treat it as a task failure
6. WHEN extracting output from result, THE Bridge SHALL look for content in `artifacts` array
7. WHEN artifacts are present, THE Bridge SHALL extract text from `parts` where `kind == "text"`
8. WHEN extracting output from result, THE Bridge SHALL look for agent messages in `history` array
9. WHEN history contains agent messages, THE Bridge SHALL extract text from the most recent agent message
10. WHEN result contains `status.state == "completed"`, THE Bridge SHALL map it to successful task completion

### Requirement 3: Output Format Conversion

**User Story:** As the Executor, I want to receive task results in a consistent format, so that I can process results regardless of the agent protocol.

#### Acceptance Criteria

1. WHEN the Bridge parses a JSON-RPC response, THE Bridge SHALL return output in the format: `{"task_id": "...", "status": "...", "output": {...}}`
2. WHEN the task completes successfully, THE Bridge SHALL set `status` to "success"
3. WHEN the task fails, THE Bridge SHALL set `status` to "error"
4. WHEN the task completes successfully, THE Bridge SHALL include extracted output in the `output` field
5. WHEN the task fails, THE Bridge SHALL set `output` to null and include error message in `error` field
6. WHEN extracting output, THE Bridge SHALL preserve the task_id from the original request

### Requirement 4: Error Handling

**User Story:** As a system operator, I want clear error messages when JSON-RPC communication fails, so that I can diagnose and fix issues.

#### Acceptance Criteria

1. WHEN a JSON-RPC response is malformed, THE Bridge SHALL log the error with the full response body
2. WHEN a JSON-RPC response has invalid `jsonrpc` version, THE Bridge SHALL log an error and fail the task
3. WHEN a JSON-RPC response is missing both `result` and `error`, THE Bridge SHALL log an error and fail the task
4. WHEN a JSON-RPC response contains an `error` field, THE Bridge SHALL extract the error code and message
5. WHEN a JSON-RPC error occurs, THE Bridge SHALL include the error code and message in the task failure
6. WHEN output extraction fails, THE Bridge SHALL log the error with context and return the full result as output
7. WHEN the agent returns an unexpected response structure, THE Bridge SHALL log a warning and attempt to extract any available output

### Requirement 5: HTTP Communication

**User Story:** As the Bridge service, I want to send JSON-RPC requests via HTTP POST, so that agents can receive requests over standard HTTP.

#### Acceptance Criteria

1. WHEN the Bridge invokes an agent, THE Bridge SHALL use HTTP POST method
2. WHEN making HTTP requests, THE Bridge SHALL set `Content-Type` header to "application/json"
3. WHEN making HTTP requests, THE Bridge SHALL set `Accept` header to "application/json"
4. WHEN making HTTP requests, THE Bridge SHALL include the JSON-RPC request as the request body
5. WHEN making HTTP requests, THE Bridge SHALL include correlation ID in headers for tracing

### Requirement 6: Input Data Conversion

**User Story:** As the Bridge service, I want to convert task input data into JSON-RPC message parts, so that agents receive properly formatted messages.

#### Acceptance Criteria

1. WHEN task input contains a `text` field, THE Bridge SHALL use it directly as message part text
2. WHEN task input contains a `query` field, THE Bridge SHALL use it as message part text
3. WHEN task input is a dictionary without `text` or `query`, THE Bridge SHALL serialize the entire input as JSON string
4. WHEN task input is a string, THE Bridge SHALL use it directly as message part text
5. WHEN creating message parts, THE Bridge SHALL always set `kind` to "text"
6. WHEN creating message parts, THE Bridge SHALL create an array with at least one part

### Requirement 7: Logging and Observability

**User Story:** As a system operator, I want detailed logging of JSON-RPC communication, so that I can monitor and debug agent interactions.

#### Acceptance Criteria

1. WHEN the Bridge constructs a JSON-RPC request, THE Bridge SHALL log the request structure at debug level
2. WHEN the Bridge receives a JSON-RPC response, THE Bridge SHALL log the response structure at debug level
3. WHEN the Bridge successfully parses a response, THE Bridge SHALL log the extracted output at info level
4. WHEN the Bridge encounters an error, THE Bridge SHALL log the error with full context at error level
5. WHEN logging JSON-RPC communication, THE Bridge SHALL include task_id, agent name, and correlation ID

### Requirement 8: Testing

**User Story:** As a developer, I want comprehensive tests for JSON-RPC communication, so that I can be confident the protocol works correctly.

#### Acceptance Criteria

1. THE System SHALL include unit tests for JSON-RPC request construction
2. THE System SHALL include unit tests for JSON-RPC response parsing
3. THE System SHALL include unit tests for output extraction from artifacts
4. THE System SHALL include unit tests for output extraction from history
5. THE System SHALL include unit tests for JSON-RPC error handling
6. THE System SHALL include integration tests with mock JSON-RPC agents
7. THE System SHALL include end-to-end tests for complete workflow execution

### Requirement 9: Documentation

**User Story:** As a developer integrating agents, I want comprehensive documentation on the JSON-RPC 2.0 protocol, so that I can implement agents correctly.

#### Acceptance Criteria

1. THE System SHALL provide documentation for JSON-RPC 2.0 request format with examples
2. THE System SHALL provide documentation for JSON-RPC 2.0 response format with examples
3. THE System SHALL provide agent implementation examples in multiple languages (Python, Node.js, Go)
4. THE System SHALL provide curl examples for testing agents
5. THE System SHALL provide a migration guide for converting existing agents to JSON-RPC 2.0

### Requirement 10: Backward Compatibility

**User Story:** As a system administrator, I want a clear migration path from Simple A2A to JSON-RPC 2.0, so that I can update agents systematically.

#### Acceptance Criteria

1. THE System SHALL provide documentation on differences between Simple A2A and JSON-RPC 2.0
2. THE System SHALL provide code examples showing before/after for agent migration
3. THE System SHALL provide a checklist for agent developers to validate JSON-RPC compliance
4. THE System SHALL provide troubleshooting guide for common migration issues
5. THE System SHALL coordinate deployment to ensure all agents are updated before bridge deployment

---

## Non-Functional Requirements

### Performance

1. JSON-RPC request construction SHALL add less than 5ms overhead per request
2. JSON-RPC response parsing SHALL add less than 10ms overhead per response
3. The system SHALL maintain current throughput levels after migration

### Reliability

1. The Bridge SHALL handle malformed JSON-RPC responses gracefully without crashing
2. The Bridge SHALL retry failed requests according to existing retry policy
3. The Bridge SHALL log all errors with sufficient context for debugging

### Maintainability

1. JSON-RPC handling code SHALL be modular and well-documented
2. Helper functions SHALL have clear single responsibilities
3. Code SHALL include comprehensive inline comments explaining JSON-RPC structure

---

## Acceptance Criteria Summary

The JSON-RPC 2.0 migration is complete when:

- ✅ Bridge sends JSON-RPC 2.0 formatted requests
- ✅ Bridge parses JSON-RPC 2.0 formatted responses
- ✅ Output is correctly extracted from artifacts and history
- ✅ JSON-RPC errors are properly handled
- ✅ All tests pass with JSON-RPC format
- ✅ Documentation is updated
- ✅ Mock agents use JSON-RPC 2.0
- ✅ Workflows execute successfully end-to-end

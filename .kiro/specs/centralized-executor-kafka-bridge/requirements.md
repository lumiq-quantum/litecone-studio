# Requirements Document

## Introduction

This document defines the requirements for the Centralized Executor and HTTP-Kafka Bridge components of a multi-agent orchestration platform. The Centralized Executor is an ephemeral service that executes a single workflow run from start to finish, while the HTTP-Kafka Bridge (External Agent Executor) serves as the adapter between the asynchronous Kafka-based core and synchronous HTTP-based external agents. Together, these components enable deterministic, scalable execution of multi-agent workflows where all agents are treated as A2A-compliant HTTP endpoints.

## Glossary

- **Centralized Executor**: An ephemeral service instance spawned per workflow run that orchestrates the execution of workflow steps by publishing tasks to Kafka and consuming results
- **External Agent Executor**: The HTTP-Kafka Bridge service that translates between Kafka messages and HTTP calls to external agent endpoints
- **A2A Protocol**: Agent-to-Agent communication protocol over HTTP/HTTPS that defines how agents receive requests and send responses
- **Workflow Plan**: A static JSON document that defines the sequence of agent invocations and their dependencies for a workflow
- **Claim Check Pattern**: A data management pattern where large payloads are stored in S3 and only URI references are passed through the system
- **SSE**: Server-Sent Events, an HTTP streaming protocol used by agents to stream responses
- **Kafka Topic**: A named stream of events in Apache Kafka used for asynchronous communication between services
- **Run ID**: A unique identifier for a single execution instance of a workflow
- **Agent Registry**: A microservice that stores metadata about all available agents including their HTTP endpoints
- **Workflow Database**: A persistent store that maintains the runtime state and execution history of workflow runs

## Requirements

### Requirement 1

**User Story:** As a platform operator, I want the system to spawn an isolated executor for each workflow run, so that multiple workflows can execute concurrently without interference

#### Acceptance Criteria

1. WHEN a workflow run is initiated, THE Centralized Executor SHALL create a new isolated executor instance with a unique Run ID
2. THE Centralized Executor SHALL load the workflow plan JSON from the request payload
3. THE Centralized Executor SHALL validate the workflow plan structure before beginning execution
4. THE Centralized Executor SHALL terminate itself upon workflow completion or unrecoverable failure
5. WHILE multiple workflow runs are active, THE Centralized Executor SHALL ensure each executor instance operates independently without shared state

### Requirement 2

**User Story:** As a workflow designer, I want the executor to process workflow steps in the correct order based on dependencies, so that agents receive the outputs they need from previous steps

#### Acceptance Criteria

1. THE Centralized Executor SHALL parse the workflow plan to identify all steps and their dependencies
2. THE Centralized Executor SHALL execute steps sequentially when dependencies exist between them
3. WHEN a step has no pending dependencies, THE Centralized Executor SHALL mark it as ready for execution
4. THE Centralized Executor SHALL pass output references from completed steps as inputs to dependent steps
5. THE Centralized Executor SHALL support hierarchical sub-plans by recursively expanding nested agent workflows

### Requirement 3

**User Story:** As a platform operator, I want the executor to communicate asynchronously via Kafka, so that the system remains non-blocking and scalable

#### Acceptance Criteria

1. WHEN the executor needs to invoke an agent, THE Centralized Executor SHALL publish a task message to the orchestrator.tasks.http Kafka topic
2. THE Centralized Executor SHALL subscribe to the results.topic to receive agent execution results
3. THE Centralized Executor SHALL publish status updates to the workflow.monitoring.updates topic for each state change
4. THE Centralized Executor SHALL include the Run ID in all published messages for correlation
5. THE Centralized Executor SHALL process incoming result messages asynchronously without blocking on HTTP calls

### Requirement 4

**User Story:** As a workflow user, I want the system to persist execution state after each step, so that I can resume failed workflows without re-running successful steps

#### Acceptance Criteria

1. WHEN a step completes successfully, THE Centralized Executor SHALL write the step status and output Claim Check URI to the Workflow Database
2. THE Centralized Executor SHALL query the Workflow Database at startup to retrieve any existing execution state for the Run ID
3. WHEN resuming a workflow, THE Centralized Executor SHALL skip steps that are marked as completed in the Workflow Database
4. THE Centralized Executor SHALL resume execution from the first incomplete or failed step
5. THE Centralized Executor SHALL maintain execution history with timestamps for audit purposes

### Requirement 5

**User Story:** As a platform operator, I want the HTTP-Kafka Bridge to handle all external agent communication, so that the executor core remains asynchronous and decoupled

#### Acceptance Criteria

1. THE External Agent Executor SHALL subscribe to the orchestrator.tasks.http Kafka topic
2. WHEN a task message is received, THE External Agent Executor SHALL query the Agent Registry to retrieve the agent's HTTP endpoint URL
3. THE External Agent Executor SHALL construct an A2A-compliant HTTP request with the task payload
4. THE External Agent Executor SHALL make the HTTP call to the agent endpoint with appropriate authentication headers
5. THE External Agent Executor SHALL implement retry logic with exponential backoff for transient HTTP failures

### Requirement 6

**User Story:** As an agent developer, I want my streaming agent responses to be handled correctly, so that downstream agents receive complete data

#### Acceptance Criteria

1. WHEN an agent responds with SSE streaming, THE External Agent Executor SHALL process each event in the stream
2. THE External Agent Executor SHALL publish each streamed token as a micro-message to a dedicated stream topic named stream.{agent_name}
3. THE External Agent Executor SHALL include sequence numbers in stream micro-messages to ensure ordering
4. WHEN the SSE stream ends, THE External Agent Executor SHALL publish an end-of-stream marker message
5. THE External Agent Executor SHALL handle stream interruptions and publish error messages to the results topic

### Requirement 7

**User Story:** As a platform operator, I want non-streaming agent responses to be published directly, so that simple agents have minimal latency

#### Acceptance Criteria

1. WHEN an agent responds with a complete HTTP response body, THE External Agent Executor SHALL store the response payload in S3
2. THE External Agent Executor SHALL generate a Claim Check URI pointing to the S3 object
3. THE External Agent Executor SHALL publish a result message to the results.topic containing the Claim Check URI
4. THE External Agent Executor SHALL include the original task correlation ID in the result message
5. THE External Agent Executor SHALL publish the result within 100 milliseconds of receiving the complete HTTP response

### Requirement 8

**User Story:** As a workflow user, I want to see real-time status updates for each workflow step, so that I can monitor execution progress

#### Acceptance Criteria

1. WHEN a step begins execution, THE Centralized Executor SHALL publish a status update with state "RUNNING"
2. WHEN a step completes successfully, THE Centralized Executor SHALL publish a status update with state "COMPLETED"
3. WHEN a step fails, THE Centralized Executor SHALL publish a status update with state "FAILED" and error details
4. THE Centralized Executor SHALL include the step name and timestamp in all status update messages
5. THE Centralized Executor SHALL publish a final workflow status update when all steps are complete

### Requirement 9

**User Story:** As a platform operator, I want the system to handle agent failures gracefully, so that workflows can recover or fail cleanly

#### Acceptance Criteria

1. WHEN an agent returns an HTTP error status code, THE External Agent Executor SHALL publish a failure result to the results topic
2. THE External Agent Executor SHALL include the HTTP status code and error message in the failure result
3. WHEN the executor receives a failure result, THE Centralized Executor SHALL check the Agent Registry for recovery logic
4. IF recovery logic exists, THEN THE Centralized Executor SHALL execute the recovery steps
5. IF no recovery logic exists, THEN THE Centralized Executor SHALL mark the workflow as failed and terminate

### Requirement 10

**User Story:** As a platform operator, I want all Kafka messages to follow a consistent schema, so that services can reliably parse and process events

#### Acceptance Criteria

1. THE Centralized Executor SHALL publish task messages with fields: run_id, task_id, agent_name, input_claim_check, correlation_id
2. THE External Agent Executor SHALL publish result messages with fields: run_id, task_id, status, output_claim_check, correlation_id, error_message
3. THE Centralized Executor SHALL publish monitoring messages with fields: run_id, step_name, status, timestamp, metadata
4. THE External Agent Executor SHALL publish stream messages with fields: run_id, agent_name, sequence, content, is_end_of_stream
5. THE Centralized Executor SHALL validate all incoming messages against the expected schema before processing

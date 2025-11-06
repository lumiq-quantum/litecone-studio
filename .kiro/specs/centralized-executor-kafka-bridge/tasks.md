# Implementation Plan

## Core Implementation (Completed)

- [x] 1. Set up project structure and core dependencies
  - Create Python project structure with src/ directory
  - Create requirements.txt with dependencies: kafka-python, httpx, sqlalchemy, psycopg2-binary, pydantic
  - Create Docker Compose file for local Kafka and PostgreSQL
  - Create .env.example file for configuration
  - Create Dockerfiles for executor and bridge services
  - _Requirements: 1.1, 1.3_

- [x] 2. Implement database models and connection
  - [x] 2.1 Create SQLAlchemy models for WorkflowRun and StepExecution
    - Define WorkflowRun model with run_id, workflow_id, status, timestamps
    - Define StepExecution model with JSONB fields for input_data and output_data
    - Create database indexes for performance
    - _Requirements: 1.1, 4.1, 4.2_
  
  - [x] 2.2 Create database connection and session management
    - Implement database connection factory with connection pooling
    - Create async session context manager
    - Add database initialization script to create tables
    - _Requirements: 4.1, 4.2_
  
  - [x] 2.3 Implement database repository layer
    - Create WorkflowRepository with methods: create_run, update_run_status, get_run
    - Create StepRepository with methods: create_step, update_step, get_steps_by_run_id
    - Add transaction management for atomic operations
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 3. Implement workflow plan data models
  - [x] 3.1 Create Pydantic models for workflow plan structure
    - Define WorkflowStep model with id, agent_name, next_step, input_mapping
    - Define WorkflowPlan model with workflow_id, name, version, start_step, steps dict
    - Add validation for workflow plan structure
    - _Requirements: 1.2, 1.3, 2.1_
  
  - [x] 3.2 Create input mapping resolver
    - Implement variable substitution logic for ${workflow.input.field} syntax
    - Implement variable substitution logic for ${step-id.output.field} syntax
    - Add error handling for missing variables
    - _Requirements: 2.4_

- [x] 4. Implement Kafka message schemas and producers/consumers
  - [x] 4.1 Create Pydantic models for Kafka messages
    - Define AgentTask message schema
    - Define AgentResult message schema
    - Define MonitoringUpdate message schema
    - Add JSON serialization/deserialization helpers
    - _Requirements: 10.1, 10.2, 10.3, 10.5_
  
  - [x] 4.2 Create Kafka producer wrapper
    - Implement KafkaProducerClient with async publish method
    - Add message serialization to JSON
    - Add error handling and logging
    - _Requirements: 3.1, 3.4_
  
  - [x] 4.3 Create Kafka consumer wrapper
    - Implement KafkaConsumerClient with async consume method
    - Add message deserialization from JSON
    - Add correlation ID filtering
    - _Requirements: 3.2, 3.5_

- [x] 5. Implement Agent Registry client
  - [x] 5.1 Create Agent Registry HTTP client
    - Implement AgentRegistryClient with get_agent method
    - Add httpx async client with retry logic
    - Define AgentMetadata response model
    - _Requirements: 5.2_
  
  - [x] 5.2 Add agent metadata caching
    - Implement in-memory cache for agent metadata
    - Add cache TTL configuration
    - _Requirements: 5.2_

- [x] 6. Implement Centralized Executor core logic
  - [x] 6.1 Create CentralizedExecutor class initialization
    - Initialize Kafka producer and consumer
    - Initialize database connection
    - Load workflow plan from input
    - Validate workflow plan structure
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x] 6.2 Implement execution state loading for replay
    - Query database for existing step executions by run_id
    - Build execution state map from database records
    - Identify last completed step
    - _Requirements: 4.2, 4.3_
  
  - [x] 6.3 Implement main workflow execution loop
    - Start from start_step or resume from last incomplete step
    - Iterate through steps using next_step references
    - Call execute_step for each step
    - Handle workflow completion when next_step is null
    - _Requirements: 2.1, 2.2, 2.3, 4.4_
  
  - [x] 6.4 Implement single step execution logic
    - Resolve input data using input_mapping and previous outputs
    - Create step execution record in database with status RUNNING
    - Publish monitoring update with status RUNNING
    - Publish AgentTask to orchestrator.tasks.http topic
    - Wait for AgentResult from results.topic with correlation ID
    - Update step execution record with output_data and status COMPLETED/FAILED
    - Publish monitoring update with final status
    - _Requirements: 2.3, 2.4, 3.1, 3.2, 4.1, 8.1, 8.2, 8.3_
  
  - [x] 6.5 Implement error handling and recovery
    - Handle agent failure results
    - Query Agent Registry for recovery logic
    - Implement retry logic if configured
    - Mark workflow as FAILED if unrecoverable
    - _Requirements: 9.3, 9.4, 9.5_
  
  - [x] 6.6 Create executor entry point and shutdown
    - Create main() function to initialize and run executor
    - Add graceful shutdown handling
    - Close Kafka connections and database
    - _Requirements: 1.4, 1.5_

- [x] 7. Implement External Agent Executor (HTTP-Kafka Bridge)
  - [x] 7.1 Create ExternalAgentExecutor class initialization
    - Initialize Kafka consumer for orchestrator.tasks.http topic
    - Initialize Kafka producer for results.topic
    - Initialize Agent Registry client
    - Initialize httpx async client
    - _Requirements: 5.1, 5.2_
  
  - [x] 7.2 Implement task consumption loop
    - Start Kafka consumer in async loop
    - Deserialize AgentTask messages
    - Process each task asynchronously
    - Handle consumer errors and reconnection
    - _Requirements: 5.1_
  
  - [x] 7.3 Implement agent invocation logic
    - Query Agent Registry for agent URL and config
    - Construct A2A-compliant HTTP POST request
    - Add authentication headers if configured
    - Make HTTP call with timeout
    - Parse JSON response
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [x] 7.4 Implement retry logic with exponential backoff
    - Create retry_with_backoff helper function
    - Implement is_retriable_error logic for network and 5xx errors
    - Apply retry logic to HTTP calls
    - _Requirements: 5.5, 9.1, 9.2_
  
  - [x] 7.5 Implement response handling and result publishing
    - Extract output data from HTTP response
    - Create AgentResult message with status SUCCESS/FAILURE
    - Publish result to results.topic with correlation ID
    - Add error handling for malformed responses
    - _Requirements: 7.2, 7.3, 7.4, 9.1, 9.2_
  
  - [x] 7.6 Create bridge entry point
    - Create main() function to start bridge
    - Add graceful shutdown handling
    - _Requirements: 5.1_

- [x] 8. Create configuration management
  - Create Config class using pydantic-settings
  - Load configuration from environment variables
  - Add validation for required config values
  - _Requirements: 1.1_

- [x] 9. Add logging and observability
  - Configure structured JSON logging
  - Add correlation ID to all log messages
  - Log key events: step start, step complete, agent call, errors
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 10. Create Docker containers and deployment files
  - [x] 10.1 Create Dockerfile for Centralized Executor
    - Use Python 3.11 slim base image
    - Install dependencies
    - Copy source code
    - Set entry point
    - _Requirements: 1.1_
  
  - [x] 10.2 Create Dockerfile for External Agent Executor
    - Use Python 3.11 slim base image
    - Install dependencies
    - Copy source code
    - Set entry point
    - _Requirements: 5.1_
  
  - [x] 10.3 Create Docker Compose for local development
    - Add Kafka service with Zookeeper
    - Add PostgreSQL service
    - Add executor and bridge services
    - Configure networking and volumes
    - _Requirements: 1.1_

- [x] 11. Create example workflow and test agent
  - [x] 11.1 Create sample workflow JSON file
    - Define 2-step workflow with sequential execution
    - Add input_mapping examples
    - _Requirements: 2.1, 2.4_
  
  - [x] 11.2 Create mock A2A agent for testing
    - Implement simple HTTP server that accepts A2A requests
    - Return mock responses
    - Add configurable delay and error modes
    - _Requirements: 5.3, 5.4_
  
  - [x] 11.3 Create end-to-end test script
    - Start all services via Docker Compose
    - Submit workflow execution request
    - Verify workflow completes successfully
    - Check database for execution records
    - _Requirements: 1.1, 4.1, 8.5_

- [x] 12. Create README and documentation
  - [x] Write README with project overview
  - [x] Document workflow JSON format with examples
  - [x] Document A2A agent interface specification
  - [x] Add setup and running instructions
  - _Requirements: 1.2, 1.3_

## Remaining Tasks

All core implementation tasks have been completed. The system is fully functional with:
- ✅ Centralized Executor with workflow orchestration
- ✅ HTTP-Kafka Bridge for external agent communication
- ✅ Database persistence with PostgreSQL
- ✅ Kafka messaging infrastructure
- ✅ Agent Registry client with caching
- ✅ Structured logging with correlation IDs
- ✅ Docker containerization and deployment
- ✅ Mock agents and E2E testing
- ✅ Comprehensive documentation

The implementation satisfies all requirements from the requirements document.

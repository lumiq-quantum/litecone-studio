/
# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create directory structure for AI workflow generator service
  - Add Gemini API client dependencies (google-generativeai)
  - Add document processing dependencies (PyPDF2, python-docx, python-magic)
  - Add property-based testing dependencies (hypothesis)
  - Set up configuration management for API keys and endpoints
  - _Requirements: 10.1, 10.2_

- [x] 2. Implement Gemini LLM Service
  - Create base LLM service interface for provider abstraction
  - Implement Gemini API client with authentication
  - Implement prompt construction for workflow generation
  - Implement structured output parsing from Gemini responses
  - Implement exponential backoff retry logic for transient failures
  - Implement token counting and context window management
  - _Requirements: 1.1, 9.1, 10.1_

- [ ]* 2.1 Write property test for LLM retry logic
  - **Property 28: LLM calls implement exponential backoff**
  - **Validates: Requirements 9.1**

- [x] 3. Implement Agent Query Service
  - Create service to query agent registry API
  - Implement agent metadata caching with TTL
  - Implement agent capability extraction from descriptions
  - Implement agent formatting for LLM prompts
  - Implement agent matching logic for capabilities
  - _Requirements: 1.2, 4.1, 4.2_

- [ ]* 3.1 Write property test for agent registry queries
  - **Property 2: Agent registry queries occur for all descriptions**
  - **Validates: Requirements 1.2, 4.1**

- [ ]* 3.2 Write property test for agent selection
  - **Property 11: Agent selection uses metadata**
  - **Validates: Requirements 4.2**

- [x] 4. Implement workflow validation service
  - Create workflow schema validator using Pydantic
  - Implement cycle detection algorithm for workflow graphs
  - Implement reachability analysis from start_step
  - Implement agent reference validation against registry
  - Implement auto-correction logic for common validation errors
  - _Requirements: 1.4, 1.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 4.1 Write property test for workflow JSON validity
  - **Property 1: Generated workflows contain valid JSON structure**
  - **Validates: Requirements 1.3, 5.1**

- [ ]* 4.2 Write property test for agent reference validation
  - **Property 3: All agent references are valid and active**
  - **Validates: Requirements 1.4, 5.2**

- [ ]* 4.3 Write property test for cycle detection
  - **Property 13: Workflows are cycle-free**
  - **Validates: Requirements 5.3**

- [ ]* 4.4 Write property test for reachability
  - **Property 14: All steps are reachable**
  - **Validates: Requirements 5.4**

- [ ]* 4.5 Write property test for auto-correction
  - **Property 15: Validation failures trigger auto-correction**
  - **Validates: Requirements 5.5**

- [x] 5. Implement Document Processing Service
  - Create document upload handler with file validation
  - Implement PDF text extraction using PyPDF2
  - Implement DOCX text extraction using python-docx
  - Implement TXT and MD text extraction
  - Implement document chunking for large files
  - Implement error handling for unsupported formats
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 9.4_

- [ ]* 5.1 Write property test for document extraction
  - **Property 4: Document extraction works for supported formats**
  - **Validates: Requirements 2.1**

- [ ]* 5.2 Write property test for processing consistency
  - **Property 5: Document and text processing consistency**
  - **Validates: Requirements 2.2**

- [ ]* 5.3 Write property test for extraction errors
  - **Property 6: Document extraction errors include details**
  - **Validates: Requirements 2.4**

- [ ]* 5.4 Write property test for document chunking
  - **Property 30: Large documents are chunked**
  - **Validates: Requirements 9.4**

- [x] 6. Implement Workflow Generation Service
  - Create core workflow generation orchestration logic
  - Implement natural language description parsing
  - Implement workflow step identification from requirements
  - Implement agent assignment to workflow steps
  - Implement input mapping generation
  - Implement workflow JSON construction
  - _Requirements: 1.1, 1.3, 1.4, 1.5_

- [ ]* 6.1 Write property test for workflow generation
  - **Property 1: Generated workflows contain valid JSON structure**
  - **Validates: Requirements 1.3, 5.1**

- [x] 7. Implement complex workflow pattern generation
  - Implement loop structure generation from iterative descriptions
  - Implement conditional step generation from conditional logic
  - Implement parallel execution block generation
  - Implement fork-join structure generation
  - Implement nested pattern handling with correct references
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 7.1 Write property test for loop generation
  - **Property 20: Loop descriptions generate loop structures**
  - **Validates: Requirements 7.1**

- [ ]* 7.2 Write property test for conditional generation
  - **Property 21: Conditional descriptions generate conditional steps**
  - **Validates: Requirements 7.2**

- [ ]* 7.3 Write property test for parallel generation
  - **Property 22: Parallel descriptions generate parallel blocks**
  - **Validates: Requirements 7.3**

- [ ]* 7.4 Write property test for fork-join generation
  - **Property 23: Fork-join descriptions generate fork-join structures**
  - **Validates: Requirements 7.4**

- [ ]* 7.5 Write property test for nested patterns
  - **Property 24: Nested patterns generate valid structures**
  - **Validates: Requirements 7.5**

- [x] 8. Implement Chat Session Manager
  - Create session data model with conversation history
  - Implement session creation with unique IDs
  - Implement session storage and retrieval
  - Implement message addition to sessions
  - Implement workflow state tracking in sessions
  - Implement session timeout and cleanup logic
  - _Requirements: 3.1, 3.5_

- [ ]* 8.1 Write property test for session state management
  - **Property 7: Chat sessions maintain state**
  - **Validates: Requirements 3.1**

- [x] 9. Implement workflow refinement logic
  - Create workflow modification parser for user requests
  - Implement surgical workflow updates preserving unchanged parts
  - Implement change explanation generation
  - Implement clarification request handling
  - Implement workflow history tracking
  - _Requirements: 3.2, 3.3, 3.4_

- [ ]* 9.1 Write property test for modification preservation
  - **Property 8: Workflow modifications preserve unchanged portions**
  - **Validates: Requirements 3.2**

- [ ]* 9.2 Write property test for modification explanations
  - **Property 9: Modifications include explanations**
  - **Validates: Requirements 3.3**

- [ ]* 9.3 Write property test for clarification responses
  - **Property 10: Clarification requests receive explanations**
  - **Validates: Requirements 3.4**

- [x] 10. Implement workflow save functionality
  - Create workflow API client for workflow creation
  - Implement unique name generation logic
  - Implement name conflict resolution
  - Implement workflow creation with error handling
  - Implement workflow ID and link generation
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 10.1 Write property test for workflow creation
  - **Property 16: Approved workflows are created via API**
  - **Validates: Requirements 6.1**

- [ ]* 10.2 Write property test for unique names
  - **Property 17: Workflow names are unique**
  - **Validates: Requirements 6.2**

- [ ]* 10.3 Write property test for creation success response
  - **Property 18: Successful creation returns workflow ID**
  - **Validates: Requirements 6.4**

- [ ]* 10.4 Write property test for creation failure handling
  - **Property 19: Creation failures allow retry**
  - **Validates: Requirements 6.5**

- [x] 11. Implement API endpoints
  - Create FastAPI router for AI workflow generator
  - Implement POST /api/v1/ai-workflows/generate endpoint
  - Implement POST /api/v1/ai-workflows/upload endpoint
  - Implement POST /api/v1/ai-workflows/chat/sessions endpoint
  - Implement POST /api/v1/ai-workflows/chat/sessions/{session_id}/messages endpoint
  - Implement GET /api/v1/ai-workflows/chat/sessions/{session_id} endpoint
  - Implement DELETE /api/v1/ai-workflows/chat/sessions/{session_id} endpoint
  - Implement POST /api/v1/ai-workflows/chat/sessions/{session_id}/save endpoint
  - Implement GET /api/v1/ai-workflows/chat/sessions/{session_id}/export endpoint
  - _Requirements: 1.1, 2.1, 3.1, 6.1, 8.1, 8.3_

- [ ]* 11.1 Write property test for JSON view endpoint
  - **Property 25: JSON view requests return formatted JSON**
  - **Validates: Requirements 8.1**

- [ ]* 11.2 Write property test for download endpoint
  - **Property 26: Download requests provide JSON files**
  - **Validates: Requirements 8.3**

- [ ]* 11.3 Write property test for JSON annotations
  - **Property 27: Displayed JSON includes annotations**
  - **Validates: Requirements 8.5**

- [x] 12. Implement request schemas and validation
  - Create Pydantic schemas for workflow generation requests
  - Create schemas for document upload requests
  - Create schemas for chat message requests
  - Create schemas for workflow save requests
  - Implement request validation with clear error messages
  - _Requirements: 1.1, 2.1, 3.1, 6.1_

- [x] 13. Implement rate limiting and throttling
  - Create rate limiter middleware for API endpoints
  - Implement per-session request throttling
  - Implement request queuing for rate-limited scenarios
  - Implement user feedback for rate limit delays
  - _Requirements: 9.2, 9.3_

- [ ]* 13.1 Write property test for session throttling
  - **Property 29: Excessive requests trigger throttling**
  - **Validates: Requirements 9.3**

- [x] 14. Implement error handling and logging
  - Create error response models with suggestions
  - Implement structured logging for all operations
  - Implement error categorization and handling strategies
  - Implement LLM prompt/response logging (sanitized)
  - Implement performance metrics logging
  - _Requirements: 2.3, 2.4, 6.5_

- [x] 15. Implement agent suggestion features
  - Create agent suggestion logic for ambiguous cases
  - Implement agent description inclusion in suggestions
  - Implement multi-agent choice presentation
  - Implement no-match scenario handling with alternatives
  - _Requirements: 4.3, 4.4, 4.5_

- [ ]* 15.1 Write property test for agent descriptions
  - **Property 12: Agent suggestions include descriptions**
  - **Validates: Requirements 4.4**

- [x] 16. Implement schema-driven validation
  - Create workflow schema loader from JSON schema files
  - Implement dynamic validation based on loaded schema
  - Implement schema version detection and handling
  - Implement schema evolution support
  - _Requirements: 10.3_

- [ ]* 16.1 Write property test for schema evolution
  - **Property 31: Schema evolution is handled automatically**
  - **Validates: Requirements 10.3**

- [x] 17. Add configuration and environment setup
  - Create configuration file for Gemini API settings
  - Add environment variable validation on startup
  - Create configuration for rate limits and timeouts
  - Add configuration for document size limits
  - Create configuration for session timeout settings
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 18. Integrate with existing API infrastructure
  - Add AI workflow generator routes to main API application
  - Configure database models for session storage
  - Add database migrations for session tables
  - Configure middleware for authentication and logging
  - Add health check endpoint for AI service
  - _Requirements: 3.1, 6.1_

- [x] 19. Create example prompts and templates
  - Create example workflow descriptions for testing
  - Create prompt templates for different workflow patterns
  - Create agent description formatting templates
  - Create error message templates
  - Create explanation templates for workflow changes
  - _Requirements: 1.1, 3.3, 4.4_

- [x] 20. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 21. Write integration tests
  - Test full workflow generation flow from description to saved workflow
  - Test document upload and processing flow
  - Test multi-turn chat session with refinement
  - Test error handling and recovery scenarios
  - Test rate limiting and throttling behavior
  - _Requirements: 1.1, 2.1, 3.1, 6.1, 9.2, 9.3_

- [x] 22. Create API documentation
  - Document all API endpoints with OpenAPI/Swagger
  - Create usage examples for each endpoint
  - Document request/response schemas
  - Create troubleshooting guide for common errors
  - Document rate limits and quotas
  - _Requirements: 1.1, 2.1, 3.1, 6.1_

- [ ] 23. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

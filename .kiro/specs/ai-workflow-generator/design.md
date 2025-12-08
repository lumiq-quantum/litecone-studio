# Design Document

## Overview

The AI Workflow Generator is a service that enables users to create complex workflow JSON definitions through natural language interactions. The system leverages Google's Gemini LLM to understand user requirements, query the agent registry for available capabilities, and generate valid workflow definitions that conform to the system's schema. The service provides both a REST API for programmatic access and supports interactive chat sessions for iterative workflow refinement.

### Key Design Goals

1. **Simplicity**: Enable non-technical users to create workflows without JSON knowledge
2. **Intelligence**: Leverage Gemini's capabilities for natural language understanding and structured output generation
3. **Validation**: Ensure all generated workflows are valid and executable
4. **Interactivity**: Support conversational refinement through stateful chat sessions
5. **Integration**: Seamlessly integrate with existing workflow and agent management APIs

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   UI / Client   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     AI Workflow Generator API           │
│  ┌─────────────────────────────────┐   │
│  │  Chat Session Manager           │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Workflow Generation Service    │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Document Processing Service    │   │
│  └─────────────────────────────────┘   │
└──────┬──────────────┬─────────────┬────┘
       │              │             │
       ▼              ▼             ▼
┌─────────────┐ ┌──────────┐ ┌──────────────┐
│   Gemini    │ │  Agent   │ │   Workflow   │
│     API     │ │ Registry │ │     API      │
└─────────────┘ └──────────┘ └──────────────┘
```

### Service Layer Architecture

The AI Workflow Generator follows a layered architecture:

1. **API Layer**: FastAPI endpoints for HTTP requests
2. **Service Layer**: Business logic for workflow generation, chat management, and document processing
3. **LLM Integration Layer**: Abstraction over Gemini API with retry logic and error handling
4. **Data Layer**: Session storage, workflow templates, and agent metadata caching

## Components and Interfaces

### 1. AI Workflow Generator API

**Endpoints:**

```python
POST   /api/v1/ai-workflows/generate
POST   /api/v1/ai-workflows/upload
POST   /api/v1/ai-workflows/chat/sessions
POST   /api/v1/ai-workflows/chat/sessions/{session_id}/messages
GET    /api/v1/ai-workflows/chat/sessions/{session_id}
DELETE /api/v1/ai-workflows/chat/sessions/{session_id}
POST   /api/v1/ai-workflows/chat/sessions/{session_id}/save
GET    /api/v1/ai-workflows/chat/sessions/{session_id}/export
```

### 2. Workflow Generation Service

**Responsibilities:**
- Orchestrate workflow generation from natural language
- Query agent registry for available agents
- Generate workflow JSON using Gemini
- Validate generated workflows
- Create workflows via workflow API

**Interface:**

```python
class WorkflowGenerationService:
    async def generate_from_text(
        self,
        description: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> WorkflowGenerationResult
    
    async def generate_from_document(
        self,
        document_content: str,
        document_type: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> WorkflowGenerationResult
    
    async def refine_workflow(
        self,
        current_workflow: Dict[str, Any],
        modification_request: str,
        conversation_history: List[Message]
    ) -> WorkflowGenerationResult
    
    async def validate_workflow(
        self,
        workflow_json: Dict[str, Any]
    ) -> ValidationResult
    
    async def save_workflow(
        self,
        workflow_json: Dict[str, Any],
        name: str,
        description: Optional[str] = None
    ) -> UUID
```

### 3. Gemini LLM Service

**Responsibilities:**
- Interface with Google Gemini API
- Handle structured output generation
- Implement retry logic and error handling
- Manage token limits and context windows

**Interface:**

```python
class GeminiService:
    async def generate_workflow(
        self,
        prompt: str,
        available_agents: List[AgentMetadata],
        conversation_history: Optional[List[Message]] = None
    ) -> GeminiResponse
    
    async def chat(
        self,
        message: str,
        conversation_history: List[Message],
        current_workflow: Optional[Dict[str, Any]] = None
    ) -> GeminiResponse
    
    async def explain_workflow(
        self,
        workflow_json: Dict[str, Any]
    ) -> str
```

### 4. Chat Session Manager

**Responsibilities:**
- Manage stateful chat sessions
- Store conversation history
- Track workflow evolution
- Handle session timeouts and cleanup

**Interface:**

```python
class ChatSessionManager:
    async def create_session(
        self,
        initial_description: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ChatSession
    
    async def get_session(
        self,
        session_id: UUID
    ) -> Optional[ChatSession]
    
    async def add_message(
        self,
        session_id: UUID,
        message: Message
    ) -> ChatSession
    
    async def update_workflow(
        self,
        session_id: UUID,
        workflow_json: Dict[str, Any]
    ) -> ChatSession
    
    async def delete_session(
        self,
        session_id: UUID
    ) -> None
```

### 5. Document Processing Service

**Responsibilities:**
- Extract text from various document formats
- Handle file uploads and validation
- Chunk large documents for LLM processing

**Interface:**

```python
class DocumentProcessingService:
    async def extract_text(
        self,
        file_content: bytes,
        file_type: str
    ) -> str
    
    def validate_file(
        self,
        file_size: int,
        file_type: str
    ) -> ValidationResult
    
    def chunk_text(
        self,
        text: str,
        max_tokens: int = 8000
    ) -> List[str]
```

### 6. Agent Query Service

**Responsibilities:**
- Query agent registry for available agents
- Cache agent metadata for performance
- Match agents to required capabilities

**Interface:**

```python
class AgentQueryService:
    async def get_all_agents(
        self,
        status: str = "active"
    ) -> List[AgentMetadata]
    
    async def find_agents_by_capability(
        self,
        capability_description: str
    ) -> List[AgentMetadata]
    
    async def get_agent_details(
        self,
        agent_name: str
    ) -> Optional[AgentMetadata]
    
    def format_agents_for_llm(
        self,
        agents: List[AgentMetadata]
    ) -> str
```

## Data Models

### ChatSession

```python
class ChatSession(BaseModel):
    id: UUID
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    status: str  # active, completed, expired
    messages: List[Message]
    current_workflow: Optional[Dict[str, Any]]
    workflow_history: List[Dict[str, Any]]
```

### Message

```python
class Message(BaseModel):
    id: UUID
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]
```

### WorkflowGenerationResult

```python
class WorkflowGenerationResult(BaseModel):
    success: bool
    workflow_json: Optional[Dict[str, Any]]
    explanation: str
    validation_errors: List[str]
    suggestions: List[str]
    agents_used: List[str]
```

### GeminiResponse

```python
class GeminiResponse(BaseModel):
    content: str
    workflow_json: Optional[Dict[str, Any]]
    finish_reason: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
```

### AgentMetadata

```python
class AgentMetadata(BaseModel):
    name: str
    description: Optional[str]
    url: str
    capabilities: List[str]  # Extracted from description
    status: str
```

## C
orrectness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

After analyzing the acceptance criteria, I've identified properties that can be eliminated due to redundancy:

**Redundancy Analysis:**
- Property 5.2 (agent reference validation) is redundant with Property 1.4 - both verify that generated workflows only reference existing active agents
- These can be combined into a single comprehensive property

**Property 1: Generated workflows contain valid JSON structure**
*For any* natural language description or document input, the generated workflow output should be valid JSON that conforms to the workflow schema
**Validates: Requirements 1.3, 5.1**

**Property 2: Agent registry queries occur for all descriptions**
*For any* workflow generation request, the system should query the agent registry to identify available agents before generating the workflow
**Validates: Requirements 1.2, 4.1**

**Property 3: All agent references are valid and active**
*For any* generated workflow JSON, all agent names referenced in steps should exist in the agent registry with active status
**Validates: Requirements 1.4, 5.2**

**Property 4: Document extraction works for supported formats**
*For any* document in a supported format (PDF, DOCX, TXT, MD), the extraction process should successfully return text content
**Validates: Requirements 2.1**

**Property 5: Document and text processing consistency**
*For any* content, processing it as a text description or as an extracted document should produce equivalent workflow structures
**Validates: Requirements 2.2**

**Property 6: Document extraction errors include details**
*For any* failed document extraction, the error response should contain specific details about the failure cause
**Validates: Requirements 2.4**

**Property 7: Chat sessions maintain state**
*For any* chat session, adding messages and updating workflows should preserve the complete conversation history and workflow evolution
**Validates: Requirements 3.1**

**Property 8: Workflow modifications preserve unchanged portions**
*For any* workflow modification request, the parts of the workflow not mentioned in the request should remain identical to the previous version
**Validates: Requirements 3.2**

**Property 9: Modifications include explanations**
*For any* workflow modification, the response should include an explanation of what changed and why
**Validates: Requirements 3.3**

**Property 10: Clarification requests receive explanations**
*For any* user clarification request, the system should provide explanations about the requested aspect (structure, agents, or decisions)
**Validates: Requirements 3.4**

**Property 11: Agent selection uses metadata**
*For any* scenario with multiple matching agents, the selection should be based on agent metadata and descriptions
**Validates: Requirements 4.2**

**Property 12: Agent suggestions include descriptions**
*For any* agent suggestion, the response should include the agent's description and capabilities
**Validates: Requirements 4.4**

**Property 13: Workflows are cycle-free**
*For any* generated workflow, the step graph should contain no circular references
**Validates: Requirements 5.3**

**Property 14: All steps are reachable**
*For any* generated workflow, all defined steps should be reachable from the start_step
**Validates: Requirements 5.4**

**Property 15: Validation failures trigger auto-correction**
*For any* workflow with validation errors, the system should automatically correct the issues and explain the corrections
**Validates: Requirements 5.5**

**Property 16: Approved workflows are created via API**
*For any* user-approved workflow, the system should create the workflow definition through the workflow API
**Validates: Requirements 6.1**

**Property 17: Workflow names are unique**
*For any* workflow creation, the assigned name should be unique or include version information to avoid conflicts
**Validates: Requirements 6.2**

**Property 18: Successful creation returns workflow ID**
*For any* successful workflow creation, the response should include the workflow ID and access information
**Validates: Requirements 6.4**

**Property 19: Creation failures allow retry**
*For any* failed workflow creation, the error should be reported and the user should be able to modify and retry
**Validates: Requirements 6.5**

**Property 20: Loop descriptions generate loop structures**
*For any* description containing iterative processing requirements, the generated workflow should include loop structures with valid collection references
**Validates: Requirements 7.1**

**Property 21: Conditional descriptions generate conditional steps**
*For any* description containing conditional logic, the generated workflow should include conditional steps with valid expressions
**Validates: Requirements 7.2**

**Property 22: Parallel descriptions generate parallel blocks**
*For any* description containing parallel processing requirements, the generated workflow should include parallel execution blocks
**Validates: Requirements 7.3**

**Property 23: Fork-join descriptions generate fork-join structures**
*For any* description containing fork-join patterns, the generated workflow should include fork-join structures with correct branch definitions
**Validates: Requirements 7.4**

**Property 24: Nested patterns generate valid structures**
*For any* description with nested workflow patterns, the generated workflow should have valid nested structures with correct step references
**Validates: Requirements 7.5**

**Property 25: JSON view requests return formatted JSON**
*For any* request to view workflow JSON, the response should include the complete workflow definition in formatted JSON
**Validates: Requirements 8.1**

**Property 26: Download requests provide JSON files**
*For any* download request, the system should provide the workflow JSON as a downloadable file
**Validates: Requirements 8.3**

**Property 27: Displayed JSON includes annotations**
*For any* workflow JSON display, the output should include comments or annotations explaining key sections
**Validates: Requirements 8.5**

**Property 28: LLM calls implement exponential backoff**
*For any* transient LLM service failure, the system should retry with exponential backoff delays
**Validates: Requirements 9.1**

**Property 29: Excessive requests trigger throttling**
*For any* chat session generating excessive LLM calls, the system should implement request throttling
**Validates: Requirements 9.3**

**Property 30: Large documents are chunked**
*For any* document exceeding token limits, the system should chunk the content before processing
**Validates: Requirements 9.4**

**Property 31: Schema evolution is handled automatically**
*For any* workflow schema change, the validation logic should automatically adapt without code changes
**Validates: Requirements 10.3**

## Error Handling

### Error Categories

1. **User Input Errors**
   - Invalid document formats
   - Malformed natural language descriptions
   - Ambiguous requirements
   - **Handling**: Return clear error messages with suggestions for correction

2. **LLM Service Errors**
   - Rate limiting (429)
   - Service unavailable (503)
   - Timeout errors
   - Invalid responses
   - **Handling**: Implement exponential backoff retry, queue requests, provide user feedback

3. **Validation Errors**
   - Invalid workflow structure
   - Missing agent references
   - Circular dependencies
   - Unreachable steps
   - **Handling**: Auto-correct when possible, explain corrections, allow user override

4. **Integration Errors**
   - Agent registry unavailable
   - Workflow API failures
   - Database connection issues
   - **Handling**: Retry with backoff, cache agent data, provide degraded functionality

5. **Resource Errors**
   - Token limit exceeded
   - Session timeout
   - Memory constraints
   - **Handling**: Chunk content, save session state, implement cleanup

### Error Response Format

```python
class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]]
    suggestions: List[str]
    recoverable: bool
```

### Retry Strategy

```python
class RetryConfig:
    max_retries: int = 3
    initial_delay_ms: int = 1000
    max_delay_ms: int = 30000
    backoff_multiplier: float = 2.0
    retriable_errors: List[str] = [
        "rate_limit_exceeded",
        "service_unavailable",
        "timeout",
        "connection_error"
    ]
```

## Testing Strategy

### Unit Testing

Unit tests will verify individual components in isolation:

1. **Document Processing Tests**
   - Test text extraction from each supported format
   - Test file validation logic
   - Test chunking algorithm

2. **Gemini Service Tests**
   - Test prompt construction
   - Test response parsing
   - Test error handling with mocked responses

3. **Validation Tests**
   - Test workflow schema validation
   - Test cycle detection
   - Test reachability analysis

4. **Session Management Tests**
   - Test session creation and retrieval
   - Test message addition
   - Test session expiration

### Property-Based Testing

Property-based tests will verify universal properties across many inputs using the **Hypothesis** library for Python:

**Configuration**: Each property-based test will run a minimum of 100 iterations to ensure comprehensive coverage.

**Tagging**: Each property-based test will include a comment explicitly referencing the correctness property from this design document using the format: `# Feature: ai-workflow-generator, Property {number}: {property_text}`

**Key Properties to Test:**

1. **Workflow Validity Property** (Property 1)
   - Generate random natural language descriptions
   - Verify all outputs are valid JSON conforming to workflow schema
   - Tag: `# Feature: ai-workflow-generator, Property 1: Generated workflows contain valid JSON structure`

2. **Agent Reference Validity Property** (Property 3)
   - Generate workflows with various agent references
   - Verify all referenced agents exist and are active
   - Tag: `# Feature: ai-workflow-generator, Property 3: All agent references are valid and active`

3. **Modification Preservation Property** (Property 8)
   - Generate random workflows and modification requests
   - Verify unchanged portions remain identical
   - Tag: `# Feature: ai-workflow-generator, Property 8: Workflow modifications preserve unchanged portions`

4. **Cycle Detection Property** (Property 13)
   - Generate various workflow structures
   - Verify no circular references exist
   - Tag: `# Feature: ai-workflow-generator, Property 13: Workflows are cycle-free`

5. **Reachability Property** (Property 14)
   - Generate workflows with various step configurations
   - Verify all steps are reachable from start_step
   - Tag: `# Feature: ai-workflow-generator, Property 14: All steps are reachable`

6. **Pattern Generation Properties** (Properties 20-24)
   - Generate descriptions with various workflow patterns
   - Verify correct pattern structures are generated
   - Tag each with corresponding property number

### Integration Testing

Integration tests will verify end-to-end functionality:

1. **Full Generation Flow**
   - Test complete workflow generation from description to saved workflow
   - Verify integration with agent registry and workflow API

2. **Chat Session Flow**
   - Test multi-turn conversations with workflow refinement
   - Verify session state persistence

3. **Document Upload Flow**
   - Test document upload, extraction, and workflow generation
   - Verify handling of various document formats

### Test Data Strategy

1. **Synthetic Test Data**
   - Generate varied natural language descriptions
   - Create test documents in all supported formats
   - Build diverse agent registry fixtures

2. **Real-World Examples**
   - Use actual workflow examples from the system
   - Test with real agent configurations
   - Validate against production-like scenarios

## Deployment Considerations

### Environment Variables

```bash
# Gemini API Configuration
GEMINI_API_KEY=<api-key>
GEMINI_MODEL=gemini-1.5-pro
GEMINI_MAX_TOKENS=8192
GEMINI_TEMPERATURE=0.7

# Service Configuration
AI_WORKFLOW_API_PORT=8000
SESSION_TIMEOUT_MINUTES=30
MAX_DOCUMENT_SIZE_MB=10
AGENT_CACHE_TTL_SECONDS=300

# Integration Endpoints
AGENT_REGISTRY_URL=http://api:8080/api/v1/agents
WORKFLOW_API_URL=http://api:8080/api/v1/workflows

# Rate Limiting
MAX_REQUESTS_PER_SESSION=50
RATE_LIMIT_WINDOW_SECONDS=60
```

### Scaling Considerations

1. **Stateless API Design**: API endpoints are stateless; session state stored in database
2. **Horizontal Scaling**: Multiple API instances can run behind a load balancer
3. **Caching**: Agent metadata cached to reduce registry queries
4. **Async Processing**: Long-running LLM calls handled asynchronously

### Monitoring and Observability

1. **Metrics to Track**
   - Workflow generation success rate
   - LLM API latency and error rates
   - Session creation and completion rates
   - Document processing success rates

2. **Logging**
   - Structured logging for all API requests
   - LLM prompt and response logging (sanitized)
   - Error tracking with stack traces
   - Performance metrics for slow operations

3. **Alerts**
   - High LLM error rate
   - Session timeout rate exceeds threshold
   - Workflow validation failure rate spikes
   - Agent registry unavailable

## Security Considerations

1. **API Key Management**
   - Store Gemini API key in secure environment variables
   - Rotate keys regularly
   - Monitor API usage for anomalies

2. **Input Validation**
   - Sanitize all user inputs
   - Validate file uploads for malicious content
   - Limit document sizes to prevent DoS

3. **Rate Limiting**
   - Implement per-user rate limits
   - Throttle excessive LLM requests
   - Prevent session abuse

4. **Data Privacy**
   - Don't log sensitive user data
   - Sanitize LLM prompts and responses in logs
   - Implement session data cleanup

## Future Enhancements

1. **Multi-Model Support**: Add support for other LLM providers (OpenAI, Anthropic)
2. **Workflow Templates**: Pre-built templates for common use cases
3. **Visual Workflow Editor**: Drag-and-drop interface for workflow refinement
4. **Workflow Testing**: Generate test cases for workflows
5. **Workflow Optimization**: Suggest performance improvements
6. **Collaborative Editing**: Multi-user workflow creation sessions
7. **Version Control**: Track workflow evolution with git-like versioning
8. **Workflow Marketplace**: Share and discover workflows created by others

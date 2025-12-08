# AI Workflow Generator API Documentation

## Overview

The AI Workflow Generator API enables users to create complex workflow JSON definitions through natural language descriptions or document uploads. The system leverages Google's Gemini LLM to understand user requirements, query the agent registry for available capabilities, and generate valid workflow definitions.

## Base URL

```
http://localhost:8000/api/v1/ai-workflows
```

## Authentication

Currently, authentication is not enforced. This will be added in a future release.

## Rate Limits

- **Per Session**: 50 requests per 60-second window
- **Document Upload**: Maximum 10MB file size
- **Text Description**: Maximum 10,000 characters
- **Chat Message**: Maximum 5,000 characters

When rate limits are exceeded, the API will return a `429 Too Many Requests` response with a `Retry-After` header indicating when to retry.

## Common Response Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 400  | Bad Request - Invalid input data |
| 404  | Not Found - Resource does not exist |
| 422  | Unprocessable Entity - Validation failed |
| 429  | Too Many Requests - Rate limit exceeded |
| 500  | Internal Server Error |
| 503  | Service Unavailable - LLM service unavailable |

## Error Response Format

All error responses follow this structure:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "errors": [
      {
        "field": "description",
        "message": "Description must contain at least 3 words",
        "type": "value_error"
      }
    ]
  },
  "suggestions": [
    "Field 'description': Description must contain at least 3 words to be meaningful"
  ],
  "recoverable": true
}
```


---

## Endpoints

### 1. Generate Workflow from Text

Generate a workflow JSON from a natural language description.

**Endpoint:** `POST /api/v1/ai-workflows/generate`

**Requirements:** 1.1, 2.1, 3.1, 6.1

**Request Body:**

```json
{
  "description": "Create a workflow that processes documents, validates them, and stores the results",
  "user_preferences": {
    "prefer_parallel": true,
    "max_steps": 10
  }
}
```

**Request Schema:**

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| description | string | Yes | Natural language workflow description | 10-10,000 characters, min 3 words |
| user_preferences | object | No | Optional generation preferences | - |

**Response (200 OK):**

```json
{
  "success": true,
  "workflow_json": {
    "name": "document-processing-workflow",
    "description": "Processes documents, validates them, and stores results",
    "start_step": "step_1",
    "steps": [
      {
        "id": "step_1",
        "name": "Process Document",
        "agent_name": "document-processor",
        "agent_url": "http://document-processor:8080",
        "input_mapping": {
          "document": "{{workflow.input.document}}"
        },
        "next_step": "step_2"
      },
      {
        "id": "step_2",
        "name": "Validate Results",
        "agent_name": "validator",
        "agent_url": "http://validator:8080",
        "input_mapping": {
          "data": "{{step_1.output.processed_data}}"
        },
        "next_step": "step_3"
      },
      {
        "id": "step_3",
        "name": "Store Results",
        "agent_name": "storage-agent",
        "agent_url": "http://storage:8080",
        "input_mapping": {
          "validated_data": "{{step_2.output.validated_data}}"
        }
      }
    ]
  },
  "explanation": "I've created a workflow with three sequential steps: document processing, validation, and storage. Each step uses an appropriate agent from your registry.",
  "validation_errors": [],
  "suggestions": [
    "Consider adding error handling steps",
    "You might want to add a notification step at the end"
  ],
  "agents_used": [
    "document-processor",
    "validator",
    "storage-agent"
  ]
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Whether generation was successful |
| workflow_json | object | Generated workflow JSON (null if failed) |
| explanation | string | Explanation of the generated workflow |
| validation_errors | array | List of validation errors |
| suggestions | array | Suggestions for improvement |
| agents_used | array | List of agent names used in workflow |

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a workflow that processes documents, validates them, and stores the results"
  }'
```

**Example Python:**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/ai-workflows/generate",
    json={
        "description": "Create a workflow that processes documents, validates them, and stores the results"
    }
)

result = response.json()
if result["success"]:
    print(f"Generated workflow: {result['workflow_json']['name']}")
    print(f"Explanation: {result['explanation']}")
else:
    print(f"Errors: {result['validation_errors']}")
```


---

### 2. Upload Document for Workflow Generation

Upload a document (PDF, DOCX, TXT, MD) and generate a workflow from its content.

**Endpoint:** `POST /api/v1/ai-workflows/upload`

**Requirements:** 2.1, 2.2, 2.3, 2.4, 2.5

**Request:**

- **Content-Type:** `multipart/form-data`
- **file:** File upload (required)

**Supported Formats:**
- PDF (.pdf)
- Microsoft Word (.docx, .doc)
- Plain Text (.txt)
- Markdown (.md)

**Maximum File Size:** 10MB

**Response (200 OK):**

```json
{
  "success": true,
  "workflow_json": {
    "name": "requirements-based-workflow",
    "description": "Workflow generated from uploaded requirements document",
    "start_step": "step_1",
    "steps": [...]
  },
  "explanation": "I've analyzed your requirements document and created a workflow with 5 steps covering data ingestion, processing, validation, transformation, and storage.",
  "validation_errors": [],
  "suggestions": [],
  "agents_used": ["data-ingestion", "processor", "validator", "transformer", "storage"]
}
```

**Error Response (400 Bad Request):**

```json
{
  "detail": "Unsupported file type 'xlsx'. Supported formats: pdf, docx, doc, txt, md"
}
```

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/upload \
  -F "file=@requirements.pdf"
```

**Example Python:**

```python
import requests

with open("requirements.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/ai-workflows/upload",
        files={"file": f}
    )

result = response.json()
print(f"Generated workflow from document: {result['workflow_json']['name']}")
```

**Example JavaScript:**

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/v1/ai-workflows/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Generated workflow:', result.workflow_json.name);
```


---

### 3. Create Chat Session

Create a new chat session for interactive workflow refinement.

**Endpoint:** `POST /api/v1/ai-workflows/chat/sessions`

**Requirements:** 3.1

**Request Body:**

```json
{
  "initial_description": "I need a workflow for customer onboarding",
  "user_id": "user-123"
}
```

**Request Schema:**

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| initial_description | string | No | Optional initial workflow description | Max 10,000 characters, min 3 words if provided |
| user_id | string | No | Optional user identifier | Alphanumeric, hyphens, underscores only |

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-15T11:00:00Z",
  "messages": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "role": "system",
      "content": "Chat session created. How can I help you create a workflow?",
      "timestamp": "2024-01-15T10:30:00Z",
      "metadata": null
    }
  ],
  "current_workflow": null,
  "workflow_history": []
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Session identifier |
| user_id | string | User identifier (if provided) |
| status | string | Session status (active, completed, expired) |
| created_at | datetime | Session creation timestamp |
| updated_at | datetime | Last update timestamp |
| expires_at | datetime | Session expiration timestamp (30 minutes default) |
| messages | array | Conversation messages |
| current_workflow | object | Current workflow JSON (null if none) |
| workflow_history | array | Previous workflow versions |

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "initial_description": "I need a workflow for customer onboarding",
    "user_id": "user-123"
  }'
```

**Example Python:**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/ai-workflows/chat/sessions",
    json={
        "initial_description": "I need a workflow for customer onboarding",
        "user_id": "user-123"
    }
)

session = response.json()
session_id = session["id"]
print(f"Created session: {session_id}")
print(f"Expires at: {session['expires_at']}")
```


---

### 4. Send Chat Message

Send a message to refine the workflow in a chat session.

**Endpoint:** `POST /api/v1/ai-workflows/chat/sessions/{session_id}/messages`

**Requirements:** 3.2, 3.3, 3.4

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | UUID | Chat session identifier |

**Request Body:**

```json
{
  "message": "Add a validation step before processing"
}
```

**Request Schema:**

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| message | string | Yes | User message | 1-5,000 characters, cannot be only whitespace |

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:32:00Z",
  "expires_at": "2024-01-15T11:00:00Z",
  "messages": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "role": "user",
      "content": "Add a validation step before processing",
      "timestamp": "2024-01-15T10:32:00Z",
      "metadata": null
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "role": "assistant",
      "content": "I've added a validation step before the processing step. The validator agent will check the input data before it's processed.",
      "timestamp": "2024-01-15T10:32:05Z",
      "metadata": {
        "success": true,
        "validation_errors": [],
        "suggestions": [],
        "agents_used": ["validator"]
      }
    }
  ],
  "current_workflow": {
    "name": "customer-onboarding-workflow",
    "steps": [...]
  },
  "workflow_history": [...]
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Chat session 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Error Response (400 Bad Request):**

```json
{
  "detail": "Chat session has expired"
}
```

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/chat/sessions/550e8400-e29b-41d4-a716-446655440000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add a validation step before processing"
  }'
```

**Example Python:**

```python
import requests

session_id = "550e8400-e29b-41d4-a716-446655440000"

response = requests.post(
    f"http://localhost:8000/api/v1/ai-workflows/chat/sessions/{session_id}/messages",
    json={"message": "Add a validation step before processing"}
)

session = response.json()
latest_message = session["messages"][-1]
print(f"Assistant: {latest_message['content']}")
print(f"Current workflow has {len(session['current_workflow']['steps'])} steps")
```

**Common Message Types:**

1. **Initial workflow creation:**
   ```json
   {"message": "Create a workflow for processing customer orders"}
   ```

2. **Modification requests:**
   ```json
   {"message": "Add error handling after the payment step"}
   ```

3. **Clarification questions:**
   ```json
   {"message": "What does the validation step do?"}
   ```

4. **Pattern requests:**
   ```json
   {"message": "Make the processing steps run in parallel"}
   ```


---

### 5. Get Chat Session

Retrieve a chat session with its messages and workflow state.

**Endpoint:** `GET /api/v1/ai-workflows/chat/sessions/{session_id}`

**Requirements:** 3.1

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | UUID | Chat session identifier |

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "expires_at": "2024-01-15T11:00:00Z",
  "messages": [...],
  "current_workflow": {...},
  "workflow_history": [...]
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Chat session 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Example cURL:**

```bash
curl -X GET http://localhost:8000/api/v1/ai-workflows/chat/sessions/550e8400-e29b-41d4-a716-446655440000
```

**Example Python:**

```python
import requests

session_id = "550e8400-e29b-41d4-a716-446655440000"

response = requests.get(
    f"http://localhost:8000/api/v1/ai-workflows/chat/sessions/{session_id}"
)

session = response.json()
print(f"Session status: {session['status']}")
print(f"Messages: {len(session['messages'])}")
print(f"Has workflow: {session['current_workflow'] is not None}")
```

---

### 6. Delete Chat Session

Delete a chat session and its data.

**Endpoint:** `DELETE /api/v1/ai-workflows/chat/sessions/{session_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | UUID | Chat session identifier |

**Response (200 OK):**

```json
{
  "message": "Chat session 550e8400-e29b-41d4-a716-446655440000 deleted successfully",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Chat session 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Example cURL:**

```bash
curl -X DELETE http://localhost:8000/api/v1/ai-workflows/chat/sessions/550e8400-e29b-41d4-a716-446655440000
```

**Example Python:**

```python
import requests

session_id = "550e8400-e29b-41d4-a716-446655440000"

response = requests.delete(
    f"http://localhost:8000/api/v1/ai-workflows/chat/sessions/{session_id}"
)

result = response.json()
print(result["message"])
```


---

### 7. Save Workflow from Session

Save the current workflow from a chat session to the system.

**Endpoint:** `POST /api/v1/ai-workflows/chat/sessions/{session_id}/save`

**Requirements:** 6.1, 6.2, 6.3, 6.4, 6.5

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | UUID | Chat session identifier |

**Request Body:**

```json
{
  "name": "customer-onboarding-workflow",
  "description": "Workflow for onboarding new customers with validation and notifications"
}
```

**Request Schema:**

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| name | string | Yes | Workflow name | 1-255 characters, alphanumeric/hyphens/underscores/spaces, cannot start/end with special chars |
| description | string | No | Workflow description | Max 1,000 characters |

**Response (200 OK):**

```json
{
  "workflow_id": "770e8400-e29b-41d4-a716-446655440003",
  "name": "customer-onboarding-workflow",
  "url": "/workflows/770e8400-e29b-41d4-a716-446655440003"
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Chat session 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Error Response (400 Bad Request):**

```json
{
  "detail": "No workflow to save in this session"
}
```

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/chat/sessions/550e8400-e29b-41d4-a716-446655440000/save \
  -H "Content-Type: application/json" \
  -d '{
    "name": "customer-onboarding-workflow",
    "description": "Workflow for onboarding new customers"
  }'
```

**Example Python:**

```python
import requests

session_id = "550e8400-e29b-41d4-a716-446655440000"

response = requests.post(
    f"http://localhost:8000/api/v1/ai-workflows/chat/sessions/{session_id}/save",
    json={
        "name": "customer-onboarding-workflow",
        "description": "Workflow for onboarding new customers"
    }
)

result = response.json()
print(f"Saved workflow: {result['name']}")
print(f"Workflow ID: {result['workflow_id']}")
print(f"View at: {result['url']}")
```


---

### 8. Export Workflow JSON

Export the current workflow JSON from a session as a downloadable file.

**Endpoint:** `GET /api/v1/ai-workflows/chat/sessions/{session_id}/export`

**Requirements:** 8.1, 8.3

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | UUID | Chat session identifier |

**Response (200 OK):**

Returns the workflow JSON with download headers.

**Headers:**
- `Content-Type: application/json`
- `Content-Disposition: attachment; filename="workflow-name.json"`

**Response Body:**

```json
{
  "name": "customer-onboarding-workflow",
  "description": "Workflow for onboarding new customers",
  "start_step": "step_1",
  "steps": [...]
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Chat session 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Error Response (400 Bad Request):**

```json
{
  "detail": "No workflow to export in this session"
}
```

**Example cURL:**

```bash
curl -X GET http://localhost:8000/api/v1/ai-workflows/chat/sessions/550e8400-e29b-41d4-a716-446655440000/export \
  -o workflow.json
```

**Example Python:**

```python
import requests

session_id = "550e8400-e29b-41d4-a716-446655440000"

response = requests.get(
    f"http://localhost:8000/api/v1/ai-workflows/chat/sessions/{session_id}/export"
)

# Save to file
with open("workflow.json", "w") as f:
    f.write(response.text)

print("Workflow exported to workflow.json")
```

**Example JavaScript:**

```javascript
const sessionId = '550e8400-e29b-41d4-a716-446655440000';

const response = await fetch(
  `http://localhost:8000/api/v1/ai-workflows/chat/sessions/${sessionId}/export`
);

const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'workflow.json';
a.click();
```


---

### 9. Suggest Agents for Capability

Get agent suggestions for a required capability with descriptions and alternatives.

**Endpoint:** `POST /api/v1/ai-workflows/agents/suggest`

**Requirements:** 4.3, 4.4, 4.5

**Request Body:**

```json
{
  "capability_description": "process PDF documents"
}
```

**Request Schema:**

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| capability_description | string | Yes | Description of required capability | 3-500 characters, min 2 words |

**Response (200 OK):**

```json
{
  "suggestions": [
    {
      "agent_name": "pdf-processor",
      "agent_url": "http://pdf-processor:8080",
      "agent_description": "Processes PDF documents and extracts text and metadata",
      "capabilities": ["pdf-processing", "text-extraction", "metadata-extraction"],
      "relevance_score": 95.5,
      "reason": "This agent specializes in PDF processing and matches your requirement exactly"
    },
    {
      "agent_name": "document-handler",
      "agent_url": "http://document-handler:8080",
      "agent_description": "Handles various document formats including PDF, DOCX, and TXT",
      "capabilities": ["pdf-processing", "docx-processing", "txt-processing"],
      "relevance_score": 78.2,
      "reason": "This agent can process PDFs but also handles other formats"
    }
  ],
  "is_ambiguous": true,
  "requires_user_choice": true,
  "no_match": false,
  "alternatives": [],
  "explanation": "I found 2 agents that can process PDF documents. The pdf-processor is more specialized, while document-handler is more versatile. Which would you prefer?"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| suggestions | array | List of suggested agents with details |
| is_ambiguous | boolean | Whether multiple agents are equally suitable |
| requires_user_choice | boolean | Whether user needs to choose between options |
| no_match | boolean | Whether no suitable agents were found |
| alternatives | array | Alternative approaches if no match found |
| explanation | string | Explanation of the suggestion result |

**No Match Response:**

```json
{
  "suggestions": [],
  "is_ambiguous": false,
  "requires_user_choice": false,
  "no_match": true,
  "alternatives": [
    "Consider creating a custom agent for blockchain integration",
    "You might be able to use the API gateway agent with custom configuration",
    "Check if the webhook agent can be adapted for your use case"
  ],
  "explanation": "I couldn't find any agents that match 'blockchain integration'. Here are some alternatives you might consider."
}
```

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/agents/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "capability_description": "process PDF documents"
  }'
```

**Example Python:**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/ai-workflows/agents/suggest",
    json={"capability_description": "process PDF documents"}
)

result = response.json()

if result["no_match"]:
    print("No matching agents found")
    print("Alternatives:", result["alternatives"])
elif result["requires_user_choice"]:
    print("Multiple agents available:")
    for suggestion in result["suggestions"]:
        print(f"  - {suggestion['agent_name']}: {suggestion['reason']}")
else:
    best_match = result["suggestions"][0]
    print(f"Best match: {best_match['agent_name']}")
```


---

## Troubleshooting Guide

### Common Errors and Solutions

#### 1. Validation Errors

**Error:**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "errors": [
      {
        "field": "description",
        "message": "Description must contain at least 3 words to be meaningful"
      }
    ]
  }
}
```

**Solution:**
- Ensure your description has at least 3 words
- Check that required fields are not empty or only whitespace
- Verify field lengths are within constraints

#### 2. Session Not Found

**Error:**
```json
{
  "detail": "Chat session 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Possible Causes:**
- Session ID is incorrect
- Session has been deleted
- Session has expired (30-minute timeout)

**Solution:**
- Verify the session ID is correct
- Create a new session if the old one expired
- Check session status before sending messages

#### 3. Session Expired

**Error:**
```json
{
  "detail": "Chat session has expired"
}
```

**Solution:**
- Create a new chat session
- Sessions expire after 30 minutes of inactivity
- Save your workflow before the session expires

#### 4. Rate Limit Exceeded

**Error:**
```
HTTP 429 Too Many Requests
Retry-After: 45
```

**Solution:**
- Wait for the time specified in `Retry-After` header (seconds)
- Reduce request frequency
- Implement exponential backoff in your client
- Current limit: 50 requests per 60-second window per session

#### 5. Document Upload Errors

**Error:**
```json
{
  "detail": "Unsupported file type 'xlsx'. Supported formats: pdf, docx, doc, txt, md"
}
```

**Solution:**
- Convert your file to a supported format
- Supported formats: PDF, DOCX, DOC, TXT, MD
- Maximum file size: 10MB

**Error:**
```json
{
  "detail": "File size exceeds maximum allowed size of 10MB"
}
```

**Solution:**
- Reduce file size by removing unnecessary content
- Split large documents into smaller files
- Compress images in PDF/DOCX files

#### 6. LLM Service Unavailable

**Error:**
```json
{
  "error_code": "SERVICE_UNAVAILABLE",
  "message": "LLM service is temporarily unavailable",
  "recoverable": true
}
```

**Solution:**
- Wait a few seconds and retry
- The service implements automatic retry with exponential backoff
- Check system status if the issue persists

#### 7. No Workflow to Save

**Error:**
```json
{
  "detail": "No workflow to save in this session"
}
```

**Solution:**
- Send at least one message to generate a workflow
- Verify the workflow was successfully generated
- Check `current_workflow` field in session response

#### 8. Invalid Workflow Name

**Error:**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Workflow name cannot start or end with hyphens, underscores, or spaces"
}
```

**Solution:**
- Use alphanumeric characters, hyphens, underscores, and spaces
- Don't start or end with special characters
- Example valid names: "my-workflow", "Customer Onboarding", "data_pipeline_v2"


---

## Usage Examples

### Complete Workflow: Text to Saved Workflow

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1/ai-workflows"

# Step 1: Create a chat session
session_response = requests.post(
    f"{BASE_URL}/chat/sessions",
    json={
        "initial_description": "Create a workflow for processing customer orders",
        "user_id": "user-123"
    }
)
session = session_response.json()
session_id = session["id"]
print(f"Created session: {session_id}")

# Step 2: Refine the workflow
message_response = requests.post(
    f"{BASE_URL}/chat/sessions/{session_id}/messages",
    json={"message": "Add a payment validation step before processing"}
)
session = message_response.json()
print(f"Assistant: {session['messages'][-1]['content']}")

# Step 3: Add more refinements
message_response = requests.post(
    f"{BASE_URL}/chat/sessions/{session_id}/messages",
    json={"message": "Add error handling and notification steps"}
)
session = message_response.json()
print(f"Workflow now has {len(session['current_workflow']['steps'])} steps")

# Step 4: Save the workflow
save_response = requests.post(
    f"{BASE_URL}/chat/sessions/{session_id}/save",
    json={
        "name": "order-processing-workflow",
        "description": "Complete order processing with validation and notifications"
    }
)
result = save_response.json()
print(f"Saved workflow: {result['name']}")
print(f"Workflow ID: {result['workflow_id']}")
print(f"View at: {result['url']}")

# Step 5: Export the workflow JSON
export_response = requests.get(
    f"{BASE_URL}/chat/sessions/{session_id}/export"
)
with open("order-processing-workflow.json", "w") as f:
    f.write(export_response.text)
print("Workflow exported to order-processing-workflow.json")
```

### Document Upload Workflow

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/ai-workflows"

# Upload a requirements document
with open("requirements.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/upload",
        files={"file": f}
    )

result = response.json()

if result["success"]:
    print(f"Generated workflow: {result['workflow_json']['name']}")
    print(f"Explanation: {result['explanation']}")
    print(f"Agents used: {', '.join(result['agents_used'])}")
    
    # Save the workflow
    workflow_json = result["workflow_json"]
    # ... continue with saving
else:
    print(f"Generation failed: {result['validation_errors']}")
```

### Agent Suggestion Workflow

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/ai-workflows"

# Get agent suggestions
response = requests.post(
    f"{BASE_URL}/agents/suggest",
    json={"capability_description": "send email notifications"}
)

result = response.json()

if result["no_match"]:
    print("No matching agents found")
    print("Consider these alternatives:")
    for alt in result["alternatives"]:
        print(f"  - {alt}")
elif result["requires_user_choice"]:
    print("Multiple agents available:")
    for i, suggestion in enumerate(result["suggestions"], 1):
        print(f"{i}. {suggestion['agent_name']}")
        print(f"   Description: {suggestion['agent_description']}")
        print(f"   Relevance: {suggestion['relevance_score']:.1f}%")
        print(f"   Reason: {suggestion['reason']}")
    
    # User selects an agent
    choice = int(input("Select agent (number): ")) - 1
    selected_agent = result["suggestions"][choice]
    print(f"Selected: {selected_agent['agent_name']}")
else:
    # Single best match
    best_match = result["suggestions"][0]
    print(f"Best match: {best_match['agent_name']}")
    print(f"Description: {best_match['agent_description']}")
```

### Error Handling Example

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1/ai-workflows"

def generate_workflow_with_retry(description, max_retries=3):
    """Generate workflow with automatic retry on rate limit."""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{BASE_URL}/generate",
                json={"description": description}
            )
            
            if response.status_code == 429:
                # Rate limited
                retry_after = int(response.headers.get("Retry-After", 60))
                print(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                # Validation error
                error_data = e.response.json()
                print(f"Validation error: {error_data.get('detail')}")
                return None
            elif e.response.status_code == 503:
                # Service unavailable
                print(f"Service unavailable. Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
                continue
            else:
                raise
    
    print("Max retries exceeded")
    return None

# Usage
result = generate_workflow_with_retry(
    "Create a workflow for data processing with validation"
)

if result and result["success"]:
    print(f"Generated workflow: {result['workflow_json']['name']}")
else:
    print("Failed to generate workflow")
```


---

## Best Practices

### 1. Session Management

- **Create sessions for iterative refinement**: Use chat sessions when you need to refine workflows through multiple interactions
- **Monitor session expiration**: Sessions expire after 30 minutes. Save workflows before expiration
- **Clean up sessions**: Delete sessions when done to free resources
- **Use meaningful user IDs**: Helps with tracking and debugging

### 2. Workflow Generation

- **Be specific in descriptions**: More detailed descriptions produce better workflows
  - ❌ "Process data"
  - ✅ "Process customer order data by validating payment, checking inventory, and sending confirmation emails"

- **Mention required patterns**: Explicitly state if you need loops, conditionals, or parallel execution
  - "Process each item in the order list" → generates loop
  - "If payment fails, send notification" → generates conditional
  - "Process validation and notification in parallel" → generates parallel block

- **Reference specific agents**: If you know which agents to use, mention them
  - "Use the payment-validator agent to check payment status"

### 3. Document Uploads

- **Prepare documents**: Ensure documents are well-formatted and readable
- **Use supported formats**: PDF, DOCX, DOC, TXT, MD
- **Keep files under 10MB**: Compress or split large documents
- **Structure content**: Use headings and clear sections for better parsing

### 4. Error Handling

- **Implement retry logic**: Handle rate limits and transient failures
- **Check response status**: Always verify `success` field in responses
- **Log errors**: Keep track of validation errors and suggestions
- **Validate inputs**: Check constraints before sending requests

### 5. Rate Limiting

- **Respect rate limits**: 50 requests per 60-second window per session
- **Implement backoff**: Use exponential backoff for retries
- **Batch operations**: Combine multiple changes into single messages when possible
- **Monitor Retry-After**: Use the header value for accurate retry timing

### 6. Workflow Refinement

- **Iterate incrementally**: Make one change at a time for better control
- **Review explanations**: Read assistant responses to understand changes
- **Check validation errors**: Address any validation issues before saving
- **Use workflow history**: Review previous versions if needed

### 7. Performance Optimization

- **Cache agent data**: Agent suggestions are cached for 5 minutes
- **Reuse sessions**: Continue existing sessions instead of creating new ones
- **Export workflows**: Download JSON for offline review and version control
- **Minimize LLM calls**: Combine related requests when possible

---

## Rate Limits and Quotas

### Request Limits

| Limit Type | Value | Window | Scope |
|------------|-------|--------|-------|
| Session requests | 50 | 60 seconds | Per session |
| Document size | 10 MB | Per upload | Per request |
| Description length | 10,000 chars | Per request | Per request |
| Message length | 5,000 chars | Per request | Per request |
| Session timeout | 30 minutes | Per session | Per session |

### LLM Service Limits

The system uses Google Gemini API with the following considerations:

- **Token limits**: Requests are automatically chunked to stay within token limits
- **Rate limiting**: Exponential backoff is implemented for rate limit errors
- **Retry logic**: Transient failures are automatically retried up to 3 times
- **Context window**: Large documents are chunked to fit within context limits

### Handling Rate Limits

When you exceed rate limits, you'll receive a `429 Too Many Requests` response:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
Content-Type: application/json

{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for this session",
  "details": {
    "limit": 50,
    "window_seconds": 60,
    "retry_after_seconds": 45
  },
  "suggestions": [
    "Wait 45 seconds before retrying",
    "Reduce request frequency",
    "Consider batching multiple changes into single requests"
  ],
  "recoverable": true
}
```

**Recommended retry strategy:**

```python
import time
import requests

def make_request_with_retry(url, data, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, json=data)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

---

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

The Swagger UI provides:
- Interactive endpoint testing
- Request/response schema documentation
- Example requests and responses
- Authentication configuration (when implemented)

---

## Support and Resources

### Documentation

- **Main API Documentation**: `/docs`
- **Requirements Document**: `.kiro/specs/ai-workflow-generator/requirements.md`
- **Design Document**: `.kiro/specs/ai-workflow-generator/design.md`
- **Implementation Tasks**: `.kiro/specs/ai-workflow-generator/tasks.md`

### Getting Help

1. **Check this documentation**: Most common issues are covered in the troubleshooting guide
2. **Review error messages**: Error responses include suggestions for resolution
3. **Check Swagger UI**: Interactive documentation with examples
4. **Review logs**: Server logs contain detailed error information

### Reporting Issues

When reporting issues, include:
- Request URL and method
- Request body (sanitized)
- Response status code and body
- Session ID (if applicable)
- Timestamp of the request

---

## Changelog

### Version 1.0.0 (Current)

**Features:**
- Natural language workflow generation
- Document upload support (PDF, DOCX, TXT, MD)
- Interactive chat sessions for workflow refinement
- Agent suggestion system
- Workflow validation and auto-correction
- Workflow save and export functionality
- Rate limiting and throttling
- Comprehensive error handling

**Supported Patterns:**
- Sequential workflows
- Conditional logic
- Loops and iteration
- Parallel execution
- Fork-join patterns
- Nested patterns

**Known Limitations:**
- Authentication not yet implemented
- Session persistence is in-memory (lost on restart)
- Maximum 30-minute session timeout
- Single LLM provider (Gemini)

### Upcoming Features

- Authentication and authorization
- Persistent session storage
- Multi-LLM provider support
- Workflow templates
- Workflow testing and validation
- Collaborative editing
- Version control for workflows

# AI Workflow Generator - Troubleshooting Guide

## Common Issues and Solutions

### 1. Validation Errors

#### Issue: "Description must contain at least 3 words"

**Error Response:**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "errors": [{
      "field": "description",
      "message": "Description must contain at least 3 words to be meaningful"
    }]
  }
}
```

**Causes:**
- Description is too short
- Description contains only 1-2 words
- Description is only whitespace

**Solutions:**
- Provide a more detailed description with at least 3 words
- Example: Instead of "process data", use "process customer order data"

---

#### Issue: "Workflow name cannot start or end with special characters"

**Error Response:**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Workflow name cannot start or end with hyphens, underscores, or spaces"
}
```

**Causes:**
- Name starts with `-`, `_`, or space
- Name ends with `-`, `_`, or space

**Solutions:**
- Remove leading/trailing special characters
- Valid: `my-workflow`, `customer_onboarding`, `Data Pipeline`
- Invalid: `-my-workflow`, `workflow_`, ` my workflow `

---

### 2. Session Errors

#### Issue: "Chat session not found"

**Error Response:**
```json
{
  "detail": "Chat session 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Causes:**
- Session ID is incorrect or malformed
- Session was deleted
- Session expired (30-minute timeout)

**Solutions:**
1. Verify the session ID is correct
2. Check if session exists: `GET /chat/sessions/{id}`
3. Create a new session if expired
4. Save important workflows before session expires

**Prevention:**
```python
# Check session before using
response = requests.get(f"{BASE_URL}/chat/sessions/{session_id}")
if response.status_code == 404:
    # Create new session
    session = create_new_session()
```

---

#### Issue: "Chat session has expired"

**Error Response:**
```json
{
  "detail": "Chat session has expired"
}
```

**Causes:**
- Session inactive for more than 30 minutes
- Session status is "expired"

**Solutions:**
1. Create a new chat session
2. If you have the workflow JSON, you can continue in a new session
3. Export workflows regularly to avoid data loss

**Prevention:**
```python
# Monitor session expiration
session = get_session(session_id)
expires_at = datetime.fromisoformat(session['expires_at'])
time_remaining = expires_at - datetime.utcnow()

if time_remaining.total_seconds() < 300:  # Less than 5 minutes
    print("Session expiring soon! Save your workflow.")
```

---

### 3. Rate Limiting

#### Issue: "Rate limit exceeded"

**Error Response:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45

{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for this session",
  "details": {
    "limit": 50,
    "window_seconds": 60,
    "retry_after_seconds": 45
  }
}
```

**Causes:**
- More than 50 requests in 60 seconds
- Rapid-fire requests without delays
- Multiple concurrent requests

**Solutions:**
1. Wait for the time specified in `Retry-After` header
2. Implement exponential backoff
3. Reduce request frequency
4. Batch multiple changes into single messages

**Implementation:**
```python
import time

def make_request_with_backoff(url, data, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, json=data)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

---

### 4. Document Upload Errors

#### Issue: "Unsupported file type"

**Error Response:**
```json
{
  "detail": "Unsupported file type 'xlsx'. Supported formats: pdf, docx, doc, txt, md"
}
```

**Causes:**
- File format not supported
- File extension is incorrect

**Solutions:**
1. Convert file to supported format:
   - PDF (.pdf)
   - Word (.docx, .doc)
   - Text (.txt)
   - Markdown (.md)
2. Verify file extension matches content

---

#### Issue: "File size exceeds maximum"

**Error Response:**
```json
{
  "detail": "File size exceeds maximum allowed size of 10MB"
}
```

**Causes:**
- File is larger than 10MB
- File contains large images or embedded content

**Solutions:**
1. Compress the file
2. Remove unnecessary images
3. Split into multiple smaller files
4. Extract text and use text generation instead

**For PDFs:**
```bash
# Compress PDF using Ghostscript
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=compressed.pdf input.pdf
```

---

#### Issue: "Failed to extract text from document"

**Error Response:**
```json
{
  "detail": "Failed to extract text from document: Document appears to be corrupted"
}
```

**Causes:**
- Document is corrupted
- Document is password-protected
- Document contains only images (scanned PDF)

**Solutions:**
1. Verify document opens correctly in native application
2. Remove password protection
3. For scanned PDFs, use OCR to extract text first
4. Try re-saving the document
5. Convert to plain text format

---

### 5. Workflow Generation Errors

#### Issue: "No suitable agents found"

**Response:**
```json
{
  "success": true,
  "workflow_json": null,
  "explanation": "I couldn't find agents for the required capabilities",
  "validation_errors": ["No agent found for capability: blockchain integration"],
  "suggestions": [
    "Register agents for the required capabilities",
    "Use more general capability descriptions",
    "Check agent registry status"
  ]
}
```

**Causes:**
- Required agents not registered
- Agent descriptions don't match requirements
- Agent registry is empty or unavailable

**Solutions:**
1. Check available agents: `GET /api/v1/agents`
2. Register required agents
3. Use agent suggestion endpoint to find alternatives
4. Modify workflow description to use available agents

---

#### Issue: "Workflow validation failed"

**Response:**
```json
{
  "success": false,
  "workflow_json": {...},
  "validation_errors": [
    "Circular reference detected: step_1 -> step_2 -> step_1",
    "Step 'step_3' is unreachable from start_step"
  ]
}
```

**Causes:**
- Generated workflow has circular dependencies
- Some steps are not reachable
- Invalid step references

**Solutions:**
- The system attempts auto-correction
- Review the explanation for what was corrected
- If auto-correction fails, provide more specific requirements
- Simplify the workflow description

---

### 6. LLM Service Errors

#### Issue: "LLM service temporarily unavailable"

**Error Response:**
```json
{
  "error_code": "SERVICE_UNAVAILABLE",
  "message": "LLM service is temporarily unavailable",
  "details": {
    "service": "gemini",
    "error": "Connection timeout"
  },
  "recoverable": true
}
```

**Causes:**
- Gemini API is down
- Network connectivity issues
- API key is invalid or expired
- Rate limits on LLM provider side

**Solutions:**
1. Wait a few seconds and retry (automatic retry is implemented)
2. Check Gemini API status
3. Verify API key is valid
4. Check network connectivity
5. Review server logs for detailed error information

---

### 7. Workflow Save Errors

#### Issue: "No workflow to save"

**Error Response:**
```json
{
  "detail": "No workflow to save in this session"
}
```

**Causes:**
- Session has no current workflow
- Workflow generation failed
- Session was just created without messages

**Solutions:**
1. Send at least one message to generate a workflow
2. Verify workflow generation was successful
3. Check `current_workflow` field in session response

---

#### Issue: "Workflow name already exists"

**Error Response:**
```json
{
  "detail": "Workflow with name 'customer-onboarding' already exists"
}
```

**Causes:**
- Workflow name conflicts with existing workflow
- Attempting to save duplicate workflow

**Solutions:**
1. Use a different name
2. Add version suffix: `customer-onboarding-v2`
3. Add timestamp: `customer-onboarding-2024-01-15`
4. Delete old workflow if no longer needed

---

## Debugging Tips

### 1. Enable Verbose Logging

Check server logs for detailed error information:

```bash
# View API logs
docker-compose logs -f api

# Filter for AI workflow logs
docker-compose logs -f api | grep "ai_workflow"
```

### 2. Test with Swagger UI

Use the interactive Swagger UI for testing:

1. Navigate to http://localhost:8000/docs
2. Expand the endpoint you want to test
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. Review response

### 3. Validate Requests Locally

Before sending requests, validate them:

```python
from pydantic import ValidationError
from api.schemas.ai_workflow import WorkflowGenerationRequest

try:
    request = WorkflowGenerationRequest(
        description="test"  # Too short
    )
except ValidationError as e:
    print(e.errors())
```

### 4. Check Session State

Regularly check session state during development:

```python
def debug_session(session_id):
    response = requests.get(f"{BASE_URL}/chat/sessions/{session_id}")
    session = response.json()
    
    print(f"Status: {session['status']}")
    print(f"Messages: {len(session['messages'])}")
    print(f"Has workflow: {session['current_workflow'] is not None}")
    print(f"Expires: {session['expires_at']}")
    
    if session['current_workflow']:
        print(f"Steps: {len(session['current_workflow']['steps'])}")
```

### 5. Monitor Rate Limits

Track your request rate:

```python
import time
from collections import deque

class RateLimitTracker:
    def __init__(self, limit=50, window=60):
        self.limit = limit
        self.window = window
        self.requests = deque()
    
    def can_make_request(self):
        now = time.time()
        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()
        
        return len(self.requests) < self.limit
    
    def record_request(self):
        self.requests.append(time.time())

tracker = RateLimitTracker()

if tracker.can_make_request():
    response = make_request()
    tracker.record_request()
else:
    print("Rate limit would be exceeded. Waiting...")
```

---

## Getting Additional Help

### 1. Check Documentation
- Full API Documentation: `API_DOCUMENTATION.md`
- Quick Reference: `API_QUICK_REFERENCE.md`
- Design Document: `.kiro/specs/ai-workflow-generator/design.md`

### 2. Review Examples
- See `API_DOCUMENTATION.md` for complete usage examples
- Check Swagger UI for interactive examples

### 3. Inspect Error Details
- All errors include `suggestions` field with resolution hints
- Check `details` field for specific error information
- Review `error_code` for programmatic error handling

### 4. Test in Isolation
- Use Swagger UI to test endpoints individually
- Verify each step of multi-step workflows
- Test with minimal examples first

### 5. Check System Status
- Verify API is running: `GET /health`
- Check dependencies: `GET /health/ready`
- Review agent registry: `GET /api/v1/agents`

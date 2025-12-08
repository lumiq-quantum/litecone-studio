# AI Workflow Generator API - Quick Reference

## Base URL
```
http://localhost:8000/api/v1/ai-workflows
```

## Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Generate workflow from text |
| POST | `/upload` | Generate workflow from document |
| POST | `/chat/sessions` | Create chat session |
| POST | `/chat/sessions/{id}/messages` | Send chat message |
| GET | `/chat/sessions/{id}` | Get chat session |
| DELETE | `/chat/sessions/{id}` | Delete chat session |
| POST | `/chat/sessions/{id}/save` | Save workflow |
| GET | `/chat/sessions/{id}/export` | Export workflow JSON |
| POST | `/agents/suggest` | Suggest agents |

## Quick Examples

### Generate Workflow
```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/generate \
  -H "Content-Type: application/json" \
  -d '{"description": "Process customer orders with validation"}'
```

### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/upload \
  -F "file=@requirements.pdf"
```

### Create Session
```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"initial_description": "Customer onboarding workflow"}'
```

### Send Message
```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/chat/sessions/{SESSION_ID}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Add validation step"}'
```

### Save Workflow
```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/chat/sessions/{SESSION_ID}/save \
  -H "Content-Type: application/json" \
  -d '{"name": "my-workflow", "description": "My workflow"}'
```

## Rate Limits

- **50 requests** per 60 seconds per session
- **10MB** max document size
- **30 minutes** session timeout

## Common Response Codes

- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Server Error

## Error Response Format

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {...},
  "suggestions": ["..."],
  "recoverable": true
}
```

## Validation Constraints

### Description
- Min: 10 characters
- Max: 10,000 characters
- Min words: 3

### Message
- Min: 1 character
- Max: 5,000 characters

### Workflow Name
- Min: 1 character
- Max: 255 characters
- Pattern: Alphanumeric, hyphens, underscores, spaces
- Cannot start/end with special characters

### Document Upload
- Formats: PDF, DOCX, DOC, TXT, MD
- Max size: 10MB

## Python Quick Start

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/ai-workflows"

# Generate workflow
response = requests.post(
    f"{BASE_URL}/generate",
    json={"description": "Process customer orders"}
)
result = response.json()

# Create session
session = requests.post(
    f"{BASE_URL}/chat/sessions",
    json={"initial_description": "Order processing"}
).json()

# Send message
session = requests.post(
    f"{BASE_URL}/chat/sessions/{session['id']}/messages",
    json={"message": "Add validation"}
).json()

# Save workflow
saved = requests.post(
    f"{BASE_URL}/chat/sessions/{session['id']}/save",
    json={"name": "order-workflow"}
).json()

print(f"Saved: {saved['workflow_id']}")
```

## Documentation Links

- **Full Documentation**: `API_DOCUMENTATION.md`
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

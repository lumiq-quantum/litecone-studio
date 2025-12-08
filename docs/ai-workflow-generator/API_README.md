# AI Workflow Generator API - Complete Documentation

## 📚 Documentation Index

This directory contains comprehensive documentation for the AI Workflow Generator API.

### Quick Links

| Document | Description | Use When |
|----------|-------------|----------|
| **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** | Complete API reference with examples | You need detailed endpoint documentation |
| **[API_QUICK_REFERENCE.md](./API_QUICK_REFERENCE.md)** | Quick reference guide | You need a quick lookup |
| **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** | Common issues and solutions | You're encountering errors |
| **[OPENAPI_ENHANCEMENTS.md](./OPENAPI_ENHANCEMENTS.md)** | Swagger/OpenAPI documentation | You want interactive docs or client generation |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs (Try it out!)
- **ReDoc**: http://localhost:8000/redoc (Read-friendly)
- **OpenAPI Spec**: http://localhost:8000/openapi.json (For tools)

---

## 🚀 Quick Start

### 1. Generate a Workflow from Text

```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a workflow that processes customer orders with validation and notifications"
  }'
```

### 2. Upload a Document

```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/upload \
  -F "file=@requirements.pdf"
```

### 3. Interactive Chat Session

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/ai-workflows"

# Create session
session = requests.post(
    f"{BASE_URL}/chat/sessions",
    json={"initial_description": "Customer onboarding workflow"}
).json()

# Refine workflow
session = requests.post(
    f"{BASE_URL}/chat/sessions/{session['id']}/messages",
    json={"message": "Add email validation step"}
).json()

# Save workflow
result = requests.post(
    f"{BASE_URL}/chat/sessions/{session['id']}/save",
    json={"name": "customer-onboarding"}
).json()

print(f"Saved: {result['workflow_id']}")
```

---

## 📖 What's in Each Document?

### API_DOCUMENTATION.md (Complete Reference)

**Contents:**
- ✅ All 9 endpoints with full details
- ✅ Request/response schemas
- ✅ Code examples (cURL, Python, JavaScript)
- ✅ Error handling examples
- ✅ Rate limits and quotas
- ✅ Best practices
- ✅ Complete usage workflows

**Read this when:**
- You're implementing API integration
- You need detailed examples
- You want to understand all features
- You're troubleshooting complex issues

**Key Sections:**
1. Overview and authentication
2. Endpoint documentation (9 endpoints)
3. Troubleshooting guide
4. Usage examples
5. Best practices
6. Rate limits and quotas

---

### API_QUICK_REFERENCE.md (Cheat Sheet)

**Contents:**
- ✅ Endpoint summary table
- ✅ Quick cURL examples
- ✅ Common response codes
- ✅ Validation constraints
- ✅ Python quick start
- ✅ Links to full docs

**Read this when:**
- You need a quick reminder
- You're looking up an endpoint
- You want a code snippet
- You need constraint values

**Perfect for:**
- Keeping open while coding
- Quick lookups
- Copy-paste examples
- Reference during development

---

### TROUBLESHOOTING.md (Problem Solving)

**Contents:**
- ✅ 15+ common issues with solutions
- ✅ Error message explanations
- ✅ Debugging tips
- ✅ Code examples for error handling
- ✅ Prevention strategies
- ✅ Monitoring techniques

**Read this when:**
- You're getting errors
- Something isn't working
- You need to debug
- You want to prevent issues

**Covers:**
1. Validation errors
2. Session errors
3. Rate limiting
4. Document upload issues
5. Workflow generation problems
6. LLM service errors
7. Workflow save errors

---

### OPENAPI_ENHANCEMENTS.md (Interactive Docs)

**Contents:**
- ✅ Swagger UI guide
- ✅ OpenAPI specification details
- ✅ Client generation instructions
- ✅ Schema documentation
- ✅ Testing workflows
- ✅ Maintenance guide

**Read this when:**
- You want interactive testing
- You need to generate API clients
- You're exploring the API
- You want type-safe clients

**Features:**
- Interactive API testing
- Automatic client generation
- Schema validation
- Request/response examples

---

## 🎯 Common Use Cases

### Use Case 1: One-Shot Workflow Generation

**Goal**: Generate a workflow from a description and save it immediately.

**Documents to read**:
- API_QUICK_REFERENCE.md (for quick example)
- API_DOCUMENTATION.md (for detailed implementation)

**Steps**:
1. Call `POST /generate` with description
2. Review generated workflow
3. Use workflow API to save (or use chat session)

---

### Use Case 2: Interactive Workflow Refinement

**Goal**: Create a workflow through conversation, refining it iteratively.

**Documents to read**:
- API_DOCUMENTATION.md (Section 3-7: Chat endpoints)
- TROUBLESHOOTING.md (Session management)

**Steps**:
1. Create chat session
2. Send messages to refine workflow
3. Review changes after each message
4. Save when satisfied
5. Export JSON if needed

---

### Use Case 3: Document-Based Generation

**Goal**: Upload a requirements document and generate a workflow.

**Documents to read**:
- API_DOCUMENTATION.md (Section 2: Upload endpoint)
- TROUBLESHOOTING.md (Document upload errors)

**Steps**:
1. Prepare document (PDF, DOCX, TXT, MD)
2. Upload via `POST /upload`
3. Review generated workflow
4. Optionally refine via chat session

---

### Use Case 4: Agent Discovery

**Goal**: Find suitable agents for a capability.

**Documents to read**:
- API_DOCUMENTATION.md (Section 9: Agent suggestions)
- API_QUICK_REFERENCE.md (Quick example)

**Steps**:
1. Call `POST /agents/suggest` with capability description
2. Review suggestions with relevance scores
3. Choose agent or explore alternatives
4. Use in workflow generation

---

## 🔧 Development Workflow

### 1. Exploration Phase

**Start with**:
- Swagger UI (http://localhost:8000/docs)
- API_QUICK_REFERENCE.md

**Actions**:
- Try endpoints interactively
- Understand request/response formats
- Test with sample data

### 2. Implementation Phase

**Start with**:
- API_DOCUMENTATION.md
- Code examples in your language

**Actions**:
- Implement API calls
- Add error handling
- Test edge cases

### 3. Debugging Phase

**Start with**:
- TROUBLESHOOTING.md
- Server logs

**Actions**:
- Identify error patterns
- Apply solutions
- Add monitoring

### 4. Production Phase

**Start with**:
- API_DOCUMENTATION.md (Best Practices)
- TROUBLESHOOTING.md (Prevention)

**Actions**:
- Implement rate limiting
- Add retry logic
- Monitor errors
- Handle edge cases

---

## 📊 API Capabilities

### Supported Features

✅ **Natural Language Processing**
- Parse workflow descriptions
- Understand requirements
- Generate structured workflows

✅ **Document Processing**
- PDF text extraction
- DOCX/DOC processing
- TXT and MD support
- 10MB file size limit

✅ **Interactive Refinement**
- Stateful chat sessions
- Conversation history
- Workflow evolution tracking
- 30-minute session timeout

✅ **Agent Integration**
- Query agent registry
- Match capabilities
- Suggest alternatives
- Validate references

✅ **Workflow Patterns**
- Sequential steps
- Conditional logic
- Loops and iteration
- Parallel execution
- Fork-join patterns

✅ **Validation**
- Schema validation
- Cycle detection
- Reachability analysis
- Auto-correction

✅ **Error Handling**
- Detailed error messages
- Recovery suggestions
- Retry logic
- Rate limiting

---

## 🎓 Learning Path

### Beginner

1. Read API_QUICK_REFERENCE.md
2. Try Swagger UI examples
3. Generate your first workflow
4. Review API_DOCUMENTATION.md overview

### Intermediate

1. Read API_DOCUMENTATION.md completely
2. Implement chat session workflow
3. Add error handling
4. Test document upload

### Advanced

1. Read TROUBLESHOOTING.md
2. Implement retry logic
3. Add rate limit monitoring
4. Generate API clients
5. Review OPENAPI_ENHANCEMENTS.md

---

## 🔗 Related Documentation

### Specification Documents

- **Requirements**: `.kiro/specs/ai-workflow-generator/requirements.md`
- **Design**: `.kiro/specs/ai-workflow-generator/design.md`
- **Tasks**: `.kiro/specs/ai-workflow-generator/tasks.md`

### Implementation Guides

- **Gemini Service**: `GEMINI_SERVICE_IMPLEMENTATION.md`
- **Chat Sessions**: `CHAT_SESSION_IMPLEMENTATION.md`
- **Agent Suggestions**: `AGENT_SUGGESTION_IMPLEMENTATION.md`
- **Pattern Generation**: `PATTERN_GENERATION_SUMMARY.md`

### Configuration

- **Config Guide**: `CONFIG_README.md`
- **Rate Limiting**: `RATE_LIMITING.md`
- **Error Handling**: `ERROR_HANDLING_AND_LOGGING.md`

---

## 📞 Support

### Getting Help

1. **Check documentation** (you're here!)
2. **Try Swagger UI** for interactive testing
3. **Review error messages** (they include suggestions)
4. **Check TROUBLESHOOTING.md** for common issues
5. **Review server logs** for detailed errors

### Reporting Issues

Include:
- Request URL and method
- Request body (sanitized)
- Response status and body
- Session ID (if applicable)
- Timestamp
- Error messages from logs

---

## 📝 Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│ AI Workflow Generator API - Quick Reference                │
├─────────────────────────────────────────────────────────────┤
│ Base URL: http://localhost:8000/api/v1/ai-workflows        │
│                                                             │
│ Generate:     POST /generate                                │
│ Upload:       POST /upload                                  │
│ New Session:  POST /chat/sessions                           │
│ Send Message: POST /chat/sessions/{id}/messages            │
│ Get Session:  GET  /chat/sessions/{id}                     │
│ Save:         POST /chat/sessions/{id}/save                │
│ Export:       GET  /chat/sessions/{id}/export              │
│ Suggest:      POST /agents/suggest                          │
│                                                             │
│ Rate Limit: 50 req/60s per session                         │
│ Session Timeout: 30 minutes                                 │
│ Max File Size: 10MB                                         │
│                                                             │
│ Docs: /docs | /redoc | /openapi.json                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎉 You're Ready!

Choose your starting point:

- 🚀 **Just want to try it?** → Open http://localhost:8000/docs
- 📖 **Need full details?** → Read API_DOCUMENTATION.md
- ⚡ **Need quick lookup?** → Use API_QUICK_REFERENCE.md
- 🐛 **Having issues?** → Check TROUBLESHOOTING.md
- 🔧 **Building clients?** → See OPENAPI_ENHANCEMENTS.md

Happy workflow generating! 🎊

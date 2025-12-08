# AI Workflow Generator Documentation

This directory contains comprehensive documentation for the AI Workflow Generator feature, which enables natural language workflow creation using LLM integration.

## Overview

The AI Workflow Generator allows users to create complex workflows through natural language descriptions, document uploads, and interactive chat sessions. It uses Google's Gemini AI to understand requirements and generate valid workflow JSON.

## Quick Links

### Getting Started
- [API Documentation](API_DOCUMENTATION.md) - Complete API reference with examples
- [API Quick Reference](API_QUICK_REFERENCE.md) - Quick lookup for endpoints
- [API README](API_README.md) - Overview and getting started guide
- [Setup Complete](SETUP_COMPLETE.md) - Setup verification and checklist

### Configuration
- [Configuration README](CONFIG_README.md) - Environment variables and settings
- [Configuration Implementation](CONFIGURATION_IMPLEMENTATION_SUMMARY.md) - Implementation details
- [Rate Limiting](RATE_LIMITING.md) - Rate limits and quota management

### Features
- [Chat Session Implementation](CHAT_SESSION_IMPLEMENTATION.md) - Interactive refinement
- [Agent Suggestion Implementation](AGENT_SUGGESTION_IMPLEMENTATION.md) - Smart agent recommendations
- [Pattern Generation](PATTERN_GENERATION_SUMMARY.md) - Complex workflow patterns
- [Schema-Driven Validation](SCHEMA_DRIVEN_VALIDATION.md) - Workflow validation system
- [Templates Implementation](TEMPLATES_IMPLEMENTATION_SUMMARY.md) - Workflow templates
- [Templates README](TEMPLATES_README.md) - Using workflow templates

### Integration & Architecture
- [Gemini Service Implementation](GEMINI_SERVICE_IMPLEMENTATION.md) - LLM integration
- [Integration Summary](INTEGRATION_SUMMARY.md) - System integration overview
- [OpenAPI Enhancements](OPENAPI_ENHANCEMENTS.md) - API specification improvements

### Operations
- [Error Handling and Logging](ERROR_HANDLING_AND_LOGGING.md) - Error management
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

### Reference
- [Documentation Index](DOCUMENTATION_INDEX.md) - Complete documentation map
- [Task 22 Completion Summary](TASK_22_COMPLETION_SUMMARY.md) - Implementation milestone

## Key Features

### 1. Natural Language Workflow Generation
Generate workflows from plain English descriptions:
```
"Create a workflow that processes insurance applications with parallel document verification"
```

### 2. Document Upload & Processing
Upload PDFs and documents to extract requirements and generate workflows automatically.

### 3. Interactive Chat Sessions
Refine workflows through conversational interactions:
- Ask questions about the workflow
- Request modifications
- Add new steps or conditions

### 4. Smart Agent Suggestions
Get intelligent agent recommendations based on:
- Task requirements
- Available agents in registry
- Workflow context

### 5. Workflow Validation
Automatic validation against workflow schema with:
- Self-correction capabilities
- Detailed error messages
- Suggested fixes

### 6. Template System
Pre-built templates for common patterns:
- Sequential processing
- Parallel execution
- Conditional logic
- Loop patterns
- Fork-join patterns

## API Endpoints

### Core Endpoints
- `POST /api/v1/ai-workflows/generate` - Generate workflow from description
- `POST /api/v1/ai-workflows/upload` - Upload document and generate workflow
- `POST /api/v1/ai-workflows/sessions` - Create chat session
- `POST /api/v1/ai-workflows/sessions/{id}/messages` - Send chat message
- `GET /api/v1/ai-workflows/agents/suggest` - Get agent suggestions
- `GET /api/v1/ai-workflows/templates` - List available templates

See [API Documentation](API_DOCUMENTATION.md) for complete details.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                             │
│  (FastAPI Routes - /api/v1/ai-workflows/*)              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 Service Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Workflow    │  │    Chat      │  │   Agent      │  │
│  │  Generation  │  │   Session    │  │  Suggestion  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Document    │  │  Validation  │  │  Templates   │  │
│  │  Processing  │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  LLM Integration                         │
│              (Gemini Service)                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              External Services                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Gemini     │  │   Workflow   │  │    Agent     │  │
│  │     API      │  │     API      │  │   Registry   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Configuration

Required environment variables:
```bash
# Gemini API
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-pro

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=10

# Workflow API
WORKFLOW_API_BASE_URL=http://localhost:8000
```

See [Configuration README](CONFIG_README.md) for complete details.

## Usage Examples

### Generate Simple Workflow
```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Process customer orders with payment verification",
    "auto_save": true
  }'
```

### Create Chat Session
```bash
curl -X POST http://localhost:8000/api/v1/ai-workflows/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "initial_description": "Build a document approval workflow"
  }'
```

### Get Agent Suggestions
```bash
curl "http://localhost:8000/api/v1/ai-workflows/agents/suggest?task_description=verify+documents"
```

See [API Documentation](API_DOCUMENTATION.md) for more examples.

## Testing

### Verify Setup
```bash
cd api/services/ai_workflow_generator
python verify_setup.py
```

### Test Endpoints
Use the Swagger UI at `http://localhost:8000/docs` to test all endpoints interactively.

## Troubleshooting

Common issues and solutions:

1. **API Key Issues** - See [Troubleshooting](TROUBLESHOOTING.md#api-key-errors)
2. **Rate Limiting** - See [Rate Limiting](RATE_LIMITING.md)
3. **Validation Errors** - See [Schema-Driven Validation](SCHEMA_DRIVEN_VALIDATION.md)
4. **Generation Failures** - See [Troubleshooting](TROUBLESHOOTING.md#generation-failures)

## Development

### Adding New Features
1. Update service layer in `api/services/ai_workflow_generator/`
2. Add routes in `api/routes/ai_workflows.py`
3. Update documentation
4. Add tests

### Code Structure
```
api/services/ai_workflow_generator/
├── __init__.py
├── gemini_service.py          # LLM integration
├── workflow_generation.py     # Core generation logic
├── chat_session.py            # Chat functionality
├── agent_suggestion.py        # Agent recommendations
├── document_processing.py     # PDF/document handling
├── workflow_validation.py     # Validation logic
├── templates.py               # Template management
├── pattern_generation.py      # Complex patterns
├── config.py                  # Configuration
└── errors.py                  # Error handling
```

## Related Documentation

- [Main API Documentation](../api/API_DOCUMENTATION.md)
- [Workflow Format Guide](../guides/WORKFLOW_FORMAT.md)
- [Feature Documentation](../features/)
- [UI Integration](../ui/)

## Support

For questions or issues:
1. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review [API Documentation](API_DOCUMENTATION.md)
3. See [Documentation Index](DOCUMENTATION_INDEX.md)

---

**Last Updated:** 2024-12-08  
**Version:** 1.0  
**Status:** Production Ready

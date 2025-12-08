# AI Workflow Generator Service

This service provides AI-powered workflow generation capabilities using Google's Gemini LLM.

## Overview

The AI Workflow Generator enables users to create complex workflow JSON definitions through natural language descriptions or document uploads. It supports interactive refinement through chat sessions and automatically validates generated workflows.

## Directory Structure

```
api/services/ai_workflow_generator/
├── __init__.py                    # Package initialization
├── config.py                      # Configuration management
├── workflow_generation.py         # Main workflow generation service
├── gemini_service.py             # Gemini LLM integration
├── agent_query.py                # Agent registry querying
├── document_processing.py        # Document text extraction
├── chat_session.py               # Chat session management
├── workflow_validation.py        # Workflow validation logic
└── README.md                     # This file
```

## Configuration

Configuration is managed through environment variables. See `config.py` for all available settings.

### Required Environment Variables

```bash
# Gemini API
GEMINI_API_KEY=your-api-key-here

# Optional Configuration
GEMINI_MODEL=gemini-1.5-pro
GEMINI_MAX_TOKENS=8192
GEMINI_TEMPERATURE=0.7
SESSION_TIMEOUT_MINUTES=30
MAX_DOCUMENT_SIZE_MB=10
```

## Components

### WorkflowGenerationService
Main orchestration service for workflow generation from text or documents.

### GeminiService
Handles all interactions with Google's Gemini LLM API, including prompt construction and response parsing.

### AgentQueryService
Queries the agent registry to find available agents and match them to workflow requirements.

### DocumentProcessingService
Extracts text from various document formats (PDF, DOCX, TXT, MD).

### ChatSessionManager
Manages stateful chat sessions for interactive workflow refinement.

### WorkflowValidationService
Validates generated workflows for schema compliance, cycles, reachability, and agent references.

## Usage

The service is integrated into the main API through the `/api/v1/ai-workflows` endpoints.

See `api/routes/ai_workflows.py` for available endpoints.

## Testing

Tests are located in `api/tests/ai_workflow_generator/`.

The service uses property-based testing with Hypothesis to verify correctness properties across many inputs.

Run tests with:
```bash
pytest api/tests/ai_workflow_generator/
```

## Implementation Status

This is the initial project structure. Components will be implemented in subsequent tasks according to the implementation plan in `.kiro/specs/ai-workflow-generator/tasks.md`.

# OpenAPI/Swagger Enhancements for AI Workflow Generator

## Overview

This document describes the OpenAPI/Swagger documentation enhancements for the AI Workflow Generator API endpoints. All endpoints are automatically documented through FastAPI's OpenAPI integration.

## Accessing Documentation

### Interactive Documentation

1. **Swagger UI** (Recommended for testing)
   - URL: http://localhost:8000/docs
   - Features:
     - Interactive API testing
     - Request/response examples
     - Schema validation
     - Try-it-out functionality

2. **ReDoc** (Recommended for reading)
   - URL: http://localhost:8000/redoc
   - Features:
     - Clean, readable layout
     - Searchable documentation
     - Code samples
     - Detailed schema documentation

3. **OpenAPI JSON Specification**
   - URL: http://localhost:8000/openapi.json
   - Use for:
     - API client generation
     - Custom documentation tools
     - Integration with other systems

## Endpoint Documentation

All AI Workflow Generator endpoints are documented with:

### 1. Endpoint Metadata
- **Summary**: Brief description of endpoint purpose
- **Description**: Detailed explanation of functionality
- **Tags**: Grouped under "AI Workflows" tag
- **Requirements**: References to requirements document

### 2. Request Documentation
- **Path Parameters**: Type, description, examples
- **Request Body**: Schema with field descriptions and constraints
- **Query Parameters**: When applicable
- **Headers**: Required headers

### 3. Response Documentation
- **Success Responses**: 200, 201 status codes with schemas
- **Error Responses**: 400, 404, 422, 429, 500, 503 with error schemas
- **Response Examples**: Sample JSON responses
- **Headers**: Response headers (e.g., Retry-After)

### 4. Schema Documentation
- **Field Types**: String, integer, boolean, object, array
- **Constraints**: Min/max length, patterns, required fields
- **Examples**: Sample values for each field
- **Descriptions**: Clear explanation of each field's purpose

## Enhanced Endpoint Descriptions

### POST /api/v1/ai-workflows/generate

**OpenAPI Metadata:**
```yaml
summary: Generate workflow from text description
description: |
  Generate a workflow JSON from a natural language description.
  
  This endpoint implements Requirement 1.1: Parse natural language descriptions
  and generate valid workflow JSON with appropriate agent assignments.
  
  The system will:
  1. Parse your natural language description
  2. Query the agent registry for available agents
  3. Generate a valid workflow JSON structure
  4. Validate the workflow against the schema
  5. Return the workflow with explanations
  
  **Rate Limit**: 50 requests per 60 seconds per session
  
tags:
  - AI Workflows
requestBody:
  required: true
  content:
    application/json:
      schema:
        $ref: '#/components/schemas/WorkflowGenerationRequest'
      examples:
        simple:
          summary: Simple workflow
          value:
            description: "Create a workflow that processes documents and stores results"
        complex:
          summary: Complex workflow with preferences
          value:
            description: "Process customer orders with validation, payment, and notification"
            user_preferences:
              prefer_parallel: true
              max_steps: 10
responses:
  200:
    description: Workflow generated successfully
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/WorkflowGenerationResponse'
  400:
    description: Invalid request
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/ErrorResponse'
  422:
    description: Validation error
  429:
    description: Rate limit exceeded
    headers:
      Retry-After:
        schema:
          type: integer
        description: Seconds to wait before retrying
  500:
    description: Internal server error
```

### POST /api/v1/ai-workflows/upload

**OpenAPI Metadata:**
```yaml
summary: Generate workflow from document
description: |
  Upload a document (PDF, DOCX, TXT, MD) and generate a workflow from its content.
  
  This endpoint implements Requirement 2.1: Extract text from documents
  and generate workflows from the content.
  
  **Supported Formats**: PDF, DOCX, DOC, TXT, MD
  **Maximum Size**: 10MB
  **Rate Limit**: 50 requests per 60 seconds per session
  
tags:
  - AI Workflows
requestBody:
  required: true
  content:
    multipart/form-data:
      schema:
        type: object
        properties:
          file:
            type: string
            format: binary
            description: Document file to process
      examples:
        pdf:
          summary: PDF document
          description: Upload a PDF requirements document
        docx:
          summary: Word document
          description: Upload a DOCX specification document
```

### POST /api/v1/ai-workflows/chat/sessions

**OpenAPI Metadata:**
```yaml
summary: Create a chat session
description: |
  Create a new chat session for interactive workflow refinement.
  
  This endpoint implements Requirement 3.1: Create stateful sessions that
  maintain conversation history and current workflow state.
  
  **Session Timeout**: 30 minutes
  **Rate Limit**: 50 requests per 60 seconds per session
  
  Sessions allow you to:
  - Iteratively refine workflows through conversation
  - Maintain workflow history
  - Track changes and explanations
  - Save workflows when ready
  
tags:
  - AI Workflows
```

## Schema Enhancements

### WorkflowGenerationRequest Schema

```yaml
WorkflowGenerationRequest:
  type: object
  required:
    - description
  properties:
    description:
      type: string
      minLength: 10
      maxLength: 10000
      description: Natural language description of the workflow
      example: "Create a workflow that processes documents, validates them, and stores the results"
    user_preferences:
      type: object
      description: Optional user preferences for generation
      properties:
        prefer_parallel:
          type: boolean
          description: Prefer parallel execution when possible
        max_steps:
          type: integer
          description: Maximum number of steps to generate
      example:
        prefer_parallel: true
        max_steps: 10
```

### ErrorResponse Schema

```yaml
ErrorResponse:
  type: object
  required:
    - error_code
    - message
    - recoverable
  properties:
    error_code:
      type: string
      description: Machine-readable error code
      enum:
        - VALIDATION_ERROR
        - SERVICE_UNAVAILABLE
        - RATE_LIMIT_EXCEEDED
        - NOT_FOUND
        - INTERNAL_ERROR
      example: "VALIDATION_ERROR"
    message:
      type: string
      description: Human-readable error message
      example: "Request validation failed"
    details:
      type: object
      description: Additional error details
      example:
        errors:
          - field: "description"
            message: "Description must contain at least 3 words"
    suggestions:
      type: array
      items:
        type: string
      description: Suggestions for resolving the error
      example:
        - "Try providing a more detailed description"
        - "Check that all required fields are filled"
    recoverable:
      type: boolean
      description: Whether the error is recoverable
      example: true
```

## Testing with Swagger UI

### Step-by-Step Guide

1. **Navigate to Swagger UI**
   ```
   http://localhost:8000/docs
   ```

2. **Find AI Workflows Section**
   - Scroll to "AI Workflows" tag
   - All endpoints are grouped together

3. **Test Generate Endpoint**
   - Click on `POST /api/v1/ai-workflows/generate`
   - Click "Try it out"
   - Enter description: "Process customer orders"
   - Click "Execute"
   - Review response

4. **Test Upload Endpoint**
   - Click on `POST /api/v1/ai-workflows/upload`
   - Click "Try it out"
   - Click "Choose File" and select a PDF/DOCX
   - Click "Execute"
   - Review response

5. **Test Chat Flow**
   - Create session: `POST /chat/sessions`
   - Copy session ID from response
   - Send message: `POST /chat/sessions/{id}/messages`
   - Paste session ID
   - Enter message
   - Review updated session

6. **Test Save Workflow**
   - Use session ID from previous step
   - Call `POST /chat/sessions/{id}/save`
   - Enter workflow name
   - Review saved workflow details

## Code Generation

### Generate Python Client

```bash
# Install openapi-generator
npm install -g @openapitools/openapi-generator-cli

# Generate Python client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./ai-workflow-client-python

# Use generated client
cd ai-workflow-client-python
pip install -e .
```

### Generate TypeScript Client

```bash
# Generate TypeScript/Axios client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o ./ai-workflow-client-ts
```

### Generate Go Client

```bash
# Generate Go client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g go \
  -o ./ai-workflow-client-go
```

## Custom Documentation

### Export OpenAPI Spec

```bash
# Download OpenAPI specification
curl http://localhost:8000/openapi.json > openapi.json

# Convert to YAML
pip install pyyaml
python -c "import json, yaml; print(yaml.dump(json.load(open('openapi.json'))))" > openapi.yaml
```

### Generate Static Documentation

```bash
# Using redoc-cli
npm install -g redoc-cli
redoc-cli bundle openapi.json -o api-docs.html

# Using swagger-ui
npx swagger-ui-watcher openapi.json
```

## Best Practices

### 1. Use Examples
- All schemas include example values
- Multiple examples for complex scenarios
- Examples demonstrate common use cases

### 2. Clear Descriptions
- Every field has a description
- Constraints are documented
- Requirements are referenced

### 3. Error Documentation
- All error responses are documented
- Error codes are enumerated
- Suggestions are provided

### 4. Interactive Testing
- Use Swagger UI for quick testing
- Validate requests before coding
- Test error scenarios

### 5. Client Generation
- Generate clients from OpenAPI spec
- Keep clients in sync with API
- Use type-safe clients

## Maintenance

### Updating Documentation

Documentation is automatically generated from:
1. FastAPI route decorators
2. Pydantic schema definitions
3. Docstrings in route handlers
4. Response model declarations

To update documentation:
1. Update route decorators (summary, description, tags)
2. Update Pydantic schemas (Field descriptions, examples)
3. Update docstrings in route handlers
4. Restart API server
5. Refresh Swagger UI

### Versioning

- API version is in URL: `/api/v1/ai-workflows`
- OpenAPI spec includes version: `1.0.0`
- Breaking changes require version bump
- Deprecation notices in descriptions

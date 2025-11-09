# Workflow JSON Format Specification

This document defines the structure and syntax for workflow definition files used by the Centralized Executor.

## Overview

A workflow is defined as a JSON document that specifies a sequential flow of agent invocations. Each workflow consists of:
- Metadata (ID, name, version)
- A starting step
- A collection of steps with input mappings and next-step references

## Schema

### Root Object

```json
{
  "workflow_id": "string",
  "name": "string",
  "version": "string",
  "start_step": "string",
  "steps": {
    "step-id": { /* WorkflowStep */ }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workflow_id` | string | Yes | Unique identifier for this workflow definition |
| `name` | string | Yes | Human-readable workflow name |
| `version` | string | Yes | Semantic version (e.g., "1.0.0") |
| `start_step` | string | Yes | ID of the first step to execute |
| `steps` | object | Yes | Map of step IDs to WorkflowStep objects |

### WorkflowStep Object

```json
{
  "id": "string",
  "agent_name": "string",
  "next_step": "string | null",
  "input_mapping": {
    "field_name": "string"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for this step (must match key in steps map) |
| `agent_name` | string | Yes | Name of the agent to invoke (must exist in Agent Registry) |
| `next_step` | string or null | Yes | ID of the next step to execute, or null if this is the final step |
| `input_mapping` | object | Yes | Map of input field names to value expressions |

## Input Mapping Syntax

The `input_mapping` object defines how to construct the input payload for an agent by mapping field names to value expressions.

### Expression Types

#### 1. Workflow Input Reference

Access fields from the initial workflow input:

```
${workflow.input.field_name}
```

**Example:**
```json
{
  "input_mapping": {
    "topic": "${workflow.input.research_topic}",
    "style": "${workflow.input.writing_style}"
  }
}
```

If the workflow is invoked with:
```json
{
  "research_topic": "Climate Change",
  "writing_style": "academic"
}
```

The agent receives:
```json
{
  "topic": "Climate Change",
  "style": "academic"
}
```

#### 2. Previous Step Output Reference

Access output fields from a previously executed step:

```
${step-id.output.field_name}
```

**Example:**
```json
{
  "input_mapping": {
    "research_data": "${step-1.output.findings}",
    "summary": "${step-1.output.summary}"
  }
}
```

If step-1 produced:
```json
{
  "findings": ["fact 1", "fact 2"],
  "summary": "Research summary text"
}
```

The agent receives:
```json
{
  "research_data": ["fact 1", "fact 2"],
  "summary": "Research summary text"
}
```

#### 3. Nested Field Access

Access nested fields using dot notation:

```
${workflow.input.config.timeout}
${step-1.output.metadata.author}
```

**Example:**
```json
{
  "input_mapping": {
    "timeout": "${workflow.input.config.timeout}",
    "author": "${step-1.output.metadata.author}"
  }
}
```

#### 4. Literal Values

Use literal JSON values (strings, numbers, booleans, objects, arrays):

```json
{
  "input_mapping": {
    "max_results": 10,
    "include_metadata": true,
    "format": "json",
    "filters": ["published", "verified"]
  }
}
```

### Combining Expressions

You can mix literal values and expressions:

```json
{
  "input_mapping": {
    "query": "${workflow.input.search_term}",
    "max_results": 50,
    "sources": ["web", "academic"],
    "previous_findings": "${step-1.output.results}"
  }
}
```

## Complete Example

### Simple Sequential Workflow

```json
{
  "workflow_id": "wf-research-write-001",
  "name": "Research and Write Article",
  "version": "1.0.0",
  "start_step": "research",
  "steps": {
    "research": {
      "id": "research",
      "agent_name": "ResearchAgent",
      "next_step": "write",
      "input_mapping": {
        "topic": "${workflow.input.topic}",
        "depth": "${workflow.input.depth}",
        "sources": ["scientific journals", "government reports"]
      }
    },
    "write": {
      "id": "write",
      "agent_name": "WriterAgent",
      "next_step": null,
      "input_mapping": {
        "research_data": "${research.output.findings}",
        "summary": "${research.output.summary}",
        "style": "${workflow.input.writing_style}",
        "word_count": "${workflow.input.target_word_count}"
      }
    }
  }
}
```

### Execution with Initial Input

**Initial Input:**
```json
{
  "topic": "Climate Change Impact on Agriculture",
  "depth": "comprehensive",
  "writing_style": "academic",
  "target_word_count": 1500
}
```

**Step 1 (research) receives:**
```json
{
  "topic": "Climate Change Impact on Agriculture",
  "depth": "comprehensive",
  "sources": ["scientific journals", "government reports"]
}
```

**Step 1 produces (example):**
```json
{
  "findings": [
    "Rising temperatures affect crop yields",
    "Changing precipitation patterns impact irrigation"
  ],
  "summary": "Climate change significantly impacts agricultural productivity through temperature increases and altered precipitation patterns."
}
```

**Step 2 (write) receives:**
```json
{
  "research_data": [
    "Rising temperatures affect crop yields",
    "Changing precipitation patterns impact irrigation"
  ],
  "summary": "Climate change significantly impacts agricultural productivity through temperature increases and altered precipitation patterns.",
  "style": "academic",
  "word_count": 1500
}
```

## Multi-Step Workflow Example

```json
{
  "workflow_id": "wf-data-pipeline-001",
  "name": "Data Processing Pipeline",
  "version": "2.1.0",
  "start_step": "extract",
  "steps": {
    "extract": {
      "id": "extract",
      "agent_name": "DataExtractorAgent",
      "next_step": "transform",
      "input_mapping": {
        "source_url": "${workflow.input.data_source}",
        "format": "json"
      }
    },
    "transform": {
      "id": "transform",
      "agent_name": "DataTransformerAgent",
      "next_step": "validate",
      "input_mapping": {
        "raw_data": "${extract.output.data}",
        "schema": "${workflow.input.target_schema}",
        "transformations": ["normalize", "deduplicate"]
      }
    },
    "validate": {
      "id": "validate",
      "agent_name": "DataValidatorAgent",
      "next_step": "load",
      "input_mapping": {
        "data": "${transform.output.transformed_data}",
        "rules": "${workflow.input.validation_rules}"
      }
    },
    "load": {
      "id": "load",
      "agent_name": "DataLoaderAgent",
      "next_step": null,
      "input_mapping": {
        "data": "${validate.output.validated_data}",
        "destination": "${workflow.input.destination_db}",
        "batch_size": 1000
      }
    }
  }
}
```

## Validation Rules

The Centralized Executor validates workflow definitions before execution:

### Required Fields
- All root fields must be present
- All step fields must be present
- `start_step` must reference an existing step ID
- Each step's `id` must match its key in the `steps` map

### Step References
- If `next_step` is not null, it must reference an existing step ID
- No circular references (step A → step B → step A)
- All steps must be reachable from `start_step`

### Input Mapping
- Expression syntax must be valid
- Step references must point to steps that execute before the current step
- Field paths must use valid identifiers

### Example Validation Errors

**Invalid start_step:**
```json
{
  "start_step": "nonexistent-step",  // Error: step not found
  "steps": {
    "step-1": { /* ... */ }
  }
}
```

**Circular reference:**
```json
{
  "steps": {
    "step-1": {
      "next_step": "step-2"
    },
    "step-2": {
      "next_step": "step-1"  // Error: circular reference
    }
  }
}
```

**Invalid step reference in input_mapping:**
```json
{
  "steps": {
    "step-1": {
      "input_mapping": {
        "data": "${step-2.output.result}"  // Error: step-2 hasn't executed yet
      },
      "next_step": "step-2"
    }
  }
}
```

## Best Practices

### 1. Use Descriptive IDs
```json
// Good
"steps": {
  "extract-user-data": { /* ... */ },
  "validate-email": { /* ... */ }
}

// Avoid
"steps": {
  "step1": { /* ... */ },
  "step2": { /* ... */ }
}
```

### 2. Version Your Workflows
Use semantic versioning to track changes:
- Major version: Breaking changes to workflow structure
- Minor version: New steps or optional fields
- Patch version: Bug fixes or documentation updates

### 3. Document Complex Mappings
Add comments in your workflow documentation explaining complex input mappings:

```json
{
  "input_mapping": {
    // Combines research findings with user preferences
    "content": "${research.output.findings}",
    "preferences": "${workflow.input.user_preferences}"
  }
}
```

### 4. Keep Steps Focused
Each step should have a single, clear responsibility. Break complex operations into multiple steps.

### 5. Handle Missing Fields
Ensure your agents handle missing or null input fields gracefully, as input mapping may reference fields that don't exist in the output.

## Error Handling

### Missing Input Fields

If an input mapping references a field that doesn't exist:
- The executor logs a warning
- The field is omitted from the agent input
- The agent should handle missing fields gracefully

### Invalid Expression Syntax

If an expression has invalid syntax:
- The executor fails workflow validation
- An error is logged with the invalid expression
- The workflow does not start

### Step Execution Failure

If a step fails:
- The executor marks the workflow as FAILED
- Subsequent steps are not executed
- The failure is persisted to the database for potential retry

## Future Enhancements

Planned features for future versions:

- **Conditional Execution**: `if` conditions on steps
- **Parallel Execution**: Execute independent steps concurrently
- **Loops**: Iterate over collections
- **Sub-workflows**: Nest workflows within steps
- **Dynamic Step Generation**: Create steps at runtime based on data

## Agent Communication Protocol

Agents invoked by workflows communicate using the JSON-RPC 2.0 protocol. The workflow definition itself is protocol-agnostic - the bridge service handles translating workflow steps into JSON-RPC requests to agents.

For details on how agents receive requests and return responses, see the [A2A Agent Interface Specification](A2A_AGENT_INTERFACE.md).

## See Also

- [A2A Agent Interface Specification](A2A_AGENT_INTERFACE.md) - JSON-RPC 2.0 protocol details
- [README.md](README.md) - Project overview
- [examples/workflow_README.md](examples/workflow_README.md) - Example workflows

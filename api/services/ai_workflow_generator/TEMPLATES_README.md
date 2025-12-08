# AI Workflow Generator Templates

This document describes the templates and examples available in the AI Workflow Generator service.

## Overview

The `templates.py` module provides reusable templates for:
- Example workflow descriptions for testing
- Prompt templates for different workflow patterns
- Agent description formatting templates
- Error message templates with helpful suggestions
- Explanation templates for workflow changes

**Requirements Addressed:** 1.1, 3.3, 4.4

## Example Workflow Descriptions

Pre-defined workflow descriptions for testing and demonstration purposes.

### Available Examples

| Example Type | Description |
|-------------|-------------|
| `simple_sequential` | Basic sequential workflow with validation and storage |
| `with_conditional` | Workflow with conditional branching logic |
| `with_loop` | Batch processing with iteration over collections |
| `with_parallel` | Parallel execution of multiple analyses |
| `with_fork_join` | Multi-channel notification with join policy |
| `complex_nested` | E-commerce order fulfillment with nested patterns |
| `data_pipeline` | Data processing pipeline with validation |
| `document_processing` | Document upload and processing workflow |

### Usage

```python
from api.services.ai_workflow_generator.templates import get_example_description

# Get an example description
description = get_example_description("simple_sequential")

# Use in workflow generation
result = await workflow_service.generate_from_text(description)
```

## Prompt Templates

Templates for constructing LLM prompts with consistent structure.

### Available Templates

#### BASE_WORKFLOW_GENERATION
Main template for generating workflows from natural language descriptions.

**Variables:**
- `description`: User's workflow requirements
- `agents`: Formatted list of available agents

**Usage:**
```python
from api.services.ai_workflow_generator.templates import build_prompt

prompt = build_prompt(
    "BASE_WORKFLOW_GENERATION",
    description="Create a data processing workflow",
    agents=formatted_agents
)
```

#### Pattern-Specific Templates

- `CONDITIONAL_PATTERN`: Template for conditional logic
- `LOOP_PATTERN`: Template for iteration patterns
- `PARALLEL_PATTERN`: Template for parallel execution
- `FORK_JOIN_PATTERN`: Template for fork-join patterns

#### WORKFLOW_REFINEMENT
Template for refining existing workflows based on user feedback.

**Variables:**
- `current_workflow`: Current workflow JSON
- `modification_request`: User's modification request
- `conversation_history`: Previous conversation
- `agents`: Available agents

#### AGENT_SUGGESTION
Template for suggesting appropriate agents for a capability.

**Variables:**
- `requirement`: Capability requirement description
- `agents`: Available agents

## Agent Formatting Templates

Templates for formatting agent information in prompts and responses.

### AgentFormattingTemplates Class

#### format_agent_list(agents)
Format a list of agents for LLM prompts.

```python
from api.services.ai_workflow_generator.templates import AgentFormattingTemplates

agents = [
    {"name": "data-processor", "description": "Processes data", "capabilities": ["transform"], "status": "active"}
]

formatted = AgentFormattingTemplates.format_agent_list(agents)
```

**Output:**
```
• data-processor (active)
  Description: Processes data
  Capabilities: transform
```

#### format_agent_detail(agent)
Format detailed information about a single agent.

```python
detail = AgentFormattingTemplates.format_agent_detail(agent)
```

#### format_agent_suggestion(agent, reason, confidence)
Format an agent suggestion with reasoning.

```python
suggestion = AgentFormattingTemplates.format_agent_suggestion(
    agent=agent,
    reason="Best match for data processing tasks",
    confidence="high"
)
```

## Error Message Templates

Comprehensive error messages with helpful suggestions for users.

### Available Error Templates

#### User Input Errors
- `INVALID_DESCRIPTION`: Description too vague or incomplete
- `NO_AGENTS_AVAILABLE`: No agents in registry
- `AGENT_NOT_FOUND`: Specified agent doesn't exist

#### Document Processing Errors
- `UNSUPPORTED_FORMAT`: File format not supported
- `DOCUMENT_TOO_LARGE`: File exceeds size limit
- `EXTRACTION_FAILED`: Failed to extract text from document

#### LLM Service Errors
- `LLM_SERVICE_ERROR`: AI service temporarily unavailable
- `RATE_LIMIT_EXCEEDED`: Too many requests

#### Validation Errors
- `VALIDATION_FAILED`: Workflow validation errors
- `CIRCULAR_REFERENCE`: Workflow contains cycles
- `UNREACHABLE_STEPS`: Steps not reachable from start

#### Session Errors
- `SESSION_EXPIRED`: Chat session timed out
- `SESSION_NOT_FOUND`: Session doesn't exist

### Usage

```python
from api.services.ai_workflow_generator.templates import format_error_message

# Format an error message
error_msg = format_error_message(
    "AGENT_NOT_FOUND",
    agent_name="missing-agent",
    available_agents="agent-1, agent-2, agent-3"
)
```

**Output:**
```
Cannot use agent 'missing-agent' in workflow.

Issue: The specified agent does not exist in the agent registry or is not active.

Suggestions:
• Check the agent name spelling
• Verify the agent is registered in the agent registry
• Ensure the agent status is 'active'
• Use the agent suggestion feature to find available agents
• Available agents: agent-1, agent-2, agent-3
```

### Error Message Features

All error messages include:
1. **Clear issue description**: What went wrong
2. **Context**: Relevant details about the error
3. **Actionable suggestions**: Steps to resolve the issue
4. **Graceful degradation**: Handles missing template variables

## Explanation Templates

Templates for explaining workflow changes and decisions to users.

### ExplanationTemplates Class

#### workflow_generated(workflow_name, num_steps, agents_used)
Explain a newly generated workflow.

```python
from api.services.ai_workflow_generator.templates import ExplanationTemplates

explanation = ExplanationTemplates.workflow_generated(
    workflow_name="data-processing",
    num_steps=5,
    agents_used=["validator", "processor", "storage"]
)
```

#### workflow_modified(changes, preserved_count)
Explain modifications made to a workflow.

```python
explanation = ExplanationTemplates.workflow_modified(
    changes=["Added validation step", "Updated agent reference"],
    preserved_count=3
)
```

#### agent_selected(agent_name, reason, alternatives)
Explain why an agent was selected.

```python
explanation = ExplanationTemplates.agent_selected(
    agent_name="data-processor",
    reason="Best match for data transformation tasks",
    alternatives=["alt-processor", "generic-processor"]
)
```

#### pattern_detected(pattern_type, description)
Explain a detected workflow pattern.

```python
explanation = ExplanationTemplates.pattern_detected(
    pattern_type="loop",
    description="Iterates over each item in the collection for batch processing"
)
```

#### validation_auto_corrected(corrections)
Explain automatic corrections made during validation.

```python
explanation = ExplanationTemplates.validation_auto_corrected(
    corrections=["Added missing start_step", "Fixed circular reference"]
)
```

#### clarification_response(question, answer)
Format a response to a clarification question.

```python
response = ExplanationTemplates.clarification_response(
    question="How does the conditional logic work?",
    answer="The conditional step evaluates an expression and branches based on the result..."
)
```

## Workflow Pattern Examples

Complete workflow JSON examples for different patterns.

### Available Pattern Examples

- `simple_sequential`: Basic sequential workflow
- `with_conditional`: Conditional branching
- `with_loop`: Loop iteration
- `with_parallel`: Parallel execution

### Usage

```python
from api.services.ai_workflow_generator.templates import get_pattern_example

# Get a pattern example
pattern = get_pattern_example("with_conditional")

# Use as a reference or starting point
workflow_json = pattern.copy()
```

## Integration Examples

### Complete Workflow Generation Flow

```python
from api.services.ai_workflow_generator.templates import (
    get_example_description,
    build_prompt,
    AgentFormattingTemplates,
    ExplanationTemplates,
    format_error_message
)

# 1. Get example description
description = get_example_description("simple_sequential")

# 2. Format agents for prompt
agents = await agent_service.get_all_agents()
formatted_agents = AgentFormattingTemplates.format_agent_list(agents)

# 3. Build prompt
prompt = build_prompt(
    "BASE_WORKFLOW_GENERATION",
    description=description,
    agents=formatted_agents
)

# 4. Generate workflow (using LLM service)
try:
    workflow = await llm_service.generate_workflow(prompt, agents)
    
    # 5. Generate explanation
    explanation = ExplanationTemplates.workflow_generated(
        workflow_name=workflow["name"],
        num_steps=len(workflow["steps"]),
        agents_used=extract_agents(workflow)
    )
    
except Exception as e:
    # 6. Format error message
    error_msg = format_error_message(
        "LLM_SERVICE_ERROR",
        error_details=str(e)
    )
```

### Error Handling with Templates

```python
try:
    workflow = await generate_workflow(description)
except ValidationError as e:
    error_msg = format_error_message(
        "VALIDATION_FAILED",
        error_count=len(e.errors),
        errors="\n".join(e.errors)
    )
    return {"error": error_msg}
except AgentNotFoundError as e:
    error_msg = format_error_message(
        "AGENT_NOT_FOUND",
        agent_name=e.agent_name,
        available_agents=", ".join(get_available_agent_names())
    )
    return {"error": error_msg}
```

## Testing

Comprehensive tests are available in `api/tests/ai_workflow_generator/test_templates.py`.

Run tests:
```bash
pytest api/tests/ai_workflow_generator/test_templates.py -v
```

Test coverage includes:
- All example descriptions are well-formed
- Prompt templates can be formatted correctly
- Agent formatting produces valid output
- Error messages include helpful suggestions
- Explanation templates provide clear information
- Integration between different template types

## Best Practices

### When to Use Templates

1. **Use example descriptions** for:
   - Testing workflow generation
   - Demonstrating capabilities
   - Creating documentation examples

2. **Use prompt templates** for:
   - Consistent LLM interactions
   - Pattern-specific guidance
   - Workflow refinement

3. **Use agent formatting** for:
   - LLM prompts requiring agent context
   - User-facing agent information
   - Agent suggestions and recommendations

4. **Use error templates** for:
   - All error responses to users
   - Consistent error messaging
   - Helpful troubleshooting guidance

5. **Use explanation templates** for:
   - Workflow generation results
   - Modification explanations
   - Clarification responses

### Customization

Templates can be customized by:

1. **Adding new examples:**
```python
EXAMPLE_WORKFLOW_DESCRIPTIONS["my_custom_example"] = """
    Custom workflow description...
"""
```

2. **Creating new error templates:**
```python
class ErrorMessageTemplates:
    MY_CUSTOM_ERROR = """Custom error message...
    
    Suggestions:
    • Helpful suggestion 1
    • Helpful suggestion 2"""
```

3. **Extending explanation templates:**
```python
class ExplanationTemplates:
    @staticmethod
    def custom_explanation(param1, param2):
        return f"Custom explanation with {param1} and {param2}"
```

## Requirements Mapping

This module addresses the following requirements:

- **Requirement 1.1**: Natural language workflow generation
  - Provides prompt templates for LLM interactions
  - Includes example descriptions for testing

- **Requirement 3.3**: Workflow modification explanations
  - Explanation templates for changes
  - Clarification response templates

- **Requirement 4.4**: Agent suggestions with descriptions
  - Agent formatting templates
  - Agent suggestion templates

## Future Enhancements

Potential improvements:
1. Internationalization support for error messages
2. Template versioning for backward compatibility
3. Dynamic template loading from configuration
4. User-customizable templates
5. Template analytics and usage tracking

# Input Mapping Quick Reference

## Most Common Fields (Available from ALL A2A Agents)

| Field | Description | Example |
|-------|-------------|---------|
| `${step.output.text}` | Main text response | `"Hello! I can help you..."` |
| `${step.output.response}` | Agent response message | `"Task completed successfully"` |
| `${step.output.id}` | Response/task ID | `"task-abc123"` |
| `${step.output.status}` | Complete status object | `{"state": "completed", "timestamp": "..."}` |
| `${step.output.artifacts}` | Output artifacts array | `[{"parts": [{"kind": "text", "text": "..."}]}]` |
| `${step.output.metadata}` | Agent metadata | `{"author": "agent_name", "usage": {...}}` |

## Quick Syntax Guide

```json
{
  "basic_field": "${previous_step.output.text}",
  "nested_field": "${step1.output.status.state}",
  "workflow_input": "${workflow.input.user_query}",
  "multiple_fields": {
    "content": "${extract.output.text}",
    "metadata": "${extract.output.metadata}"
  }
}
```

## Debug Command

```bash
# See all available fields from latest run
python debug_step_output.py

# See fields from specific run
python debug_step_output.py run-abc123-def456
```

## Common Patterns

### Text Processing
```json
{
  "text_to_process": "${extract_text.output.text}",
  "operation": "summarize"
}
```

### Data Analysis
```json
{
  "data": "${fetch_data.output.text}",
  "analysis_type": "sentiment",
  "previous_results": "${analyze.output.response}"
}
```

### Multi-Step Chain
```json
{
  "research_findings": "${research.output.text}",
  "analysis_results": "${analyze.output.response}",
  "user_context": "${workflow.input.context}"
}
```

**💡 Tip:** Always use `.text` or `.response` if you're unsure - these fields are guaranteed to exist!
# Input Mapping Reference Guide

This guide documents all possible fields available for input mapping when working with A2A agents in LiteCone Studio.

## Overview

When an agent completes execution, its JSON-RPC 2.0 response is processed and all fields are made available for input mapping in subsequent workflow steps. You can reference any field from previous steps using the syntax: `${step_id.output.field_name}`

## Standard JSON-RPC 2.0 Response Fields

### Core Fields (Always Available)

These fields are extracted from every A2A agent response:

| Field | Type | Description | Example Usage |
|-------|------|-------------|---------------|
| `text` | string | Main text content from artifacts | `${step1.output.text}` |
| `response` | string | Agent's response message from history | `${step1.output.response}` |
| `id` | string | Task/response identifier | `${step1.output.id}` |
| `task_id` | string | Original task identifier | `${step1.output.task_id}` |
| `kind` | string | Response type (usually "task") | `${step1.output.kind}` |

### Status Information

| Field | Type | Description | Example Usage |
|-------|------|-------------|---------------|
| `status` | object | Complete status object | `${step1.output.status}` |
| `status.state` | string | Execution state ("completed", "failed") | `${step1.output.status.state}` |
| `status.timestamp` | string | ISO timestamp of completion | `${step1.output.status.timestamp}` |

### Structured Data Fields

| Field | Type | Description | Example Usage |
|-------|------|-------------|---------------|
| `artifacts` | array | Output artifacts from agent | `${step1.output.artifacts}` |
| `history` | array | Complete conversation history | `${step1.output.history}` |
| `metadata` | object | Agent-specific metadata | `${step1.output.metadata}` |

### Context Fields

| Field | Type | Description | Example Usage |
|-------|------|-------------|---------------|
| `context_id` | string | Session/context identifier | `${step1.output.context_id}` |
| `contextId` | string | Alternative context identifier | `${step1.output.contextId}` |

## Agent-Specific Fields

Different agents may return additional custom fields. Common examples:

### Data Processing Agents
```json
{
  "data": "Processed content here",
  "extracted_entities": [...],
  "confidence_score": 0.95,
  "processing_time_ms": 1250
}
```

**Usage:**
- `${step1.output.data}` - Main processed data
- `${step1.output.extracted_entities}` - Extracted entities
- `${step1.output.confidence_score}` - Confidence level
- `${step1.output.processing_time_ms}` - Processing time

### Research Agents
```json
{
  "findings": "Research results...",
  "sources": [...],
  "summary": "Brief summary...",
  "citations": [...]
}
```

**Usage:**
- `${research.output.findings}` - Main research findings
- `${research.output.sources}` - Source references
- `${research.output.summary}` - Research summary
- `${research.output.citations}` - Citation list

### Analysis Agents
```json
{
  "analysis_result": {...},
  "recommendations": [...],
  "risk_score": 0.3,
  "key_insights": [...]
}
```

**Usage:**
- `${analyze.output.analysis_result}` - Complete analysis
- `${analyze.output.recommendations}` - Recommendations
- `${analyze.output.risk_score}` - Risk assessment
- `${analyze.output.key_insights}` - Key insights

## Input Mapping Syntax

### Basic Field Access
```json
{
  "field_name": "${step_id.output.field_name}"
}
```

### Nested Field Access
```json
{
  "state": "${step1.output.status.state}",
  "timestamp": "${step1.output.status.timestamp}"
}
```

### Multiple Field Mapping
```json
{
  "main_content": "${step1.output.text}",
  "metadata": "${step1.output.metadata}",
  "artifacts": "${step1.output.artifacts}",
  "processing_info": {
    "task_id": "${step1.output.task_id}",
    "completion_time": "${step1.output.status.timestamp}"
  }
}
```

### Workflow Input References
```json
{
  "user_query": "${workflow.input.query}",
  "previous_result": "${step1.output.text}",
  "config": "${workflow.input.settings}"
}
```

## Common Patterns

### Text Processing Chain
```json
{
  "input_mapping": {
    "text_to_process": "${extract_text.output.text}",
    "operation": "summarize",
    "max_length": "${workflow.input.summary_length}"
  }
}
```

### Data Transformation
```json
{
  "input_mapping": {
    "raw_data": "${fetch_data.output.data}",
    "format": "json",
    "schema": "${workflow.input.output_schema}"
  }
}
```

### Multi-Step Analysis
```json
{
  "input_mapping": {
    "research_findings": "${research.output.findings}",
    "initial_analysis": "${analyze.output.analysis_result}",
    "context": "${workflow.input.context}"
  }
}
```

## Field Discovery

### Debugging Available Fields

To see what fields are available from a step, check the step execution output in the database:

```sql
SELECT jsonb_pretty(output_data) 
FROM step_executions 
WHERE step_id = 'your_step_id' 
ORDER BY started_at DESC 
LIMIT 1;
```

### Using the Debug Script

Use the provided debug script to inspect step outputs:

```bash
python debug_step_output.py [run_id]
```

This will show:
- All available fields
- Example input mapping syntax
- Field types and sample values

## Best Practices

### 1. Use Descriptive Field Names
```json
{
  "source_text": "${extract.output.text}",
  "extracted_data": "${extract.output.data}",
  "processing_metadata": "${extract.output.metadata}"
}
```

### 2. Handle Missing Fields Gracefully
Always check if a field exists before referencing it. The system will throw an error if you reference a non-existent field.

### 3. Prefer Standard Fields
When possible, use standard fields like `text` and `response` as they're available from all agents:

```json
{
  "content": "${step1.output.text}",
  "agent_response": "${step1.output.response}"
}
```

### 4. Document Custom Fields
If your agents return custom fields, document them for your team:

```json
// Custom fields from MyCustomAgent:
// - processed_data: Main output data
// - confidence: Processing confidence (0-1)
// - metadata.source: Original data source
{
  "data": "${process.output.processed_data}",
  "confidence": "${process.output.confidence}",
  "source": "${process.output.metadata.source}"
}
```

## Error Handling

### Common Errors

1. **Field Not Found**
   ```
   Cannot resolve '${step1.output.missing_field}' in field 'data': Field 'missing_field' not found
   ```
   **Solution:** Check available fields using the debug script

2. **Step Not Executed**
   ```
   Cannot resolve '${missing_step.output.text}': Step 'missing_step' has not been executed
   ```
   **Solution:** Ensure the referenced step exists and has completed

3. **Invalid Syntax**
   ```
   Invalid variable reference '${step1.missing.text}': Expected format ${step.output.field}
   ```
   **Solution:** Use correct syntax: `${step_id.output.field_name}`

## Examples by Agent Type

### Hello World Agent
```json
{
  "greeting": "${hello.output.text}",
  "task_info": "${hello.output.task_id}"
}
```

### PDF Processing Agent
```json
{
  "pdf_content": "${pdf_extract.output.text}",
  "page_count": "${pdf_extract.output.metadata.pages}",
  "extracted_tables": "${pdf_extract.output.artifacts}"
}
```

### Data Analysis Agent
```json
{
  "analysis": "${analyze.output.analysis_result}",
  "insights": "${analyze.output.key_insights}",
  "confidence": "${analyze.output.confidence_score}"
}
```

### Translation Agent
```json
{
  "translated_text": "${translate.output.text}",
  "source_language": "${translate.output.metadata.source_lang}",
  "target_language": "${translate.output.metadata.target_lang}"
}
```

## Advanced Usage

### Conditional Field Access
While not directly supported in input mapping, you can handle optional fields by checking in your agent logic.

### Array and Object Handling
Complex nested structures are preserved:

```json
{
  "full_artifacts": "${step1.output.artifacts}",
  "first_artifact": "${step1.output.artifacts[0]}",
  "metadata_keys": "${step1.output.metadata}"
}
```

### Loop Context Variables
When inside loops, additional context is available:

```json
{
  "current_item": "${loop.item}",
  "iteration_index": "${loop.index}",
  "total_items": "${loop.total}",
  "previous_result": "${process_item.output.text}"
}
```

## Troubleshooting

### 1. Check Step Completion
Ensure the referenced step completed successfully:
```bash
docker compose -f docker-compose.prod.standalone.yml logs execution-consumer | grep "step_complete"
```

### 2. Inspect Step Output
Use the debug script to see exactly what fields are available:
```bash
python debug_step_output.py
```

### 3. Validate Syntax
Ensure your input mapping uses the correct syntax:
- ✅ `${step_id.output.field_name}`
- ❌ `$.steps.step_id.output.field_name`
- ❌ `{step_id.output.field_name}`

### 4. Check Agent Response
If fields are missing, verify your agent is returning the expected JSON-RPC structure.

## Summary

LiteCone Studio preserves **all fields** from A2A agent responses, making them available for input mapping. The key is knowing what fields your specific agents return and using the correct syntax to reference them.

**Remember:** Use `${step_id.output.field_name}` syntax and always check available fields using the debug tools when in doubt.
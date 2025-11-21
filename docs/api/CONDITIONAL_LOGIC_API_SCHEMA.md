# Conditional Logic API Schema Updates

## Overview

This document describes the API schema updates to support conditional logic in workflow definitions.

## Changes Made

### Updated File
`api/schemas/workflow.py`

### New Schema: ConditionSchema

Added a new Pydantic model for condition expressions:

```python
class ConditionSchema(BaseModel):
    expression: str  # Required: The condition expression
    operator: Optional[str]  # Optional: Simple operator
```

### Updated Schema: WorkflowStepSchema

#### New Fields

**Type Field:**
- `type: Optional[str]` - Step type (default: "agent")
- Allowed values: "agent", "parallel", "conditional"

**Made Optional (for conditional steps):**
- `agent_name: Optional[str]` - Only required for type="agent"
- `input_mapping: Optional[Dict[str, Any]]` - Only required for type="agent"

**Conditional Step Fields:**
- `condition: Optional[ConditionSchema]` - Required for type="conditional"
- `if_true_step: Optional[str]` - Optional branch for true condition
- `if_false_step: Optional[str]` - Optional branch for false condition

**Parallel Step Fields (already existed):**
- `parallel_steps: Optional[list[str]]` - Required for type="parallel"
- `max_parallelism: Optional[int]` - Optional for type="parallel"

#### Validation Logic

Added `model_validator` to enforce type-specific requirements:

**For type="agent":**
- `agent_name` is required
- `input_mapping` is required

**For type="parallel":**
- `parallel_steps` is required (minimum 2 steps)
- `max_parallelism` must be >= 1 if specified

**For type="conditional":**
- `condition` is required
- At least one of `if_true_step` or `if_false_step` must be specified

### Updated Validation: Reachability Check

Updated `_validate_all_steps_reachable()` to use BFS (Breadth-First Search) instead of simple chain following:

**Now handles:**
- Sequential steps (next_step)
- Parallel steps (parallel_steps array)
- Conditional branches (if_true_step, if_false_step)

**Algorithm:**
1. Start from `start_step`
2. Visit each step and add its connections to the queue
3. For conditional steps, add both branches
4. For parallel steps, add all parallel step IDs
5. Mark all visited steps as reachable
6. Report any unreachable steps as validation errors

## API Request Format

### Creating a Workflow with Conditional Steps

```json
{
  "name": "Conditional Workflow Example",
  "description": "Workflow with conditional branching",
  "start_step": "step-1",
  "steps": {
    "step-1": {
      "id": "step-1",
      "type": "agent",
      "agent_name": "DataAnalyzer",
      "input_mapping": {
        "data": "${workflow.input.data}"
      },
      "next_step": "step-2"
    },
    "step-2": {
      "id": "step-2",
      "type": "conditional",
      "condition": {
        "expression": "${step-1.output.score} > 0.8"
      },
      "if_true_step": "step-3-high-score",
      "if_false_step": "step-4-low-score",
      "next_step": "step-5"
    },
    "step-3-high-score": {
      "id": "step-3-high-score",
      "type": "agent",
      "agent_name": "HighScoreProcessor",
      "input_mapping": {
        "data": "${step-1.output.data}"
      },
      "next_step": null
    },
    "step-4-low-score": {
      "id": "step-4-low-score",
      "type": "agent",
      "agent_name": "LowScoreProcessor",
      "input_mapping": {
        "data": "${step-1.output.data}"
      },
      "next_step": null
    },
    "step-5": {
      "id": "step-5",
      "type": "agent",
      "agent_name": "FinalProcessor",
      "input_mapping": {
        "result": "${step-2.output.branch_output}"
      },
      "next_step": null
    }
  }
}
```

## Validation Errors

### Before Fix

```json
{
  "error": "Validation Error",
  "errors": [
    {
      "field": "body.steps.step-2.agent_name",
      "message": "Field required",
      "type": "missing"
    },
    {
      "field": "body.steps.step-2.input_mapping",
      "message": "Field required",
      "type": "missing"
    }
  ]
}
```

### After Fix

Conditional steps no longer require `agent_name` or `input_mapping`. The API correctly validates based on step type.

## Error Messages

### Type-Specific Validation Errors

**Missing agent_name for agent step:**
```
agent_name is required for step type 'agent' (step: step-1)
```

**Missing input_mapping for agent step:**
```
input_mapping is required for step type 'agent' (step: step-1)
```

**Missing condition for conditional step:**
```
condition is required for step type 'conditional' (step: step-2)
```

**Missing branches for conditional step:**
```
At least one of if_true_step or if_false_step must be specified for step type 'conditional' (step: step-2)
```

**Invalid parallel_steps:**
```
parallel_steps must contain at least 2 steps (step: parallel-block)
```

## Backward Compatibility

The changes are **backward compatible**:

1. **Default type:** Steps without a `type` field default to "agent"
2. **Existing workflows:** All existing agent-based workflows continue to work
3. **Validation:** Agent steps still require `agent_name` and `input_mapping`

## Testing

### Test Cases

1. **Valid conditional workflow** - Should pass validation
2. **Conditional without condition** - Should fail with clear error
3. **Conditional without branches** - Should fail with clear error
4. **Agent without agent_name** - Should fail with clear error
5. **Mixed step types** - Should validate each type correctly
6. **Unreachable conditional branches** - Should detect and report

### Manual Testing

```bash
# Test creating a conditional workflow
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @examples/conditional_workflow_example.json
```

## Deployment

### Prerequisites

1. Update API service with new schema
2. Restart API service
3. Test with example workflows

### Verification

```bash
# Verify API accepts conditional workflows
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-conditional",
    "start_step": "check",
    "steps": {
      "check": {
        "id": "check",
        "type": "conditional",
        "condition": {"expression": "true"},
        "if_true_step": "success",
        "next_step": null
      },
      "success": {
        "id": "success",
        "type": "agent",
        "agent_name": "TestAgent",
        "input_mapping": {},
        "next_step": null
      }
    }
  }'
```

## Related Documentation

- [Conditional Logic Backend](../docs/conditional_logic.md)
- [Conditional Logic UI](../workflow-ui/CONDITIONAL_LOGIC_UI.md)
- [Workflow Format Specification](../WORKFLOW_FORMAT.md)
- [API Documentation](../API_DOCUMENTATION.md)

## Summary

The API schema now fully supports conditional logic with:
- ✅ Type-based validation
- ✅ Conditional step fields
- ✅ Branch reachability checking
- ✅ Clear error messages
- ✅ Backward compatibility
- ✅ Complete validation coverage

Workflows with conditional steps can now be created, updated, and validated through the API without errors.

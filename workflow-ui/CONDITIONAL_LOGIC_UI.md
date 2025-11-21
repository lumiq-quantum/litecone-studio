# Conditional Logic UI Support

## Overview

This document describes the frontend updates to support conditional logic in workflow definitions.

## Changes Made

### 1. Type Definitions (`src/types/workflow.ts`)

Added support for conditional step types:

```typescript
export interface Condition {
  expression: string;
  operator?: string;
}

export interface WorkflowStep {
  // ... existing fields
  type?: 'agent' | 'parallel' | 'conditional';
  condition?: Condition;
  if_true_step?: string;
  if_false_step?: string;
}
```

### 2. Validation Library (`src/lib/validation.ts`)

Updated `validateWorkflowDefinition()` to handle conditional steps:

- Validates `condition` object with `expression` field
- Ensures at least one of `if_true_step` or `if_false_step` is specified
- Skips `agent_name` and `input_mapping` validation for conditional steps

### 3. JSON Editor (`src/components/common/JSONEditor.tsx`)

#### Monaco Schema Updates

Added conditional step type to the enum:
```typescript
enum: ['agent', 'parallel', 'conditional']
```

Added conditional step properties to the schema:
- `condition`: Object with `expression` (required) and `operator` (optional)
- `if_true_step`: String reference to branch step
- `if_false_step`: String reference to branch step

#### Validation Logic

Added conditional step validation:
- Checks for required `condition` object with `expression`
- Validates at least one branch is specified
- Validates branch step references exist
- Skips agent-specific validation for conditional steps

## Usage

### Creating a Conditional Step

In the JSON editor, define a conditional step:

```json
{
  "check-score": {
    "id": "check-score",
    "type": "conditional",
    "condition": {
      "expression": "${analyze.output.score} > 0.8"
    },
    "if_true_step": "high-quality-process",
    "if_false_step": "low-quality-process",
    "next_step": "finalize"
  }
}
```

### Validation

The editor will validate:
- ✅ Condition object is present
- ✅ Expression is not empty
- ✅ At least one branch is specified
- ✅ Branch steps exist in the workflow
- ✅ No circular dependencies

### Error Messages

Common validation errors:
- "Conditional step 'X' is missing required field: condition (object)"
- "Conditional step 'X' condition is missing required field: expression"
- "Conditional step 'X' must have at least one of if_true_step or if_false_step"
- "Conditional step 'X' references non-existent if_true_step: 'Y'"

## Visual Graph Support

The workflow graph visualization will need to be updated to display conditional steps with:
- Diamond shape for conditional nodes
- Two outgoing edges labeled "true" and "false"
- Different colors for condition evaluation paths

**Note**: Graph visualization updates are not included in this implementation and should be added separately.

## Auto-completion

The Monaco editor provides:
- Syntax highlighting for JSON
- Auto-completion for step types
- Validation as you type
- Error highlighting with hover tooltips

## Testing

Test the conditional logic UI by:

1. Creating a new workflow
2. Adding a conditional step with the JSON editor
3. Verifying validation works correctly
4. Saving and executing the workflow
5. Checking that branch execution is tracked

## Example Workflow

See `examples/conditional_workflow_example.json` for a complete example of a workflow with conditional logic.

## Future Enhancements

Potential UI improvements:
- Visual conditional step builder (form-based)
- Expression builder with syntax help
- Condition testing/preview
- Branch execution visualization in run details
- Conditional step icon in graph view

## Related Documentation

- [Conditional Logic Backend](../docs/conditional_logic.md)
- [Workflow Format Specification](../WORKFLOW_FORMAT.md)
- [Implementation Summary](../CONDITIONAL_LOGIC_IMPLEMENTATION.md)

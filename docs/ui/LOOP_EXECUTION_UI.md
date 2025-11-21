# Loop Execution UI Support

## Overview

The workflow UI now supports visualizing and editing loop execution steps. This document describes the UI enhancements for loop functionality.

## Features

### 1. Type Definitions (`src/types/workflow.ts`)

Added `LoopConfig` interface and extended `WorkflowStep` to support loop steps:

```typescript
export interface LoopConfig {
  collection: string;
  loop_body: string[];
  execution_mode?: 'sequential' | 'parallel';
  max_parallelism?: number;
  max_iterations?: number;
  on_error?: 'stop' | 'continue' | 'collect';
}

export interface WorkflowStep {
  // ... existing fields
  loop_config?: LoopConfig; // For type='loop'
}
```

### 2. JSON Editor Validation (`src/components/common/JSONEditor.tsx`)

The Monaco editor now validates loop steps with:

- **Schema validation** for loop_config structure
- **Required fields**: `collection` and `loop_body`
- **Enum validation** for `execution_mode` and `on_error`
- **Numeric validation** for `max_parallelism` and `max_iterations`
- **Reference validation** for loop_body step IDs

#### Validation Rules

- `collection`: Must be a non-empty string (variable reference)
- `loop_body`: Must be an array with at least 1 step ID
- `execution_mode`: Must be 'sequential' or 'parallel' (optional)
- `max_parallelism`: Must be a number >= 1 (optional)
- `max_iterations`: Must be a number >= 1 (optional)
- `on_error`: Must be 'stop', 'continue', or 'collect' (optional)

### 3. Workflow Graph Visualization (`src/components/workflows/WorkflowGraph.tsx`)

Loop steps are visualized with:

- **Orange dashed edges** connecting loop block to loop body steps
- **Automatic layout** positioning loop body steps relative to loop block
- **Display name** showing execution mode: "Loop (sequential)" or "Loop (parallel)"

#### Edge Styling

```typescript
{
  stroke: '#f59e0b',        // Orange color
  strokeWidth: 2,
  strokeDasharray: '8,4',   // Dashed pattern
}
```

### 4. Step Node Component (`src/components/workflows/WorkflowStepNode.tsx`)

Loop steps display with:

- **RotateCw icon** (circular arrow) in orange
- **Loop indicator** (↻) prefix in step name
- **Execution mode** shown in display name

## Usage Examples

### Creating a Loop Step in UI

```json
{
  "step-2": {
    "id": "step-2",
    "type": "loop",
    "loop_config": {
      "collection": "${step-1.output.items}",
      "loop_body": ["step-2-process"],
      "execution_mode": "parallel",
      "max_parallelism": 5,
      "on_error": "continue"
    },
    "next_step": "step-3"
  }
}
```

### Visual Representation

```
┌─────────────┐
│  step-1     │
│  DataFetch  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  step-2         │
│  Loop (parallel)│  ← Orange RotateCw icon
└──────┬──────────┘
       │ (orange dashed)
       ▼
┌─────────────────┐
│  step-2-process │
│  ItemProcessor  │
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│  step-3     │
│  Aggregator │
└─────────────┘
```

## Validation Errors

The editor will show validation errors for:

1. **Missing required fields**:
   - "Loop step 'step-2' loop_config is missing required field: collection"
   - "Loop step 'step-2' loop_config is missing required field: loop_body (array)"

2. **Invalid values**:
   - "Loop step 'step-2' has invalid execution_mode (must be 'sequential' or 'parallel')"
   - "Loop step 'step-2' has invalid max_parallelism (must be a number >= 1)"

3. **Invalid references**:
   - "Loop step 'step-2' references non-existent loop_body step: 'step-99'"

## Monaco Editor Autocomplete

The editor provides autocomplete for:

- Step types: `"agent"`, `"parallel"`, `"conditional"`, `"loop"`
- Execution modes: `"sequential"`, `"parallel"`
- Error policies: `"stop"`, `"continue"`, `"collect"`

## Color Scheme

- **Loop edges**: Orange (#f59e0b)
- **Loop icon**: Orange (text-orange-600)
- **Loop indicator**: ↻ symbol in orange

This matches the existing color scheme:
- Parallel: Purple (#8b5cf6)
- Conditional: Green/Red (#10b981/#ef4444)
- Agent: Gray (#6b7280)

## Testing

To test loop visualization:

1. Create a workflow with a loop step
2. Verify the loop icon appears (RotateCw)
3. Verify orange dashed edges to loop body steps
4. Verify display name shows execution mode
5. Test validation with invalid configurations

## Future Enhancements

Potential UI improvements:

1. **Loop context preview**: Show loop.item, loop.index in tooltips
2. **Iteration count display**: Show max_iterations in node
3. **Error policy indicator**: Visual indicator for on_error setting
4. **Loop body grouping**: Visual grouping of loop body steps
5. **Execution mode toggle**: Quick toggle between sequential/parallel

## See Also

- [Loop Execution Documentation](../docs/loop_execution.md)
- [Workflow Format Specification](../WORKFLOW_FORMAT.md)
- [Parallel Execution UI](PARALLEL_EXECUTION_UI.md)
- [Conditional Logic UI](CONDITIONAL_LOGIC_UI.md)

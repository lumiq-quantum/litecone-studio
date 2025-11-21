# Parallel Execution in Workflow UI

## Overview

The Workflow UI now supports creating and visualizing workflows with parallel execution. This document explains how to use parallel execution features in the UI.

## Creating Parallel Workflows

### Using the JSON Editor

1. **Navigate to Workflows** → Click "Create Workflow"
2. **Switch to JSON Editor** tab
3. **Define a parallel step**:

```json
{
  "workflow_id": "my-parallel-workflow",
  "name": "Parallel Data Processing",
  "version": "1.0",
  "start_step": "parallel-block-1",
  "steps": {
    "parallel-block-1": {
      "id": "parallel-block-1",
      "type": "parallel",
      "parallel_steps": ["step-a", "step-b", "step-c"],
      "max_parallelism": 2,
      "next_step": "final-step"
    },
    "step-a": {
      "id": "step-a",
      "type": "agent",
      "agent_name": "AgentA",
      "input_mapping": {
        "input": "${workflow.input.data}"
      },
      "next_step": null
    },
    "step-b": {
      "id": "step-b",
      "type": "agent",
      "agent_name": "AgentB",
      "input_mapping": {
        "input": "${workflow.input.data}"
      },
      "next_step": null
    },
    "step-c": {
      "id": "step-c",
      "type": "agent",
      "agent_name": "AgentC",
      "input_mapping": {
        "input": "${workflow.input.data}"
      },
      "next_step": null
    },
    "final-step": {
      "id": "final-step",
      "type": "agent",
      "agent_name": "Aggregator",
      "input_mapping": {
        "result_a": "${step-a.output}",
        "result_b": "${step-b.output}",
        "result_c": "${step-c.output}"
      },
      "next_step": null
    }
  }
}
```

### Key Fields for Parallel Steps

- **`type`**: Must be `"parallel"`
- **`parallel_steps`**: Array of step IDs to execute concurrently
- **`max_parallelism`** (optional): Limit concurrent executions (e.g., `2` means max 2 steps run at once)
- **`next_step`**: Step to execute after all parallel steps complete

### Validation

The JSON editor will validate your parallel workflow:

✅ **Valid**:
- `type` is `"parallel"`
- `parallel_steps` is an array with at least 2 step IDs
- All referenced step IDs exist in the workflow
- Parallel steps have `next_step: null` (they don't chain)

❌ **Invalid**:
- Missing `parallel_steps` field
- Empty `parallel_steps` array
- Referenced steps don't exist
- Circular dependencies

## Visual Representation

### In the Workflow Graph

Parallel steps are displayed in the visual graph:

```
┌─────────────────┐
│ parallel-block  │
│   (parallel)    │
└────────┬────────┘
         │
    ┌────┴────┬────────┐
    │         │        │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐
│step-a │ │step-b│ │step-c│
└───┬───┘ └──┬───┘ └──┬───┘
    │        │        │
    └────┬───┴────┬───┘
         │        │
    ┌────▼────────▼───┐
    │   final-step    │
    └─────────────────┘
```

### Visual Indicators

- **Parallel Block Node**: Displayed with a special icon/color
- **Parallel Steps**: Grouped visually under the parallel block
- **Concurrent Execution**: During execution, multiple steps show "running" status simultaneously

## Monitoring Parallel Execution

### In the Runs View

1. **Navigate to Runs** → Select a run with parallel execution
2. **View Execution Graph**: Parallel steps are displayed side-by-side
3. **Real-time Status**: Watch multiple steps execute concurrently

### Status Indicators

- 🔵 **Pending**: Step waiting to start
- 🟡 **Running**: Step currently executing (multiple can be running)
- 🟢 **Completed**: Step finished successfully
- 🔴 **Failed**: Step failed

### Execution Timeline

The execution graph shows:
- Which steps ran in parallel
- How long each step took
- Which steps were limited by `max_parallelism`

## Example Use Cases

### 1. Parallel Data Fetching

Fetch data from multiple APIs concurrently:

```json
{
  "parallel-fetch": {
    "type": "parallel",
    "parallel_steps": ["fetch-weather", "fetch-news", "fetch-stocks"],
    "max_parallelism": 3
  }
}
```

### 2. Parallel Processing with Limit

Process items with a concurrency limit:

```json
{
  "parallel-process": {
    "type": "parallel",
    "parallel_steps": ["process-1", "process-2", "process-3", "process-4"],
    "max_parallelism": 2
  }
}
```

Only 2 steps run at a time, preventing resource overload.

### 3. Fan-Out / Fan-In Pattern

Distribute work, then aggregate results:

```json
{
  "steps": {
    "fan-out": {
      "type": "parallel",
      "parallel_steps": ["worker-1", "worker-2", "worker-3"],
      "next_step": "fan-in"
    },
    "fan-in": {
      "type": "agent",
      "agent_name": "Aggregator",
      "input_mapping": {
        "results": [
          "${worker-1.output}",
          "${worker-2.output}",
          "${worker-3.output}"
        ]
      }
    }
  }
}
```

## Best Practices

### 1. Use Meaningful Step IDs

```json
// Good
"parallel_steps": ["fetch-user-data", "fetch-product-data", "fetch-order-data"]

// Avoid
"parallel_steps": ["step1", "step2", "step3"]
```

### 2. Set Appropriate Parallelism Limits

```json
// For I/O-bound tasks (API calls)
"max_parallelism": 5

// For CPU-intensive tasks
"max_parallelism": 2

// For unlimited (use with caution)
"max_parallelism": null
```

### 3. Handle Partial Failures

Design your aggregation step to handle cases where some parallel steps fail:

```json
{
  "aggregate": {
    "agent_name": "RobustAggregator",
    "input_mapping": {
      "results": {
        "step_a": "${step-a.output}",
        "step_b": "${step-b.output}",
        "step_c": "${step-c.output}"
      }
    }
  }
}
```

### 4. Keep Parallel Steps Independent

Parallel steps should not depend on each other's outputs. If they do, use sequential steps instead.

## Troubleshooting

### Issue: Parallel steps not executing concurrently

**Possible Causes**:
- `max_parallelism` is set to 1
- Backend executor not updated
- Database migration not applied

**Solution**:
- Check `max_parallelism` value
- Verify backend is running latest version
- Run database migration

### Issue: Validation error on parallel step

**Possible Causes**:
- Missing `parallel_steps` field
- Invalid step references
- Wrong `type` value

**Solution**:
- Check JSON editor validation errors
- Ensure all referenced steps exist
- Verify `type: "parallel"`

### Issue: Graph doesn't show parallel structure

**Possible Causes**:
- UI not updated
- Invalid workflow definition
- Browser cache

**Solution**:
- Refresh the page
- Clear browser cache
- Check browser console for errors

## Performance Considerations

### When to Use Parallel Execution

✅ **Good Use Cases**:
- Fetching data from multiple independent sources
- Processing independent items in a collection
- Calling multiple external APIs
- I/O-bound operations

❌ **Avoid For**:
- Steps that depend on each other
- Very fast operations (overhead not worth it)
- Resource-intensive operations without limits

### Monitoring Performance

Track these metrics:
- **Total execution time**: Should be less than sequential
- **Concurrent steps**: How many ran simultaneously
- **Resource usage**: CPU, memory, database connections

## UI Components

### Workflow Editor

The workflow editor provides:
- ✅ Syntax highlighting for parallel steps
- ✅ Autocomplete for `type: "parallel"`
- ✅ Validation for parallel step structure
- ✅ Visual preview of parallel execution

### Execution Graph

The execution graph shows:
- ✅ Parallel steps grouped visually
- ✅ Real-time status updates
- ✅ Execution timeline
- ✅ Step details on click

## Future UI Enhancements

Planned improvements:
- 🔮 Drag-and-drop parallel step creation
- 🔮 Visual parallel block editor
- 🔮 Performance metrics dashboard
- 🔮 Parallel execution templates

## Support

For issues or questions:
- Check validation errors in JSON editor
- Review backend logs for execution issues
- See [docs/parallel_execution.md](../docs/parallel_execution.md) for backend details
- Check [WORKFLOW_FORMAT.md](../WORKFLOW_FORMAT.md) for schema reference

## Related Documentation

- [Parallel Execution Backend](../docs/parallel_execution.md)
- [Workflow Format Specification](../WORKFLOW_FORMAT.md)
- [Workflow Visualizer Implementation](./WORKFLOW_VISUALIZER_IMPLEMENTATION.md)
- [UI README](./README.md)

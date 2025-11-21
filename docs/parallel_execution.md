# Parallel Execution

## Overview

The Parallel Execution feature allows multiple workflow steps to execute concurrently, improving performance for independent operations.

## Features

- **Concurrent Execution**: Execute multiple steps simultaneously using asyncio
- **Concurrency Control**: Limit the number of concurrent executions with `max_parallelism`
- **Result Aggregation**: Collect and aggregate outputs from all parallel steps
- **Partial Failure Handling**: Continue executing all steps even if some fail
- **Monitoring**: Track execution status of each parallel step

## Workflow Definition

To use parallel execution, define a step with `type: "parallel"`:

```json
{
  "id": "parallel-block-1",
  "type": "parallel",
  "parallel_steps": ["step-a", "step-b", "step-c"],
  "max_parallelism": 2,
  "next_step": "next-step"
}
```

### Fields

- **id**: Unique identifier for the parallel block
- **type**: Must be `"parallel"`
- **parallel_steps**: Array of step IDs to execute in parallel
- **max_parallelism** (optional): Maximum number of concurrent executions (default: unlimited)
- **next_step**: ID of the step to execute after all parallel steps complete

## Example

See `examples/parallel_workflow_example.json` for a complete example.

### Workflow Structure

```
parallel-block-1 (parallel)
├── step-a (agent)
├── step-b (agent)
└── step-c (agent)
↓
final-step (agent) - receives outputs from all parallel steps
```

## Output Aggregation

The parallel block aggregates outputs from all steps into a single result:

```json
{
  "step-a": { "result": "..." },
  "step-b": { "result": "..." },
  "step-c": { "result": "..." }
}
```

Subsequent steps can reference individual outputs:
- `${step-a.output.result}`
- `${step-b.output.result}`
- `${step-c.output.result}`

## Error Handling

- If any parallel step fails, the parallel block is marked as FAILED
- All parallel steps continue executing even if one fails
- Failed steps are logged with error details
- The workflow can handle failures in subsequent steps

## Performance Considerations

- **max_parallelism**: Use this to prevent overwhelming downstream services
- **Resource Usage**: Each parallel step consumes resources (memory, connections)
- **Database Connections**: Ensure your database pool can handle concurrent queries

## Database Schema

Parallel execution tracking columns in `step_executions` table:

- **parent_step_id**: ID of the parallel block
- **branch_name**: Branch name (for fork-join patterns)
- **join_policy**: Join policy (for fork-join patterns)

## Requirements Satisfied

- 1.1: Execute independent steps concurrently
- 1.2: Publish all agent tasks simultaneously
- 1.3: Collect results from all steps before proceeding
- 1.4: Wait for all parallel steps even if one fails
- 1.5: Aggregate outputs and make available to subsequent steps
- 1.7: Limit concurrent execution with max_parallelism

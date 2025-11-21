# Loop Execution

## Overview

Loop execution allows workflows to iterate over collections of data, executing a set of steps for each item. This feature supports both sequential and parallel execution modes, with configurable error handling policies.

## Features

- **Sequential Execution**: Process items one at a time in order
- **Parallel Execution**: Process multiple items concurrently with configurable parallelism limits
- **Error Handling**: Choose how to handle failures (stop, continue, or collect errors)
- **Iteration Limits**: Set maximum number of iterations to process
- **Loop Context**: Access current item, index, and other iteration metadata

## Loop Step Configuration

### Basic Structure

```json
{
  "step-id": {
    "id": "step-id",
    "type": "loop",
    "loop_config": {
      "collection": "${step-0.output.items}",
      "loop_body": ["step-process"],
      "execution_mode": "sequential",
      "max_iterations": 100,
      "on_error": "continue"
    },
    "next_step": "next-step-id"
  }
}
```

### Configuration Fields

- **collection** (required): Variable reference to the collection to iterate over
  - Format: `${step-id.output.field}` or `${workflow.input.field}`
  - Must resolve to a list/array

- **loop_body** (required): Array of step IDs to execute for each iteration
  - Steps execute sequentially within each iteration
  - Can reference loop context variables

- **execution_mode** (optional): How to execute iterations
  - `"sequential"`: One at a time (default)
  - `"parallel"`: All at once or with max_parallelism limit

- **max_parallelism** (optional): Maximum concurrent iterations (parallel mode only)
  - Must be >= 1
  - Limits resource usage

- **max_iterations** (optional): Maximum number of items to process
  - Useful for limiting large collections
  - Processes first N items only

- **on_error** (optional): Error handling policy
  - `"stop"`: Stop immediately on first error (default)
  - `"continue"`: Continue with remaining iterations, collect errors
  - `"collect"`: Complete all iterations, report errors at end

## Loop Context Variables

Within loop body steps, you can access iteration context:

- `${loop.item}`: Current item from the collection
- `${loop.index}`: Current iteration index (0-based)
- `${loop.total}`: Total number of items in collection
- `${loop.is_first}`: Boolean, true if first iteration
- `${loop.is_last}`: Boolean, true if last iteration

### Example Usage

```json
{
  "step-process": {
    "id": "step-process",
    "type": "agent",
    "agent_name": "ItemProcessor",
    "input_mapping": {
      "item": "${loop.item}",
      "index": "${loop.index}",
      "total": "${loop.total}"
    }
  }
}
```

## Execution Modes

### Sequential Execution

Processes items one at a time in order. Best for:
- Order-dependent processing
- Resource-constrained environments
- Debugging and testing

```json
{
  "loop_config": {
    "collection": "${step-1.output.items}",
    "loop_body": ["process-step"],
    "execution_mode": "sequential"
  }
}
```

### Parallel Execution

Processes multiple items concurrently. Best for:
- Independent item processing
- High-throughput requirements
- I/O-bound operations

```json
{
  "loop_config": {
    "collection": "${step-1.output.items}",
    "loop_body": ["process-step"],
    "execution_mode": "parallel",
    "max_parallelism": 10
  }
}
```

## Error Handling Policies

### Stop (Default)

Stops immediately on first error. Best for:
- Critical processing where any failure is unacceptable
- Fail-fast scenarios

```json
{
  "loop_config": {
    "on_error": "stop"
  }
}
```

### Continue

Continues with remaining iterations, logs errors. Best for:
- Best-effort processing
- When some failures are acceptable

```json
{
  "loop_config": {
    "on_error": "continue"
  }
}
```

### Collect

Completes all iterations, reports all errors at end. Best for:
- Batch processing
- When you need complete error reporting

```json
{
  "loop_config": {
    "on_error": "collect"
  }
}
```

## Complete Examples

### Sequential Loop Example

```json
{
  "workflow_id": "sequential-loop",
  "name": "Sequential Loop Example",
  "version": "1.0",
  "start_step": "fetch-data",
  "steps": {
    "fetch-data": {
      "id": "fetch-data",
      "type": "agent",
      "agent_name": "DataFetcher",
      "input_mapping": {
        "source": "${workflow.input.source}"
      },
      "next_step": "process-loop"
    },
    "process-loop": {
      "id": "process-loop",
      "type": "loop",
      "loop_config": {
        "collection": "${fetch-data.output.items}",
        "loop_body": ["process-item"],
        "execution_mode": "sequential",
        "on_error": "continue"
      },
      "next_step": "aggregate"
    },
    "process-item": {
      "id": "process-item",
      "type": "agent",
      "agent_name": "ItemProcessor",
      "input_mapping": {
        "item": "${loop.item}",
        "index": "${loop.index}"
      },
      "next_step": null
    },
    "aggregate": {
      "id": "aggregate",
      "type": "agent",
      "agent_name": "Aggregator",
      "input_mapping": {
        "results": "${process-loop.output.iterations}"
      },
      "next_step": null
    }
  }
}
```

### Parallel Loop Example

```json
{
  "workflow_id": "parallel-loop",
  "name": "Parallel Loop Example",
  "version": "1.0",
  "start_step": "fetch-data",
  "steps": {
    "fetch-data": {
      "id": "fetch-data",
      "type": "agent",
      "agent_name": "DataFetcher",
      "input_mapping": {
        "source": "${workflow.input.source}"
      },
      "next_step": "process-loop"
    },
    "process-loop": {
      "id": "process-loop",
      "type": "loop",
      "loop_config": {
        "collection": "${fetch-data.output.items}",
        "loop_body": ["process-item"],
        "execution_mode": "parallel",
        "max_parallelism": 5,
        "max_iterations": 100,
        "on_error": "collect"
      },
      "next_step": "aggregate"
    },
    "process-item": {
      "id": "process-item",
      "type": "agent",
      "agent_name": "ItemProcessor",
      "input_mapping": {
        "item": "${loop.item}",
        "index": "${loop.index}"
      },
      "next_step": null
    },
    "aggregate": {
      "id": "aggregate",
      "type": "agent",
      "agent_name": "Aggregator",
      "input_mapping": {
        "results": "${process-loop.output.iterations}",
        "total": "${process-loop.output.total_count}"
      },
      "next_step": null
    }
  }
}
```

## Output Format

Loop steps produce output with the following structure:

```json
{
  "iterations": [
    {
      "step_id": "process-item",
      "status": "COMPLETED",
      "output_data": { ... }
    },
    ...
  ],
  "total_count": 10,
  "failed_count": 0
}
```

- **iterations**: Array of results from each iteration
- **total_count**: Total number of iterations executed
- **failed_count**: Number of failed iterations (if any)

## Best Practices

1. **Use Sequential for Order-Dependent Processing**
   - When items must be processed in order
   - When later items depend on earlier results

2. **Use Parallel for Independent Items**
   - When items can be processed independently
   - When throughput is more important than order

3. **Set Reasonable Parallelism Limits**
   - Consider downstream system capacity
   - Balance throughput vs resource usage

4. **Use max_iterations for Large Collections**
   - Prevent runaway processing
   - Test with small subsets first

5. **Choose Appropriate Error Policy**
   - Use "stop" for critical processing
   - Use "continue" for best-effort scenarios
   - Use "collect" when you need complete error reporting

6. **Monitor Loop Performance**
   - Track iteration times
   - Watch for bottlenecks
   - Adjust parallelism as needed

## Limitations

- Loop body steps cannot reference other loop iterations
- Nested loops are supported but should be used carefully
- Very large collections may impact performance
- Parallel execution requires sufficient system resources

## See Also

- [Parallel Execution](parallel_execution.md)
- [Conditional Logic](conditional_logic.md)
- [Workflow Format](../WORKFLOW_FORMAT.md)

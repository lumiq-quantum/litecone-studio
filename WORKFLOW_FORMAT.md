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
  "type": "agent | parallel",
  "agent_name": "string",
  "next_step": "string | null",
  "input_mapping": {
    "field_name": "string"
  },
  "parallel_steps": ["string"],
  "max_parallelism": "number"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for this step (must match key in steps map) |
| `type` | string | No | Step type: `"agent"` (default) or `"parallel"` |
| `agent_name` | string | Conditional | Name of the agent to invoke (required for type="agent") |
| `next_step` | string or null | Yes | ID of the next step to execute, or null if this is the final step |
| `input_mapping` | object | Conditional | Map of input field names to value expressions (required for type="agent") |
| `parallel_steps` | array | Conditional | Array of step IDs to execute in parallel (required for type="parallel") |
| `max_parallelism` | number | No | Maximum concurrent executions (for type="parallel") |

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

## Advanced Features

### Parallel Execution ✅ AVAILABLE

Execute multiple independent steps concurrently for improved performance.

**Step Type**: `parallel`

```json
{
  "id": "parallel-block-1",
  "type": "parallel",
  "parallel_steps": ["step-a", "step-b", "step-c"],
  "max_parallelism": 2,
  "next_step": "next-step"
}
```

**Fields**:
- `type`: Must be `"parallel"`
- `parallel_steps`: Array of step IDs to execute concurrently
- `max_parallelism` (optional): Maximum number of concurrent executions
- `next_step`: Step to execute after all parallel steps complete

**Example**:
```json
{
  "workflow_id": "parallel-example",
  "name": "Parallel Data Processing",
  "version": "1.0",
  "start_step": "parallel-fetch",
  "steps": {
    "parallel-fetch": {
      "id": "parallel-fetch",
      "type": "parallel",
      "parallel_steps": ["fetch-api-1", "fetch-api-2", "fetch-api-3"],
      "max_parallelism": 2,
      "next_step": "aggregate"
    },
    "fetch-api-1": {
      "id": "fetch-api-1",
      "type": "agent",
      "agent_name": "DataFetcher",
      "input_mapping": {
        "url": "${workflow.input.api1_url}"
      },
      "next_step": null
    },
    "fetch-api-2": {
      "id": "fetch-api-2",
      "type": "agent",
      "agent_name": "DataFetcher",
      "input_mapping": {
        "url": "${workflow.input.api2_url}"
      },
      "next_step": null
    },
    "fetch-api-3": {
      "id": "fetch-api-3",
      "type": "agent",
      "agent_name": "DataFetcher",
      "input_mapping": {
        "url": "${workflow.input.api3_url}"
      },
      "next_step": null
    },
    "aggregate": {
      "id": "aggregate",
      "type": "agent",
      "agent_name": "DataAggregator",
      "input_mapping": {
        "data1": "${fetch-api-1.output}",
        "data2": "${fetch-api-2.output}",
        "data3": "${fetch-api-3.output}"
      },
      "next_step": null
    }
  }
}
```

**Output Aggregation**: Parallel steps' outputs are aggregated and available to subsequent steps using standard step output references.

**Error Handling**: If any parallel step fails, the parallel block is marked as FAILED, but all steps continue executing to completion.

See [docs/parallel_execution.md](docs/parallel_execution.md) for detailed documentation.

### Conditional Execution ✅ AVAILABLE

Execute different steps based on runtime conditions for dynamic workflow branching.

**Step Type**: `conditional`

```json
{
  "id": "conditional-step",
  "type": "conditional",
  "condition": {
    "expression": "${step-1.output.score} > 0.8"
  },
  "if_true_step": "high-score-handler",
  "if_false_step": "low-score-handler",
  "next_step": "final-step"
}
```

**Fields**:
- `type`: Must be `"conditional"`
- `condition`: Object containing the condition expression
  - `expression`: The condition to evaluate (required)
- `if_true_step` (optional): Step ID to execute if condition is true
- `if_false_step` (optional): Step ID to execute if condition is false
- `next_step`: Step to execute after the conditional branch completes

**Supported Operators**:
- Comparison: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `and`, `or`, `not`
- Membership: `in`, `not in`, `contains`

**Example**:
```json
{
  "workflow_id": "conditional-example",
  "name": "Score-Based Routing",
  "version": "1.0",
  "start_step": "analyze",
  "steps": {
    "analyze": {
      "id": "analyze",
      "type": "agent",
      "agent_name": "DataAnalyzer",
      "input_mapping": {
        "data": "${workflow.input.data}"
      },
      "next_step": "check-score"
    },
    "check-score": {
      "id": "check-score",
      "type": "conditional",
      "condition": {
        "expression": "${analyze.output.score} > 0.8"
      },
      "if_true_step": "high-quality-process",
      "if_false_step": "low-quality-process",
      "next_step": "finalize"
    },
    "high-quality-process": {
      "id": "high-quality-process",
      "type": "agent",
      "agent_name": "HighQualityProcessor",
      "input_mapping": {
        "data": "${analyze.output.data}"
      },
      "next_step": null
    },
    "low-quality-process": {
      "id": "low-quality-process",
      "type": "agent",
      "agent_name": "LowQualityProcessor",
      "input_mapping": {
        "data": "${analyze.output.data}"
      },
      "next_step": null
    },
    "finalize": {
      "id": "finalize",
      "type": "agent",
      "agent_name": "Finalizer",
      "input_mapping": {
        "result": "${check-score.output.branch_output}"
      },
      "next_step": null
    }
  }
}
```

See [docs/conditional_logic.md](docs/conditional_logic.md) for detailed documentation.

### Loop Execution ✅ AVAILABLE

Iterate over collections of data, executing steps for each item with support for sequential or parallel execution.

**Step Type**: `loop`

```json
{
  "id": "loop-step",
  "type": "loop",
  "loop_config": {
    "collection": "${step-1.output.items}",
    "loop_body": ["process-item"],
    "execution_mode": "sequential",
    "max_parallelism": 5,
    "max_iterations": 100,
    "on_error": "continue"
  },
  "next_step": "aggregate-results"
}
```

**Fields**:
- `type`: Must be `"loop"`
- `loop_config`: Object containing loop configuration (required)
  - `collection`: Variable reference to array/list to iterate over (required)
  - `loop_body`: Array of step IDs to execute for each item (required)
  - `execution_mode`: `"sequential"` or `"parallel"` (default: `"sequential"`)
  - `max_parallelism`: Maximum concurrent iterations for parallel mode (optional)
  - `max_iterations`: Maximum number of items to process (optional)
  - `on_error`: Error handling policy - `"stop"`, `"continue"`, or `"collect"` (default: `"stop"`)
- `next_step`: Step to execute after loop completes

**Loop Context Variables**:

Within loop body steps, access iteration context:
- `${loop.item}`: Current item from collection
- `${loop.index}`: Current iteration index (0-based)
- `${loop.total}`: Total number of items
- `${loop.is_first}`: Boolean, true if first iteration
- `${loop.is_last}`: Boolean, true if last iteration

**Example - Sequential Loop**:

```json
{
  "workflow_id": "sequential-loop-example",
  "name": "Process Items Sequentially",
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

**Example - Parallel Loop**:

```json
{
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
  }
}
```

**Error Handling Policies**:
- `"stop"`: Stop immediately on first error (default)
- `"continue"`: Continue with remaining iterations, log errors
- `"collect"`: Complete all iterations, report all errors at end

**Loop Output Format**:

```json
{
  "iterations": [
    { "step_id": "process-item", "status": "COMPLETED", "output_data": {...} },
    ...
  ],
  "total_count": 10,
  "failed_count": 0
}
```

See [docs/loop_execution.md](docs/loop_execution.md) for detailed documentation.

### Fork-Join Pattern ✅ AVAILABLE

Split execution into multiple named parallel branches with configurable join policies for advanced parallel processing patterns.

**Step Type**: `fork_join`

```json
{
  "id": "fork-join-step",
  "type": "fork_join",
  "fork_join_config": {
    "branches": {
      "branch_a": {
        "steps": ["step-a-1", "step-a-2"],
        "timeout_seconds": 300
      },
      "branch_b": {
        "steps": ["step-b-1"]
      }
    },
    "join_policy": "all",
    "n_required": null,
    "branch_timeout_seconds": 600
  },
  "next_step": "aggregate-results"
}
```

**Fields**:
- `type`: Must be `"fork_join"`
- `fork_join_config`: Object containing fork-join configuration (required)
  - `branches`: Object with named branches (required, minimum 2)
    - Each branch has:
      - `steps`: Array of step IDs to execute sequentially in this branch (required)
      - `timeout_seconds`: Optional timeout for this specific branch
  - `join_policy`: Policy for determining when to proceed (default: `"all"`)
    - `"all"`: All branches must succeed
    - `"any"`: At least one branch must succeed
    - `"majority"`: More than 50% of branches must succeed
    - `"n_of_m"`: At least N branches must succeed (requires `n_required`)
  - `n_required`: Number of branches required for `"n_of_m"` policy (optional)
  - `branch_timeout_seconds`: Default timeout for all branches (optional)
- `next_step`: Step to execute after fork-join completes

**Example - Multi-Provider Data Fetch (ALL Policy)**:

```json
{
  "workflow_id": "fork-join-all-example",
  "name": "Multi-Provider Data Aggregation",
  "version": "1.0",
  "start_step": "fork-join-fetch",
  "steps": {
    "fork-join-fetch": {
      "id": "fork-join-fetch",
      "type": "fork_join",
      "fork_join_config": {
        "branches": {
          "weather_api": {
            "steps": ["fetch-weather"],
            "timeout_seconds": 30
          },
          "news_api": {
            "steps": ["fetch-news"],
            "timeout_seconds": 30
          },
          "stock_api": {
            "steps": ["fetch-stocks"],
            "timeout_seconds": 30
          }
        },
        "join_policy": "all",
        "branch_timeout_seconds": 60
      },
      "next_step": "aggregate-data"
    },
    "fetch-weather": {
      "id": "fetch-weather",
      "type": "agent",
      "agent_name": "WeatherAgent",
      "input_mapping": {
        "location": "${workflow.input.location}"
      },
      "next_step": null
    },
    "fetch-news": {
      "id": "fetch-news",
      "type": "agent",
      "agent_name": "NewsAgent",
      "input_mapping": {
        "topic": "${workflow.input.topic}"
      },
      "next_step": null
    },
    "fetch-stocks": {
      "id": "fetch-stocks",
      "type": "agent",
      "agent_name": "StockAgent",
      "input_mapping": {
        "symbols": "${workflow.input.stock_symbols}"
      },
      "next_step": null
    },
    "aggregate-data": {
      "id": "aggregate-data",
      "type": "agent",
      "agent_name": "AggregatorAgent",
      "input_mapping": {
        "weather": "${fork-join-fetch.output.weather_api}",
        "news": "${fork-join-fetch.output.news_api}",
        "stocks": "${fork-join-fetch.output.stock_api}"
      },
      "next_step": null
    }
  }
}
```

**Example - Redundant Service Calls (ANY Policy)**:

```json
{
  "fork-join-redundant": {
    "id": "fork-join-redundant",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "primary_service": {
          "steps": ["call-primary"],
          "timeout_seconds": 10
        },
        "backup_service_1": {
          "steps": ["call-backup-1"],
          "timeout_seconds": 15
        },
        "backup_service_2": {
          "steps": ["call-backup-2"],
          "timeout_seconds": 15
        }
      },
      "join_policy": "any"
    },
    "next_step": "process-result"
  }
}
```

**Example - Multi-Region Deployment (N_OF_M Policy)**:

```json
{
  "fork-join-deploy": {
    "id": "fork-join-deploy",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "us_east": {
          "steps": ["deploy-us-east", "verify-us-east"],
          "timeout_seconds": 300
        },
        "us_west": {
          "steps": ["deploy-us-west", "verify-us-west"],
          "timeout_seconds": 300
        },
        "eu_west": {
          "steps": ["deploy-eu-west", "verify-eu-west"],
          "timeout_seconds": 300
        },
        "ap_south": {
          "steps": ["deploy-ap-south", "verify-ap-south"],
          "timeout_seconds": 300
        }
      },
      "join_policy": "n_of_m",
      "n_required": 3,
      "branch_timeout_seconds": 600
    },
    "next_step": "finalize-deployment"
  }
}
```

**Fork-Join Output Format**:

Results are aggregated by branch name:

```json
{
  "branch_a": {
    "result": "data from branch A"
  },
  "branch_b": {
    "result": "data from branch B"
  }
}
```

**Join Policy Behavior**:
- `"all"`: Fails if any branch fails
- `"any"`: Succeeds if at least one branch succeeds
- `"majority"`: Succeeds if > 50% of branches succeed
- `"n_of_m"`: Succeeds if at least N branches succeed

**Error Handling**: The executor waits for all branches to complete before evaluating the join policy, even if some branches fail early.

See [docs/fork_join_pattern.md](docs/fork_join_pattern.md) for detailed documentation.

## Future Enhancements

Planned features for future versions:

- **Sub-workflows**: Nest workflows within steps
- **Dynamic Step Generation**: Create steps at runtime based on data
- **Event-Driven Steps**: Wait for external events
- **State Machines**: Define workflows as state machines

## Agent Communication Protocol

Agents invoked by workflows communicate using the JSON-RPC 2.0 protocol. The workflow definition itself is protocol-agnostic - the bridge service handles translating workflow steps into JSON-RPC requests to agents.

For details on how agents receive requests and return responses, see the [A2A Agent Interface Specification](A2A_AGENT_INTERFACE.md).

## See Also

- [A2A Agent Interface Specification](A2A_AGENT_INTERFACE.md) - JSON-RPC 2.0 protocol details
- [README.md](README.md) - Project overview
- [examples/workflow_README.md](examples/workflow_README.md) - Example workflows

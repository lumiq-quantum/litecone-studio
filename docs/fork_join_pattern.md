# Fork-Join Pattern

## Overview

The Fork-Join pattern enables workflows to split execution into multiple parallel branches, execute them concurrently, and then join the results based on a configurable policy. This pattern is ideal for scenarios where you need to:

- Execute multiple independent operations in parallel
- Aggregate results from different data sources
- Implement redundancy with multiple service providers
- Perform A/B testing or multi-variant processing

## Key Concepts

### Branches

A fork-join step contains multiple named branches. Each branch:
- Has a unique name (used to identify results)
- Contains a list of steps to execute sequentially
- Can have its own timeout
- Executes in parallel with other branches

### Join Policies

The join policy determines when the fork-join step completes:

- **ALL** (default): All branches must succeed
- **ANY**: At least one branch must succeed
- **MAJORITY**: More than 50% of branches must succeed
- **N_OF_M**: At least N branches must succeed (requires `n_required` parameter)

## Workflow Definition Format

```json
{
  "step-1": {
    "id": "step-1",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "branch_a": {
          "steps": ["step-1a-1", "step-1a-2"],
          "timeout_seconds": 300
        },
        "branch_b": {
          "steps": ["step-1b-1", "step-1b-2"]
        },
        "branch_c": {
          "steps": ["step-1c-1"]
        }
      },
      "join_policy": "all",
      "branch_timeout_seconds": 600,
      "n_required": null
    },
    "next_step": "step-2"
  },
  "step-1a-1": {
    "id": "step-1a-1",
    "type": "agent",
    "agent_name": "AgentA",
    "input_mapping": {
      "data": "${workflow.input.data}"
    },
    "next_step": null
  },
  "step-1a-2": {
    "id": "step-1a-2",
    "type": "agent",
    "agent_name": "AgentA2",
    "input_mapping": {
      "result": "${step-1a-1.output.result}"
    },
    "next_step": null
  }
}
```

## Configuration Options

### Fork-Join Config

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `branches` | Object | Yes | Named branches to execute in parallel (minimum 2) |
| `join_policy` | String | No | Join policy: "all", "any", "majority", "n_of_m" (default: "all") |
| `n_required` | Integer | Conditional | Number of branches required (required for "n_of_m" policy) |
| `branch_timeout_seconds` | Integer | No | Default timeout for all branches in seconds |

### Branch Config

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `steps` | Array[String] | Yes | Step IDs to execute in this branch (minimum 1) |
| `timeout_seconds` | Integer | No | Timeout for this specific branch (overrides default) |

## Examples

### Example 1: Multi-Provider Data Fetch (ALL Policy)

Fetch data from multiple providers and require all to succeed:

```json
{
  "fetch-data": {
    "id": "fetch-data",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "provider_a": {
          "steps": ["fetch-from-a"]
        },
        "provider_b": {
          "steps": ["fetch-from-b"]
        },
        "provider_c": {
          "steps": ["fetch-from-c"]
        }
      },
      "join_policy": "all",
      "branch_timeout_seconds": 30
    },
    "next_step": "aggregate-results"
  }
}
```

**Use Case**: Fetching required data from multiple sources where all data is needed.

### Example 2: Redundant Service Calls (ANY Policy)

Call multiple redundant services and proceed with the first success:

```json
{
  "redundant-call": {
    "id": "redundant-call",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "primary": {
          "steps": ["call-primary-service"]
        },
        "backup1": {
          "steps": ["call-backup-service-1"]
        },
        "backup2": {
          "steps": ["call-backup-service-2"]
        }
      },
      "join_policy": "any",
      "branch_timeout_seconds": 10
    },
    "next_step": "process-result"
  }
}
```

**Use Case**: High availability scenarios where any successful response is acceptable.

### Example 3: Consensus-Based Processing (MAJORITY Policy)

Execute processing across multiple nodes and require majority agreement:

```json
{
  "consensus-check": {
    "id": "consensus-check",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "node1": {
          "steps": ["validate-on-node1"]
        },
        "node2": {
          "steps": ["validate-on-node2"]
        },
        "node3": {
          "steps": ["validate-on-node3"]
        },
        "node4": {
          "steps": ["validate-on-node4"]
        },
        "node5": {
          "steps": ["validate-on-node5"]
        }
      },
      "join_policy": "majority"
    },
    "next_step": "finalize"
  }
}
```

**Use Case**: Distributed validation or consensus algorithms.

### Example 4: Flexible Success Threshold (N_OF_M Policy)

Require a specific number of branches to succeed:

```json
{
  "multi-region-deploy": {
    "id": "multi-region-deploy",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "us-east": {
          "steps": ["deploy-us-east"]
        },
        "us-west": {
          "steps": ["deploy-us-west"]
        },
        "eu-west": {
          "steps": ["deploy-eu-west"]
        },
        "ap-south": {
          "steps": ["deploy-ap-south"]
        }
      },
      "join_policy": "n_of_m",
      "n_required": 3,
      "branch_timeout_seconds": 300
    },
    "next_step": "verify-deployment"
  }
}
```

**Use Case**: Multi-region deployments where you need a minimum number of regions to succeed.

### Example 5: Complex Branch with Multiple Steps

Each branch can contain multiple sequential steps:

```json
{
  "data-pipeline": {
    "id": "data-pipeline",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "customer_data": {
          "steps": [
            "fetch-customers",
            "enrich-customers",
            "validate-customers"
          ],
          "timeout_seconds": 120
        },
        "order_data": {
          "steps": [
            "fetch-orders",
            "enrich-orders",
            "validate-orders"
          ],
          "timeout_seconds": 180
        },
        "product_data": {
          "steps": [
            "fetch-products",
            "enrich-products"
          ],
          "timeout_seconds": 60
        }
      },
      "join_policy": "all"
    },
    "next_step": "merge-data"
  }
}
```

**Use Case**: Parallel data pipelines with multiple processing stages per branch.

## Output Data Structure

The fork-join step aggregates outputs from all branches into a single object keyed by branch name:

```json
{
  "branch_a": {
    "result": "data from branch A"
  },
  "branch_b": {
    "result": "data from branch B"
  },
  "branch_c": {
    "result": "data from branch C"
  }
}
```

You can reference branch outputs in subsequent steps:

```json
{
  "step-2": {
    "id": "step-2",
    "type": "agent",
    "agent_name": "AggregatorAgent",
    "input_mapping": {
      "branch_a_result": "${step-1.output.branch_a.result}",
      "branch_b_result": "${step-1.output.branch_b.result}",
      "branch_c_result": "${step-1.output.branch_c.result}"
    }
  }
}
```

## Error Handling

### Branch Failures

When a branch fails:
1. The executor waits for all other branches to complete
2. The join policy is evaluated
3. If the policy is not satisfied, the fork-join step fails
4. Failed branch outputs are still included in the result (with error information)

### Timeouts

Branches can timeout in two ways:
1. **Branch-specific timeout**: Set via `timeout_seconds` in the branch config
2. **Default timeout**: Set via `branch_timeout_seconds` in the fork-join config

When a branch times out:
- It is marked as failed
- Other branches continue executing
- The timeout error is included in the branch result

### Join Policy Failures

If the join policy is not satisfied, the fork-join step fails with a detailed error message:

```
Fork-join failed: 2 branch(es) failed (policy: ALL). Failed branches: branch_a, branch_c
```

## Best Practices

### 1. Choose the Right Join Policy

- Use **ALL** when all results are required
- Use **ANY** for redundancy and failover scenarios
- Use **MAJORITY** for consensus-based decisions
- Use **N_OF_M** when you need a specific success threshold

### 2. Set Appropriate Timeouts

- Set branch-specific timeouts for branches with different expected durations
- Use `branch_timeout_seconds` as a safety net for all branches
- Consider network latency and processing time when setting timeouts

### 3. Keep Branches Independent

- Branches should not depend on each other's results
- Each branch should be able to execute independently
- Use sequential steps within a branch for dependent operations

### 4. Handle Partial Failures

- When using ANY, MAJORITY, or N_OF_M policies, design downstream steps to handle missing data
- Check which branches succeeded before accessing their outputs
- Implement fallback logic for failed branches

### 5. Monitor Branch Performance

- Track execution time for each branch
- Identify slow branches that may need optimization
- Use timeouts to prevent slow branches from blocking the workflow

### 6. Limit Branch Count

- Keep the number of branches reasonable (typically < 10)
- Too many branches can overwhelm the system
- Consider using loops with parallel execution for large-scale parallelism

## Comparison with Parallel Execution

| Feature | Fork-Join | Parallel Execution |
|---------|-----------|-------------------|
| Branch naming | Named branches | Unnamed steps |
| Join policies | Multiple policies (ALL, ANY, MAJORITY, N_OF_M) | Always ALL |
| Branch complexity | Multiple steps per branch | Single step per parallel item |
| Timeout control | Per-branch timeouts | Global timeout only |
| Result structure | Keyed by branch name | Array of results |
| Use case | Complex parallel workflows with policies | Simple parallel step execution |

## Monitoring and Debugging

### Execution Tracking

Each branch execution is tracked separately in the database:
- Branch name is stored in `step_executions.branch_name`
- Join policy is stored in `step_executions.join_policy`
- Parent fork-join step ID is stored in `step_executions.parent_step_id`

### Logs

Fork-join execution produces detailed logs:

```
INFO: Executing fork-join step 'data-pipeline' with 3 branches, join_policy=all
INFO: Executing branch 'customer_data' with 3 steps
INFO: Executing branch 'order_data' with 3 steps
INFO: Executing branch 'product_data' with 2 steps
INFO: Branch 'customer_data' completed with status COMPLETED
INFO: Branch 'order_data' completed with status COMPLETED
INFO: Branch 'product_data' completed with status COMPLETED
INFO: Fork-join step 'data-pipeline' completed: 3/3 branches succeeded
```

### Troubleshooting

**Problem**: Fork-join step fails with "All branches failed"
- **Solution**: Check individual branch logs for errors, verify agent availability

**Problem**: Fork-join step times out
- **Solution**: Increase `branch_timeout_seconds` or optimize slow branches

**Problem**: Join policy not satisfied
- **Solution**: Review failed branches, adjust join policy if appropriate

**Problem**: Missing branch outputs in subsequent steps
- **Solution**: Verify branch names match in output references, check for branch failures

## API Integration

### Creating Fork-Join Workflows

Use the Workflow Management API to create workflows with fork-join steps:

```bash
POST /api/v1/workflows
Content-Type: application/json

{
  "name": "Multi-Provider Data Fetch",
  "start_step": "fetch-data",
  "steps": {
    "fetch-data": {
      "id": "fetch-data",
      "type": "fork_join",
      "fork_join_config": {
        "branches": {
          "provider_a": {"steps": ["fetch-from-a"]},
          "provider_b": {"steps": ["fetch-from-b"]}
        },
        "join_policy": "all"
      },
      "next_step": null
    }
  }
}
```

### Monitoring Fork-Join Execution

Query step executions to see branch-level details:

```bash
GET /api/v1/runs/{run_id}/steps

Response:
[
  {
    "step_id": "fetch-data",
    "status": "COMPLETED",
    "branch_name": null,
    "join_policy": "all"
  },
  {
    "step_id": "fetch-from-a",
    "status": "COMPLETED",
    "branch_name": "provider_a",
    "parent_step_id": "fetch-data"
  },
  {
    "step_id": "fetch-from-b",
    "status": "COMPLETED",
    "branch_name": "provider_b",
    "parent_step_id": "fetch-data"
  }
]
```

## Related Patterns

- **Parallel Execution**: Simpler pattern for executing independent steps in parallel
- **Conditional Logic**: Can be used within branches for branch-specific decisions
- **Loops**: Can be combined with fork-join for iterative parallel processing

## Limitations

1. **Maximum Branches**: Recommended limit of 10 branches per fork-join step
2. **Nesting**: Fork-join steps can be nested within branches, but keep nesting shallow
3. **Circular Dependencies**: Branches cannot reference each other's outputs
4. **Resource Limits**: Consider system resources when executing many parallel branches

## Future Enhancements

Potential future improvements to the fork-join pattern:

- Dynamic branch creation based on runtime data
- Weighted join policies (e.g., require specific branches to succeed)
- Branch priority and execution ordering
- Partial result streaming before all branches complete
- Branch retry policies independent of step retry

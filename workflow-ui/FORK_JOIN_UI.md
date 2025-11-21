# Fork-Join Pattern UI Support

## Overview

The Workflow UI provides full support for visualizing and editing fork-join workflow steps. Fork-join steps enable parallel execution of multiple named branches with configurable join policies.

## Visual Representation

### Step Node Icon

Fork-join steps are displayed with a distinctive **GitFork** icon (⑂) in indigo color:

- **Icon**: GitFork from lucide-react
- **Color**: Indigo (#6366f1)
- **Symbol**: ⑂ (fork symbol)

### Step Display Name

The step node shows:
```
Fork-Join (N branches, policy)
```

Example: `Fork-Join (3 branches, all)`

### Graph Visualization

Fork-join steps create multiple edges to branch steps:

- **Edge Color**: Indigo (#6366f1)
- **Edge Style**: Dashed line (strokeDasharray: '6,3')
- **Branch Labels**: First step in each branch is labeled with the branch name
- **Edge Type**: Smooth step curves

## JSON Editor Support

### Schema Validation

The Monaco editor provides full schema validation for fork-join steps:


```typescript
{
  "type": "fork_join",
  "fork_join_config": {
    "branches": {
      "branch_name": {
        "steps": ["step-id"],
        "timeout_seconds": 300
      }
    },
    "join_policy": "all" | "any" | "majority" | "n_of_m",
    "n_required": 2,
    "branch_timeout_seconds": 600
  }
}
```

### Validation Rules

The editor validates:

1. **Step Type**: Must be `"fork_join"`
2. **Branches**: Must have at least 2 branches
3. **Branch Steps**: Each branch must have at least 1 step
4. **Step References**: All branch steps must exist in the workflow
5. **Join Policy**: Must be one of: `"all"`, `"any"`, `"majority"`, `"n_of_m"`
6. **N Required**: Required for `"n_of_m"` policy, must be ≥ 1 and ≤ branch count
7. **Timeouts**: Must be positive integers

### Auto-completion

The editor provides auto-completion for:
- Step type: `fork_join`
- Join policies: `all`, `any`, `majority`, `n_of_m`
- Branch configuration fields

## TypeScript Types

```typescript
interface Branch {
  steps: string[];
  timeout_seconds?: number;
}

interface ForkJoinConfig {
  branches: Record<string, Branch>;
  join_policy?: 'all' | 'any' | 'majority' | 'n_of_m';
  n_required?: number;
  branch_timeout_seconds?: number;
}

interface WorkflowStep {
  id: string;
  type: 'fork_join';
  fork_join_config: ForkJoinConfig;
  next_step: string | null;
}
```

## Example Workflows

### Example 1: Multi-Provider Data Fetch (ALL Policy)

All branches must succeed:

```json
{
  "fork-join-fetch": {
    "id": "fork-join-fetch",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "weather_api": {
          "steps": ["fetch-weather"]
        },
        "news_api": {
          "steps": ["fetch-news"]
        }
      },
      "join_policy": "all"
    },
    "next_step": "aggregate"
  }
}
```

### Example 2: Redundant Services (ANY Policy)

At least one branch must succeed:

```json
{
  "fork-join-redundant": {
    "id": "fork-join-redundant",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "primary": {
          "steps": ["call-primary"]
        },
        "backup": {
          "steps": ["call-backup"]
        }
      },
      "join_policy": "any"
    },
    "next_step": "process"
  }
}
```

### Example 3: Multi-Region Deploy (N_OF_M Policy)

At least 3 out of 4 regions must succeed:

```json
{
  "fork-join-deploy": {
    "id": "fork-join-deploy",
    "type": "fork_join",
    "fork_join_config": {
      "branches": {
        "us_east": {"steps": ["deploy-us-east"]},
        "us_west": {"steps": ["deploy-us-west"]},
        "eu_west": {"steps": ["deploy-eu-west"]},
        "ap_south": {"steps": ["deploy-ap-south"]}
      },
      "join_policy": "n_of_m",
      "n_required": 3
    },
    "next_step": "finalize"
  }
}
```

## Visual Graph Features

### Branch Visualization

- Each branch creates separate edges from the fork-join node to its steps
- Branch names are displayed as edge labels on the first step
- Branches are laid out vertically to show parallel execution

### Status Indicators

Fork-join steps show execution status:
- **Pending**: Gray border
- **Running**: Blue border with pulse animation
- **Completed**: Green border
- **Failed**: Red border

### Tooltips

Hovering over a fork-join step shows:
- Step ID
- Number of branches
- Join policy
- Execution status
- Error message (if failed)

## Best Practices

### Naming Branches

Use descriptive branch names:
```json
"branches": {
  "primary_service": {...},
  "backup_service": {...}
}
```

### Organizing Complex Branches

For branches with multiple steps, use clear step naming:
```json
"branches": {
  "data_pipeline_a": {
    "steps": [
      "fetch-data-a",
      "transform-data-a",
      "validate-data-a"
    ]
  }
}
```

### Choosing Join Policies

- **ALL**: Use when all results are required
- **ANY**: Use for redundancy/failover
- **MAJORITY**: Use for consensus
- **N_OF_M**: Use for flexible thresholds

## Troubleshooting

### Validation Errors

**"Fork-join must have at least 2 branches"**
- Add more branches to the `branches` object

**"Branch references non-existent step"**
- Ensure all step IDs in branch `steps` arrays exist in the workflow

**"n_required must be specified for n_of_m policy"**
- Add `n_required` field when using `join_policy: "n_of_m"`

**"n_required cannot be greater than number of branches"**
- Reduce `n_required` or add more branches

### Graph Display Issues

If the graph doesn't display correctly:
1. Check that all branch steps exist in the workflow
2. Verify step IDs don't have circular references
3. Ensure `next_step` references are valid

## Related Documentation

- [Fork-Join Pattern Documentation](../docs/fork_join_pattern.md)
- [Workflow Format Specification](../WORKFLOW_FORMAT.md)
- [Parallel Execution UI](./PARALLEL_EXECUTION_UI.md)
- [Conditional Logic UI](./CONDITIONAL_LOGIC_UI.md)
- [Loop Execution UI](./LOOP_EXECUTION_UI.md)

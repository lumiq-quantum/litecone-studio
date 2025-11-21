# Troubleshooting Workflow UI Errors

## Common Validation Errors

### Error: "Missing required field: start_step"

**Cause**: The workflow JSON is missing the `start_step` field.

**Solution**: Add `start_step` field pointing to the first step:

```json
{
  "workflow_id": "my-workflow",
  "name": "My Workflow",
  "start_step": "step-1",  ← Add this
  "steps": {
    "step-1": {
      "id": "step-1",
      "agent_name": "MyAgent",
      "input_mapping": {}
    }
  }
}
```

### Error: "start_step 'X' not found in steps"

**Cause**: The `start_step` references a step that doesn't exist in the `steps` object.

**Solution**: Make sure `start_step` matches an actual step ID:

```json
{
  "start_step": "fetch-data",  ← Must match a step ID below
  "steps": {
    "fetch-data": {  ← This must match
      "id": "fetch-data",
      ...
    }
  }
}
```

### Error: "Missing or invalid field: steps"

**Cause**: The `steps` field is missing or not an object.

**Solution**: Add a `steps` object with at least one step:

```json
{
  "workflow_id": "my-workflow",
  "start_step": "step-1",
  "steps": {  ← Must be an object
    "step-1": {
      "id": "step-1",
      "agent_name": "MyAgent",
      "input_mapping": {}
    }
  }
}
```

### Error: "Step 'X' is missing required field: id"

**Cause**: A step is missing the `id` field.

**Solution**: Add `id` field to each step (should match the key):

```json
{
  "steps": {
    "my-step": {
      "id": "my-step",  ← Add this, must match the key
      "agent_name": "MyAgent",
      "input_mapping": {}
    }
  }
}
```

### Error: "Step 'X' is missing required field: agent_name"

**Cause**: A regular step (not parallel, conditional, loop, or fork-join) is missing `agent_name`.

**Solution**: Add `agent_name` field:

```json
{
  "steps": {
    "my-step": {
      "id": "my-step",
      "agent_name": "MyAgent",  ← Add this
      "input_mapping": {}
    }
  }
}
```

### Error: "Step 'X' is missing required field: input_mapping"

**Cause**: A step is missing the `input_mapping` field.

**Solution**: Add `input_mapping` (can be empty object):

```json
{
  "steps": {
    "my-step": {
      "id": "my-step",
      "agent_name": "MyAgent",
      "input_mapping": {}  ← Add this (can be empty)
    }
  }
}
```

## Parallel Step Errors

### Error: "Parallel step 'X' is missing required field: parallel_steps (array)"

**Solution**: Add `parallel_steps` array:

```json
{
  "my-parallel": {
    "id": "my-parallel",
    "type": "parallel",
    "parallel_steps": ["step-a", "step-b"],  ← Add this
    "next_step": "next"
  }
}
```

### Error: "Parallel step 'X' must have at least 2 parallel_steps"

**Solution**: Include at least 2 steps in `parallel_steps`:

```json
{
  "parallel_steps": ["step-a", "step-b"]  ← At least 2
}
```

### Error: "Parallel step 'X' references non-existent step: 'Y'"

**Solution**: Make sure all steps in `parallel_steps` exist:

```json
{
  "steps": {
    "parallel-block": {
      "type": "parallel",
      "parallel_steps": ["step-a", "step-b"]
    },
    "step-a": {  ← Must exist
      "id": "step-a",
      "agent_name": "AgentA",
      "input_mapping": {}
    },
    "step-b": {  ← Must exist
      "id": "step-b",
      "agent_name": "AgentB",
      "input_mapping": {}
    }
  }
}
```

## Conditional Step Errors

### Error: "Conditional step 'X' is missing required field: condition (object)"

**Solution**: Add `condition` object:

```json
{
  "my-conditional": {
    "id": "my-conditional",
    "type": "conditional",
    "condition": {  ← Add this
      "expression": "${step-1.output.status} == 'success'"
    },
    "if_true_step": "success-step",
    "if_false_step": "failure-step"
  }
}
```

### Error: "Conditional step 'X' condition is missing required field: expression"

**Solution**: Add `expression` to condition:

```json
{
  "condition": {
    "expression": "${step-1.output.value} > 10"  ← Add this
  }
}
```

### Error: "Conditional step 'X' must have at least one of if_true_step or if_false_step"

**Solution**: Add at least one branch:

```json
{
  "condition": {...},
  "if_true_step": "success-step",  ← Add at least one
  "if_false_step": "failure-step"
}
```

## Loop Step Errors

### Error: "Loop step 'X' is missing required field: loop_config (object)"

**Solution**: Add `loop_config` object:

```json
{
  "my-loop": {
    "id": "my-loop",
    "type": "loop",
    "loop_config": {  ← Add this
      "collection": "${workflow.input.items}",
      "loop_body": ["process-item"],
      "execution_mode": "sequential"
    }
  }
}
```

### Error: "Loop step 'X' loop_config is missing required field: collection"

**Solution**: Add `collection` field:

```json
{
  "loop_config": {
    "collection": "${workflow.input.items}",  ← Add this
    "loop_body": ["process-item"]
  }
}
```

### Error: "Loop step 'X' loop_config is missing required field: loop_body (array)"

**Solution**: Add `loop_body` array:

```json
{
  "loop_config": {
    "collection": "${workflow.input.items}",
    "loop_body": ["process-item"]  ← Add this
  }
}
```

## Fork-Join Step Errors

### Error: "Fork-join step 'X' is missing required field: fork_join_config (object)"

**Solution**: Add `fork_join_config` object:

```json
{
  "my-fork-join": {
    "id": "my-fork-join",
    "type": "fork_join",
    "fork_join_config": {  ← Add this
      "branches": {
        "branch-a": {
          "steps": ["step-a"]
        },
        "branch-b": {
          "steps": ["step-b"]
        }
      },
      "join_policy": "all"
    }
  }
}
```

### Error: "Fork-join step 'X' must have at least 2 branches"

**Solution**: Add at least 2 branches:

```json
{
  "fork_join_config": {
    "branches": {
      "branch-a": {...},  ← At least 2 branches
      "branch-b": {...}
    }
  }
}
```

## Complete Valid Workflow Example

Here's a complete, valid workflow that will pass all validation:

```json
{
  "workflow_id": "complete-example",
  "name": "Complete Example Workflow",
  "description": "A complete workflow with all required fields",
  "start_step": "step-1",
  "steps": {
    "step-1": {
      "id": "step-1",
      "agent_name": "ResearchAgent",
      "input_mapping": {
        "topic": "${workflow.input.topic}"
      },
      "next_step": "step-2"
    },
    "step-2": {
      "id": "step-2",
      "agent_name": "WriterAgent",
      "input_mapping": {
        "research": "${step-1.output.text}",
        "style": "${workflow.input.style}"
      }
    }
  }
}
```

## Minimal Valid Workflow

The absolute minimum required for a valid workflow:

```json
{
  "workflow_id": "minimal",
  "start_step": "step-1",
  "steps": {
    "step-1": {
      "id": "step-1",
      "agent_name": "MyAgent",
      "input_mapping": {}
    }
  }
}
```

## Checking for Errors

### In the UI

1. Look at the top-right corner for error count (e.g., "2 Errors")
2. Click on "Invalid JSON" to see error details
3. The editor will show red squiggly lines under errors
4. Hover over red lines to see specific error messages

### Using JSON Validator

```bash
# Validate JSON syntax
python -m json.tool my-workflow.json

# Or use jq
jq . my-workflow.json
```

## Common Mistakes

### 1. Missing Comma

```json
{
  "workflow_id": "test"  ← Missing comma
  "start_step": "step-1"
}
```

**Fix**: Add comma after each field (except the last one)

### 2. Trailing Comma

```json
{
  "workflow_id": "test",
  "start_step": "step-1",  ← Remove this comma
}
```

**Fix**: Remove trailing comma before closing brace

### 3. Mismatched Quotes

```json
{
  "workflow_id": 'test'  ← Use double quotes
}
```

**Fix**: Always use double quotes in JSON

### 4. Step ID Mismatch

```json
{
  "steps": {
    "my-step": {
      "id": "different-id"  ← Should match key
    }
  }
}
```

**Fix**: Make sure `id` matches the step key

### 5. Referencing Non-Existent Steps

```json
{
  "start_step": "step-1",
  "steps": {
    "step-2": {  ← start_step references step-1, but only step-2 exists
      "id": "step-2",
      ...
    }
  }
}
```

**Fix**: Make sure all referenced steps exist

## Getting Help

If you're still seeing errors:

1. **Copy the error message** from the UI
2. **Check this guide** for the specific error
3. **Validate JSON syntax** using a JSON validator
4. **Compare with examples** in the `examples/` directory
5. **Check the console** (F12 in browser) for additional error details

## Quick Checklist

Before saving a workflow, verify:

- [ ] `workflow_id` is present and unique
- [ ] `start_step` is present
- [ ] `start_step` references an existing step
- [ ] `steps` object is present
- [ ] Each step has an `id` field matching its key
- [ ] Regular steps have `agent_name` and `input_mapping`
- [ ] Special steps (parallel, conditional, loop, fork-join) have required config
- [ ] All referenced steps exist (in `next_step`, `parallel_steps`, etc.)
- [ ] JSON syntax is valid (no missing commas, quotes, etc.)

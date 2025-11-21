# Conditional Logic in Workflows

## Overview

Conditional logic allows workflows to make decisions and execute different paths based on runtime data. This enables dynamic workflows that adapt to data and context.

## Features

- **Comparison Operators**: `==`, `!=`, `>`, `<`, `>=`, `<=`
- **Logical Operators**: `and`, `or`, `not`
- **Membership Operators**: `in`, `not in`, `contains`
- **JSONPath Support**: Access nested data with array indices
- **Variable References**: Access workflow input and step outputs

## Workflow Definition

### Basic Conditional Step

```json
{
  "step-id": {
    "id": "step-id",
    "type": "conditional",
    "condition": {
      "expression": "${step-1.output.score} > 0.8"
    },
    "if_true_step": "high-score-handler",
    "if_false_step": "low-score-handler",
    "next_step": "final-step"
  }
}
```

### Conditional Step Fields

- **type**: Must be `"conditional"`
- **condition**: Object containing the condition expression
  - **expression**: The condition to evaluate (required)
  - **operator**: Optional simple operator for basic comparisons
- **if_true_step**: Step ID to execute if condition is true (optional)
- **if_false_step**: Step ID to execute if condition is false (optional)
- **next_step**: Step ID to execute after the conditional branch completes (optional)

**Note**: At least one of `if_true_step` or `if_false_step` must be specified.

## Condition Expressions

### Simple Comparisons

```json
{
  "expression": "${step-1.output.status} == 'success'"
}
```

### Numeric Comparisons

```json
{
  "expression": "${step-1.output.count} > 10"
}
```

### Logical Operations

```json
{
  "expression": "${step-1.output.valid} and ${step-2.output.approved}"
}
```

### Membership Tests

```json
{
  "expression": "'error' in ${step-1.output.message}"
}
```

or using `contains`:

```json
{
  "expression": "${step-1.output.message} contains 'error'"
}
```

### JSONPath Expressions

Access nested data and array elements:

```json
{
  "expression": "${step-1.output.results[0].score} >= 0.9"
}
```

### Complex Conditions

Combine multiple operators:

```json
{
  "expression": "${step-1.output.score} > 0.8 and ${step-1.output.valid} == true"
}
```

## Variable References

### Workflow Input

Access initial workflow input data:

```json
"${workflow.input.field_name}"
```

### Step Output

Access output from previous steps:

```json
"${step-id.output.field_name}"
```

### Nested Fields

Access nested fields using dot notation:

```json
"${step-1.output.result.data.value}"
```

### Array Elements

Access array elements using JSONPath:

```json
"${step-1.output.items[0].name}"
"${step-1.output.results[2].score}"
```

## Execution Behavior

1. **Condition Evaluation**: The condition expression is evaluated using current workflow input and step outputs
2. **Branch Selection**: Based on the result (true/false), the appropriate branch step is selected
3. **Branch Execution**: The selected branch step is executed
4. **Output Storage**: The branch output is stored and made available to subsequent steps
5. **Next Step**: After branch completion, execution continues to `next_step` if specified

## Conditional Step Output

The conditional step itself produces output containing:

```json
{
  "condition_result": true,
  "branch_taken": "then",
  "branch_step_id": "high-score-handler",
  "branch_output": {
    // Output from the executed branch step
  }
}
```

## Error Handling

- **Evaluation Errors**: If condition evaluation fails, it is treated as `false`
- **Missing Variables**: If a referenced variable doesn't exist, the condition evaluates to `false`
- **Branch Failures**: If a branch step fails, the conditional step fails
- **Missing Branch**: If no branch is specified for the result, execution continues to `next_step`

## Examples

### Example 1: Score-Based Routing

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

### Example 2: Status Check

```json
{
  "check-status": {
    "id": "check-status",
    "type": "conditional",
    "condition": {
      "expression": "${validate.output.status} == 'approved'"
    },
    "if_true_step": "proceed-with-order",
    "if_false_step": "reject-order",
    "next_step": "send-notification"
  }
}
```

### Example 3: Multiple Conditions

```json
{
  "check-eligibility": {
    "id": "check-eligibility",
    "type": "conditional",
    "condition": {
      "expression": "${user.output.age} >= 18 and ${user.output.verified} == true"
    },
    "if_true_step": "grant-access",
    "if_false_step": "deny-access",
    "next_step": "log-decision"
  }
}
```

### Example 4: Array Check

```json
{
  "check-errors": {
    "id": "check-errors",
    "type": "conditional",
    "condition": {
      "expression": "${process.output.errors} != null and len(${process.output.errors}) > 0"
    },
    "if_true_step": "handle-errors",
    "if_false_step": null,
    "next_step": "complete"
  }
}
```

### Example 5: Nested Data Access

```json
{
  "check-nested": {
    "id": "check-nested",
    "type": "conditional",
    "condition": {
      "expression": "${api-call.output.response.data.items[0].status} == 'active'"
    },
    "if_true_step": "process-active",
    "if_false_step": "process-inactive",
    "next_step": "done"
  }
}
```

## Best Practices

1. **Keep Conditions Simple**: Complex conditions are harder to debug
2. **Use Descriptive Step Names**: Make branch steps clearly indicate their purpose
3. **Handle Both Branches**: Consider what happens in both true and false cases
4. **Test Edge Cases**: Test with null values, empty arrays, and missing fields
5. **Log Decisions**: Use monitoring to track which branches are taken
6. **Avoid Deep Nesting**: Too many nested conditionals make workflows hard to understand

## Limitations

1. **No Custom Functions**: Only built-in Python operators are supported
2. **String Evaluation**: Conditions are evaluated as Python expressions
3. **Type Safety**: Be careful with type comparisons (string vs number)
4. **Null Handling**: Missing variables evaluate to null, which may cause unexpected results

## Monitoring

Conditional steps emit monitoring events that include:
- Condition expression
- Evaluation result (true/false)
- Branch taken (then/else)
- Branch step ID

Check the `workflow.monitoring.updates` Kafka topic for these events.

## Database Tracking

Conditional execution is tracked in the `step_executions` table with these columns:
- `condition_expression`: The evaluated condition
- `condition_result`: Boolean result (true/false)
- `branch_taken`: Which branch was executed ("then" or "else")

## See Also

- [Workflow Format Guide](../WORKFLOW_FORMAT.md)
- [Parallel Execution](parallel_execution.md)
- [Loop Execution](loop_execution.md)

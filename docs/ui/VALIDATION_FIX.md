# Validation Fix for Parallel Steps

## Issue

When defining a parallel block in the workflow editor, users were seeing validation errors:
- "Missing property 'agent_name'"
- "Missing property 'input_mapping'"

## Root Cause

The Monaco Editor's JSON schema had `required: ['id', 'agent_name', 'input_mapping']` for ALL steps, but parallel blocks don't need `agent_name` or `input_mapping` - they need `parallel_steps` instead.

## Solution

### 1. Updated Monaco Schema

Changed the schema to:
- Only require `id` for all steps
- Added `type`, `parallel_steps`, and `max_parallelism` properties
- Added descriptions indicating conditional requirements
- Removed `agent_name` and `input_mapping` from required array

### 2. Custom Validation

The custom validation logic (in `validateJSON` function) properly handles:
- Type-based validation (agent vs parallel)
- Conditional required fields based on step type
- Parallel-specific validation (min 2 steps, valid references, etc.)

## Result

✅ Parallel blocks no longer show false validation errors
✅ Agent steps still properly validated
✅ Clear error messages for actual validation issues

## Example Valid Parallel Block

```json
{
  "parallel-block-1": {
    "id": "parallel-block-1",
    "type": "parallel",
    "parallel_steps": ["step-a", "step-b", "step-c"],
    "max_parallelism": 2,
    "next_step": "final-step"
  }
}
```

## Example Valid Agent Step

```json
{
  "step-a": {
    "id": "step-a",
    "type": "agent",
    "agent_name": "DataFetcher",
    "input_mapping": {
      "url": "${workflow.input.api_url}"
    },
    "next_step": null
  }
}
```

## Testing

To test the fix:

1. Open workflow editor
2. Create a parallel block with the JSON above
3. Verify no validation errors appear
4. Try removing `parallel_steps` - should show error
5. Try removing `agent_name` from agent step - should show error

## Technical Details

### Monaco Schema (Before)

```typescript
required: ['id', 'agent_name', 'input_mapping']
```

### Monaco Schema (After)

```typescript
required: ['id']
// Conditional requirements handled by custom validation
```

### Custom Validation Logic

```typescript
const stepType = step.type || 'agent';

if (stepType === 'parallel') {
  // Validate parallel_steps
  if (!step.parallel_steps || !Array.isArray(step.parallel_steps)) {
    errors.push(`Parallel step "${stepId}" is missing required field: parallel_steps (array)`);
  }
} else {
  // Validate agent_name and input_mapping
  if (!step.agent_name) {
    errors.push(`Step "${stepId}" is missing required field: agent_name`);
  }
  if (step.input_mapping === undefined) {
    errors.push(`Step "${stepId}" is missing required field: input_mapping`);
  }
}
```

## Related Files

- `workflow-ui/src/components/common/JSONEditor.tsx` - Fixed Monaco schema and validation
- `workflow-ui/src/types/workflow.ts` - TypeScript types for parallel steps
- `workflow-ui/PARALLEL_EXECUTION_UI.md` - User documentation

## Deployment

After this fix, rebuild the UI:

```bash
cd workflow-ui
npm run build
```

Or rebuild Docker container:

```bash
docker-compose build workflow-ui
docker-compose up -d workflow-ui
```

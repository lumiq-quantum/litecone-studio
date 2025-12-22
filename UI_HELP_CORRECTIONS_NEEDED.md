# UI Help Page Corrections Needed

## Critical Issues Found

The current UI help page at `/help` contains **incorrect input mapping syntax** that will cause workflow failures.

### ❌ Current (Incorrect) Documentation in UI:

```json
"input_mapping": {
  "user_id": "$.input.user_id",
  "data": "$.steps.fetch_data.output.result"
}
```

### ✅ Correct Syntax (Should Be):

```json
"input_mapping": {
  "user_id": "${workflow.input.user_id}",
  "data": "${fetch_data.output.result}"
}
```

## Required Changes to Help.tsx

### 1. Fix Input Mapping Examples

**Line ~200-210 in Help.tsx:**
```typescript
// WRONG:
"input_mapping": {
  "key": "value"
}

// CORRECT:
"input_mapping": {
  "user_query": "${workflow.input.query}",
  "previous_data": "${step1.output.text}"
}
```

### 2. Fix JSONPath Reference Section

**Line ~250-260 in Help.tsx:**
```typescript
// WRONG:
• $.input.* - Access workflow input
• $.steps.step_id.output.* - Access previous step output

// CORRECT:
• ${workflow.input.*} - Access workflow input  
• ${step_id.output.*} - Access previous step output
```

### 3. Fix Complete Example

**Line ~300-350 in Help.tsx:**
```json
// WRONG:
"input_mapping": {
  "user_id": "$.input.user_id"
}

// CORRECT:
"input_mapping": {
  "user_id": "${workflow.input.user_id}"
}
```

### 4. Add Available Fields Documentation

Add section about commonly available fields:
- `${step.output.text}` - Main text response
- `${step.output.response}` - Agent response  
- `${step.output.artifacts}` - Output artifacts
- `${step.output.metadata}` - Agent metadata

## Impact

**Current UI help will cause ALL workflows to fail** because users will copy the incorrect syntax.

## Recommendation

1. **Immediately update Help.tsx** with correct syntax
2. **Add field reference section** showing available output fields
3. **Test examples** to ensure they work with actual system
4. **Consider linking** to the comprehensive documentation I created

## Files to Reference

- `docs/guides/INPUT_MAPPING_REFERENCE.md` - Complete reference
- `INPUT_MAPPING_QUICK_REFERENCE.md` - Quick reference
- Both contain accurate, tested syntax and examples
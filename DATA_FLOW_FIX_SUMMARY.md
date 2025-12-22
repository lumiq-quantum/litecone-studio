# Data Flow Fix: Preserving Structured Data Between Workflow Steps

## Issue Description

The system was not properly passing structured data from one agent to the next in workflow executions. When an agent returned complex data structures (like JSON objects with `data`, `metadata`, etc.), only text content was being extracted and passed to subsequent steps.

### Example of the Problem

**Agent 1 Output:**
```json
{
  "data": "Actual PDF content here",
  "metadata": {
    "file_type": "pdf",
    "pages": 10
  },
  "task_id": "81d210e0-d935-4448-9985-d2760b17a907"
}
```

**What Agent 2 Received (BEFORE fix):**
```json
{
  "text": "Some extracted text",
  "response": "Agent response text"
}
```

**What Agent 2 Should Receive (AFTER fix):**
```json
{
  "data": "Actual PDF content here",
  "metadata": {
    "file_type": "pdf", 
    "pages": 10
  },
  "task_id": "81d210e0-d935-4448-9985-d2760b17a907",
  "text": "Some extracted text",
  "response": "Agent response text"
}
```

## Root Cause Analysis

The issue was in the `_extract_output_from_result` method in `src/bridge/external_agent_executor.py`. This method was designed to extract only text content from JSON-RPC responses, losing structured data fields.

### Data Flow Path

1. **Agent Response** → JSON-RPC 2.0 response with structured data
2. **Bridge Processing** → `_parse_jsonrpc_response` calls `_extract_output_from_result`
3. **Output Extraction** → ❌ Only text was extracted, structured data lost
4. **Kafka Message** → `AgentResult` published with incomplete `output_data`
5. **Executor Processing** → Incomplete data stored in `step_outputs`
6. **Next Step** → `InputMappingResolver` resolves `${step.output.field}` but data is missing

## The Fix

Modified the `_extract_output_from_result` method to preserve the complete result structure while maintaining backward compatibility.

### Before (Problematic Code)
```python
def _extract_output_from_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
    output = {}
    
    # Only extracted text from artifacts and history
    # Lost all other structured data fields
    
    if not output:
        # Fallback: return full result (but this rarely triggered)
        output = result
    
    return output
```

### After (Fixed Code)
```python
def _extract_output_from_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
    output = {}
    
    # ✅ ALWAYS include the full result for complete data access
    output.update(result)
    
    # Still extract text for backward compatibility
    # ... text extraction logic ...
    
    return output
```

## Files Modified

- **`src/bridge/external_agent_executor.py`** - Fixed `_extract_output_from_result` method

## Testing

Created comprehensive tests to verify the fix:

- **`tests/test_data_flow.py`** - Unit tests for data flow
- **`examples/data_flow_fix_example.py`** - Demonstration example

### Test Results
```bash
$ python tests/test_data_flow.py
Testing input mapping resolver with structured data...
✓ PASSED
Testing extract output preserves structured data...
✓ PASSED
Testing end-to-end data flow...
✓ PASSED

All tests passed! The data flow fix should work correctly.
```

## Impact

### ✅ Benefits
- **Complete Data Preservation**: All structured data from agents is now preserved
- **Backward Compatibility**: Existing workflows using text extraction continue to work
- **Enhanced Capabilities**: Agents can now pass complex data structures between steps
- **Better Debugging**: Full agent responses available for troubleshooting

### 🔄 Migration
- **No Breaking Changes**: Existing workflows continue to work unchanged
- **Immediate Effect**: Fix applies to all new workflow executions
- **Enhanced Input Mapping**: Can now reference any field from previous steps

## Usage Examples

### Basic Data Passing
```json
{
  "input_mapping": {
    "data": "${fetch_data.output.data}",
    "metadata": "${fetch_data.output.metadata}"
  }
}
```

### Complex Nested Data
```json
{
  "input_mapping": {
    "pdf_content": "${extract_pdf.output.data}",
    "page_count": "${extract_pdf.output.metadata.pages}",
    "file_size": "${extract_pdf.output.metadata.size_bytes}"
  }
}
```

### Backward Compatibility
```json
{
  "input_mapping": {
    "text_content": "${process_text.output.text}",
    "agent_response": "${process_text.output.response}"
  }
}
```

## Verification

To verify the fix is working in your environment:

1. **Run the test**: `python tests/test_data_flow.py`
2. **Check logs**: Look for complete `output_data` in step execution logs
3. **Test workflow**: Create a workflow with data passing between steps
4. **Monitor results**: Verify structured data appears in subsequent step inputs

## Related Documentation

- [Workflow Format Guide](docs/guides/WORKFLOW_FORMAT.md)
- [Input Mapping Documentation](docs/features/input_mapping.md)
- [Agent Communication Protocol](docs/api/A2A_AGENT_INTERFACE.md)
- [Testing Guide](examples/TESTING.md)
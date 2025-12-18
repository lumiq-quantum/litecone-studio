# Complete Input Mapping Reference

## 🔄 **How Data Flows from Agent to Next Step**

### **The Complete Flow:**

1. **Agent Execution** → Agent returns JSON-RPC 2.0 response (any format)
2. **Bridge Processing** → `_extract_output_from_result()` preserves ALL fields
3. **Database Storage** → Complete response stored in `step_executions.output_data`
4. **Memory Storage** → Available in `step_outputs[step_id]` for next step
5. **Input Mapping** → Next step can reference any field using `${step_id.output.field}`

### **Key Point: We DON'T tell agents what to return!**
- ✅ Agents return whatever they want (following JSON-RPC 2.0)
- ✅ System preserves ALL fields automatically
- ✅ Works with any A2A-compliant agent

---

## 📝 **All Input Mapping Possibilities**

### **1. Workflow Input Variables**

Access data provided when starting the workflow:

```json
{
  "user_query": "${workflow.input.query}",
  "user_id": "${workflow.input.user_id}",
  "settings": "${workflow.input.config}",
  "nested_data": "${workflow.input.user.profile.name}"
}
```

**Examples:**
- `${workflow.input.topic}` - Simple field
- `${workflow.input.user.email}` - Nested field
- `${workflow.input.settings.max_results}` - Deep nested field

### **2. Step Output Variables**

Access data from any previous step:

```json
{
  "previous_result": "${fetch_data.output.text}",
  "agent_response": "${fetch_data.output.response}",
  "metadata": "${fetch_data.output.metadata}",
  "custom_field": "${fetch_data.output.custom_data}"
}
```

### **3. Standard Agent Output Fields (Always Available)**

Every A2A agent response includes these fields:

```json
{
  "main_content": "${step_id.output.text}",
  "agent_message": "${step_id.output.response}",
  "task_identifier": "${step_id.output.id}",
  "task_id": "${step_id.output.task_id}",
  "response_type": "${step_id.output.kind}",
  "execution_status": "${step_id.output.status}",
  "structured_artifacts": "${step_id.output.artifacts}",
  "conversation_history": "${step_id.output.history}",
  "agent_metadata": "${step_id.output.metadata}",
  "session_context": "${step_id.output.context_id}"
}
```

### **4. Nested Field Access**

Access nested data within agent responses:

```json
{
  "completion_state": "${process_data.output.status.state}",
  "completion_time": "${process_data.output.status.timestamp}",
  "processing_duration": "${process_data.output.metadata.processing_time_ms}",
  "confidence_score": "${analyze.output.metadata.confidence}",
  "first_artifact_text": "${extract.output.artifacts[0].parts[0].text}"
}
```

### **5. Loop Context Variables (When Inside Loops)**

When executing within loop iterations:

```json
{
  "current_item": "${loop.item}",
  "iteration_number": "${loop.index}",
  "total_items": "${loop.total}",
  "is_first_iteration": "${loop.is_first}",
  "is_last_iteration": "${loop.is_last}",
  "item_data": "${process_item.output.text}"
}
```

### **6. Mixed Content and String Interpolation**

Combine multiple variables in strings:

```json
{
  "summary": "Processing ${workflow.input.filename} - Status: ${extract.output.status.state}",
  "log_message": "User ${workflow.input.user_id} processed ${loop.total} items",
  "file_path": "/data/${workflow.input.project}/${extract.output.filename}"
}
```

### **7. Complex Data Structures**

Pass entire objects or arrays:

```json
{
  "complete_metadata": "${fetch_data.output.metadata}",
  "all_artifacts": "${process.output.artifacts}",
  "full_history": "${chat.output.history}",
  "entire_response": "${agent_call.output}"
}
```

---

## 🎯 **Real-World Examples by Agent Type**

### **PDF Processing Agent**
```json
{
  "pdf_content": "${extract_pdf.output.text}",
  "page_count": "${extract_pdf.output.metadata.pages}",
  "file_size": "${extract_pdf.output.metadata.size_bytes}",
  "extracted_tables": "${extract_pdf.output.artifacts}",
  "processing_status": "${extract_pdf.output.status.state}"
}
```

### **Data Analysis Agent**
```json
{
  "analysis_results": "${analyze.output.text}",
  "insights": "${analyze.output.insights}",
  "confidence": "${analyze.output.confidence_score}",
  "recommendations": "${analyze.output.recommendations}",
  "raw_data": "${analyze.output.processed_data}"
}
```

### **Translation Agent**
```json
{
  "translated_text": "${translate.output.text}",
  "source_language": "${translate.output.metadata.source_lang}",
  "target_language": "${translate.output.metadata.target_lang}",
  "confidence": "${translate.output.metadata.confidence}",
  "alternative_translations": "${translate.output.alternatives}"
}
```

### **Research Agent**
```json
{
  "research_findings": "${research.output.text}",
  "sources": "${research.output.sources}",
  "citations": "${research.output.citations}",
  "summary": "${research.output.summary}",
  "confidence_level": "${research.output.metadata.confidence}"
}
```

### **Hello World / Simple Agent**
```json
{
  "greeting": "${hello.output.text}",
  "agent_response": "${hello.output.response}",
  "task_info": "${hello.output.id}",
  "completion_status": "${hello.output.status.state}"
}
```

---

## 🔧 **Advanced Patterns**

### **Multi-Step Data Chaining**
```json
{
  "original_query": "${workflow.input.query}",
  "research_data": "${research.output.text}",
  "analysis_results": "${analyze.output.text}",
  "final_summary": "${summarize.output.text}",
  "combined_metadata": {
    "research_confidence": "${research.output.metadata.confidence}",
    "analysis_confidence": "${analyze.output.metadata.confidence}",
    "processing_times": {
      "research": "${research.output.metadata.duration}",
      "analysis": "${analyze.output.metadata.duration}"
    }
  }
}
```

### **Conditional Data Access**
```json
{
  "primary_result": "${main_process.output.text}",
  "fallback_result": "${backup_process.output.text}",
  "status_check": "${main_process.output.status.state}",
  "error_info": "${main_process.output.error_message}"
}
```

### **Array and List Processing**
```json
{
  "all_results": "${batch_process.output.results}",
  "first_result": "${batch_process.output.results[0]}",
  "result_count": "${batch_process.output.metadata.count}",
  "processing_summary": "${batch_process.output.summary}"
}
```

---

## ⚠️ **Important Rules and Limitations**

### **✅ Valid Syntax:**
- `${workflow.input.field}` - Workflow input
- `${step_id.output.field}` - Step output
- `${step_id.output.nested.field}` - Nested fields
- `${loop.item}` - Loop context (inside loops only)

### **❌ Invalid Syntax:**
- `$.workflow.input.field` - Wrong prefix
- `$.steps.step_id.output.field` - Wrong format
- `{step_id.output.field}` - Missing $
- `step_id.output.field` - Missing ${}

### **🔍 String Interpolation Rules:**
- **Single variable**: `"${step.output.data}"` → Returns actual data type
- **Mixed content**: `"Status: ${step.output.status}"` → Returns string
- **Multiple variables**: `"${user}: ${message}"` → Returns string
- **Complex types**: Use single variable reference for objects/arrays

### **📋 Field Resolution:**
1. **Exact match required** - Field names are case-sensitive
2. **Step must exist** - Referenced step must have completed
3. **Field must exist** - Will error if field not found
4. **Nested access** - Use dot notation for nested fields

---

## 🛠️ **Debugging and Discovery**

### **Find Available Fields:**

1. **Check Run Details** - View step execution in UI
2. **Database Query**:
   ```sql
   SELECT jsonb_pretty(output_data) 
   FROM step_executions 
   WHERE step_id = 'your_step_id' 
   ORDER BY started_at DESC LIMIT 1;
   ```
3. **Debug Script**:
   ```bash
   python debug_step_output.py [run_id]
   ```

### **Common Field Discovery:**
```bash
# List all available fields from a step
SELECT jsonb_object_keys(output_data) as available_fields 
FROM step_executions 
WHERE step_id = 'fetch_data';
```

---

## 📚 **Quick Reference Card**

### **Most Common Patterns:**
```json
{
  "user_input": "${workflow.input.query}",
  "previous_text": "${step1.output.text}",
  "previous_response": "${step1.output.response}",
  "metadata": "${step1.output.metadata}",
  "status": "${step1.output.status.state}",
  "nested_data": "${step1.output.data.results[0].value}"
}
```

### **Safe Defaults (Always Work):**
- `${step.output.text}` - Main content
- `${step.output.response}` - Agent message
- `${step.output.id}` - Task identifier
- `${workflow.input.*}` - User input

---

## 🎯 **Summary**

**The system is designed to work with ANY A2A agent:**
1. **Agents return whatever they want** (following JSON-RPC 2.0)
2. **System preserves ALL fields** automatically
3. **You can reference ANY field** the agent returned
4. **Use `text` or `response`** if unsure what's available
5. **Check run details** to discover available fields

**The input mapping is flexible and powerful - you can access any data structure the agents return!**
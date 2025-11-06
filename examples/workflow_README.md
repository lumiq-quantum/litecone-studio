# Sample Workflow Examples

This directory contains example workflow definitions and inputs for the Centralized Executor.

## Files

### sample_workflow.json

A 2-step sequential workflow that demonstrates:
- **Step 1 (ResearchAgent)**: Performs research on a given topic
- **Step 2 (WriterAgent)**: Writes content based on research findings

This workflow showcases:
- Sequential execution using `next_step` references
- Input mapping from workflow initial input using `${workflow.input.field}` syntax
- Input mapping from previous step outputs using `${step-id.output.field}` syntax

### sample_workflow_input.json

Example input payload for executing the sample workflow, including:
- `run_id`: Unique identifier for this workflow execution
- `workflow_plan`: Path to the workflow definition
- `initial_input`: Input data that will be mapped to step inputs

## Workflow Execution Flow

1. **Step 1 (ResearchAgent)** receives:
   ```json
   {
     "topic": "Climate Change Impact on Agriculture",
     "depth": "comprehensive",
     "sources": ["scientific journals", "government reports"]
   }
   ```

2. **Step 1** produces output (example):
   ```json
   {
     "findings": [...],
     "summary": "Research summary text..."
   }
   ```

3. **Step 2 (WriterAgent)** receives:
   ```json
   {
     "research_data": [...],  // from step-1.output.findings
     "summary": "Research summary text...",  // from step-1.output.summary
     "style": "academic",  // from workflow.input.writing_style
     "word_count": 1500  // from workflow.input.target_word_count
   }
   ```

## Input Mapping Syntax

The workflow uses variable substitution to map data:

- `${workflow.input.field}` - References fields from the initial workflow input
- `${step-id.output.field}` - References output fields from a previous step

## Usage

To execute this workflow with the Centralized Executor:

```bash
# Set environment variables
export RUN_ID="run-12345-abcde"
export WORKFLOW_PLAN=$(cat examples/sample_workflow.json)
export INITIAL_INPUT=$(cat examples/sample_workflow_input.json | jq '.initial_input')

# Run the executor
python -m src.executor
```

Or via Docker:

```bash
docker run -e RUN_ID="run-12345-abcde" \
  -e WORKFLOW_PLAN="$(cat examples/sample_workflow.json)" \
  -e INITIAL_INPUT="$(cat examples/sample_workflow_input.json | jq '.initial_input')" \
  centralized-executor:latest
```

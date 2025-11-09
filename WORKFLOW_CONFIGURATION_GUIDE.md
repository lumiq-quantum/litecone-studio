# Workflow Configuration Guide

This guide explains how to create, configure, and execute workflows in the Centralized Executor system.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Workflow Structure](#workflow-structure)
3. [Step-by-Step Configuration](#step-by-step-configuration)
4. [Input Mapping](#input-mapping)
5. [Agent Registration](#agent-registration)
6. [Execution](#execution)
7. [Examples](#examples)
8. [Best Practices](#best-practices)

---

## Quick Start

### 1. Create Workflow JSON

Create a file `my_workflow.json`:

```json
{
  "workflow_id": "my-workflow-001",
  "name": "my-workflow",
  "version": "1.0.0",
  "start_step": "step-1",
  "steps": {
    "step-1": {
      "id": "step-1",
      "agent_name": "MyAgent",
      "next_step": null,
      "input_mapping": {
        "input_field": "${workflow.input.my_field}"
      }
    }
  }
}
```

### 2. Create Input JSON

Create a file `my_input.json`:

```json
{
  "my_field": "Hello World"
}
```

### 3. Run the Workflow

```bash
export RUN_ID="test-$(date +%s)"
export WORKFLOW_PLAN=$(cat my_workflow.json)
export WORKFLOW_INPUT=$(cat my_input.json)

docker compose run --rm \
  -e RUN_ID="$RUN_ID" \
  -e WORKFLOW_PLAN="$WORKFLOW_PLAN" \
  -e WORKFLOW_INPUT="$WORKFLOW_INPUT" \
  -e KAFKA_BROKERS=kafka:29092 \
  -e DATABASE_URL=postgresql://workflow_user:workflow_pass@postgres:5432/workflow_db \
  -e AGENT_REGISTRY_URL=http://agent-registry:8080 \
  -e LOG_FORMAT=text \
  executor
```

---

## Workflow Structure

A workflow consists of:

1. **Metadata** - Workflow identification and versioning
2. **Steps** - Individual tasks executed by agents
3. **Flow Control** - Sequential execution via `next_step` references
4. **Input Mapping** - How data flows between steps

### Workflow JSON Schema

```json
{
  "workflow_id": "string",        // Unique identifier
  "name": "string",               // Human-readable name
  "version": "string",            // Version (e.g., "1.0.0")
  "start_step": "string",         // ID of first step
  "steps": {
    "step-id": {
      "id": "string",             // Step identifier
      "agent_name": "string",     // Agent to execute this step
      "next_step": "string|null", // Next step ID (null = end)
      "input_mapping": {          // Input data mapping
        "field": "${reference}"
      }
    }
  }
}
```

---

## Step-by-Step Configuration

### Step 1: Define Workflow Metadata

```json
{
  "workflow_id": "data-processing-pipeline-001",
  "name": "data-processing-pipeline",
  "version": "1.0.0",
  "start_step": "extract"
}
```

**Fields:**
- `workflow_id`: Unique identifier (use kebab-case)
- `name`: Short, descriptive name
- `version`: Semantic versioning (major.minor.patch)
- `start_step`: Must match a step ID in the `steps` object

### Step 2: Define Steps

Each step represents a task executed by an agent.

#### Single Step Workflow

```json
{
  "workflow_id": "simple-task-001",
  "name": "simple-task",
  "version": "1.0.0",
  "start_step": "process",
  "steps": {
    "process": {
      "id": "process",
      "agent_name": "DataProcessor",
      "next_step": null,
      "input_mapping": {
        "data": "${workflow.input.raw_data}"
      }
    }
  }
}
```

#### Multi-Step Sequential Workflow

```json
{
  "workflow_id": "etl-pipeline-001",
  "name": "etl-pipeline",
  "version": "1.0.0",
  "start_step": "extract",
  "steps": {
    "extract": {
      "id": "extract",
      "agent_name": "DataExtractor",
      "next_step": "transform",
      "input_mapping": {
        "source": "${workflow.input.data_source}",
        "query": "${workflow.input.query}"
      }
    },
    "transform": {
      "id": "transform",
      "agent_name": "DataTransformer",
      "next_step": "load",
      "input_mapping": {
        "raw_data": "${extract.output.data}",
        "schema": "${workflow.input.target_schema}"
      }
    },
    "load": {
      "id": "load",
      "agent_name": "DataLoader",
      "next_step": null,
      "input_mapping": {
        "transformed_data": "${transform.output.data}",
        "destination": "${workflow.input.destination}"
      }
    }
  }
}
```

### Step 3: Configure Input Mapping

Input mapping defines how data flows into each step.

#### Syntax

```
${workflow.input.field_name}     - From workflow input
${step-id.output.field_name}     - From previous step output
```

#### Examples

**From Workflow Input:**
```json
{
  "input_mapping": {
    "topic": "${workflow.input.research_topic}",
    "depth": "${workflow.input.analysis_depth}"
  }
}
```

**From Previous Step:**
```json
{
  "input_mapping": {
    "research_data": "${research-step.output.findings}",
    "summary": "${research-step.output.summary}"
  }
}
```

**Mixed Sources:**
```json
{
  "input_mapping": {
    "data": "${extract-step.output.raw_data}",
    "format": "${workflow.input.output_format}",
    "metadata": "${extract-step.output.metadata}"
  }
}
```

---

## Input Mapping

### Variable References

#### Workflow Input

Access initial workflow input data:

```json
"${workflow.input.field_name}"
```

**Example:**
```json
// Workflow input
{
  "topic": "AI",
  "language": "English"
}

// Input mapping
{
  "research_topic": "${workflow.input.topic}",
  "output_language": "${workflow.input.language}"
}

// Resolved to
{
  "research_topic": "AI",
  "output_language": "English"
}
```

#### Step Output

Access output from previous steps:

```json
"${step-id.output.field_name}"
```

**Example:**
```json
// Step 1 output
{
  "findings": ["Finding 1", "Finding 2"],
  "confidence": 0.95
}

// Step 2 input mapping
{
  "research_results": "${step-1.output.findings}",
  "quality_score": "${step-1.output.confidence}"
}

// Resolved to
{
  "research_results": ["Finding 1", "Finding 2"],
  "quality_score": 0.95
}
```

#### Nested Fields

Access nested fields using dot notation:

```json
"${step-1.output.metadata.author}"
```

**Example:**
```json
// Step output
{
  "result": {
    "data": {
      "items": [1, 2, 3],
      "count": 3
    }
  }
}

// Input mapping
{
  "items": "${step-1.output.result.data.items}",
  "total": "${step-1.output.result.data.count}"
}
```

### Data Types

Input mapping preserves data types:

```json
// Workflow input
{
  "count": 42,                    // number
  "enabled": true,                // boolean
  "tags": ["ai", "ml"],          // array
  "config": {"key": "value"}     // object
}

// Input mapping
{
  "num": "${workflow.input.count}",      // → 42 (number)
  "flag": "${workflow.input.enabled}",   // → true (boolean)
  "list": "${workflow.input.tags}",      // → ["ai", "ml"] (array)
  "obj": "${workflow.input.config}"      // → {"key": "value"} (object)
}
```

### String Interpolation

**Not Supported:** You cannot mix variables with static text:

```json
// ❌ This will NOT work
{
  "message": "Hello ${workflow.input.name}!"
}
```

**Workaround:** Pass the full value and let the agent handle formatting:

```json
// ✅ Do this instead
{
  "name": "${workflow.input.name}",
  "greeting_template": "Hello {name}!"
}
```

---

## Agent Registration

Before running a workflow, ensure all agents are registered in the Agent Registry.

### Mock Agent Registry

For testing, the mock registry is pre-configured with:
- `ResearchAgent` - http://research-agent:8080
- `WriterAgent` - http://writer-agent:8080

### Adding a New Agent

#### Option 1: Update Mock Registry

Edit `examples/mock_agent_registry.py`:

```python
AGENTS = {
    "ResearchAgent": {...},
    "WriterAgent": {...},
    "MyNewAgent": {
        "name": "MyNewAgent",
        "url": "http://my-agent:8080",
        "auth_config": None,
        "timeout": 30000,
        "retry_config": {
            "max_retries": 3,
            "initial_delay_ms": 1000,
            "max_delay_ms": 30000,
            "backoff_multiplier": 2.0
        }
    }
}
```

Restart the agent registry:
```bash
docker compose -f docker-compose.test.yml restart agent-registry
```

#### Option 2: Production Agent Registry

In production, implement a proper Agent Registry API that:
1. Stores agent metadata in a database
2. Provides REST endpoints for CRUD operations
3. Supports dynamic agent registration

---

## Execution

### Method 1: Docker Compose (Recommended)

```bash
# Set environment variables
export RUN_ID="my-run-$(date +%s)"
export WORKFLOW_PLAN=$(cat my_workflow.json)
export WORKFLOW_INPUT=$(cat my_input.json)

# Run workflow
docker compose run --rm \
  -e RUN_ID="$RUN_ID" \
  -e WORKFLOW_PLAN="$WORKFLOW_PLAN" \
  -e WORKFLOW_INPUT="$WORKFLOW_INPUT" \
  -e KAFKA_BROKERS=kafka:29092 \
  -e DATABASE_URL=postgresql://workflow_user:workflow_pass@postgres:5432/workflow_db \
  -e AGENT_REGISTRY_URL=http://agent-registry:8080 \
  -e LOG_LEVEL=INFO \
  -e LOG_FORMAT=text \
  executor
```

### Method 2: Python Script

```python
import asyncio
import json
from src.executor.centralized_executor import CentralizedExecutor
from src.models.workflow import WorkflowPlan

async def run_workflow():
    # Load workflow
    with open('my_workflow.json', 'r') as f:
        workflow_dict = json.load(f)
    workflow_plan = WorkflowPlan(**workflow_dict)
    
    # Load input
    with open('my_input.json', 'r') as f:
        workflow_input = json.load(f)
    
    # Create executor
    executor = CentralizedExecutor(
        run_id="my-run-123",
        workflow_plan=workflow_plan,
        initial_input=workflow_input,
        kafka_bootstrap_servers="localhost:9092",
        database_url="postgresql://workflow_user:workflow_pass@localhost:5432/workflow_db",
        agent_registry_url="http://localhost:8080"
    )
    
    try:
        await executor.initialize()
        await executor.load_execution_state()
        await executor.execute_workflow()
    finally:
        await executor.shutdown()

asyncio.run(run_workflow())
```

### Method 3: Shell Script

Create `run_workflow.sh`:

```bash
#!/bin/bash

WORKFLOW_FILE=${1:-"workflow.json"}
INPUT_FILE=${2:-"input.json"}
RUN_ID=${3:-"run-$(date +%s)"}

echo "Running workflow: $WORKFLOW_FILE"
echo "Input: $INPUT_FILE"
echo "Run ID: $RUN_ID"

export RUN_ID="$RUN_ID"
export WORKFLOW_PLAN=$(cat "$WORKFLOW_FILE")
export WORKFLOW_INPUT=$(cat "$INPUT_FILE")

docker compose run --rm \
  -e RUN_ID="$RUN_ID" \
  -e WORKFLOW_PLAN="$WORKFLOW_PLAN" \
  -e WORKFLOW_INPUT="$WORKFLOW_INPUT" \
  -e KAFKA_BROKERS=kafka:29092 \
  -e DATABASE_URL=postgresql://workflow_user:workflow_pass@postgres:5432/workflow_db \
  -e AGENT_REGISTRY_URL=http://agent-registry:8080 \
  -e LOG_FORMAT=text \
  executor
```

Usage:
```bash
chmod +x run_workflow.sh
./run_workflow.sh my_workflow.json my_input.json my-custom-run-id
```

---

## Examples

### Example 1: Simple Data Processing

**Workflow:** `data_processing.json`
```json
{
  "workflow_id": "data-processing-001",
  "name": "data-processing",
  "version": "1.0.0",
  "start_step": "process",
  "steps": {
    "process": {
      "id": "process",
      "agent_name": "DataProcessor",
      "next_step": null,
      "input_mapping": {
        "data": "${workflow.input.raw_data}",
        "format": "${workflow.input.output_format}"
      }
    }
  }
}
```

**Input:** `data_input.json`
```json
{
  "raw_data": [1, 2, 3, 4, 5],
  "output_format": "json"
}
```

**Run:**
```bash
export RUN_ID="data-proc-$(date +%s)"
export WORKFLOW_PLAN=$(cat data_processing.json)
export WORKFLOW_INPUT=$(cat data_input.json)
# ... run executor
```

---

### Example 2: Research and Write Pipeline

**Workflow:** `research_write.json`
```json
{
  "workflow_id": "research-write-001",
  "name": "research-and-write",
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
        "sources": "${workflow.input.sources}"
      }
    },
    "write": {
      "id": "write",
      "agent_name": "WriterAgent",
      "next_step": null,
      "input_mapping": {
        "research_data": "${research.output.findings}",
        "summary": "${research.output.summary}",
        "style": "${workflow.input.style}",
        "word_count": "${workflow.input.word_count}"
      }
    }
  }
}
```

**Input:** `research_input.json`
```json
{
  "topic": "Quantum Computing",
  "depth": "comprehensive",
  "sources": ["scientific journals", "arxiv"],
  "style": "academic",
  "word_count": 2000
}
```

---

### Example 3: ETL Pipeline

**Workflow:** `etl_pipeline.json`
```json
{
  "workflow_id": "etl-pipeline-001",
  "name": "etl-pipeline",
  "version": "1.0.0",
  "start_step": "extract",
  "steps": {
    "extract": {
      "id": "extract",
      "agent_name": "DataExtractor",
      "next_step": "transform",
      "input_mapping": {
        "source_url": "${workflow.input.source}",
        "query": "${workflow.input.query}",
        "credentials": "${workflow.input.credentials}"
      }
    },
    "transform": {
      "id": "transform",
      "agent_name": "DataTransformer",
      "next_step": "validate",
      "input_mapping": {
        "raw_data": "${extract.output.data}",
        "schema": "${workflow.input.target_schema}",
        "transformations": "${workflow.input.transformations}"
      }
    },
    "validate": {
      "id": "validate",
      "agent_name": "DataValidator",
      "next_step": "load",
      "input_mapping": {
        "data": "${transform.output.transformed_data}",
        "rules": "${workflow.input.validation_rules}"
      }
    },
    "load": {
      "id": "load",
      "agent_name": "DataLoader",
      "next_step": null,
      "input_mapping": {
        "data": "${validate.output.validated_data}",
        "destination": "${workflow.input.destination}",
        "batch_size": "${workflow.input.batch_size}"
      }
    }
  }
}
```

**Input:** `etl_input.json`
```json
{
  "source": "https://api.example.com/data",
  "query": "SELECT * FROM users WHERE active = true",
  "credentials": {"api_key": "secret"},
  "target_schema": {
    "id": "integer",
    "name": "string",
    "email": "string"
  },
  "transformations": ["lowercase_email", "trim_whitespace"],
  "validation_rules": ["email_format", "required_fields"],
  "destination": "postgresql://localhost/warehouse",
  "batch_size": 1000
}
```

---

## Best Practices

### 1. Workflow Design

✅ **DO:**
- Use descriptive workflow IDs and names
- Keep workflows focused on a single purpose
- Use semantic versioning
- Document expected input/output formats

❌ **DON'T:**
- Create overly complex workflows (>10 steps)
- Use generic names like "workflow1"
- Skip version numbers
- Assume input structure without validation

### 2. Step Configuration

✅ **DO:**
- Use clear, descriptive step IDs
- Map all required agent inputs
- Handle optional fields gracefully
- Test each step independently

❌ **DON'T:**
- Use cryptic step IDs like "s1", "s2"
- Leave required fields unmapped
- Assume previous step output structure
- Skip error handling

### 3. Input Mapping

✅ **DO:**
- Use explicit field mappings
- Validate input data before execution
- Document variable references
- Test with sample data

❌ **DON'T:**
- Use string interpolation (not supported)
- Reference non-existent fields
- Assume data types
- Skip input validation

### 4. Error Handling

✅ **DO:**
- Configure appropriate retry settings
- Monitor workflow execution
- Log all errors
- Implement fallback strategies

❌ **DON'T:**
- Ignore failed steps
- Use infinite retries
- Skip logging
- Assume success

### 5. Testing

✅ **DO:**
- Test with mock agents first
- Validate workflow JSON structure
- Test with various input data
- Monitor database and Kafka

❌ **DON'T:**
- Test directly in production
- Skip validation
- Use production data for testing
- Ignore monitoring

---

## Validation

### Validate Workflow JSON

```python
from src.models.workflow import WorkflowPlan
import json

# Load workflow
with open('my_workflow.json', 'r') as f:
    workflow_dict = json.load(f)

# Validate (will raise exception if invalid)
try:
    workflow = WorkflowPlan(**workflow_dict)
    print("✓ Workflow is valid")
except Exception as e:
    print(f"✗ Workflow is invalid: {e}")
```

### Common Validation Errors

**Error:** `start_step 'step-1' not found in steps dictionary`
**Fix:** Ensure `start_step` matches a key in `steps`

**Error:** `Step 'step-2' references non-existent next_step 'step-3'`
**Fix:** Ensure all `next_step` values reference valid step IDs

**Error:** `Circular reference detected in workflow at step 'step-1'`
**Fix:** Remove circular references (step A → step B → step A)

**Error:** `Workflow must have at least one terminal step`
**Fix:** Ensure at least one step has `next_step: null`

---

## Monitoring

### Check Workflow Status

```bash
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "SELECT run_id, status, created_at, completed_at 
   FROM workflow_runs 
   WHERE run_id = 'your-run-id';"
```

### Check Step Execution

```bash
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "SELECT step_id, agent_name, status, started_at, completed_at 
   FROM step_executions 
   WHERE run_id = 'your-run-id' 
   ORDER BY started_at;"
```

### View Step Output

```bash
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "SELECT step_id, output_data 
   FROM step_executions 
   WHERE run_id = 'your-run-id';"
```

---

## Troubleshooting

### Workflow Not Starting

**Check:**
1. All services are running
2. Workflow JSON is valid
3. Input JSON is valid
4. Environment variables are set

### Step Failing

**Check:**
1. Agent is registered in Agent Registry
2. Agent is running and healthy
3. Input mapping is correct
4. Agent logs for errors

### Timeout Errors

**Solutions:**
1. Increase agent timeout in Agent Registry
2. Optimize agent processing time
3. Check network connectivity
4. Review agent logs

---

## See Also

- [WORKFLOW_FORMAT.md](WORKFLOW_FORMAT.md) - Detailed workflow specification
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference
- [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md) - Testing guide
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [examples/](examples/) - Example workflows

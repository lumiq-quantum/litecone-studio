# Migration Scripts

This directory contains scripts to help migrate from CLI-based workflow execution to the API-based Workflow Management system.

## Scripts

### 1. migrate_workflows.py

Import existing workflow JSON files into the Workflow Management API database.

**Usage:**
```bash
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --api-url http://localhost:8000 \
  --verbose
```

**Options:**
- `--workflow-dir`: Directory containing workflow JSON files (required)
- `--api-url`: API base URL (default: http://localhost:8000)
- `--api-key`: API key for authentication (optional)
- `--skip-existing`: Skip workflows that already exist
- `--dry-run`: Validate workflows without importing
- `--verbose`: Show detailed output

**Example:**
```bash
# Dry run to validate workflows
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --dry-run \
  --verbose

# Import workflows, skipping existing ones
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --skip-existing
```

### 2. register_agents.py

Register agents from a YAML configuration file into the Workflow Management API.

**Usage:**
```bash
python3 scripts/register_agents.py \
  --config scripts/agents.yaml \
  --api-url http://localhost:8000 \
  --verbose
```

**Options:**
- `--config`: YAML configuration file with agent definitions (required)
- `--api-url`: API base URL (default: http://localhost:8000)
- `--api-key`: API key for authentication (optional)
- `--skip-existing`: Skip agents that already exist
- `--verbose`: Show detailed output

**Configuration Format:**

Create a `agents.yaml` file (see `agents.yaml.example`):

```yaml
agents:
  - name: ResearchAgent
    url: http://research-agent:8081
    description: Research agent
    auth_type: none
    timeout_ms: 30000
    retry_config:
      max_retries: 3
      initial_delay_ms: 1000
      max_delay_ms: 30000
      backoff_multiplier: 2.0
```

**Example:**
```bash
# Copy example configuration
cp scripts/agents.yaml.example scripts/agents.yaml

# Edit agents.yaml with your agent details
vim scripts/agents.yaml

# Register agents
python3 scripts/register_agents.py \
  --config scripts/agents.yaml \
  --skip-existing
```

## Dependencies

The scripts use dependencies already included in the main requirements file:

```bash
pip install -r requirements.txt
```

Required packages:
- `httpx` - HTTP client for API calls
- `pyyaml` - YAML configuration parsing

## Migration Workflow

Follow these steps for a complete migration:

### Step 1: Start API Service

```bash
docker compose --profile api up -d
```

### Step 2: Register Agents

```bash
# Create agent configuration
cp scripts/agents.yaml.example scripts/agents.yaml
# Edit agents.yaml with your agents

# Register agents
python3 scripts/register_agents.py \
  --config scripts/agents.yaml \
  --verbose
```

### Step 3: Import Workflows

```bash
# Validate workflows first
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --dry-run \
  --verbose

# Import workflows
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --verbose
```

### Step 4: Verify Migration

```bash
# List registered agents
curl http://localhost:8000/api/v1/agents | jq

# List imported workflows
curl http://localhost:8000/api/v1/workflows | jq
```

### Step 5: Test Execution

```bash
# Get workflow ID
WORKFLOW_ID=$(curl -s http://localhost:8000/api/v1/workflows | \
  jq -r '.items[0].id')

# Execute workflow
curl -X POST http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/execute \
  -H "Content-Type: application/json" \
  -d @examples/sample_workflow_input.json | jq
```

## Troubleshooting

### Script fails with "Cannot connect to API"

**Solution:**
```bash
# Check API is running
docker compose ps api

# Check API health
curl http://localhost:8000/health

# Start API if needed
docker compose --profile api up -d
```

### "Missing agents" error during workflow import

**Solution:**
```bash
# Register agents first
python3 scripts/register_agents.py --config scripts/agents.yaml

# Then import workflows
python3 scripts/migrate_workflows.py --workflow-dir examples/
```

### "Agent already exists" error

**Solution:**
```bash
# Use --skip-existing flag
python3 scripts/register_agents.py \
  --config scripts/agents.yaml \
  --skip-existing
```

### Import fails with validation errors

**Solution:**
```bash
# Use dry-run to see validation errors
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --dry-run \
  --verbose

# Fix workflow JSON files based on errors
# Then import again
```

## Advanced Usage

### Import from Multiple Directories

```bash
# Import workflows from different directories
for dir in workflows/prod workflows/dev workflows/test; do
  python3 scripts/migrate_workflows.py \
    --workflow-dir $dir \
    --skip-existing
done
```

### Register Agents from Multiple Configs

```bash
# Register different agent groups
python3 scripts/register_agents.py --config agents-prod.yaml
python3 scripts/register_agents.py --config agents-dev.yaml
```

### Use with Authentication

```bash
# Set API key
export API_KEY="your-api-key-here"

# Register agents with authentication
python3 scripts/register_agents.py \
  --config scripts/agents.yaml \
  --api-key $API_KEY

# Import workflows with authentication
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --api-key $API_KEY
```

## See Also

- [Migration Guide](../MIGRATION_GUIDE.md) - Complete migration documentation
- [API Documentation](../API_DOCUMENTATION.md) - API endpoint reference
- [Quick Start](../QUICKSTART.md) - Getting started guide

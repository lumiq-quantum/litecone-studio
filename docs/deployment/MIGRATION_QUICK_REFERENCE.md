# Migration Quick Reference

Quick commands for migrating from CLI-based to API-based workflow execution.

## Prerequisites

```bash
# Start API service
docker compose --profile api up -d

# Verify API is running
curl http://localhost:8000/health
```

## 1. Register Agents

```bash
# Create agent config from example
cp scripts/agents.yaml.example scripts/agents.yaml

# Edit with your agents
vim scripts/agents.yaml

# Register agents
python3 scripts/register_agents.py \
  --config scripts/agents.yaml \
  --skip-existing \
  --verbose

# Verify
curl http://localhost:8000/api/v1/agents | jq
```

## 2. Import Workflows

```bash
# Validate first (dry run)
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --dry-run \
  --verbose

# Import workflows
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --skip-existing \
  --verbose

# Verify
curl http://localhost:8000/api/v1/workflows | jq
```

## 3. Execute Workflows

### Old Way (CLI)
```bash
export RUN_ID="test-$(date +%s)"
export WORKFLOW_PLAN=$(cat examples/sample_workflow.json)
export WORKFLOW_INPUT=$(cat examples/sample_workflow_input.json)

docker-compose run --rm \
  -e RUN_ID="$RUN_ID" \
  -e WORKFLOW_PLAN="$WORKFLOW_PLAN" \
  -e WORKFLOW_INPUT="$WORKFLOW_INPUT" \
  executor
```

### New Way (API)
```bash
# Get workflow ID
WORKFLOW_ID=$(curl -s http://localhost:8000/api/v1/workflows?name=research-and-write | \
  jq -r '.items[0].id')

# Execute workflow
RUN_RESPONSE=$(curl -s -X POST \
  http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/execute \
  -H "Content-Type: application/json" \
  -d @examples/sample_workflow_input.json)

# Get run ID
RUN_ID=$(echo $RUN_RESPONSE | jq -r '.run_id')
echo "Started: $RUN_ID"

# Monitor execution
curl http://localhost:8000/api/v1/runs/$RUN_ID | jq
```

## 4. Monitor Runs

### Old Way (CLI)
```bash
docker exec -it postgres psql -U workflow_user -d workflow_db \
  -c "SELECT * FROM workflow_runs WHERE run_id = '$RUN_ID';"
```

### New Way (API)
```bash
# Get run details
curl http://localhost:8000/api/v1/runs/$RUN_ID | jq

# Get step executions
curl http://localhost:8000/api/v1/runs/$RUN_ID/steps | jq

# List all runs
curl "http://localhost:8000/api/v1/runs?page=1&page_size=10" | jq

# Filter by status
curl "http://localhost:8000/api/v1/runs?status=COMPLETED" | jq
```

## 5. Retry Failed Runs

### Old Way (CLI)
```bash
# Re-run with same RUN_ID
docker-compose run --rm \
  -e RUN_ID="$RUN_ID" \
  -e WORKFLOW_PLAN="$WORKFLOW_PLAN" \
  -e WORKFLOW_INPUT="$WORKFLOW_INPUT" \
  executor
```

### New Way (API)
```bash
# Single API call
curl -X POST http://localhost:8000/api/v1/runs/$RUN_ID/retry | jq
```

## 6. Cancel Running Workflows

### New Feature (API Only)
```bash
curl -X POST http://localhost:8000/api/v1/runs/$RUN_ID/cancel | jq
```

## Common Tasks

### List All Agents
```bash
curl http://localhost:8000/api/v1/agents | jq
```

### List All Workflows
```bash
curl http://localhost:8000/api/v1/workflows | jq
```

### Get Workflow Details
```bash
curl http://localhost:8000/api/v1/workflows/$WORKFLOW_ID | jq
```

### Get Workflow Versions
```bash
curl http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/versions | jq
```

### Update Agent
```bash
curl -X PUT http://localhost:8000/api/v1/agents/$AGENT_ID \
  -H "Content-Type: application/json" \
  -d '{"timeout_ms": 60000}' | jq
```

### Update Workflow
```bash
curl -X PUT http://localhost:8000/api/v1/workflows/$WORKFLOW_ID \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated description"}' | jq
```

### Delete Agent (Soft Delete)
```bash
curl -X DELETE http://localhost:8000/api/v1/agents/$AGENT_ID
```

### Delete Workflow (Soft Delete)
```bash
curl -X DELETE http://localhost:8000/api/v1/workflows/$WORKFLOW_ID
```

## API Documentation

### Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# Readiness (includes DB check)
curl http://localhost:8000/health/ready

# Metrics (if enabled)
curl http://localhost:8000/metrics
```

## Troubleshooting

### API Not Responding
```bash
# Check API status
docker compose ps api

# View logs
docker compose logs api

# Restart API
docker compose restart api
```

### Database Issues
```bash
# Check database
docker exec postgres pg_isready -U workflow_user

# Run migrations
docker compose exec api alembic upgrade head
```

### Workflow Import Fails
```bash
# Check agents are registered first
curl http://localhost:8000/api/v1/agents | jq

# Use dry-run to validate
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --dry-run \
  --verbose
```

## Environment Variables

### API Configuration (.env.api)
```bash
DATABASE_URL=postgresql://workflow_user:workflow_pass@postgres:5432/workflow_db
KAFKA_BROKERS=kafka:29092
JWT_SECRET=your-secret-key
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

## Useful Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
# API shortcuts
alias api-health='curl http://localhost:8000/health | jq'
alias api-agents='curl http://localhost:8000/api/v1/agents | jq'
alias api-workflows='curl http://localhost:8000/api/v1/workflows | jq'
alias api-runs='curl http://localhost:8000/api/v1/runs | jq'

# Migration shortcuts
alias migrate-agents='python3 scripts/register_agents.py --config scripts/agents.yaml --skip-existing'
alias migrate-workflows='python3 scripts/migrate_workflows.py --workflow-dir examples/ --skip-existing'

# Docker shortcuts
alias api-logs='docker compose logs -f api'
alias api-restart='docker compose restart api'
alias api-start='docker compose --profile api up -d'
alias api-stop='docker compose --profile api down'
```

## See Also

- [Complete Migration Guide](MIGRATION_GUIDE.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Scripts README](scripts/README.md)
- [Quick Start Guide](QUICKSTART.md)

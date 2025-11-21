# Migration Guide: CLI to API-Based Workflow Execution

## Overview

This guide helps you migrate from the CLI-based workflow execution approach to the new API-based Workflow Management system. The API provides a more robust, scalable, and user-friendly way to manage agents, workflows, and executions.

## Table of Contents

1. [Key Differences](#key-differences)
2. [Migration Steps](#migration-steps)
3. [Importing Existing Workflows](#importing-existing-workflows)
4. [Backward Compatibility](#backward-compatibility)
5. [Migration Scripts](#migration-scripts)
6. [Troubleshooting](#troubleshooting)

---

## Key Differences

### Before (CLI-Based)

**Workflow Execution:**
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

**Characteristics:**
- Workflows defined in JSON files
- Manual environment variable management
- Direct Docker container execution
- No centralized workflow registry
- Limited monitoring capabilities
- Manual retry requires re-running with same RUN_ID

### After (API-Based)

**Workflow Execution:**
```bash
# Register workflow once
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @examples/sample_workflow.json

# Execute multiple times
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d @examples/sample_workflow_input.json
```

**Characteristics:**
- Workflows stored in database
- RESTful API interface
- Centralized workflow registry
- Built-in versioning
- Comprehensive monitoring via API
- Automatic retry with single API call
- Web UI support (Swagger/ReDoc)

---

## Migration Steps

### Step 1: Start the API Service

1. **Configure environment:**
   ```bash
   cp .env.api.example .env.api
   # Edit .env.api with your configuration
   ```

2. **Start API with infrastructure:**
   ```bash
   docker compose --profile api up -d
   ```

3. **Verify API is running:**
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status": "healthy"}
   ```

4. **Access API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Step 2: Register Agents

Before creating workflows, register all agents that your workflows will use.

**Example: Register ResearchAgent**
```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ResearchAgent",
    "url": "http://research-agent:8081",
    "description": "Agent for conducting research",
    "auth_type": "none",
    "timeout_ms": 30000,
    "retry_config": {
      "max_retries": 3,
      "initial_delay_ms": 1000,
      "max_delay_ms": 30000,
      "backoff_multiplier": 2.0
    }
  }'
```

**Example: Register WriterAgent**
```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "WriterAgent",
    "url": "http://writer-agent:8082",
    "description": "Agent for writing content",
    "auth_type": "none",
    "timeout_ms": 30000,
    "retry_config": {
      "max_retries": 3,
      "initial_delay_ms": 1000,
      "max_delay_ms": 30000,
      "backoff_multiplier": 2.0
    }
  }'
```

**Verify agents:**
```bash
curl http://localhost:8000/api/v1/agents
```

### Step 3: Import Existing Workflows

Use the migration script to import your existing workflow JSON files:

```bash
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --api-url http://localhost:8000
```

Or manually import a single workflow:

```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @examples/sample_workflow.json
```

### Step 4: Update Execution Scripts

**Old approach:**
```bash
#!/bin/bash
export RUN_ID="test-$(date +%s)"
export WORKFLOW_PLAN=$(cat workflow.json)
export WORKFLOW_INPUT=$(cat input.json)

docker-compose run --rm \
  -e RUN_ID="$RUN_ID" \
  -e WORKFLOW_PLAN="$WORKFLOW_PLAN" \
  -e WORKFLOW_INPUT="$WORKFLOW_INPUT" \
  executor
```

**New approach:**
```bash
#!/bin/bash
# Get workflow ID (one-time lookup)
WORKFLOW_ID=$(curl -s http://localhost:8000/api/v1/workflows?name=research-and-write | \
  jq -r '.items[0].id')

# Execute workflow
RUN_RESPONSE=$(curl -s -X POST \
  http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/execute \
  -H "Content-Type: application/json" \
  -d @input.json)

RUN_ID=$(echo $RUN_RESPONSE | jq -r '.run_id')
echo "Started workflow run: $RUN_ID"

# Monitor execution
curl http://localhost:8000/api/v1/runs/$RUN_ID
```

### Step 5: Update Monitoring

**Old approach:**
```bash
# Direct database query
docker exec -it postgres psql -U workflow_user -d workflow_db \
  -c "SELECT * FROM workflow_runs WHERE run_id = '$RUN_ID';"
```

**New approach:**
```bash
# API query
curl http://localhost:8000/api/v1/runs/$RUN_ID

# Get step details
curl http://localhost:8000/api/v1/runs/$RUN_ID/steps

# List all runs
curl "http://localhost:8000/api/v1/runs?status=COMPLETED&page=1&page_size=10"
```

---

## Importing Existing Workflows

### Automatic Import Script

The migration script automatically imports workflows from JSON files:

```bash
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --api-url http://localhost:8000 \
  --dry-run  # Test without importing
```

**Script features:**
- Validates workflow structure
- Checks agent references
- Handles duplicates
- Provides detailed import report

### Manual Import

For individual workflows:

1. **Prepare workflow JSON:**
   ```json
   {
     "name": "research-and-write",
     "description": "Research a topic and write content",
     "start_step": "step-1",
     "steps": {
       "step-1": {
         "id": "step-1",
         "agent_name": "ResearchAgent",
         "next_step": "step-2",
         "input_mapping": {
           "topic": "${workflow.input.topic}"
         }
       },
       "step-2": {
         "id": "step-2",
         "agent_name": "WriterAgent",
         "next_step": null,
         "input_mapping": {
           "research_data": "${step-1.output.findings}"
         }
       }
     }
   }
   ```

2. **Import via API:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/workflows \
     -H "Content-Type: application/json" \
     -d @workflow.json
   ```

3. **Verify import:**
   ```bash
   curl http://localhost:8000/api/v1/workflows
   ```

### Batch Import

Import multiple workflows at once:

```bash
for workflow in examples/*.json; do
  echo "Importing $workflow..."
  curl -X POST http://localhost:8000/api/v1/workflows \
    -H "Content-Type: application/json" \
    -d @$workflow
  echo ""
done
```

---

## Backward Compatibility

### Executor Service Compatibility

The existing Executor service continues to work with both approaches:

**CLI-based execution:**
- Still supported for backward compatibility
- Useful for testing and debugging
- Can run alongside API-based execution

**API-based execution:**
- Executor consumes from same Kafka topics
- Database schema is backward compatible
- Existing runs remain accessible

### Running Both Approaches

You can run both CLI and API-based executions simultaneously:

```bash
# Start everything
docker compose --profile api --profile executor --profile bridge up -d

# CLI execution (old way)
docker-compose run --rm \
  -e RUN_ID="cli-test-$(date +%s)" \
  -e WORKFLOW_PLAN="$(cat workflow.json)" \
  -e WORKFLOW_INPUT="$(cat input.json)" \
  executor

# API execution (new way)
curl -X POST http://localhost:8000/api/v1/workflows/{id}/execute \
  -H "Content-Type: application/json" \
  -d @input.json
```

Both executions will:
- Use the same Kafka topics
- Write to the same database
- Be processed by the same executor
- Appear in the same monitoring views

### Database Schema

The API adds new tables but doesn't modify existing ones:

**New tables:**
- `agents` - Agent registry
- `workflow_definitions` - Workflow templates
- `workflow_steps` - Workflow step definitions
- `audit_logs` - Audit trail

**Enhanced tables:**
- `workflow_runs` - Added `workflow_definition_id`, `input_data`, `triggered_by`
- Compatible with existing data

**Migration safety:**
- Alembic migrations are reversible
- Existing data is preserved
- Old executor continues to work

### Gradual Migration

You can migrate gradually:

1. **Phase 1: API alongside CLI**
   - Deploy API service
   - Keep using CLI for existing workflows
   - Test API with new workflows

2. **Phase 2: Import workflows**
   - Import existing workflows to database
   - Run both CLI and API executions
   - Validate API behavior

3. **Phase 3: Switch to API**
   - Update automation scripts to use API
   - Deprecate CLI execution
   - Keep CLI available for emergencies

---

## Migration Scripts

### 1. Workflow Import Script

**Location:** `scripts/migrate_workflows.py`

**Usage:**
```bash
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --api-url http://localhost:8000 \
  --api-key YOUR_API_KEY \
  --dry-run
```

**Options:**
- `--workflow-dir`: Directory containing workflow JSON files
- `--api-url`: API base URL (default: http://localhost:8000)
- `--api-key`: API key for authentication (optional)
- `--dry-run`: Validate without importing
- `--skip-existing`: Skip workflows that already exist
- `--verbose`: Show detailed output

**Example output:**
```
Scanning for workflows in examples/...
Found 3 workflow files

Validating sample_workflow.json...
✓ Valid workflow structure
✓ All agents exist: ResearchAgent, WriterAgent

Importing sample_workflow.json...
✓ Created workflow: research-and-write (ID: 123e4567-e89b-12d3-a456-426614174000)

Summary:
- Total files: 3
- Imported: 3
- Skipped: 0
- Failed: 0
```

### 2. Agent Registration Script

**Location:** `scripts/register_agents.py`

**Usage:**
```bash
python3 scripts/register_agents.py \
  --config agents.yaml \
  --api-url http://localhost:8000
```

**Example config (agents.yaml):**
```yaml
agents:
  - name: ResearchAgent
    url: http://research-agent:8081
    description: Research agent
    timeout_ms: 30000
    
  - name: WriterAgent
    url: http://writer-agent:8082
    description: Writer agent
    timeout_ms: 30000
```

### 3. Execution Migration Script

**Location:** `scripts/migrate_executions.py`

**Purpose:** Update existing automation scripts to use API

**Usage:**
```bash
# Analyze existing scripts
python3 scripts/migrate_executions.py analyze ./scripts/

# Generate API-based versions
python3 scripts/migrate_executions.py convert ./scripts/ --output ./scripts_api/
```

---

## Troubleshooting

### Issue: Workflow import fails with "Agent not found"

**Cause:** Agents referenced in workflow don't exist in database

**Solution:**
```bash
# List registered agents
curl http://localhost:8000/api/v1/agents

# Register missing agents
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "MissingAgent", "url": "http://agent:8080", ...}'
```

### Issue: API returns 500 error

**Cause:** Database connection or migration issues

**Solution:**
```bash
# Check API logs
docker compose logs api

# Check database connectivity
docker exec postgres pg_isready -U workflow_user

# Run migrations manually
docker compose exec api alembic upgrade head
```

### Issue: Workflow execution doesn't start

**Cause:** Executor service not running or Kafka issues

**Solution:**
```bash
# Check executor is running
docker compose ps executor

# Start executor if needed
docker compose --profile executor up -d

# Check Kafka connectivity
docker compose logs kafka
```

### Issue: Can't access API documentation

**Cause:** API service not started or port conflict

**Solution:**
```bash
# Check API is running
docker compose ps api

# Check port 8000 is available
lsof -i :8000

# Restart API service
docker compose restart api
```

### Issue: Old CLI executions not visible in API

**Cause:** CLI executions don't have `workflow_definition_id`

**Solution:**
```bash
# CLI executions are still visible via direct database queries
# Or use the migration script to link them:
python3 scripts/link_historical_runs.py
```

---

## Best Practices

### 1. Test in Development First

```bash
# Use separate environment for testing
cp .env.api.example .env.api.dev
# Edit .env.api.dev with dev settings

# Start dev environment
docker compose --env-file .env.api.dev --profile api up -d
```

### 2. Backup Before Migration

```bash
# Backup database
docker exec postgres pg_dump -U workflow_user workflow_db > backup.sql

# Backup workflow files
tar -czf workflows_backup.tar.gz examples/*.json
```

### 3. Validate Workflows

```bash
# Use dry-run mode first
python3 scripts/migrate_workflows.py \
  --workflow-dir examples/ \
  --dry-run

# Check for issues before actual import
```

### 4. Monitor During Migration

```bash
# Watch API logs
docker compose logs -f api

# Monitor database
docker exec -it postgres psql -U workflow_user -d workflow_db

# Check metrics
curl http://localhost:8000/metrics
```

### 5. Keep CLI Available

Don't remove CLI execution capability immediately:
- Keep it for emergency fallback
- Use it for debugging
- Maintain it for special cases

---

## Migration Checklist

- [ ] API service deployed and healthy
- [ ] Database migrations applied
- [ ] All agents registered via API
- [ ] Existing workflows imported
- [ ] Execution scripts updated
- [ ] Monitoring updated to use API
- [ ] Team trained on new API
- [ ] Documentation updated
- [ ] Backup procedures updated
- [ ] Rollback plan prepared

---

## Support

For issues during migration:

1. **Check logs:**
   ```bash
   docker compose logs api
   docker compose logs executor
   ```

2. **Review documentation:**
   - [API Documentation](API_DOCUMENTATION.md)
   - [Deployment Guide](api/DEPLOYMENT.md)
   - [Quick Start](QUICKSTART.md)

3. **Test with examples:**
   ```bash
   # Run end-to-end test
   python3 examples/e2e_test.py
   ```

4. **Verify health:**
   ```bash
   curl http://localhost:8000/health/ready
   ```

---

## Next Steps

After successful migration:

1. **Explore API features:**
   - Workflow versioning
   - Advanced filtering
   - Audit logs
   - Health monitoring

2. **Build integrations:**
   - CI/CD pipelines
   - Monitoring dashboards
   - Custom UIs

3. **Optimize:**
   - Configure retry policies
   - Set up alerting
   - Tune performance

4. **Scale:**
   - Add more agents
   - Create complex workflows
   - Deploy to production

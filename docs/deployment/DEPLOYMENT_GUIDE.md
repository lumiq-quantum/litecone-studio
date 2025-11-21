# Deployment Guide - Parallel Execution Feature

## Overview

This guide covers deploying the parallel execution feature to your local environment.

## Services That Need Rebuilding

The following services contain updated Python code and need to be rebuilt:

1. **executor** - Contains the updated `CentralizedExecutor` with parallel execution support
2. **bridge** - No changes, but rebuild recommended for consistency
3. **execution-consumer** - Spawns executors, needs updated code

## Quick Deployment (Recommended)

### Step 1: Stop Running Services

```bash
# Stop all services
docker-compose --profile executor --profile bridge --profile consumer down
```

### Step 2: Rebuild Images

```bash
# Rebuild the executor service
docker-compose build executor

# Rebuild the execution consumer
docker-compose build execution-consumer

# Optional: Rebuild bridge (no code changes, but good practice)
docker-compose build bridge
```

### Step 3: Start Services

```bash
# Start infrastructure (if not already running)
docker-compose up -d zookeeper kafka postgres

# Wait a few seconds for Kafka to be ready
sleep 10

# Start the executor (for manual workflow execution)
docker-compose --profile executor up -d

# Start the execution consumer (for API-triggered workflows)
docker-compose --profile consumer up -d

# Start the bridge (to handle agent communication)
docker-compose --profile bridge up -d
```

### Step 4: Verify Deployment

```bash
# Check that services are running
docker-compose ps

# Check executor logs
docker logs centralized-executor

# Check consumer logs
docker logs execution-consumer

# Verify database migration
python scripts/verify_parallel_execution_migration.py
```

## Alternative: Rebuild All Services

If you want to ensure everything is fresh:

```bash
# Stop all services
docker-compose down

# Rebuild all services
docker-compose build

# Start infrastructure
docker-compose up -d zookeeper kafka postgres

# Wait for Kafka
sleep 10

# Start your desired services
docker-compose --profile executor --profile bridge --profile consumer up -d
```

## Testing the Deployment

### Test 1: Verify Services Are Running

```bash
# Check running containers
docker ps --filter "name=executor" --filter "name=consumer" --filter "name=bridge"

# Expected output: 3 containers running
```

### Test 2: Check Logs for Parallel Executor Initialization

```bash
# Check executor logs for ParallelExecutor initialization
docker logs centralized-executor 2>&1 | grep -i "parallel"

# Expected: "Initializing Parallel Executor"
```

### Test 3: Test with Example Workflow (if using API)

```bash
# Create a workflow with parallel execution
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @examples/parallel_workflow_example.json

# Execute the workflow
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {"data": "test"}}'
```

## Troubleshooting

### Issue: Services Won't Start

```bash
# Check logs
docker-compose logs executor
docker-compose logs execution-consumer

# Common issues:
# - Kafka not ready: Wait longer or restart Kafka
# - Database connection: Check DATABASE_URL in .env
# - Port conflicts: Check if ports are already in use
```

### Issue: Import Errors

```bash
# Rebuild with no cache
docker-compose build --no-cache executor
docker-compose build --no-cache execution-consumer
```

### Issue: Database Connection Errors

```bash
# Verify database is running
docker ps --filter "name=postgres"

# Test database connection
docker exec -i postgres psql -U workflow_user -d workflow_db -c "SELECT 1;"

# Verify migration was applied
python scripts/verify_parallel_execution_migration.py
```

## Rollback Procedure

If you need to rollback to the previous version:

### Step 1: Rollback Database Migration

```bash
docker exec -i postgres psql -U workflow_user -d workflow_db < migrations/001_add_parallel_execution_columns_rollback.sql
```

### Step 2: Revert Code Changes

```bash
# Checkout previous version
git checkout <previous-commit>

# Rebuild services
docker-compose build executor execution-consumer

# Restart services
docker-compose --profile executor --profile consumer up -d
```

## Production Deployment Considerations

When deploying to production:

1. **Test in Staging First**
   - Deploy to staging environment
   - Run integration tests
   - Monitor for 24-48 hours

2. **Backup Database**
   ```bash
   docker exec postgres pg_dump -U workflow_user workflow_db > backup_before_parallel_exec.sql
   ```

3. **Apply Migration During Low Traffic**
   - Schedule during maintenance window
   - Monitor for errors

4. **Gradual Rollout**
   - Deploy to one instance first
   - Monitor metrics and logs
   - Gradually roll out to all instances

5. **Monitor Key Metrics**
   - Workflow execution time
   - Parallel step success rate
   - Database query performance
   - Resource usage (CPU, memory)

## Environment Variables

No new environment variables are required for parallel execution. The feature uses existing configuration.

## Resource Requirements

Parallel execution may increase resource usage:

- **CPU**: More concurrent operations
- **Memory**: Multiple steps in memory simultaneously
- **Database Connections**: More concurrent queries

Consider adjusting Docker resource limits if needed:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

## Next Steps

After successful deployment:

1. ✅ Services rebuilt and running
2. ✅ Database migration applied
3. 🧪 Test with example workflows
4. 📊 Monitor performance
5. 📝 Update team documentation
6. 🚀 Enable for production workflows

## Loop Execution Feature Deployment

### Overview

Loop execution feature (Epic 1.3) adds iteration capabilities to workflows. This section covers deploying the loop execution feature.

### Database Migration

Apply the loop execution migration:

```bash
# Apply migration
docker exec -i postgres psql -U workflow_user -d workflow_db < migrations/003_add_loop_execution_columns.sql
```

Verify the migration:

```bash
# Check that new columns exist
docker exec -i postgres psql -U workflow_user -d workflow_db -c "\d step_executions"
```

You should see the new columns:
- `loop_collection_size`
- `loop_iteration_index`
- `loop_execution_mode`

### Service Updates

The loop execution feature requires rebuilding the executor service:

```bash
# Stop services
docker-compose --profile executor --profile consumer down

# Rebuild executor
docker-compose build executor
docker-compose build execution-consumer

# Restart services
docker-compose --profile executor up -d
docker-compose --profile consumer up -d
```

### Testing Loop Execution

Test with the provided examples:

```bash
# Sequential loop example
# (Use API to create workflow from examples/loop_sequential_example.json)

# Parallel loop example
# (Use API to create workflow from examples/loop_parallel_example.json)
```

### Rollback

If needed, rollback the migration:

```bash
docker exec -i postgres psql -U workflow_user -d workflow_db < migrations/003_add_loop_execution_columns_rollback.sql
```

## Support

For issues:
- Check logs: `docker-compose logs <service>`
- Verify parallel migration: `python scripts/verify_parallel_execution_migration.py`
- Review docs: 
  - `docs/parallel_execution.md`
  - `docs/conditional_logic.md`
  - `docs/loop_execution.md`
- Check completion summaries:
  - `.kiro/specs/advanced-workflow-execution/EPIC_1.1_COMPLETION_SUMMARY.md`
  - `.kiro/specs/advanced-workflow-execution/EPIC_1.2_COMPLETION_SUMMARY.md`
  - `.kiro/specs/advanced-workflow-execution/EPIC_1.3_COMPLETION_SUMMARY.md`

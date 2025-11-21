# API Restart Guide

## Why Restart is Needed

When you update Python code in the API (like schema changes in `api/schemas/workflow.py`), the running Docker container still has the old code loaded in memory. You need to restart the container to pick up the changes.

## Quick Reference

### Option 1: Quick Restart (Fastest - ~10 seconds)
Use this when you've only changed Python code (no dependency changes):

```bash
./quick-restart-api.sh
```

Or manually:
```bash
docker-compose restart api
```

### Option 2: Full Rebuild (Slower - ~2-3 minutes)
Use this when you've changed dependencies or want a clean build:

```bash
./restart-api.sh
```

Or manually:
```bash
docker-compose --profile api down
docker-compose build --no-cache api
docker-compose --profile api up -d
```

### Option 3: Rebuild Without Cache (Slowest - ~5 minutes)
Use this for troubleshooting or major changes:

```bash
docker-compose --profile api down
docker-compose build --no-cache --pull api
docker-compose --profile api up -d
```

## Step-by-Step Manual Process

### 1. Stop the API Service

```bash
docker-compose --profile api down
```

This stops and removes the API container.

### 2. Rebuild the Image (Optional but Recommended)

```bash
# Rebuild with cache (faster)
docker-compose build api

# OR rebuild without cache (slower but cleaner)
docker-compose build --no-cache api
```

### 3. Start the API Service

```bash
docker-compose --profile api up -d
```

The `-d` flag runs it in detached mode (background).

### 4. Verify API is Running

```bash
# Check container status
docker-compose ps api

# Check API health
curl http://localhost:8000/health

# View logs
docker-compose logs -f api
```

## Troubleshooting

### API Won't Start

**Check logs:**
```bash
docker-compose logs api
```

**Common issues:**
- Database not ready: Wait a few seconds and try again
- Port 8000 already in use: Stop other services using that port
- Syntax errors in Python code: Check the logs for error messages

### Changes Not Reflected

**Clear everything and rebuild:**
```bash
# Stop all services
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache api

# Start fresh
docker-compose --profile api up -d
```

### Database Connection Issues

**Ensure PostgreSQL is running:**
```bash
docker-compose ps postgres

# If not running, start it
docker-compose up -d postgres

# Wait for it to be ready
sleep 5

# Then start API
docker-compose --profile api up -d
```

## Verification Steps

### 1. Check Container Status

```bash
docker-compose ps api
```

Should show:
```
NAME                      STATUS          PORTS
workflow-management-api   Up X seconds    0.0.0.0:8000->8000/tcp
```

### 2. Check Health Endpoint

```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status": "healthy"}
```

### 3. Check API Documentation

Open in browser:
```
http://localhost:8000/docs
```

Should show the Swagger UI with all endpoints.

### 4. Test Conditional Workflow Creation

```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @examples/conditional_workflow_example.json
```

Should return a successful response with the workflow ID.

## Development Workflow

### For Schema Changes (like conditional logic)

1. **Edit the schema file:**
   ```bash
   # Edit api/schemas/workflow.py
   ```

2. **Quick restart:**
   ```bash
   ./quick-restart-api.sh
   ```

3. **Test the changes:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/workflows \
     -H "Content-Type: application/json" \
     -d @examples/conditional_workflow_example.json
   ```

### For Dependency Changes

1. **Update requirements:**
   ```bash
   # Edit requirements.txt
   ```

2. **Full rebuild:**
   ```bash
   ./restart-api.sh
   ```

3. **Verify:**
   ```bash
   docker-compose exec api pip list
   ```

## Docker Commands Reference

### View Logs

```bash
# Follow logs in real-time
docker-compose logs -f api

# Last 50 lines
docker-compose logs --tail=50 api

# Since specific time
docker-compose logs --since 5m api
```

### Execute Commands in Container

```bash
# Open shell
docker-compose exec api bash

# Run Python command
docker-compose exec api python -c "import api.schemas.workflow; print('Schema loaded')"

# Check Python version
docker-compose exec api python --version
```

### Resource Usage

```bash
# Check resource usage
docker stats workflow-management-api

# Check disk usage
docker system df
```

### Clean Up

```bash
# Remove stopped containers
docker-compose rm

# Remove unused images
docker image prune

# Remove everything (careful!)
docker system prune -a
```

## Performance Tips

### 1. Use Quick Restart for Code Changes

The quick restart (`docker-compose restart api`) is much faster than rebuilding because it:
- Doesn't rebuild the Docker image
- Doesn't reinstall dependencies
- Just restarts the Python process

### 2. Use Build Cache

When rebuilding, Docker uses cached layers. Only rebuild without cache when necessary:

```bash
# With cache (faster)
docker-compose build api

# Without cache (slower but cleaner)
docker-compose build --no-cache api
```

### 3. Keep Dependencies Stable

Frequent dependency changes require full rebuilds. Try to:
- Batch dependency updates
- Use version pinning in requirements.txt
- Test locally before adding to requirements

## Automated Scripts

### restart-api.sh

Full rebuild and restart with health checks:
- Stops API service
- Rebuilds image without cache
- Starts service
- Waits for health check
- Shows logs

### quick-restart-api.sh

Quick restart without rebuild:
- Restarts container
- Waits for health check
- Shows status

## Integration with CI/CD

For automated deployments:

```bash
# In your CI/CD pipeline
docker-compose --profile api down
docker-compose build --no-cache api
docker-compose --profile api up -d

# Wait for health
timeout 60 bash -c 'until curl -s http://localhost:8000/health; do sleep 2; done'

# Run tests
pytest tests/api/
```

## Summary

**For the conditional logic schema update:**

1. ✅ Schema updated in `api/schemas/workflow.py`
2. ⚠️ **Need to restart API** to load new schema
3. 🚀 **Run:** `./quick-restart-api.sh` or `docker-compose restart api`
4. ✅ Test with conditional workflow

**Quick command:**
```bash
docker-compose restart api && sleep 5 && curl http://localhost:8000/health
```

This will restart the API and verify it's healthy!

# Migration Troubleshooting Guide

## Issue: Migration Revision Not Found

### Error Message
```
KeyError: '001_add_workflow_run_fields'
```

### Root Cause
The migration file `002_add_conditional_execution_columns.py` was referencing a revision ID that didn't match the actual revision ID in the previous migration.

**Problem:**
- Migration 002 had: `down_revision = '001_add_workflow_run_fields'`
- Migration 001 actually has: `revision = '001'`

### Solution ✅

Updated `002_add_conditional_execution_columns.py` to reference the correct revision:

```python
# Before (incorrect)
down_revision = '001_add_workflow_run_fields'

# After (correct)
down_revision = '001'
```

## How to Apply the Fix

### Step 1: Restart the API Service

The API container needs to pick up the corrected migration file:

```bash
# Quick restart
./quick-restart-api.sh

# OR manual restart
docker-compose restart api
```

### Step 2: Run Migrations

```bash
# Using the script
./run-migrations.sh

# OR manually
docker-compose exec api alembic upgrade head
```

### Step 3: Verify Migration Status

```bash
# Check current migration version
docker-compose exec api alembic current

# Should show:
# 002_conditional (head)
```

## Common Migration Issues

### 1. Revision Chain Broken

**Symptom:**
```
KeyError: 'some_revision_id'
```

**Solution:**
- Check the `down_revision` in your migration file
- Ensure it matches the `revision` ID of the previous migration
- Use `alembic history` to see the chain

```bash
docker-compose exec api alembic history
```

### 2. Migration Already Applied

**Symptom:**
```
Target database is not up to date.
```

**Solution:**
```bash
# Check current version
docker-compose exec api alembic current

# Downgrade if needed
docker-compose exec api alembic downgrade -1

# Then upgrade again
docker-compose exec api alembic upgrade head
```

### 3. Database Connection Issues

**Symptom:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
```bash
# Ensure PostgreSQL is running
docker-compose ps postgres

# If not running, start it
docker-compose up -d postgres

# Wait for it to be ready
sleep 5

# Try migration again
docker-compose exec api alembic upgrade head
```

### 4. Column Already Exists

**Symptom:**
```
sqlalchemy.exc.ProgrammingError: column "condition_expression" already exists
```

**Solution:**
```bash
# Mark migration as applied without running it
docker-compose exec api alembic stamp 002_conditional

# OR drop the columns manually and re-run
docker-compose exec api psql $DATABASE_URL -c "
ALTER TABLE step_executions 
DROP COLUMN IF EXISTS condition_expression,
DROP COLUMN IF EXISTS condition_result,
DROP COLUMN IF EXISTS branch_taken;
"

# Then run migration
docker-compose exec api alembic upgrade head
```

### 5. Multiple Heads

**Symptom:**
```
Multiple head revisions are present
```

**Solution:**
```bash
# Check heads
docker-compose exec api alembic heads

# Merge heads (create a merge migration)
docker-compose exec api alembic merge -m "merge heads" head1 head2

# Then upgrade
docker-compose exec api alembic upgrade head
```

## Migration Commands Reference

### Check Status

```bash
# Current version
docker-compose exec api alembic current

# Show verbose info
docker-compose exec api alembic current -v

# Show all heads
docker-compose exec api alembic heads

# Show history
docker-compose exec api alembic history
```

### Upgrade/Downgrade

```bash
# Upgrade to latest
docker-compose exec api alembic upgrade head

# Upgrade to specific version
docker-compose exec api alembic upgrade 002_conditional

# Downgrade one version
docker-compose exec api alembic downgrade -1

# Downgrade to specific version
docker-compose exec api alembic downgrade 001

# Downgrade all
docker-compose exec api alembic downgrade base
```

### Create New Migration

```bash
# Auto-generate from model changes
docker-compose exec api alembic revision --autogenerate -m "description"

# Create empty migration
docker-compose exec api alembic revision -m "description"
```

### Stamp (Mark as Applied)

```bash
# Mark current state as specific version
docker-compose exec api alembic stamp 002_conditional

# Mark as head
docker-compose exec api alembic stamp head
```

## Verification Steps

### 1. Check Migration Files

```bash
# List migration files
ls -la api/migrations/versions/

# Should see:
# 001_add_workflow_run_fields.py
# 002_add_conditional_execution_columns.py
```

### 2. Verify Revision Chain

```bash
# Check migration history
docker-compose exec api alembic history

# Should show:
# 001 -> 002_conditional (head)
```

### 3. Check Database Schema

```bash
# Connect to database
docker-compose exec postgres psql -U workflow_user -d workflow_db

# Check if columns exist
\d step_executions

# Should show:
# condition_expression | text
# condition_result     | boolean
# branch_taken         | character varying(50)
```

### 4. Test API

```bash
# Create a conditional workflow
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @examples/conditional_workflow_example.json

# Should succeed without validation errors
```

## Clean Slate (Nuclear Option)

If all else fails, start fresh:

```bash
# WARNING: This deletes all data!

# Stop everything
docker-compose down -v

# Remove database volume
docker volume rm orchestrator_postgres-data

# Start fresh
docker-compose up -d postgres
sleep 10

# Run migrations
docker-compose --profile api up -d
sleep 5
docker-compose exec api alembic upgrade head

# Verify
docker-compose exec api alembic current
```

## Best Practices

### 1. Always Check Revision Chain

Before creating a new migration:
```bash
# Check current head
docker-compose exec api alembic current

# Use that revision as down_revision in new migration
```

### 2. Use Simple Revision IDs

```python
# Good
revision = '001'
revision = '002_conditional'

# Avoid
revision = '001_add_workflow_run_fields_and_other_stuff'
```

### 3. Test Migrations Locally

```bash
# Test upgrade
docker-compose exec api alembic upgrade head

# Test downgrade
docker-compose exec api alembic downgrade -1

# Test upgrade again
docker-compose exec api alembic upgrade head
```

### 4. Keep Migration Files Simple

- One migration per feature
- Clear, descriptive names
- Include both upgrade() and downgrade()
- Test rollback functionality

### 5. Version Control

```bash
# Always commit migration files
git add api/migrations/versions/*.py
git commit -m "Add migration for conditional logic"
```

## Summary for Conditional Logic Migration

### What Was Fixed

1. ✅ Updated `down_revision` from `'001_add_workflow_run_fields'` to `'001'`
2. ✅ Migration file now references correct previous revision
3. ✅ Alembic can now find the revision chain

### How to Apply

```bash
# 1. Restart API to pick up fixed migration
docker-compose restart api

# 2. Run migrations
docker-compose exec api alembic upgrade head

# 3. Verify
docker-compose exec api alembic current
# Should show: 002_conditional (head)

# 4. Test API
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @examples/conditional_workflow_example.json
```

### Expected Result

- ✅ Migration applies successfully
- ✅ Database has new columns: `condition_expression`, `condition_result`, `branch_taken`
- ✅ API accepts conditional workflows
- ✅ No validation errors

## Quick Fix Command

```bash
docker-compose restart api && \
sleep 5 && \
docker-compose exec api alembic upgrade head && \
docker-compose exec api alembic current
```

This will:
1. Restart API with fixed migration
2. Apply migrations
3. Show current version

Done! 🎉

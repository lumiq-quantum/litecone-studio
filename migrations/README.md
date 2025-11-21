# Database Migrations

This directory contains SQL migration scripts for the workflow orchestration system.

## Migration Files

### 001_add_parallel_execution_columns.sql

Adds columns to the `step_executions` table for tracking parallel execution:

- `parent_step_id`: ID of the parent parallel/fork-join step
- `branch_name`: Branch name for fork-join execution
- `join_policy`: Join policy for fork-join (ALL, ANY, MAJORITY, N_OF_M)

**Rollback**: `001_add_parallel_execution_columns_rollback.sql`

## Running Migrations

### Apply Migration

```bash
psql -h <host> -U <user> -d <database> -f migrations/001_add_parallel_execution_columns.sql
```

### Rollback Migration

```bash
psql -h <host> -U <user> -d <database> -f migrations/001_add_parallel_execution_columns_rollback.sql
```

## Migration Order

Migrations should be applied in numerical order:
1. 001_add_parallel_execution_columns.sql

## Testing Migrations

Always test migrations on a development database before applying to production:

```bash
# Create test database
createdb workflow_test

# Apply migration
psql -d workflow_test -f migrations/001_add_parallel_execution_columns.sql

# Verify schema
psql -d workflow_test -c "\d step_executions"

# Test rollback
psql -d workflow_test -f migrations/001_add_parallel_execution_columns_rollback.sql

# Verify rollback
psql -d workflow_test -c "\d step_executions"
```

## Notes

- Always backup your database before running migrations
- Test migrations on development environment first
- Keep rollback scripts up to date
- Document any manual steps required

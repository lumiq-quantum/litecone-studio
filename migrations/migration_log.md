# Migration Log

## Applied Migrations

### 001_add_parallel_execution_columns.sql
- **Applied**: November 18, 2025
- **Status**: ✅ SUCCESS
- **Database**: workflow_db
- **User**: workflow_user

#### Changes Applied
- Added `parent_step_id` column to `step_executions` table
- Added `branch_name` column to `step_executions` table
- Added `join_policy` column to `step_executions` table
- Created index `idx_step_branch` on (run_id, parent_step_id, branch_name)
- Added column comments for documentation

#### Verification
```sql
\d step_executions
```

#### Rollback Available
```bash
docker exec -i postgres psql -U workflow_user -d workflow_db < migrations/001_add_parallel_execution_columns_rollback.sql
```

---

## Migration History

| Migration | Date | Status | Notes |
|-----------|------|--------|-------|
| 001_add_parallel_execution_columns | 2025-11-18 | ✅ Applied | Parallel execution support |


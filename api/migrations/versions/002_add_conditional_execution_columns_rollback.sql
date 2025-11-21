-- Rollback migration for conditional execution columns
-- This script removes the columns added for conditional execution tracking

-- Remove conditional execution columns from step_executions table
ALTER TABLE step_executions DROP COLUMN IF EXISTS branch_taken;
ALTER TABLE step_executions DROP COLUMN IF EXISTS condition_result;
ALTER TABLE step_executions DROP COLUMN IF EXISTS condition_expression;

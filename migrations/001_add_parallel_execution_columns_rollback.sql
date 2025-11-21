-- Rollback Migration: Remove parallel execution tracking columns
-- Date: 2025-11-18
-- Description: Removes columns from step_executions table for parallel execution tracking

-- Drop index
DROP INDEX IF EXISTS idx_step_branch;

-- Remove columns
ALTER TABLE step_executions 
DROP COLUMN IF EXISTS parent_step_id,
DROP COLUMN IF EXISTS branch_name,
DROP COLUMN IF EXISTS join_policy;

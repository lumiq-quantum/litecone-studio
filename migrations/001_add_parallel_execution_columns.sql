-- Migration: Add parallel execution tracking columns
-- Date: 2025-11-18
-- Description: Adds columns to step_executions table for tracking parallel execution

-- Add columns for parallel execution tracking
ALTER TABLE step_executions 
ADD COLUMN parent_step_id VARCHAR(255) NULL,
ADD COLUMN branch_name VARCHAR(255) NULL,
ADD COLUMN join_policy VARCHAR(50) NULL;

-- Add index for querying parallel branches
CREATE INDEX idx_step_branch ON step_executions(run_id, parent_step_id, branch_name);

-- Add comment
COMMENT ON COLUMN step_executions.parent_step_id IS 'Parent step ID for parallel/fork-join steps';
COMMENT ON COLUMN step_executions.branch_name IS 'Branch name for fork-join execution';
COMMENT ON COLUMN step_executions.join_policy IS 'Join policy for fork-join (ALL, ANY, MAJORITY, N_OF_M)';

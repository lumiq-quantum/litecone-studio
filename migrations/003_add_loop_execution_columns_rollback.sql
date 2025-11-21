-- Rollback Migration: Remove loop execution tracking columns
-- Date: 2025-11-18
-- Description: Removes loop execution tracking columns from step_executions table

-- Drop index
DROP INDEX IF EXISTS idx_step_loop_iteration;

-- Remove columns
ALTER TABLE step_executions 
DROP COLUMN IF EXISTS loop_collection_size,
DROP COLUMN IF EXISTS loop_iteration_index,
DROP COLUMN IF EXISTS loop_execution_mode;

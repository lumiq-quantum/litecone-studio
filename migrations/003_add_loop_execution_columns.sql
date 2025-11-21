-- Migration: Add loop execution tracking columns
-- Date: 2025-11-18
-- Description: Adds columns to step_executions table for tracking loop execution

-- Add columns for loop execution tracking
ALTER TABLE step_executions 
ADD COLUMN loop_collection_size INTEGER NULL,
ADD COLUMN loop_iteration_index INTEGER NULL,
ADD COLUMN loop_execution_mode VARCHAR(50) NULL;

-- Add index for querying loop iterations
CREATE INDEX idx_step_loop_iteration ON step_executions(run_id, parent_step_id, loop_iteration_index);

-- Add comments
COMMENT ON COLUMN step_executions.loop_collection_size IS 'Total number of items in the loop collection';
COMMENT ON COLUMN step_executions.loop_iteration_index IS 'Current iteration index (0-based) for loop steps';
COMMENT ON COLUMN step_executions.loop_execution_mode IS 'Loop execution mode (sequential or parallel)';

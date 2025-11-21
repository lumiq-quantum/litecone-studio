/**
 * Workflow-related types and interfaces
 */

/**
 * Workflow status types
 */
export type WorkflowStatus = 'active' | 'inactive' | 'deleted';

/**
 * Condition definition for conditional steps
 */
export interface Condition {
  expression: string;
  operator?: string;
}

/**
 * Loop configuration for loop steps
 */
export interface LoopConfig {
  collection: string; // Variable reference to array/list
  loop_body: string[]; // Step IDs to execute for each item
  execution_mode?: 'sequential' | 'parallel'; // Default: 'sequential'
  max_parallelism?: number; // Optional for parallel mode
  max_iterations?: number; // Maximum items to process
  on_error?: 'stop' | 'continue' | 'collect'; // Default: 'stop'
}

/**
 * Branch definition for fork-join steps
 */
export interface Branch {
  steps: string[]; // Step IDs to execute in this branch
  timeout_seconds?: number; // Optional timeout for this branch
}

/**
 * Fork-join configuration for fork-join steps
 */
export interface ForkJoinConfig {
  branches: Record<string, Branch>; // Named branches to execute in parallel
  join_policy?: 'all' | 'any' | 'majority' | 'n_of_m'; // Default: 'all'
  n_required?: number; // Required for join_policy='n_of_m'
  branch_timeout_seconds?: number; // Default timeout for all branches
}

/**
 * Workflow step definition
 */
export interface WorkflowStep {
  id: string;
  type?: 'agent' | 'parallel' | 'conditional' | 'loop' | 'fork_join'; // Step type (default: 'agent')
  agent_name?: string; // Required for type='agent'
  next_step: string | null;
  input_mapping?: Record<string, unknown>; // Required for type='agent'
  parallel_steps?: string[]; // Required for type='parallel'
  max_parallelism?: number; // Optional for type='parallel'
  condition?: Condition; // Required for type='conditional'
  if_true_step?: string; // Optional for type='conditional'
  if_false_step?: string; // Optional for type='conditional'
  loop_config?: LoopConfig; // Required for type='loop'
  fork_join_config?: ForkJoinConfig; // Required for type='fork_join'
}

/**
 * Complete workflow definition structure
 */
export interface WorkflowDefinition {
  workflow_id?: string;
  name: string;
  version?: string;
  start_step: string;
  steps: Record<string, WorkflowStep>;
}

/**
 * Request payload for creating a new workflow
 */
export interface WorkflowCreate {
  name: string;
  description?: string;
  start_step: string;
  steps: Record<string, WorkflowStep>;
}

/**
 * Request payload for updating an existing workflow
 */
export interface WorkflowUpdate {
  description?: string;
  start_step?: string;
  steps?: Record<string, WorkflowStep>;
  status?: WorkflowStatus;
}

/**
 * Workflow response from API
 */
export interface WorkflowResponse {
  id: string;
  name: string;
  description?: string;
  version: number;
  workflow_data: WorkflowDefinition;
  status: WorkflowStatus;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
}

/**
 * Request payload for executing a workflow
 */
export interface WorkflowExecuteRequest {
  input_data: Record<string, unknown>;
}

/**
 * Response from workflow execution trigger
 */
export interface WorkflowExecuteResponse {
  message: string;
  run_id: string;
  workflow_id: string;
  status: string;
  timestamp: string;
}

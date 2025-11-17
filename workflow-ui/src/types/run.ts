/**
 * Run-related types and interfaces
 */

/**
 * Run status types
 */
export type RunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

/**
 * Step execution status types
 */
export type StepStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';

/**
 * Workflow run response
 */
export interface RunResponse {
  id: string;
  run_id: string;
  workflow_id: string;
  workflow_name: string;
  workflow_definition_id?: string;
  status: RunStatus;
  input_data?: Record<string, unknown>;
  triggered_by?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  cancelled_at?: string;
  cancelled_by?: string;
  error_message?: string;
  // Retry relationship fields
  original_run_id?: string;  // If this is a retry, the original failed run
  retried_by_run_id?: string;  // If this run was retried, the new run ID
  retry_count?: number;  // Number of times this run has been retried
}

/**
 * Step execution response
 */
export interface StepExecutionResponse {
  id: string;
  run_id: string;
  step_id: string;
  step_name: string;
  agent_name: string;
  status: StepStatus;
  input_data: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

/**
 * Request payload for retrying a failed workflow
 */
export interface WorkflowRetryRequest {
  resume_from_step?: string;
}

/**
 * Request payload for cancelling a running workflow
 */
export interface WorkflowCancelRequest {
  reason?: string;
}

/**
 * Response from retry operation
 */
export interface WorkflowRetryResponse {
  message: string;
  new_run_id: string;
  original_run_id: string;
  timestamp: string;
}

/**
 * Response from cancel operation
 */
export interface WorkflowCancelResponse {
  message: string;
  run_id: string;
  status: string;
  timestamp: string;
}

/**
 * List of step executions for a run
 */
export interface StepExecutionListResponse {
  items: StepExecutionResponse[];
  total: number;
}

/**
 * Filter parameters for run list
 */
export interface RunFilterParams {
  status?: RunStatus;
  workflow_id?: string;
  workflow_definition_id?: string;
  created_after?: string;
  created_before?: string;
  sort_by?: 'created_at' | 'updated_at' | 'completed_at' | 'status';
  sort_order?: 'asc' | 'desc';
}

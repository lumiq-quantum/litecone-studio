/**
 * Workflow-related types and interfaces
 */

/**
 * Workflow status types
 */
export type WorkflowStatus = 'active' | 'inactive' | 'deleted';

/**
 * Workflow step definition
 */
export interface WorkflowStep {
  id: string;
  agent_name: string;
  next_step: string | null;
  input_mapping: Record<string, unknown>;
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

/**
 * Workflow API service
 */
import apiClient from './client';
import type {
  WorkflowCreate,
  WorkflowUpdate,
  WorkflowResponse,
  WorkflowExecuteRequest,
  WorkflowExecuteResponse,
  PaginatedResponse,
  PaginationParams,
  FilterParams,
} from '@/types';

/**
 * List all workflows with pagination and filtering
 */
export const listWorkflows = async (
  params?: PaginationParams & FilterParams
): Promise<PaginatedResponse<WorkflowResponse>> => {
  const response = await apiClient.get<PaginatedResponse<WorkflowResponse>>('/workflows', { params });
  return response.data;
};

/**
 * Get a single workflow by ID
 */
export const getWorkflow = async (workflowId: string): Promise<WorkflowResponse> => {
  const response = await apiClient.get<WorkflowResponse>(`/workflows/${workflowId}`);
  return response.data;
};

/**
 * Create a new workflow
 */
export const createWorkflow = async (data: WorkflowCreate): Promise<WorkflowResponse> => {
  const response = await apiClient.post<WorkflowResponse>('/workflows', data);
  return response.data;
};

/**
 * Update an existing workflow
 */
export const updateWorkflow = async (
  workflowId: string,
  data: WorkflowUpdate
): Promise<WorkflowResponse> => {
  const response = await apiClient.put<WorkflowResponse>(`/workflows/${workflowId}`, data);
  return response.data;
};

/**
 * Delete a workflow (soft delete)
 */
export const deleteWorkflow = async (workflowId: string): Promise<void> => {
  await apiClient.delete(`/workflows/${workflowId}`);
};

/**
 * Get all versions of a workflow
 */
export const getWorkflowVersions = async (
  workflowId: string,
  params?: PaginationParams
): Promise<PaginatedResponse<WorkflowResponse>> => {
  const response = await apiClient.get<PaginatedResponse<WorkflowResponse>>(
    `/workflows/${workflowId}/versions`,
    { params }
  );
  return response.data;
};

/**
 * Execute a workflow
 */
export const executeWorkflow = async (
  workflowId: string,
  data: WorkflowExecuteRequest
): Promise<WorkflowExecuteResponse> => {
  const response = await apiClient.post<WorkflowExecuteResponse>(
    `/workflows/${workflowId}/execute`,
    data
  );
  return response.data;
};

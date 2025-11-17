/**
 * Run API service
 */
import apiClient from './client';
import type {
  RunResponse,
  StepExecutionListResponse,
  WorkflowRetryRequest,
  WorkflowRetryResponse,
  WorkflowCancelRequest,
  WorkflowCancelResponse,
  PaginatedResponse,
  PaginationParams,
  RunFilterParams,
} from '@/types';

/**
 * List all runs with pagination and filtering
 */
export const listRuns = async (
  params?: PaginationParams & RunFilterParams
): Promise<PaginatedResponse<RunResponse>> => {
  const response = await apiClient.get<PaginatedResponse<RunResponse>>('/runs', { params });
  return response.data;
};

/**
 * Get a single run by ID
 */
export const getRun = async (runId: string): Promise<RunResponse> => {
  const response = await apiClient.get<RunResponse>(`/runs/${runId}`);
  return response.data;
};

/**
 * Get step executions for a run
 */
export const getRunSteps = async (runId: string): Promise<StepExecutionListResponse> => {
  const response = await apiClient.get(`/runs/${runId}/steps`);
  
  // Handle both array and paginated response formats
  if (Array.isArray(response.data)) {
    return {
      items: response.data,
      total: response.data.length,
    };
  }
  
  return response.data;
};

/**
 * Retry a failed workflow run
 */
export const retryRun = async (
  runId: string,
  data?: WorkflowRetryRequest
): Promise<WorkflowRetryResponse> => {
  const response = await apiClient.post<WorkflowRetryResponse>(`/runs/${runId}/retry`, data || {});
  return response.data;
};

/**
 * Cancel a running workflow
 */
export const cancelRun = async (
  runId: string,
  data?: WorkflowCancelRequest
): Promise<WorkflowCancelResponse> => {
  const response = await apiClient.post<WorkflowCancelResponse>(`/runs/${runId}/cancel`, data || {});
  return response.data;
};

/**
 * Get run logs (placeholder)
 */
export const getRunLogs = async (runId: string): Promise<string[]> => {
  const response = await apiClient.get<string[]>(`/runs/${runId}/logs`);
  return response.data;
};

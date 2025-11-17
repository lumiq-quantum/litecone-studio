/**
 * React Query hooks for workflow management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsApi } from '@/services/api';
import type {
  WorkflowCreate,
  WorkflowUpdate,
  WorkflowExecuteRequest,
  PaginationParams,
  FilterParams,
} from '@/types';

/**
 * Query key factory for workflows
 */
export const workflowKeys = {
  all: ['workflows'] as const,
  lists: () => [...workflowKeys.all, 'list'] as const,
  list: (params?: PaginationParams & FilterParams) => [...workflowKeys.lists(), params] as const,
  details: () => [...workflowKeys.all, 'detail'] as const,
  detail: (id: string) => [...workflowKeys.details(), id] as const,
  versions: (id: string) => [...workflowKeys.all, 'versions', id] as const,
};

/**
 * Hook to list all workflows with pagination and filtering
 */
export const useWorkflows = (params?: PaginationParams & FilterParams) => {
  return useQuery({
    queryKey: workflowKeys.list(params),
    queryFn: () => workflowsApi.listWorkflows(params),
    staleTime: 3 * 60 * 1000, // 3 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
};

/**
 * Hook to get a single workflow by ID
 */
export const useWorkflow = (workflowId: string, enabled = true) => {
  return useQuery({
    queryKey: workflowKeys.detail(workflowId),
    queryFn: () => workflowsApi.getWorkflow(workflowId),
    enabled: enabled && !!workflowId,
    staleTime: 5 * 60 * 1000, // 5 minutes - workflow definitions are relatively stable
    gcTime: 30 * 60 * 1000, // 30 minutes - keep in cache longer
  });
};

/**
 * Hook to get all versions of a workflow
 */
export const useWorkflowVersions = (
  workflowId: string,
  params?: PaginationParams,
  enabled = true
) => {
  return useQuery({
    queryKey: [...workflowKeys.versions(workflowId), params],
    queryFn: () => workflowsApi.getWorkflowVersions(workflowId, params),
    enabled: enabled && !!workflowId,
  });
};

/**
 * Hook to create a new workflow
 */
export const useCreateWorkflow = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: WorkflowCreate) => workflowsApi.createWorkflow(data),
    onSuccess: () => {
      // Invalidate and refetch workflow lists
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
    },
  });
};

/**
 * Hook to update an existing workflow
 */
export const useUpdateWorkflow = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workflowId, data }: { workflowId: string; data: WorkflowUpdate }) =>
      workflowsApi.updateWorkflow(workflowId, data),
    onSuccess: (updatedWorkflow) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      // Update the specific workflow in cache
      queryClient.setQueryData(workflowKeys.detail(updatedWorkflow.id), updatedWorkflow);
      // Invalidate versions as a new version was created
      queryClient.invalidateQueries({ queryKey: workflowKeys.versions(updatedWorkflow.id) });
    },
  });
};

/**
 * Hook to delete a workflow
 */
export const useDeleteWorkflow = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workflowId: string) => workflowsApi.deleteWorkflow(workflowId),
    onSuccess: (_, workflowId) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      // Remove the specific workflow from cache
      queryClient.removeQueries({ queryKey: workflowKeys.detail(workflowId) });
      queryClient.removeQueries({ queryKey: workflowKeys.versions(workflowId) });
    },
  });
};

/**
 * Hook to execute a workflow
 */
export const useExecuteWorkflow = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workflowId, data }: { workflowId: string; data: WorkflowExecuteRequest }) =>
      workflowsApi.executeWorkflow(workflowId, data),
    onSuccess: () => {
      // Invalidate runs list as a new run was created
      queryClient.invalidateQueries({ queryKey: ['runs'] });
    },
  });
};

/**
 * React Query hooks for run management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { runsApi } from '@/services/api';
import type {
  WorkflowRetryRequest,
  WorkflowCancelRequest,
  PaginationParams,
  RunFilterParams,
} from '@/types';

/**
 * Query key factory for runs
 */
export const runKeys = {
  all: ['runs'] as const,
  lists: () => [...runKeys.all, 'list'] as const,
  list: (params?: PaginationParams & RunFilterParams) => [...runKeys.lists(), params] as const,
  details: () => [...runKeys.all, 'detail'] as const,
  detail: (id: string) => [...runKeys.details(), id] as const,
  steps: (id: string) => [...runKeys.all, 'steps', id] as const,
  logs: (id: string) => [...runKeys.all, 'logs', id] as const,
};

/**
 * Hook to list all runs with pagination and filtering
 */
export const useRuns = (params?: PaginationParams & RunFilterParams) => {
  return useQuery({
    queryKey: runKeys.list(params),
    queryFn: () => runsApi.listRuns(params),
    staleTime: 30 * 1000, // 30 seconds - runs change frequently
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook to get a single run by ID
 */
export const useRun = (runId: string, enabled = true) => {
  return useQuery({
    queryKey: runKeys.detail(runId),
    queryFn: () => runsApi.getRun(runId),
    enabled: enabled && !!runId,
    staleTime: 10 * 1000, // 10 seconds - runs update frequently when active
    gcTime: 10 * 60 * 1000, // 10 minutes
    // Refetch more frequently for active runs
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Poll every 2 seconds for running/pending runs
      if (status === 'RUNNING' || status === 'PENDING') {
        return 2000;
      }
      // Don't poll for completed runs
      return false;
    },
  });
};

/**
 * Hook to get step executions for a run
 */
export const useRunSteps = (runId: string, enabled = true) => {
  return useQuery({
    queryKey: runKeys.steps(runId),
    queryFn: () => runsApi.getRunSteps(runId),
    enabled: enabled && !!runId,
  });
};

/**
 * Hook to get run logs
 */
export const useRunLogs = (runId: string, enabled = true) => {
  return useQuery({
    queryKey: runKeys.logs(runId),
    queryFn: () => runsApi.getRunLogs(runId),
    enabled: enabled && !!runId,
  });
};

/**
 * Hook to retry a failed workflow run
 */
export const useRetryRun = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ runId, data }: { runId: string; data?: WorkflowRetryRequest }) =>
      runsApi.retryRun(runId, data),
    onSuccess: (response) => {
      // Invalidate run lists
      queryClient.invalidateQueries({ queryKey: runKeys.lists() });
      // Invalidate the original run
      queryClient.invalidateQueries({ queryKey: runKeys.detail(response.original_run_id) });
      // The new run will be fetched when navigating to it
    },
  });
};

/**
 * Hook to cancel a running workflow
 */
export const useCancelRun = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ runId, data }: { runId: string; data?: WorkflowCancelRequest }) =>
      runsApi.cancelRun(runId, data),
    onSuccess: (response) => {
      // Invalidate run lists
      queryClient.invalidateQueries({ queryKey: runKeys.lists() });
      // Invalidate the specific run to refetch updated status
      queryClient.invalidateQueries({ queryKey: runKeys.detail(response.run_id) });
    },
  });
};

/**
 * Hook to get the original run for a retry
 */
export const useOriginalRun = (originalRunId?: string) => {
  return useQuery({
    queryKey: runKeys.detail(originalRunId || ''),
    queryFn: () => runsApi.getRun(originalRunId || ''),
    enabled: !!originalRunId,
  });
};

/**
 * Hook to get retry attempts for a run
 */
export const useRetryAttempts = (runId: string) => {
  return useQuery({
    queryKey: [...runKeys.all, 'retries', runId],
    queryFn: async () => {
      // Fetch all runs and filter for retries of this run
      const result = await runsApi.listRuns({ page_size: 100 });
      return result.items.filter((run) => run.original_run_id === runId);
    },
    enabled: !!runId,
  });
};

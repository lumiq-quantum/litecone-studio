import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { runKeys } from './useRuns';
import type { RunStatus } from '@/types';

interface UsePollingOptions {
  /**
   * Run ID to poll
   */
  runId: string;
  /**
   * Whether polling is enabled
   */
  enabled: boolean;
  /**
   * Polling interval in milliseconds (default: 2000)
   */
  interval?: number;
  /**
   * Callback when run completes
   */
  onComplete?: () => void;
  /**
   * Callback when polling error occurs
   */
  onError?: (error: Error) => void;
}

/**
 * Hook to poll run status at regular intervals
 * Automatically stops polling when run reaches a terminal state
 */
export function useRunPolling({
  runId,
  enabled,
  interval = 2000,
  onComplete,
  onError,
}: UsePollingOptions) {
  const queryClient = useQueryClient();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const errorCountRef = useRef(0);
  const maxErrors = 3;

  useEffect(() => {
    if (!enabled || !runId) {
      return;
    }

    // Start polling
    intervalRef.current = setInterval(async () => {
      try {
        // Invalidate the run query to trigger a refetch
        await queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) });
        
        // Also invalidate steps
        await queryClient.invalidateQueries({ queryKey: runKeys.steps(runId) });

        // Get the current run data to check status
        const runData = queryClient.getQueryData<{ status: RunStatus }>(runKeys.detail(runId));

        // Reset error count on successful poll
        errorCountRef.current = 0;

        // Stop polling if run is in terminal state
        if (runData?.status && ['COMPLETED', 'FAILED', 'CANCELLED'].includes(runData.status)) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
          }
          onComplete?.();
        }
      } catch (error) {
        errorCountRef.current += 1;
        
        if (errorCountRef.current >= maxErrors) {
          // Stop polling after max errors
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
          }
          onError?.(error as Error);
        }
      }
    }, interval);

    // Cleanup on unmount or when dependencies change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [runId, enabled, interval, queryClient, onComplete, onError]);

  // Function to manually stop polling
  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  };

  return { stopPolling };
}

/**
 * Hook to determine if a run should be polled based on its status
 */
export function useShouldPoll(status?: RunStatus): boolean {
  if (!status) return false;
  return status === 'PENDING' || status === 'RUNNING';
}

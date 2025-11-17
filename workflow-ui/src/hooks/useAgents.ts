/**
 * React Query hooks for agent management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentsApi } from '@/services/api';
import type {
  AgentCreate,
  AgentUpdate,
  PaginationParams,
} from '@/types';

/**
 * Query key factory for agents
 */
export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (params?: PaginationParams & { status?: string }) =>
    [...agentKeys.lists(), params] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentKeys.details(), id] as const,
  health: (id: string) => [...agentKeys.all, 'health', id] as const,
};

/**
 * Hook to list all agents with pagination
 */
export const useAgents = (params?: PaginationParams & { status?: string }) => {
  return useQuery({
    queryKey: agentKeys.list(params),
    queryFn: () => agentsApi.listAgents(params),
    staleTime: 2 * 60 * 1000, // 2 minutes - agents don't change frequently
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
};

/**
 * Hook to get a single agent by ID
 */
export const useAgent = (agentId: string, enabled = true) => {
  return useQuery({
    queryKey: agentKeys.detail(agentId),
    queryFn: () => agentsApi.getAgent(agentId),
    enabled: enabled && !!agentId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
  });
};

/**
 * Hook to check agent health
 */
export const useAgentHealth = (agentId: string, enabled = true) => {
  return useQuery({
    queryKey: agentKeys.health(agentId),
    queryFn: () => agentsApi.checkAgentHealth(agentId),
    enabled: enabled && !!agentId,
    retry: false, // Don't retry health checks
    staleTime: 30000, // Consider health data stale after 30 seconds
  });
};

/**
 * Hook to create a new agent
 */
export const useCreateAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AgentCreate) => agentsApi.createAgent(data),
    onSuccess: () => {
      // Invalidate and refetch agent lists
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
};

/**
 * Hook to update an existing agent
 */
export const useUpdateAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, data }: { agentId: string; data: AgentUpdate }) =>
      agentsApi.updateAgent(agentId, data),
    onSuccess: (updatedAgent) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      // Update the specific agent in cache
      queryClient.setQueryData(agentKeys.detail(updatedAgent.id), updatedAgent);
    },
  });
};

/**
 * Hook to delete an agent
 */
export const useDeleteAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (agentId: string) => agentsApi.deleteAgent(agentId),
    onSuccess: (_, agentId) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      // Remove the specific agent from cache
      queryClient.removeQueries({ queryKey: agentKeys.detail(agentId) });
    },
  });
};

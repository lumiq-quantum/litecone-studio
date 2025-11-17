/**
 * Agent API service
 */
import apiClient from './client';
import type {
  AgentCreate,
  AgentUpdate,
  AgentResponse,
  AgentHealthResponse,
  PaginatedResponse,
  PaginationParams,
} from '@/types';

/**
 * List all agents with pagination
 */
export const listAgents = async (
  params?: PaginationParams & { status?: string }
): Promise<PaginatedResponse<AgentResponse>> => {
  const response = await apiClient.get<PaginatedResponse<AgentResponse>>('/agents', { params });
  return response.data;
};

/**
 * Get a single agent by ID
 */
export const getAgent = async (agentId: string): Promise<AgentResponse> => {
  const response = await apiClient.get<AgentResponse>(`/agents/${agentId}`);
  return response.data;
};

/**
 * Create a new agent
 */
export const createAgent = async (data: AgentCreate): Promise<AgentResponse> => {
  const response = await apiClient.post<AgentResponse>('/agents', data);
  return response.data;
};

/**
 * Update an existing agent
 */
export const updateAgent = async (agentId: string, data: AgentUpdate): Promise<AgentResponse> => {
  const response = await apiClient.put<AgentResponse>(`/agents/${agentId}`, data);
  return response.data;
};

/**
 * Delete an agent (soft delete)
 */
export const deleteAgent = async (agentId: string): Promise<void> => {
  await apiClient.delete(`/agents/${agentId}`);
};

/**
 * Check agent health
 */
export const checkAgentHealth = async (agentId: string): Promise<AgentHealthResponse> => {
  const response = await apiClient.get<AgentHealthResponse>(`/agents/${agentId}/health`);
  return response.data;
};

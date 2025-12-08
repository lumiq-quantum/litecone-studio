/**
 * AI Workflow Generator API service
 */
import apiClient from './client';
import type {
  WorkflowGenerateRequest,
  WorkflowGenerationResult,
  ChatSessionCreateRequest,
  ChatSession,
  ChatMessageSendRequest,
  WorkflowSaveRequest,
  WorkflowSaveResponse,
  AgentSuggestRequest,
  AgentSuggestionResult,
  SessionDeleteResponse,
} from '@/types';

/**
 * Generate workflow from text description
 */
export const generateWorkflow = async (
  data: WorkflowGenerateRequest
): Promise<WorkflowGenerationResult> => {
  const response = await apiClient.post<WorkflowGenerationResult>(
    '/ai-workflows/generate',
    data
  );
  return response.data;
};

/**
 * Upload document for workflow generation
 */
export const uploadDocument = async (file: File): Promise<WorkflowGenerationResult> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<WorkflowGenerationResult>(
    '/ai-workflows/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minutes for large PDF processing
    }
  );
  return response.data;
};

/**
 * Create a new chat session
 */
export const createChatSession = async (
  data?: ChatSessionCreateRequest
): Promise<ChatSession> => {
  const response = await apiClient.post<ChatSession>(
    '/ai-workflows/chat/sessions',
    data || {},
    {
      timeout: 60000, // 1 minute for initial workflow generation
    }
  );
  return response.data;
};

/**
 * Send message to chat session
 */
export const sendChatMessage = async (
  sessionId: string,
  data: ChatMessageSendRequest
): Promise<ChatSession> => {
  const response = await apiClient.post<ChatSession>(
    `/ai-workflows/chat/sessions/${sessionId}/messages`,
    data,
    {
      timeout: 60000, // 1 minute for workflow refinement
    }
  );
  return response.data;
};

/**
 * Get chat session details
 */
export const getChatSession = async (sessionId: string): Promise<ChatSession> => {
  const response = await apiClient.get<ChatSession>(
    `/ai-workflows/chat/sessions/${sessionId}`
  );
  return response.data;
};

/**
 * Delete chat session
 */
export const deleteChatSession = async (sessionId: string): Promise<SessionDeleteResponse> => {
  const response = await apiClient.delete<SessionDeleteResponse>(
    `/ai-workflows/chat/sessions/${sessionId}`
  );
  return response.data;
};

/**
 * Save workflow from chat session
 */
export const saveWorkflowFromSession = async (
  sessionId: string,
  data: WorkflowSaveRequest
): Promise<WorkflowSaveResponse> => {
  const response = await apiClient.post<WorkflowSaveResponse>(
    `/ai-workflows/chat/sessions/${sessionId}/save`,
    data
  );
  return response.data;
};

/**
 * Export workflow JSON from session
 */
export const exportWorkflowFromSession = async (sessionId: string): Promise<Blob> => {
  const response = await apiClient.get(`/ai-workflows/chat/sessions/${sessionId}/export`, {
    responseType: 'blob',
  });
  return response.data;
};

/**
 * Get agent suggestions for a capability
 */
export const suggestAgents = async (
  data: AgentSuggestRequest
): Promise<AgentSuggestionResult> => {
  const response = await apiClient.post<AgentSuggestionResult>(
    '/ai-workflows/agents/suggest',
    data
  );
  return response.data;
};

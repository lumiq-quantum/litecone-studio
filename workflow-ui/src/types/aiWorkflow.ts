/**
 * AI Workflow Generator types and interfaces
 */

import type { WorkflowDefinition } from './workflow';

/**
 * Message role types
 */
export type MessageRole = 'user' | 'assistant' | 'system';

/**
 * Chat session status types
 */
export type ChatSessionStatus = 'active' | 'completed' | 'expired';

/**
 * Message metadata for assistant responses
 */
export interface MessageMetadata {
  success?: boolean;
  validation_errors?: string[];
  suggestions?: string[];
  agents_used?: string[];
}

/**
 * Chat message
 */
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  metadata?: MessageMetadata | null;
}

/**
 * Chat session
 */
export interface ChatSession {
  id: string;
  user_id?: string;
  status: ChatSessionStatus;
  created_at: string;
  updated_at: string;
  expires_at: string;
  messages: Message[];
  current_workflow: WorkflowDefinition | null;
  workflow_history: WorkflowDefinition[];
}

/**
 * Workflow generation result
 */
export interface WorkflowGenerationResult {
  success: boolean;
  workflow_json: WorkflowDefinition | null;
  explanation: string;
  validation_errors: string[];
  suggestions: string[];
  agents_used: string[];
}

/**
 * User preferences for workflow generation
 */
export interface UserPreferences {
  prefer_parallel?: boolean;
  max_steps?: number;
}

/**
 * Request payload for generating workflow from text
 */
export interface WorkflowGenerateRequest {
  description: string;
  user_preferences?: UserPreferences;
}

/**
 * Request payload for creating a chat session
 */
export interface ChatSessionCreateRequest {
  initial_description?: string;
  user_id?: string;
}

/**
 * Request payload for sending a chat message
 */
export interface ChatMessageSendRequest {
  message: string;
}

/**
 * Request payload for saving workflow from session
 */
export interface WorkflowSaveRequest {
  name: string;
  description?: string;
}

/**
 * Response from saving workflow
 */
export interface WorkflowSaveResponse {
  workflow_id: string;
  name: string;
  url: string;
}

/**
 * Agent suggestion
 */
export interface AgentSuggestion {
  agent_name: string;
  agent_url: string;
  agent_description: string;
  capabilities: string[];
  relevance_score: number;
  reason: string;
}

/**
 * Agent suggestion result
 */
export interface AgentSuggestionResult {
  suggestions: AgentSuggestion[];
  is_ambiguous: boolean;
  requires_user_choice: boolean;
  no_match: boolean;
  alternatives: string[];
  explanation: string;
}

/**
 * Request payload for agent suggestions
 */
export interface AgentSuggestRequest {
  capability_description: string;
}

/**
 * Session deletion response
 */
export interface SessionDeleteResponse {
  message: string;
  session_id: string;
}

/**
 * AI Workflow API error details
 */
export interface AIWorkflowErrorDetails {
  errors?: Array<{
    field: string;
    message: string;
    type: string;
  }>;
  limit?: number;
  window_seconds?: number;
  retry_after_seconds?: number;
}

/**
 * AI Workflow API error response
 */
export interface AIWorkflowError {
  error_code?: string;
  message: string;
  details?: AIWorkflowErrorDetails;
  suggestions?: string[];
  recoverable?: boolean;
}

/**
 * Agent-related types and interfaces
 */

/**
 * Retry configuration for agent requests
 */
export interface RetryConfig {
  max_retries: number;
  initial_delay_ms: number;
  max_delay_ms: number;
  backoff_multiplier: number;
}

/**
 * Circuit breaker configuration for agent resilience
 */
export interface CircuitBreakerConfig {
  enabled: boolean;
  failure_threshold: number;
  failure_rate_threshold: number;
  timeout_seconds: number;
  half_open_max_calls: number;
  window_size_seconds: number;
}

/**
 * Agent authentication types
 */
export type AuthType = 'none' | 'bearer' | 'apikey';

/**
 * Agent status types
 */
export type AgentStatus = 'active' | 'inactive' | 'deleted';

/**
 * Authentication configuration for bearer token
 */
export interface BearerAuthConfig {
  token: string;
}

/**
 * Authentication configuration for API key
 */
export interface ApiKeyAuthConfig {
  key: string;
  header_name: string;
}

/**
 * Union type for auth configuration
 */
export type AuthConfig = BearerAuthConfig | ApiKeyAuthConfig | null;

/**
 * Request payload for creating a new agent
 */
export interface AgentCreate {
  name: string;
  url: string;
  description?: string;
  auth_type?: AuthType;
  auth_config?: AuthConfig;
  timeout_ms?: number;
  retry_config?: RetryConfig;
  circuit_breaker_config?: CircuitBreakerConfig;
}

/**
 * Request payload for updating an existing agent
 */
export interface AgentUpdate {
  url?: string;
  description?: string;
  auth_type?: AuthType;
  auth_config?: AuthConfig;
  timeout_ms?: number;
  retry_config?: RetryConfig;
  circuit_breaker_config?: CircuitBreakerConfig;
  status?: AgentStatus;
}

/**
 * Agent response from API
 */
export interface AgentResponse {
  id: string;
  name: string;
  url: string;
  description?: string;
  auth_type: AuthType;
  auth_config?: AuthConfig;
  timeout_ms: number;
  retry_config: RetryConfig;
  circuit_breaker_config?: CircuitBreakerConfig;
  status: AgentStatus;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
}

/**
 * Agent Card data from /.well-known/agent-card.json
 */
export interface AgentCard {
  name: string;
  description?: string;
  version?: string;
  capabilities?: string[];
  [key: string]: any; // Allow additional properties
}

/**
 * Agent health check response
 */
export interface AgentHealthResponse {
  status: 'healthy' | 'unhealthy';
  message?: string;
  response_time_ms?: number;
  timestamp: string;
  agent_card?: AgentCard; // Include agent card data when available
}

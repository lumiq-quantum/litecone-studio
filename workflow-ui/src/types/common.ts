/**
 * Common types and interfaces used across the application
 */

/**
 * Pagination parameters for list requests
 */
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Error detail for validation errors
 */
export interface ErrorDetail {
  field?: string;
  message: string;
  type?: string;
}

/**
 * Standard API error response
 */
export interface ApiError {
  error: string;
  detail?: string;
  errors?: ErrorDetail[];
  status_code: number;
  timestamp: string;
  path?: string;
  request_id?: string;
}

/**
 * Health status for individual services
 */
export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  message?: string;
  response_time_ms?: number;
}

/**
 * Health check response
 */
export interface HealthResponse {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  version?: string;
  uptime_seconds?: number;
  services?: Record<string, HealthStatus>;
}

/**
 * Readiness check response
 */
export interface ReadinessResponse {
  ready: boolean;
  timestamp: string;
  checks: Record<string, HealthStatus>;
}

/**
 * Simple message response
 */
export interface MessageResponse {
  message: string;
  timestamp: string;
  data?: Record<string, unknown>;
}

/**
 * Filter and sort parameters for list requests
 */
export interface FilterParams {
  status?: string;
  name?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

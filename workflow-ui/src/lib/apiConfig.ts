/**
 * Dynamic API URL configuration
 * Automatically detects the current host and constructs the API URL
 */

/**
 * Get the API base URL dynamically based on the current window location
 * 
 * Logic:
 * - If running on localhost:3000 → API is at localhost:8000
 * - If running on any other host:3000 → API is at same-host:8000
 * - If VITE_API_URL is explicitly set, use that (for custom deployments)
 * 
 * Examples:
 * - http://localhost:3000 → http://localhost:8000/api/v1
 * - http://3.111.65.158:3000 → http://3.111.65.158:8000/api/v1
 * - http://myapp.com:3000 → http://myapp.com:8000/api/v1
 */
export function getApiBaseUrl(): string {
  // Check if VITE_API_URL is explicitly set (for custom configurations)
  const envApiUrl = import.meta.env.VITE_API_URL;
  if (envApiUrl && envApiUrl !== '') {
    return envApiUrl;
  }

  // Get current window location
  const { protocol, hostname } = window.location;

  // Construct API URL with same protocol and hostname, but port 8000
  const apiUrl = `${protocol}//${hostname}:8000/api/v1`;

  // Log in development mode
  if (import.meta.env.DEV) {
    console.log('[API Config] Dynamically constructed API URL:', apiUrl);
    console.log('[API Config] Current location:', window.location.href);
  }

  return apiUrl;
}

/**
 * Get the WebSocket URL for real-time updates (if needed in future)
 */
export function getWebSocketUrl(): string {
  const { protocol, hostname } = window.location;
  const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
  return `${wsProtocol}//${hostname}:8000/ws`;
}

/**
 * Configuration object for API settings
 */
export const apiConfig = {
  baseURL: getApiBaseUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
} as const;

/**
 * Get polling interval from environment or use default
 */
export function getPollingInterval(): number {
  const envInterval = import.meta.env.VITE_POLLING_INTERVAL;
  return envInterval ? parseInt(envInterval, 10) : 2000;
}

/**
 * Get app name from environment or use default
 */
export function getAppName(): string {
  return import.meta.env.VITE_APP_NAME || 'LiteCone Studio';
}

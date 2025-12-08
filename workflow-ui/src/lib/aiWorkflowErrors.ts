/**
 * AI Workflow Error Handling Utilities
 * 
 * Provides user-friendly error messages for AI workflow API errors.
 * Task 27: Enhanced error recovery mechanisms
 */

import type { AIWorkflowError } from '@/types';

/**
 * Error category types for better error handling
 * Task 27: Categorize errors for appropriate recovery strategies
 */
export type ErrorCategory = 
  | 'network'           // Network connectivity issues
  | 'rate_limit'        // Rate limiting
  | 'session_expired'   // Session expiration
  | 'validation'        // Input validation errors
  | 'service_unavailable' // Service temporarily down
  | 'server_error'      // Internal server errors
  | 'client_error'      // Client-side errors
  | 'unknown';          // Unknown errors

/**
 * Error information with recovery details
 * Task 27: Structured error information for recovery
 */
export interface ErrorInfo {
  message: string;
  category: ErrorCategory;
  recoverable: boolean;
  retryAfter?: number;
  suggestions: string[];
  details?: string;
}

/**
 * Handle AI Workflow API errors and return user-friendly messages
 * 
 * @param error - The error object from the API
 * @returns User-friendly error message
 */
export function handleAIWorkflowError(error: unknown): string {
  const errorInfo = getErrorInfo(error);
  return errorInfo.message;
}

/**
 * Get detailed error information for recovery strategies
 * Task 27: Enhanced error analysis for recovery mechanisms
 * 
 * @param error - The error object from the API
 * @returns Detailed error information
 */
export function getErrorInfo(error: unknown): ErrorInfo {
  // Handle axios error structure
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const axiosError = error as {
      response?: {
        status: number;
        data?: AIWorkflowError;
        headers?: Record<string, string>;
      };
      message?: string;
    };

    const status = axiosError.response?.status;
    const data = axiosError.response?.data;
    const headers = axiosError.response?.headers;

    // Rate limit error (429)
    // Task 27: Enhanced rate limit handling with countdown
    if (status === 429) {
      const retryAfter = headers?.['retry-after'] 
        ? parseInt(headers['retry-after'], 10)
        : data?.details?.retry_after_seconds || 60;
      
      return {
        message: `Rate limit exceeded. Please wait ${retryAfter} seconds before trying again.`,
        category: 'rate_limit',
        recoverable: true,
        retryAfter,
        suggestions: data?.suggestions || [
          'Wait for the rate limit to reset',
          'Reduce the frequency of requests',
        ],
        details: data?.details ? JSON.stringify(data.details) : undefined,
      };
    }

    // Bad request (400)
    // Task 27: Enhanced validation error handling
    if (status === 400) {
      const isValidationError = data?.error_code?.includes('validation') || 
                                data?.details?.errors !== undefined;
      
      let message = data?.message || 'Invalid request. Please check your input and try again.';
      
      // Add validation details if available
      if (data?.details?.errors && Array.isArray(data.details.errors)) {
        const errorDetails = data.details.errors
          .map(e => `${e.field}: ${e.message}`)
          .join('\n');
        message += `\n\nValidation errors:\n${errorDetails}`;
      }
      
      return {
        message,
        category: isValidationError ? 'validation' : 'client_error',
        recoverable: isValidationError,
        suggestions: data?.suggestions || [
          'Check your input for errors',
          'Ensure all required fields are provided',
          'Verify the format of your data',
        ],
        details: data?.details ? JSON.stringify(data.details) : undefined,
      };
    }

    // Not found (404)
    // Task 27: Session expiration recovery
    if (status === 404) {
      return {
        message: 'Session not found or expired. Starting a new session...',
        category: 'session_expired',
        recoverable: true,
        suggestions: [
          'A new session will be created automatically',
          'Your previous conversation history will be cleared',
        ],
      };
    }

    // Service unavailable (503)
    // Task 27: Service unavailable recovery
    if (status === 503) {
      const retryAfter = headers?.['retry-after'] 
        ? parseInt(headers['retry-after'], 10)
        : 30;
      
      return {
        message: 'AI service is temporarily unavailable. Please try again in a moment.',
        category: 'service_unavailable',
        recoverable: true,
        retryAfter,
        suggestions: data?.suggestions || [
          'Wait a moment and try again',
          'The service should be back online shortly',
        ],
      };
    }

    // Internal server error (500)
    // Task 27: Server error handling
    if (status === 500) {
      return {
        message: data?.message 
          ? `Server error: ${data.message}`
          : 'An internal server error occurred. Please try again.',
        category: 'server_error',
        recoverable: true,
        suggestions: data?.suggestions || [
          'Try your request again',
          'If the problem persists, contact support',
        ],
        details: data?.details ? JSON.stringify(data.details) : undefined,
      };
    }

    // Other HTTP errors
    if (status && data?.message) {
      return {
        message: data.message,
        category: status >= 500 ? 'server_error' : 'client_error',
        recoverable: data.recoverable !== undefined ? data.recoverable : status >= 500,
        suggestions: data.suggestions || [],
        details: data?.details ? JSON.stringify(data.details) : undefined,
      };
    }
  }

  // Network errors
  // Task 27: Enhanced network error handling
  if (error instanceof Error) {
    if (error.message.includes('Network Error') || error.message.includes('ECONNREFUSED')) {
      return {
        message: 'Unable to connect to the server. Please check your connection and try again.',
        category: 'network',
        recoverable: true,
        suggestions: [
          'Check your internet connection',
          'Verify the server is running',
          'Try refreshing the page',
        ],
      };
    }
    if (error.message.includes('timeout')) {
      return {
        message: 'Request timed out. The server took too long to respond.',
        category: 'network',
        recoverable: true,
        suggestions: [
          'Try your request again',
          'Check your internet connection',
          'The server may be experiencing high load',
        ],
      };
    }
    return {
      message: error.message,
      category: 'unknown',
      recoverable: false,
      suggestions: ['Try refreshing the page', 'Contact support if the problem persists'],
    };
  }

  // Fallback error message
  // Task 27: Fallback for unknown errors
  return {
    message: 'An unexpected error occurred. Please try again.',
    category: 'unknown',
    recoverable: false,
    suggestions: [
      'Try refreshing the page',
      'Clear your browser cache',
      'Contact support if the problem persists',
    ],
  };
}

/**
 * Check if an error is recoverable
 * Task 27: Enhanced recoverability check
 * 
 * @param error - The error object
 * @returns Whether the error is recoverable
 */
export function isRecoverableError(error: unknown): boolean {
  const errorInfo = getErrorInfo(error);
  return errorInfo.recoverable;
}

/**
 * Check if an error is a critical error that requires fallback UI
 * Task 27: Critical error detection for fallback UI
 * 
 * @param error - The error object
 * @returns Whether the error is critical
 */
export function isCriticalError(error: unknown): boolean {
  const errorInfo = getErrorInfo(error);
  
  // Critical errors are those that are not recoverable and not user-fixable
  return !errorInfo.recoverable && 
         errorInfo.category !== 'validation' &&
         errorInfo.category !== 'client_error';
}

/**
 * Extract retry-after seconds from error
 * 
 * @param error - The error object
 * @returns Number of seconds to wait before retrying, or null
 */
export function getRetryAfterSeconds(error: unknown): number | null {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const axiosError = error as {
      response?: {
        headers?: Record<string, string>;
        data?: AIWorkflowError;
      };
    };

    // Check retry-after header
    const retryAfter = axiosError.response?.headers?.['retry-after'];
    if (retryAfter) {
      const seconds = parseInt(retryAfter, 10);
      if (!isNaN(seconds)) {
        return seconds;
      }
    }

    // Check data for retry information
    const retrySeconds = axiosError.response?.data?.details?.retry_after_seconds;
    if (retrySeconds !== undefined) {
      return retrySeconds;
    }
  }

  return null;
}

/**
 * Extract suggestions from error
 * Task 27: Enhanced suggestion extraction
 * 
 * @param error - The error object
 * @returns Array of suggestion strings
 */
export function getErrorSuggestions(error: unknown): string[] {
  const errorInfo = getErrorInfo(error);
  return errorInfo.suggestions;
}

/**
 * Retry configuration for automatic retry with exponential backoff
 * Task 27: Automatic retry mechanism
 */
export interface RetryConfig {
  maxAttempts: number;
  initialDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

/**
 * Default retry configuration
 */
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  initialDelay: 1000, // 1 second
  maxDelay: 10000,    // 10 seconds
  backoffMultiplier: 2,
};

/**
 * Retry a function with exponential backoff
 * Task 27: Network error retry logic with exponential backoff
 * 
 * @param fn - The function to retry
 * @param config - Retry configuration
 * @returns Promise that resolves with the function result
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const finalConfig = { ...DEFAULT_RETRY_CONFIG, ...config };
  let lastError: unknown;
  
  for (let attempt = 0; attempt < finalConfig.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // Check if error is recoverable
      if (!isRecoverableError(error)) {
        throw error;
      }
      
      // Don't retry on the last attempt
      if (attempt === finalConfig.maxAttempts - 1) {
        throw error;
      }
      
      // Calculate delay with exponential backoff
      const delay = Math.min(
        finalConfig.initialDelay * Math.pow(finalConfig.backoffMultiplier, attempt),
        finalConfig.maxDelay
      );
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
}

/**
 * Check if an error should trigger automatic retry
 * Task 27: Determine if automatic retry should be attempted
 * 
 * @param error - The error object
 * @returns Whether automatic retry should be attempted
 */
export function shouldAutoRetry(error: unknown): boolean {
  const errorInfo = getErrorInfo(error);
  
  // Auto-retry for network errors and service unavailable
  return errorInfo.category === 'network' || 
         errorInfo.category === 'service_unavailable';
}

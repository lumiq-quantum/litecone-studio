/**
 * Error handling utilities
 */
import { AxiosError } from 'axios';
import type { ApiError } from '@/types';

/**
 * Extract user-friendly error message from API error
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const apiError = error.response?.data as ApiError | undefined;

    // Use API error message if available
    if (apiError?.detail) {
      return apiError.detail;
    }
    if (apiError?.error) {
      return apiError.error;
    }

    // Handle specific HTTP status codes
    const status = error.response?.status;
    switch (status) {
      case 400:
        return 'Invalid request. Please check your input and try again.';
      case 401:
        return 'You are not authorized to perform this action.';
      case 403:
        return 'Access forbidden. You do not have permission to access this resource.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return 'A conflict occurred. The resource may already exist.';
      case 422:
        return 'Validation failed. Please check your input.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'An internal server error occurred. Please try again later.';
      case 502:
        return 'Bad gateway. The server is temporarily unavailable.';
      case 503:
        return 'Service unavailable. Please try again later.';
      case 504:
        return 'Gateway timeout. The request took too long to complete.';
      default:
        if (status && status >= 500) {
          return 'A server error occurred. Please try again later.';
        }
        if (status && status >= 400) {
          return 'An error occurred while processing your request.';
        }
    }

    // Handle network errors
    if (error.code === 'ECONNABORTED') {
      return 'Request timeout. Please check your connection and try again.';
    }
    if (error.code === 'ERR_NETWORK') {
      return 'Network error. Please check your internet connection.';
    }
    if (!error.response) {
      return 'Unable to connect to the server. Please check your connection.';
    }

    return error.message || 'An unexpected error occurred.';
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred.';
}

/**
 * Get actionable suggestion for error
 */
export function getErrorSuggestion(error: unknown): string | null {
  if (error instanceof AxiosError) {
    const status = error.response?.status;

    switch (status) {
      case 400:
        return 'Double-check the form fields and ensure all required information is provided.';
      case 401:
        return 'You may need to log in again to continue.';
      case 403:
        return 'Contact your administrator if you believe you should have access.';
      case 404:
        return 'The item may have been deleted or moved. Try refreshing the page.';
      case 409:
        return 'Try using a different name or identifier.';
      case 422:
        return 'Review the highlighted fields and correct any validation errors.';
      case 429:
        return 'Wait a few moments before trying again.';
      case 500:
      case 502:
      case 503:
      case 504:
        return 'Our team has been notified. Please try again in a few minutes.';
      default:
        if (!error.response) {
          return 'Check your internet connection and try again.';
        }
    }
  }

  return null;
}

/**
 * Get validation errors from API response
 */
export function getValidationErrors(error: unknown): Record<string, string[]> | null {
  if (error instanceof AxiosError) {
    const apiError = error.response?.data as ApiError | undefined;
    if (apiError?.errors) {
      // Convert ErrorDetail[] to Record<string, string[]>
      const validationErrors: Record<string, string[]> = {};
      apiError.errors.forEach((err) => {
        const field = err.field || 'general';
        if (!validationErrors[field]) {
          validationErrors[field] = [];
        }
        validationErrors[field].push(err.message);
      });
      return validationErrors;
    }
  }
  return null;
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return !error.response || error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED';
  }
  return false;
}

/**
 * Check if error is a validation error
 */
export function isValidationError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 422;
  }
  return false;
}

/**
 * Check if error is a server error
 */
export function isServerError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    const status = error.response?.status;
    return status !== undefined && status >= 500;
  }
  return false;
}

/**
 * Format error for display
 */
export interface FormattedError {
  title: string;
  message: string;
  suggestion: string | null;
  validationErrors: Record<string, string[]> | null;
  isRetryable: boolean;
}

export function formatError(error: unknown): FormattedError {
  const message = getErrorMessage(error);
  const suggestion = getErrorSuggestion(error);
  const validationErrors = getValidationErrors(error);
  const isRetryable = isNetworkError(error) || isServerError(error);

  let title = 'Error';
  if (isNetworkError(error)) {
    title = 'Connection Error';
  } else if (isServerError(error)) {
    title = 'Server Error';
  } else if (isValidationError(error)) {
    title = 'Validation Error';
  }

  return {
    title,
    message,
    suggestion,
    validationErrors,
    isRetryable,
  };
}

/**
 * Create error toast message
 */
export function createErrorToast(error: unknown): { message: string; description?: string } {
  const formatted = formatError(error);
  return {
    message: formatted.message,
    description: formatted.suggestion || undefined,
  };
}

import { describe, it, expect } from 'vitest';
import { AxiosError } from 'axios';
import {
  getErrorMessage,
  getErrorSuggestion,
  getValidationErrors,
  isNetworkError,
  isValidationError,
  isServerError,
  formatError,
} from '../errors';

describe('getErrorMessage', () => {
  it('should extract message from API error', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      status: 400,
      data: { message: 'Invalid input' },
      statusText: 'Bad Request',
      headers: {},
      config: {} as any,
    };
    expect(getErrorMessage(error)).toBe('Invalid input');
  });

  it('should return default message for 400 status', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      status: 400,
      data: {},
      statusText: 'Bad Request',
      headers: {},
      config: {} as any,
    };
    expect(getErrorMessage(error)).toBe('Invalid request. Please check your input and try again.');
  });

  it('should return default message for 404 status', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      status: 404,
      data: {},
      statusText: 'Not Found',
      headers: {},
      config: {} as any,
    };
    expect(getErrorMessage(error)).toBe('The requested resource was not found.');
  });

  it('should return default message for 500 status', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      status: 500,
      data: {},
      statusText: 'Internal Server Error',
      headers: {},
      config: {} as any,
    };
    expect(getErrorMessage(error)).toBe('An internal server error occurred. Please try again later.');
  });

  it('should handle network errors', () => {
    const error = new AxiosError('Network Error');
    error.code = 'ERR_NETWORK';
    expect(getErrorMessage(error)).toBe('Network error. Please check your internet connection.');
  });

  it('should handle timeout errors', () => {
    const error = new AxiosError('Timeout');
    error.code = 'ECONNABORTED';
    expect(getErrorMessage(error)).toBe('Request timeout. Please check your connection and try again.');
  });

  it('should handle generic Error', () => {
    const error = new Error('Something went wrong');
    expect(getErrorMessage(error)).toBe('Something went wrong');
  });

  it('should handle unknown errors', () => {
    expect(getErrorMessage('string error')).toBe('An unexpected error occurred.');
  });
});

describe('getErrorSuggestion', () => {
  it('should return suggestion for 400 status', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      status: 400,
      data: {},
      statusText: 'Bad Request',
      headers: {},
      config: {} as any,
    };
    expect(getErrorSuggestion(error)).toBe('Double-check the form fields and ensure all required information is provided.');
  });

  it('should return suggestion for 404 status', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      status: 404,
      data: {},
      statusText: 'Not Found',
      headers: {},
      config: {} as any,
    };
    expect(getErrorSuggestion(error)).toBe('The item may have been deleted or moved. Try refreshing the page.');
  });

  it('should return suggestion for network error', () => {
    const error = new AxiosError('Network Error');
    error.code = 'ERR_NETWORK';
    expect(getErrorSuggestion(error)).toBe('Check your internet connection and try again.');
  });

  it('should return null for unknown errors', () => {
    expect(getErrorSuggestion('string error')).toBeNull();
  });
});

describe('getValidationErrors', () => {
  it('should extract validation errors from API response', () => {
    const error = new AxiosError('Validation failed');
    error.response = {
      status: 422,
      data: {
        errors: {
          name: ['Name is required'],
          email: ['Invalid email format'],
        },
      },
      statusText: 'Unprocessable Entity',
      headers: {},
      config: {} as any,
    };
    const errors = getValidationErrors(error);
    expect(errors).toEqual({
      name: ['Name is required'],
      email: ['Invalid email format'],
    });
  });

  it('should return null when no validation errors', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      status: 400,
      data: {},
      statusText: 'Bad Request',
      headers: {},
      config: {} as any,
    };
    expect(getValidationErrors(error)).toBeNull();
  });
});

describe('isNetworkError', () => {
  it('should return true for network errors', () => {
    const error = new AxiosError('Network Error');
    error.code = 'ERR_NETWORK';
    expect(isNetworkError(error)).toBe(true);
  });

  it('should return true for timeout errors', () => {
    const error = new AxiosError('Timeout');
    error.code = 'ECONNABORTED';
    expect(isNetworkError(error)).toBe(true);
  });

  it('should return true when no response', () => {
    const error = new AxiosError('No response');
    expect(isNetworkError(error)).toBe(true);
  });

  it('should return false for other errors', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      status: 400,
      data: {},
      statusText: 'Bad Request',
      headers: {},
      config: {} as any,
    };
    expect(isNetworkError(error)).toBe(false);
  });
});

describe('isValidationError', () => {
  it('should return true for 422 status', () => {
    const error = new AxiosError('Validation failed');
    error.response = {
      status: 422,
      data: {},
      statusText: 'Unprocessable Entity',
      headers: {},
      config: {} as any,
    };
    expect(isValidationError(error)).toBe(true);
  });

  it('should return false for other statuses', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      status: 400,
      data: {},
      statusText: 'Bad Request',
      headers: {},
      config: {} as any,
    };
    expect(isValidationError(error)).toBe(false);
  });
});

describe('isServerError', () => {
  it('should return true for 500 status', () => {
    const error = new AxiosError('Server error');
    error.response = {
      status: 500,
      data: {},
      statusText: 'Internal Server Error',
      headers: {},
      config: {} as any,
    };
    expect(isServerError(error)).toBe(true);
  });

  it('should return true for 503 status', () => {
    const error = new AxiosError('Service unavailable');
    error.response = {
      status: 503,
      data: {},
      statusText: 'Service Unavailable',
      headers: {},
      config: {} as any,
    };
    expect(isServerError(error)).toBe(true);
  });

  it('should return false for client errors', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      status: 400,
      data: {},
      statusText: 'Bad Request',
      headers: {},
      config: {} as any,
    };
    expect(isServerError(error)).toBe(false);
  });
});

describe('formatError', () => {
  it('should format network error', () => {
    const error = new AxiosError('Network Error');
    error.code = 'ERR_NETWORK';
    const formatted = formatError(error);
    expect(formatted.title).toBe('Connection Error');
    expect(formatted.isRetryable).toBe(true);
  });

  it('should format server error', () => {
    const error = new AxiosError('Server error');
    error.response = {
      status: 500,
      data: {},
      statusText: 'Internal Server Error',
      headers: {},
      config: {} as any,
    };
    const formatted = formatError(error);
    expect(formatted.title).toBe('Server Error');
    expect(formatted.isRetryable).toBe(true);
  });

  it('should format validation error', () => {
    const error = new AxiosError('Validation failed');
    error.response = {
      status: 422,
      data: {
        errors: { name: ['Required'] },
      },
      statusText: 'Unprocessable Entity',
      headers: {},
      config: {} as any,
    };
    const formatted = formatError(error);
    expect(formatted.title).toBe('Validation Error');
    expect(formatted.validationErrors).toEqual({ name: ['Required'] });
    expect(formatted.isRetryable).toBe(false);
  });
});

/**
 * Tests for AI Workflow Error Handling Utilities
 * Task 27: Test error recovery mechanisms
 */

import { describe, it, expect, vi } from 'vitest';
import {
  handleAIWorkflowError,
  getErrorInfo,
  isRecoverableError,
  isCriticalError,
  getRetryAfterSeconds,
  getErrorSuggestions,
  retryWithBackoff,
  shouldAutoRetry,
} from '../aiWorkflowErrors';

describe('aiWorkflowErrors', () => {
  describe('getErrorInfo', () => {
    it('should categorize rate limit errors correctly', () => {
      const error = {
        response: {
          status: 429,
          headers: { 'retry-after': '60' },
          data: {
            message: 'Rate limit exceeded',
            suggestions: ['Wait before retrying'],
          },
        },
      };

      const info = getErrorInfo(error);
      expect(info.category).toBe('rate_limit');
      expect(info.recoverable).toBe(true);
      expect(info.retryAfter).toBe(60);
      expect(info.suggestions).toContain('Wait before retrying');
    });

    it('should categorize session expiration errors correctly', () => {
      const error = {
        response: {
          status: 404,
          data: {
            message: 'Session not found',
          },
        },
      };

      const info = getErrorInfo(error);
      expect(info.category).toBe('session_expired');
      expect(info.recoverable).toBe(true);
    });

    it('should categorize validation errors correctly', () => {
      const error = {
        response: {
          status: 400,
          data: {
            message: 'Validation failed',
            error_code: 'validation_error',
            details: {
              errors: [
                { field: 'name', message: 'Required', type: 'required' },
              ],
            },
          },
        },
      };

      const info = getErrorInfo(error);
      expect(info.category).toBe('validation');
      expect(info.recoverable).toBe(true);
    });

    it('should categorize network errors correctly', () => {
      const error = new Error('Network Error');

      const info = getErrorInfo(error);
      expect(info.category).toBe('network');
      expect(info.recoverable).toBe(true);
    });

    it('should categorize service unavailable errors correctly', () => {
      const error = {
        response: {
          status: 503,
          headers: { 'retry-after': '30' },
          data: {
            message: 'Service temporarily unavailable',
          },
        },
      };

      const info = getErrorInfo(error);
      expect(info.category).toBe('service_unavailable');
      expect(info.recoverable).toBe(true);
      expect(info.retryAfter).toBe(30);
    });

    it('should categorize server errors correctly', () => {
      const error = {
        response: {
          status: 500,
          data: {
            message: 'Internal server error',
          },
        },
      };

      const info = getErrorInfo(error);
      expect(info.category).toBe('server_error');
      expect(info.recoverable).toBe(true);
    });
  });

  describe('handleAIWorkflowError', () => {
    it('should return user-friendly message for rate limit', () => {
      const error = {
        response: {
          status: 429,
          headers: { 'retry-after': '60' },
        },
      };

      const message = handleAIWorkflowError(error);
      expect(message).toContain('Rate limit exceeded');
      expect(message).toContain('60 seconds');
    });

    it('should return user-friendly message for network error', () => {
      const error = new Error('Network Error');

      const message = handleAIWorkflowError(error);
      expect(message).toContain('Unable to connect');
    });
  });

  describe('isRecoverableError', () => {
    it('should return true for rate limit errors', () => {
      const error = {
        response: {
          status: 429,
        },
      };

      expect(isRecoverableError(error)).toBe(true);
    });

    it('should return true for network errors', () => {
      const error = new Error('Network Error');

      expect(isRecoverableError(error)).toBe(true);
    });

    it('should return false for unknown errors', () => {
      const error = new Error('Something went wrong');

      expect(isRecoverableError(error)).toBe(false);
    });
  });

  describe('isCriticalError', () => {
    it('should return false for recoverable errors', () => {
      const error = {
        response: {
          status: 429,
        },
      };

      expect(isCriticalError(error)).toBe(false);
    });

    it('should return false for validation errors', () => {
      const error = {
        response: {
          status: 400,
          data: {
            error_code: 'validation_error',
          },
        },
      };

      expect(isCriticalError(error)).toBe(false);
    });

    it('should return true for unknown non-recoverable errors', () => {
      const error = new Error('Critical failure');

      expect(isCriticalError(error)).toBe(true);
    });
  });

  describe('getRetryAfterSeconds', () => {
    it('should extract retry-after from headers', () => {
      const error = {
        response: {
          headers: { 'retry-after': '60' },
        },
      };

      expect(getRetryAfterSeconds(error)).toBe(60);
    });

    it('should extract retry-after from data', () => {
      const error = {
        response: {
          data: {
            details: {
              retry_after_seconds: 30,
            },
          },
        },
      };

      expect(getRetryAfterSeconds(error)).toBe(30);
    });

    it('should return null if no retry-after', () => {
      const error = {
        response: {
          status: 500,
        },
      };

      expect(getRetryAfterSeconds(error)).toBeNull();
    });
  });

  describe('getErrorSuggestions', () => {
    it('should extract suggestions from error', () => {
      const error = {
        response: {
          status: 400,
          data: {
            message: 'Bad request',
            suggestions: ['Try again', 'Check your input'],
          },
        },
      };

      const suggestions = getErrorSuggestions(error);
      expect(suggestions).toContain('Try again');
      expect(suggestions).toContain('Check your input');
    });

    it('should return default suggestions for network errors', () => {
      const error = new Error('Network Error');

      const suggestions = getErrorSuggestions(error);
      expect(suggestions.length).toBeGreaterThan(0);
    });
  });

  describe('retryWithBackoff', () => {
    it('should succeed on first attempt', async () => {
      const fn = vi.fn().mockResolvedValue('success');

      const result = await retryWithBackoff(fn);

      expect(result).toBe('success');
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should retry on recoverable errors', async () => {
      const fn = vi
        .fn()
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValue('success');

      const result = await retryWithBackoff(fn, {
        maxAttempts: 3,
        initialDelay: 10,
        maxDelay: 100,
        backoffMultiplier: 2,
      });

      expect(result).toBe('success');
      expect(fn).toHaveBeenCalledTimes(2);
    });

    it('should not retry on non-recoverable errors', async () => {
      const error = new Error('Critical error');
      const fn = vi.fn().mockRejectedValue(error);

      await expect(
        retryWithBackoff(fn, {
          maxAttempts: 3,
          initialDelay: 10,
          maxDelay: 100,
          backoffMultiplier: 2,
        })
      ).rejects.toThrow('Critical error');

      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should throw after max attempts', async () => {
      const error = new Error('Network Error');
      const fn = vi.fn().mockRejectedValue(error);

      await expect(
        retryWithBackoff(fn, {
          maxAttempts: 3,
          initialDelay: 10,
          maxDelay: 100,
          backoffMultiplier: 2,
        })
      ).rejects.toThrow('Network Error');

      expect(fn).toHaveBeenCalledTimes(3);
    });
  });

  describe('shouldAutoRetry', () => {
    it('should return true for network errors', () => {
      const error = new Error('Network Error');

      expect(shouldAutoRetry(error)).toBe(true);
    });

    it('should return true for service unavailable', () => {
      const error = {
        response: {
          status: 503,
        },
      };

      expect(shouldAutoRetry(error)).toBe(true);
    });

    it('should return false for validation errors', () => {
      const error = {
        response: {
          status: 400,
          data: {
            error_code: 'validation_error',
          },
        },
      };

      expect(shouldAutoRetry(error)).toBe(false);
    });

    it('should return false for rate limit errors', () => {
      const error = {
        response: {
          status: 429,
        },
      };

      expect(shouldAutoRetry(error)).toBe(false);
    });
  });
});

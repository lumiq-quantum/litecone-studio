/**
 * Tests for dynamic API URL configuration
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getApiBaseUrl, getWebSocketUrl, getPollingInterval, getAppName } from '../apiConfig';

describe('apiConfig', () => {
  beforeEach(() => {
    // Clear any mocked environment variables
    vi.unstubAllEnvs();
  });

  describe('getApiBaseUrl', () => {
    it('should construct API URL from localhost', () => {
      // Mock window.location
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'http:',
          hostname: 'localhost',
        },
        writable: true,
      });

      const apiUrl = getApiBaseUrl();
      expect(apiUrl).toBe('http://localhost:8000/api/v1');
    });

    it('should construct API URL from production IP', () => {
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'http:',
          hostname: '3.111.65.158',
        },
        writable: true,
      });

      const apiUrl = getApiBaseUrl();
      expect(apiUrl).toBe('http://3.111.65.158:8000/api/v1');
    });

    it('should construct API URL from custom domain', () => {
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'https:',
          hostname: 'myapp.com',
        },
        writable: true,
      });

      const apiUrl = getApiBaseUrl();
      expect(apiUrl).toBe('https://myapp.com:8000/api/v1');
    });

    it('should use VITE_API_URL if explicitly set', () => {
      // Mock environment variable
      vi.stubEnv('VITE_API_URL', 'http://custom-api.com/api/v1');

      const apiUrl = getApiBaseUrl();
      expect(apiUrl).toBe('http://custom-api.com/api/v1');
    });

    it('should handle different protocols', () => {
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'https:',
          hostname: 'secure.example.com',
        },
        writable: true,
      });

      const apiUrl = getApiBaseUrl();
      expect(apiUrl).toBe('https://secure.example.com:8000/api/v1');
    });
  });

  describe('getWebSocketUrl', () => {
    it('should construct WebSocket URL with ws:// for http', () => {
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'http:',
          hostname: 'localhost',
        },
        writable: true,
      });

      const wsUrl = getWebSocketUrl();
      expect(wsUrl).toBe('ws://localhost:8000/ws');
    });

    it('should construct WebSocket URL with wss:// for https', () => {
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'https:',
          hostname: 'secure.example.com',
        },
        writable: true,
      });

      const wsUrl = getWebSocketUrl();
      expect(wsUrl).toBe('wss://secure.example.com:8000/ws');
    });
  });

  describe('getPollingInterval', () => {
    it('should return default polling interval', () => {
      const interval = getPollingInterval();
      expect(interval).toBe(2000);
    });

    it('should return custom polling interval from env', () => {
      vi.stubEnv('VITE_POLLING_INTERVAL', '5000');

      const interval = getPollingInterval();
      expect(interval).toBe(5000);
    });
  });

  describe('getAppName', () => {
    it('should return default app name', () => {
      const appName = getAppName();
      expect(appName).toBe('Workflow Manager');
    });

    it('should return custom app name from env', () => {
      vi.stubEnv('VITE_APP_NAME', 'Custom Workflow App');

      const appName = getAppName();
      expect(appName).toBe('Custom Workflow App');
    });
  });
});

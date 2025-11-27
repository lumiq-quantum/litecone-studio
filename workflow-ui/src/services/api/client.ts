/**
 * Axios client configuration with interceptors
 */
import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import type { ApiError } from '@/types';
import { apiConfig } from '@/lib/apiConfig';

/**
 * Create and configure the Axios client instance
 * Uses dynamic API URL detection based on current host
 */
const apiClient: AxiosInstance = axios.create(apiConfig);

/**
 * Request interceptor for adding authentication and logging
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Future: Add authentication token here when implemented
    // const token = getAuthToken();
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }

    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    }

    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling and logging
 */
apiClient.interceptors.response.use(
  (response) => {
    // Log response in development
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.status);
    }
    return response;
  },
  (error: AxiosError<ApiError>) => {
    // Log error
    console.error('[API Error]', error.response?.data || error.message);

    // Handle specific error cases
    if (error.response) {
      const { status, data } = error.response;

      // Handle common HTTP errors
      switch (status) {
        case 401:
          // Future: Handle unauthorized (redirect to login)
          console.error('Unauthorized access');
          break;
        case 403:
          console.error('Forbidden access');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 422:
          console.error('Validation error', data?.errors);
          break;
        case 500:
          console.error('Server error occurred');
          break;
        case 503:
          console.error('Service unavailable');
          break;
        default:
          console.error(`HTTP ${status} error`);
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error('No response from server');
    } else {
      // Something else happened
      console.error('Request setup error', error.message);
    }

    return Promise.reject(error);
  }
);

export default apiClient;

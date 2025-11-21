import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AgentCreate, AgentUpdate, AgentResponse, AuthType } from '@/types';

interface AgentFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: AgentCreate | AgentUpdate) => Promise<void>;
  agent?: AgentResponse;
  isLoading?: boolean;
}

interface FormData {
  name: string;
  url: string;
  description: string;
  auth_type: AuthType;
  bearer_token: string;
  api_key: string;
  api_key_header: string;
  timeout_ms: string;
  max_retries: string;
  initial_delay_ms: string;
  max_delay_ms: string;
  backoff_multiplier: string;
  circuit_breaker_enabled: boolean;
  circuit_breaker_failure_threshold: string;
  circuit_breaker_failure_rate_threshold: string;
  circuit_breaker_timeout_seconds: string;
  circuit_breaker_half_open_max_calls: string;
  circuit_breaker_window_size_seconds: string;
}

interface FormErrors {
  [key: string]: string;
}

export default function AgentForm({
  isOpen,
  onClose,
  onSubmit,
  agent,
  isLoading = false,
}: AgentFormProps) {
  const isEditMode = !!agent;

  const [formData, setFormData] = useState<FormData>({
    name: '',
    url: '',
    description: '',
    auth_type: 'none',
    bearer_token: '',
    api_key: '',
    api_key_header: 'X-API-Key',
    timeout_ms: '30000',
    max_retries: '3',
    initial_delay_ms: '1000',
    max_delay_ms: '10000',
    backoff_multiplier: '2',
    circuit_breaker_enabled: true,
    circuit_breaker_failure_threshold: '5',
    circuit_breaker_failure_rate_threshold: '0.5',
    circuit_breaker_timeout_seconds: '60',
    circuit_breaker_half_open_max_calls: '3',
    circuit_breaker_window_size_seconds: '120',
  });

  const [errors, setErrors] = useState<FormErrors>({});

  // Populate form when editing
  useEffect(() => {
    if (agent) {
      setFormData({
        name: agent.name,
        url: agent.url,
        description: agent.description || '',
        auth_type: agent.auth_type,
        bearer_token:
          agent.auth_type === 'bearer' && agent.auth_config
            ? (agent.auth_config as { token: string }).token
            : '',
        api_key:
          agent.auth_type === 'apikey' && agent.auth_config
            ? (agent.auth_config as { key: string }).key
            : '',
        api_key_header:
          agent.auth_type === 'apikey' && agent.auth_config
            ? (agent.auth_config as { header_name: string }).header_name
            : 'X-API-Key',
        timeout_ms: agent.timeout_ms.toString(),
        max_retries: agent.retry_config.max_retries.toString(),
        initial_delay_ms: agent.retry_config.initial_delay_ms.toString(),
        max_delay_ms: agent.retry_config.max_delay_ms.toString(),
        backoff_multiplier: agent.retry_config.backoff_multiplier.toString(),
        circuit_breaker_enabled: agent.circuit_breaker_config?.enabled ?? true,
        circuit_breaker_failure_threshold: agent.circuit_breaker_config?.failure_threshold?.toString() ?? '5',
        circuit_breaker_failure_rate_threshold: agent.circuit_breaker_config?.failure_rate_threshold?.toString() ?? '0.5',
        circuit_breaker_timeout_seconds: agent.circuit_breaker_config?.timeout_seconds?.toString() ?? '60',
        circuit_breaker_half_open_max_calls: agent.circuit_breaker_config?.half_open_max_calls?.toString() ?? '3',
        circuit_breaker_window_size_seconds: agent.circuit_breaker_config?.window_size_seconds?.toString() ?? '120',
      });
    }
  }, [agent]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.url.trim()) {
      newErrors.url = 'URL is required';
    } else {
      try {
        new URL(formData.url);
      } catch {
        newErrors.url = 'Invalid URL format';
      }
    }

    if (formData.auth_type === 'bearer' && !formData.bearer_token.trim()) {
      newErrors.bearer_token = 'Bearer token is required';
    }

    if (formData.auth_type === 'apikey') {
      if (!formData.api_key.trim()) {
        newErrors.api_key = 'API key is required';
      }
      if (!formData.api_key_header.trim()) {
        newErrors.api_key_header = 'Header name is required';
      }
    }

    const timeout = parseInt(formData.timeout_ms);
    if (isNaN(timeout) || timeout <= 0) {
      newErrors.timeout_ms = 'Timeout must be a positive number';
    }

    const maxRetries = parseInt(formData.max_retries);
    if (isNaN(maxRetries) || maxRetries < 0) {
      newErrors.max_retries = 'Max retries must be 0 or greater';
    }

    const initialDelay = parseInt(formData.initial_delay_ms);
    if (isNaN(initialDelay) || initialDelay <= 0) {
      newErrors.initial_delay_ms = 'Initial delay must be a positive number';
    }

    const maxDelay = parseInt(formData.max_delay_ms);
    if (isNaN(maxDelay) || maxDelay <= 0) {
      newErrors.max_delay_ms = 'Max delay must be a positive number';
    }

    const backoff = parseFloat(formData.backoff_multiplier);
    if (isNaN(backoff) || backoff <= 0) {
      newErrors.backoff_multiplier = 'Backoff multiplier must be a positive number';
    }

    // Circuit breaker validation (only if enabled)
    if (formData.circuit_breaker_enabled) {
      const failureThreshold = parseInt(formData.circuit_breaker_failure_threshold);
      if (isNaN(failureThreshold) || failureThreshold <= 0) {
        newErrors.circuit_breaker_failure_threshold = 'Failure threshold must be a positive number';
      }

      const failureRate = parseFloat(formData.circuit_breaker_failure_rate_threshold);
      if (isNaN(failureRate) || failureRate <= 0 || failureRate > 1) {
        newErrors.circuit_breaker_failure_rate_threshold = 'Failure rate must be between 0 and 1';
      }

      const timeoutSeconds = parseInt(formData.circuit_breaker_timeout_seconds);
      if (isNaN(timeoutSeconds) || timeoutSeconds <= 0) {
        newErrors.circuit_breaker_timeout_seconds = 'Timeout must be a positive number';
      }

      const halfOpenCalls = parseInt(formData.circuit_breaker_half_open_max_calls);
      if (isNaN(halfOpenCalls) || halfOpenCalls <= 0) {
        newErrors.circuit_breaker_half_open_max_calls = 'Half-open max calls must be a positive number';
      }

      const windowSize = parseInt(formData.circuit_breaker_window_size_seconds);
      if (isNaN(windowSize) || windowSize <= 0) {
        newErrors.circuit_breaker_window_size_seconds = 'Window size must be a positive number';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const baseData = {
      url: formData.url.trim(),
      description: formData.description.trim() || undefined,
      auth_type: formData.auth_type,
      auth_config:
        formData.auth_type === 'bearer'
          ? { token: formData.bearer_token }
          : formData.auth_type === 'apikey'
            ? { key: formData.api_key, header_name: formData.api_key_header }
            : null,
      timeout_ms: parseInt(formData.timeout_ms),
      retry_config: {
        max_retries: parseInt(formData.max_retries),
        initial_delay_ms: parseInt(formData.initial_delay_ms),
        max_delay_ms: parseInt(formData.max_delay_ms),
        backoff_multiplier: parseFloat(formData.backoff_multiplier),
      },
      circuit_breaker_config: {
        enabled: formData.circuit_breaker_enabled,
        failure_threshold: parseInt(formData.circuit_breaker_failure_threshold),
        failure_rate_threshold: parseFloat(formData.circuit_breaker_failure_rate_threshold),
        timeout_seconds: parseInt(formData.circuit_breaker_timeout_seconds),
        half_open_max_calls: parseInt(formData.circuit_breaker_half_open_max_calls),
        window_size_seconds: parseInt(formData.circuit_breaker_window_size_seconds),
      },
    };

    const submitData = isEditMode
      ? baseData
      : { ...baseData, name: formData.name.trim() };

    await onSubmit(submitData);
  };

  const handleChange = (field: keyof FormData, value: string | boolean) => {
    setFormData((prev) => ({ 
      ...prev, 
      [field]: field === 'circuit_breaker_enabled' ? value === 'true' || value === true : value 
    }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-50"
          />

          {/* Dialog */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="bg-white rounded-lg shadow-xl max-w-2xl w-full my-8"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">
                  {isEditMode ? 'Edit Agent' : 'Create New Agent'}
                </h2>
                <button
                  onClick={onClose}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
                  aria-label="Close"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="px-6 py-4 max-h-[calc(100vh-200px)] overflow-y-auto">
                <div className="space-y-6">
                  {/* Basic Information */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-4">Basic Information</h3>
                    <div className="space-y-4">
                      <div>
                        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                          Name {!isEditMode && <span className="text-red-500">*</span>}
                        </label>
                        <input
                          id="name"
                          type="text"
                          value={formData.name}
                          onChange={(e) => handleChange('name', e.target.value)}
                          disabled={isEditMode}
                          className={cn(
                            'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                            errors.name ? 'border-red-500' : 'border-gray-300',
                            isEditMode && 'bg-gray-50 cursor-not-allowed'
                          )}
                          placeholder="e.g., DataFetcher"
                        />
                        {errors.name && (
                          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-4 h-4" />
                            {errors.name}
                          </p>
                        )}
                        {isEditMode && (
                          <p className="mt-1 text-xs text-gray-500">Agent name cannot be changed</p>
                        )}
                      </div>

                      <div>
                        <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">
                          URL <span className="text-red-500">*</span>
                        </label>
                        <input
                          id="url"
                          type="text"
                          value={formData.url}
                          onChange={(e) => handleChange('url', e.target.value)}
                          className={cn(
                            'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                            errors.url ? 'border-red-500' : 'border-gray-300'
                          )}
                          placeholder="https://api.example.com/agent"
                        />
                        {errors.url && (
                          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-4 h-4" />
                            {errors.url}
                          </p>
                        )}
                      </div>

                      <div>
                        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                          Description
                        </label>
                        <textarea
                          id="description"
                          value={formData.description}
                          onChange={(e) => handleChange('description', e.target.value)}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          placeholder="Brief description of what this agent does"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Authentication */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-4">Authentication</h3>
                    <div className="space-y-4">
                      <div>
                        <label htmlFor="auth_type" className="block text-sm font-medium text-gray-700 mb-1">
                          Authentication Type
                        </label>
                        <select
                          id="auth_type"
                          value={formData.auth_type}
                          onChange={(e) => handleChange('auth_type', e.target.value as AuthType)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="none">None</option>
                          <option value="bearer">Bearer Token</option>
                          <option value="apikey">API Key</option>
                        </select>
                      </div>

                      {formData.auth_type === 'bearer' && (
                        <div>
                          <label htmlFor="bearer_token" className="block text-sm font-medium text-gray-700 mb-1">
                            Bearer Token <span className="text-red-500">*</span>
                          </label>
                          <input
                            id="bearer_token"
                            type="password"
                            value={formData.bearer_token}
                            onChange={(e) => handleChange('bearer_token', e.target.value)}
                            className={cn(
                              'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                              errors.bearer_token ? 'border-red-500' : 'border-gray-300'
                            )}
                            placeholder="Enter bearer token"
                          />
                          {errors.bearer_token && (
                            <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                              <AlertCircle className="w-4 h-4" />
                              {errors.bearer_token}
                            </p>
                          )}
                        </div>
                      )}

                      {formData.auth_type === 'apikey' && (
                        <>
                          <div>
                            <label htmlFor="api_key" className="block text-sm font-medium text-gray-700 mb-1">
                              API Key <span className="text-red-500">*</span>
                            </label>
                            <input
                              id="api_key"
                              type="password"
                              value={formData.api_key}
                              onChange={(e) => handleChange('api_key', e.target.value)}
                              className={cn(
                                'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                                errors.api_key ? 'border-red-500' : 'border-gray-300'
                              )}
                              placeholder="Enter API key"
                            />
                            {errors.api_key && (
                              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                <AlertCircle className="w-4 h-4" />
                                {errors.api_key}
                              </p>
                            )}
                          </div>
                          <div>
                            <label htmlFor="api_key_header" className="block text-sm font-medium text-gray-700 mb-1">
                              Header Name <span className="text-red-500">*</span>
                            </label>
                            <input
                              id="api_key_header"
                              type="text"
                              value={formData.api_key_header}
                              onChange={(e) => handleChange('api_key_header', e.target.value)}
                              className={cn(
                                'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                                errors.api_key_header ? 'border-red-500' : 'border-gray-300'
                              )}
                              placeholder="X-API-Key"
                            />
                            {errors.api_key_header && (
                              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                <AlertCircle className="w-4 h-4" />
                                {errors.api_key_header}
                              </p>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Configuration */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-4">Configuration</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="timeout_ms" className="block text-sm font-medium text-gray-700 mb-1">
                          Timeout (ms) <span className="text-red-500">*</span>
                        </label>
                        <input
                          id="timeout_ms"
                          type="number"
                          value={formData.timeout_ms}
                          onChange={(e) => handleChange('timeout_ms', e.target.value)}
                          className={cn(
                            'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                            errors.timeout_ms ? 'border-red-500' : 'border-gray-300'
                          )}
                          placeholder="30000"
                        />
                        {errors.timeout_ms && (
                          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-4 h-4" />
                            {errors.timeout_ms}
                          </p>
                        )}
                      </div>

                      <div>
                        <label htmlFor="max_retries" className="block text-sm font-medium text-gray-700 mb-1">
                          Max Retries <span className="text-red-500">*</span>
                        </label>
                        <input
                          id="max_retries"
                          type="number"
                          value={formData.max_retries}
                          onChange={(e) => handleChange('max_retries', e.target.value)}
                          className={cn(
                            'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                            errors.max_retries ? 'border-red-500' : 'border-gray-300'
                          )}
                          placeholder="3"
                        />
                        {errors.max_retries && (
                          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-4 h-4" />
                            {errors.max_retries}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Retry Configuration */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-4">Retry Configuration</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="initial_delay_ms" className="block text-sm font-medium text-gray-700 mb-1">
                          Initial Delay (ms) <span className="text-red-500">*</span>
                        </label>
                        <input
                          id="initial_delay_ms"
                          type="number"
                          value={formData.initial_delay_ms}
                          onChange={(e) => handleChange('initial_delay_ms', e.target.value)}
                          className={cn(
                            'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                            errors.initial_delay_ms ? 'border-red-500' : 'border-gray-300'
                          )}
                          placeholder="1000"
                        />
                        {errors.initial_delay_ms && (
                          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-4 h-4" />
                            {errors.initial_delay_ms}
                          </p>
                        )}
                      </div>

                      <div>
                        <label htmlFor="max_delay_ms" className="block text-sm font-medium text-gray-700 mb-1">
                          Max Delay (ms) <span className="text-red-500">*</span>
                        </label>
                        <input
                          id="max_delay_ms"
                          type="number"
                          value={formData.max_delay_ms}
                          onChange={(e) => handleChange('max_delay_ms', e.target.value)}
                          className={cn(
                            'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                            errors.max_delay_ms ? 'border-red-500' : 'border-gray-300'
                          )}
                          placeholder="10000"
                        />
                        {errors.max_delay_ms && (
                          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-4 h-4" />
                            {errors.max_delay_ms}
                          </p>
                        )}
                      </div>

                      <div className="col-span-2">
                        <label htmlFor="backoff_multiplier" className="block text-sm font-medium text-gray-700 mb-1">
                          Backoff Multiplier <span className="text-red-500">*</span>
                        </label>
                        <input
                          id="backoff_multiplier"
                          type="number"
                          step="0.1"
                          value={formData.backoff_multiplier}
                          onChange={(e) => handleChange('backoff_multiplier', e.target.value)}
                          className={cn(
                            'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                            errors.backoff_multiplier ? 'border-red-500' : 'border-gray-300'
                          )}
                          placeholder="2"
                        />
                        {errors.backoff_multiplier && (
                          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-4 h-4" />
                            {errors.backoff_multiplier}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Circuit Breaker Configuration */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-semibold text-gray-900">Circuit Breaker</h3>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.circuit_breaker_enabled}
                          onChange={(e) => handleChange('circuit_breaker_enabled', e.target.checked.toString())}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">Enabled</span>
                      </label>
                    </div>
                    
                    {formData.circuit_breaker_enabled && (
                      <div className="space-y-4 pl-4 border-l-2 border-blue-200">
                        <p className="text-xs text-gray-600">
                          Circuit breaker prevents cascading failures by automatically stopping calls to failing agents.
                        </p>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label htmlFor="circuit_breaker_failure_threshold" className="block text-sm font-medium text-gray-700 mb-1">
                              Failure Threshold
                            </label>
                            <input
                              id="circuit_breaker_failure_threshold"
                              type="number"
                              value={formData.circuit_breaker_failure_threshold}
                              onChange={(e) => handleChange('circuit_breaker_failure_threshold', e.target.value)}
                              className={cn(
                                'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                                errors.circuit_breaker_failure_threshold ? 'border-red-500' : 'border-gray-300'
                              )}
                              placeholder="5"
                            />
                            {errors.circuit_breaker_failure_threshold && (
                              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                <AlertCircle className="w-4 h-4" />
                                {errors.circuit_breaker_failure_threshold}
                              </p>
                            )}
                            <p className="mt-1 text-xs text-gray-500">Consecutive failures before opening</p>
                          </div>

                          <div>
                            <label htmlFor="circuit_breaker_failure_rate_threshold" className="block text-sm font-medium text-gray-700 mb-1">
                              Failure Rate Threshold
                            </label>
                            <input
                              id="circuit_breaker_failure_rate_threshold"
                              type="number"
                              step="0.1"
                              min="0"
                              max="1"
                              value={formData.circuit_breaker_failure_rate_threshold}
                              onChange={(e) => handleChange('circuit_breaker_failure_rate_threshold', e.target.value)}
                              className={cn(
                                'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                                errors.circuit_breaker_failure_rate_threshold ? 'border-red-500' : 'border-gray-300'
                              )}
                              placeholder="0.5"
                            />
                            {errors.circuit_breaker_failure_rate_threshold && (
                              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                <AlertCircle className="w-4 h-4" />
                                {errors.circuit_breaker_failure_rate_threshold}
                              </p>
                            )}
                            <p className="mt-1 text-xs text-gray-500">Rate (0.0-1.0) to trigger opening</p>
                          </div>

                          <div>
                            <label htmlFor="circuit_breaker_timeout_seconds" className="block text-sm font-medium text-gray-700 mb-1">
                              Timeout (seconds)
                            </label>
                            <input
                              id="circuit_breaker_timeout_seconds"
                              type="number"
                              value={formData.circuit_breaker_timeout_seconds}
                              onChange={(e) => handleChange('circuit_breaker_timeout_seconds', e.target.value)}
                              className={cn(
                                'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                                errors.circuit_breaker_timeout_seconds ? 'border-red-500' : 'border-gray-300'
                              )}
                              placeholder="60"
                            />
                            {errors.circuit_breaker_timeout_seconds && (
                              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                <AlertCircle className="w-4 h-4" />
                                {errors.circuit_breaker_timeout_seconds}
                              </p>
                            )}
                            <p className="mt-1 text-xs text-gray-500">Time circuit stays open</p>
                          </div>

                          <div>
                            <label htmlFor="circuit_breaker_half_open_max_calls" className="block text-sm font-medium text-gray-700 mb-1">
                              Half-Open Max Calls
                            </label>
                            <input
                              id="circuit_breaker_half_open_max_calls"
                              type="number"
                              value={formData.circuit_breaker_half_open_max_calls}
                              onChange={(e) => handleChange('circuit_breaker_half_open_max_calls', e.target.value)}
                              className={cn(
                                'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                                errors.circuit_breaker_half_open_max_calls ? 'border-red-500' : 'border-gray-300'
                              )}
                              placeholder="3"
                            />
                            {errors.circuit_breaker_half_open_max_calls && (
                              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                <AlertCircle className="w-4 h-4" />
                                {errors.circuit_breaker_half_open_max_calls}
                              </p>
                            )}
                            <p className="mt-1 text-xs text-gray-500">Test calls during recovery</p>
                          </div>

                          <div className="col-span-2">
                            <label htmlFor="circuit_breaker_window_size_seconds" className="block text-sm font-medium text-gray-700 mb-1">
                              Window Size (seconds)
                            </label>
                            <input
                              id="circuit_breaker_window_size_seconds"
                              type="number"
                              value={formData.circuit_breaker_window_size_seconds}
                              onChange={(e) => handleChange('circuit_breaker_window_size_seconds', e.target.value)}
                              className={cn(
                                'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                                errors.circuit_breaker_window_size_seconds ? 'border-red-500' : 'border-gray-300'
                              )}
                              placeholder="120"
                            />
                            {errors.circuit_breaker_window_size_seconds && (
                              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                <AlertCircle className="w-4 h-4" />
                                {errors.circuit_breaker_window_size_seconds}
                              </p>
                            )}
                            <p className="mt-1 text-xs text-gray-500">Sliding window for failure rate calculation</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </form>

              {/* Actions */}
              <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 border-t border-gray-200">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isLoading}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  onClick={handleSubmit}
                  disabled={isLoading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? 'Saving...' : isEditMode ? 'Update Agent' : 'Create Agent'}
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}

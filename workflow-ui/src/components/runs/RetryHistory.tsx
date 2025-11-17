/**
 * RetryHistory component - displays retry relationship timeline
 */
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { RotateCcw, Clock, AlertCircle, CheckCircle } from 'lucide-react';
import { format } from 'date-fns';
import RunStatusBadge from './RunStatusBadge';
import type { RunResponse } from '@/types';

interface RetryHistoryProps {
  currentRun: RunResponse;
  originalRun?: RunResponse;
  retryAttempts?: RunResponse[];
}

export function RetryHistory({ currentRun, originalRun, retryAttempts = [] }: RetryHistoryProps) {
  // Determine if this is a retry or has been retried
  const isRetry = !!currentRun.original_run_id;
  const hasRetries = !!currentRun.retried_by_run_id || retryAttempts.length > 0;

  if (!isRetry && !hasRetries) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg border border-gray-200 shadow-sm p-6"
    >
      <div className="flex items-center gap-2 mb-4">
        <RotateCcw className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">Retry History</h3>
      </div>

      {/* Timeline */}
      <div className="space-y-4">
        {/* Original Run */}
        {isRetry && originalRun && (
          <div className="flex items-start gap-4">
            <div className="flex flex-col items-center">
              <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                <AlertCircle className="w-5 h-5 text-red-600" />
              </div>
              {(hasRetries || retryAttempts.length > 0) && (
                <div className="w-0.5 h-full bg-gray-200 mt-2" />
              )}
            </div>

            <div className="flex-1 pb-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-gray-900">Original Run</span>
                <RunStatusBadge status={originalRun.status} size="sm" />
              </div>
              <Link
                to={`/runs/${originalRun.run_id}`}
                className="text-sm text-blue-600 hover:text-blue-700 font-mono hover:underline"
              >
                {originalRun.run_id}
              </Link>
              <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
                <Clock className="w-3 h-3" />
                {format(new Date(originalRun.created_at), 'PPp')}
              </div>
              {originalRun.error_message && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                  {originalRun.error_message}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Current Run (if it's a retry) */}
        {isRetry && (
          <div className="flex items-start gap-4">
            <div className="flex flex-col items-center">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                <RotateCcw className="w-5 h-5 text-blue-600" />
              </div>
              {hasRetries && <div className="w-0.5 h-full bg-gray-200 mt-2" />}
            </div>

            <div className="flex-1 pb-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-gray-900">Current Run (Retry)</span>
                <RunStatusBadge status={currentRun.status} size="sm" />
              </div>
              <span className="text-sm text-gray-600 font-mono">{currentRun.run_id}</span>
              <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
                <Clock className="w-3 h-3" />
                {format(new Date(currentRun.created_at), 'PPp')}
              </div>
            </div>
          </div>
        )}

        {/* Retry Attempts (if current run has been retried) */}
        {!isRetry && hasRetries && (
          <>
            {/* Current Run */}
            <div className="flex items-start gap-4">
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                </div>
                <div className="w-0.5 h-full bg-gray-200 mt-2" />
              </div>

              <div className="flex-1 pb-4">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-900">Original Run</span>
                  <RunStatusBadge status={currentRun.status} size="sm" />
                </div>
                <span className="text-sm text-gray-600 font-mono">{currentRun.run_id}</span>
                <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
                  <Clock className="w-3 h-3" />
                  {format(new Date(currentRun.created_at), 'PPp')}
                </div>
                {currentRun.error_message && (
                  <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                    {currentRun.error_message}
                  </div>
                )}
              </div>
            </div>

            {/* Retry Attempts */}
            {retryAttempts.map((retry, index) => (
              <div key={retry.run_id} className="flex items-start gap-4">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                      retry.status === 'COMPLETED'
                        ? 'bg-green-100'
                        : retry.status === 'FAILED'
                        ? 'bg-red-100'
                        : 'bg-blue-100'
                    }`}
                  >
                    {retry.status === 'COMPLETED' ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : retry.status === 'FAILED' ? (
                      <AlertCircle className="w-5 h-5 text-red-600" />
                    ) : (
                      <RotateCcw className="w-5 h-5 text-blue-600" />
                    )}
                  </div>
                  {index < retryAttempts.length - 1 && (
                    <div className="w-0.5 h-full bg-gray-200 mt-2" />
                  )}
                </div>

                <div className="flex-1 pb-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-900">
                      Retry Attempt {index + 1}
                    </span>
                    <RunStatusBadge status={retry.status} size="sm" />
                  </div>
                  <Link
                    to={`/runs/${retry.run_id}`}
                    className="text-sm text-blue-600 hover:text-blue-700 font-mono hover:underline"
                  >
                    {retry.run_id}
                  </Link>
                  <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    {format(new Date(retry.created_at), 'PPp')}
                  </div>
                  {retry.error_message && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                      {retry.error_message}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </>
        )}
      </div>

      {/* Retry Count Summary */}
      {currentRun.retry_count !== undefined && currentRun.retry_count > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <RotateCcw className="w-4 h-4" />
            <span>
              Total retry attempts: <span className="font-medium">{currentRun.retry_count}</span>
            </span>
          </div>
        </div>
      )}
    </motion.div>
  );
}

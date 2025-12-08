/**
 * ErrorFallback Component
 * 
 * Displays a fallback UI for critical errors that cannot be recovered automatically.
 * Provides clear information about the error and actionable steps for the user.
 * 
 * Task 27: Fallback UI for critical errors
 * Requirements: 6.1, 6.2, 6.5
 */

import { AlertTriangle, RefreshCw, Home, Mail } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Props for the ErrorFallback component
 */
export interface ErrorFallbackProps {
  /** Error message to display */
  message: string;
  /** Additional error details (optional) */
  details?: string;
  /** Suggestions for resolving the error */
  suggestions: string[];
  /** Callback to retry the failed action */
  onRetry?: () => void;
  /** Callback to reset the component state */
  onReset?: () => void;
  /** Whether the retry action is in progress */
  isRetrying?: boolean;
}

/**
 * ErrorFallback Component
 * 
 * A comprehensive error display component that provides:
 * - Clear error message
 * - Actionable suggestions
 * - Retry and reset options
 * - Contact support information
 */
export default function ErrorFallback({
  message,
  details,
  suggestions,
  onRetry,
  onReset,
  isRetrying = false,
}: ErrorFallbackProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-6 bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 border border-gray-200">
        {/* Error Icon */}
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-gradient-to-br from-red-100 to-red-200 rounded-full flex items-center justify-center shadow-lg">
            <AlertTriangle className="w-10 h-10 text-red-600" aria-hidden="true" />
          </div>
        </div>

        {/* Error Title */}
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-3">
          Something Went Wrong
        </h2>

        {/* Error Message */}
        <div
          className="mb-5 p-4 bg-gradient-to-br from-red-50 to-red-100/50 border border-red-200 rounded-xl shadow-sm"
          role="alert"
        >
          <p className="text-sm text-red-800 font-medium whitespace-pre-wrap">{message}</p>
        </div>

        {/* Error Details (if available) */}
        {details && (
          <details className="mb-5">
            <summary className="text-sm font-semibold text-gray-700 cursor-pointer hover:text-gray-900 transition-colors duration-200 px-3 py-2 rounded-lg hover:bg-gray-50">
              Technical Details
            </summary>
            <div className="mt-3 p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border border-gray-200 shadow-inner">
              <pre className="text-xs text-gray-600 whitespace-pre-wrap overflow-x-auto">
                {details}
              </pre>
            </div>
          </details>
        )}

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div className="mb-5">
            <h3 className="text-sm font-bold text-gray-800 mb-3">
              What you can try:
            </h3>
            <ul className="space-y-2">
              {suggestions.map((suggestion, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 text-sm text-gray-700 p-2 rounded-lg hover:bg-gray-50 transition-colors duration-150"
                >
                  <span className="flex-shrink-0 w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-[10px] font-bold mt-0.5">{index + 1}</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-3">
          {/* Retry Button */}
          {onRetry && (
            <button
              onClick={onRetry}
              disabled={isRetrying}
              className={cn(
                'w-full flex items-center justify-center gap-2 px-4 py-3',
                'rounded-xl font-semibold text-sm transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                'shadow-md',
                isRetrying
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed shadow-none'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg transform hover:scale-[1.02]'
              )}
              aria-label={isRetrying ? 'Retrying, please wait' : 'Retry failed action'}
              aria-disabled={isRetrying}
              aria-busy={isRetrying}
            >
              <RefreshCw
                className={cn('w-5 h-5', isRetrying && 'animate-spin')}
                aria-hidden="true"
              />
              <span>{isRetrying ? 'Retrying...' : 'Try Again'}</span>
            </button>
          )}

          {/* Reset Button */}
          {onReset && (
            <button
              onClick={onReset}
              disabled={isRetrying}
              className={cn(
                'w-full flex items-center justify-center gap-2 px-4 py-3',
                'rounded-xl font-semibold text-sm transition-all duration-200',
                'border-2 border-gray-300',
                'focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2',
                'shadow-sm',
                isRetrying
                  ? 'bg-gray-50 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-400 hover:shadow-md transform hover:scale-[1.02]'
              )}
              aria-label="Start over with a fresh session"
              aria-disabled={isRetrying}
            >
              <Home className="w-5 h-5" aria-hidden="true" />
              <span>Start Over</span>
            </button>
          )}
        </div>

        {/* Support Information */}
        <div className="mt-6 pt-5 border-t border-gray-200">
          <p className="text-xs text-gray-600 text-center mb-3 font-medium">
            If the problem persists, please contact support
          </p>
          <div className="flex items-center justify-center gap-2 text-xs">
            <div className="p-1.5 bg-blue-100 rounded-full">
              <Mail className="w-3 h-3 text-blue-600" aria-hidden="true" />
            </div>
            <a
              href="mailto:support@example.com"
              className="text-blue-600 hover:text-blue-700 font-semibold hover:underline transition-colors duration-200"
            >
              support@example.com
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

import { motion } from 'framer-motion';
import { AlertCircle, AlertTriangle, XCircle, RefreshCw, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatError } from '@/lib/errors';
import { fadeInVariants } from '@/lib/animations';

interface ErrorDisplayProps {
  error: unknown;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  variant?: 'inline' | 'banner' | 'card';
}

export default function ErrorDisplay({
  error,
  onRetry,
  onDismiss,
  className,
  variant = 'inline',
}: ErrorDisplayProps) {
  const formatted = formatError(error);

  const getIcon = () => {
    if (formatted.title === 'Validation Error') {
      return <AlertCircle className="w-5 h-5" />;
    }
    if (formatted.title === 'Connection Error' || formatted.title === 'Server Error') {
      return <XCircle className="w-5 h-5" />;
    }
    return <AlertTriangle className="w-5 h-5" />;
  };

  const getColorClasses = () => {
    if (formatted.title === 'Validation Error') {
      return {
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        text: 'text-yellow-800',
        icon: 'text-yellow-600',
      };
    }
    return {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      icon: 'text-red-600',
    };
  };

  const colors = getColorClasses();

  if (variant === 'banner') {
    return (
      <motion.div
        variants={fadeInVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        className={cn(
          'flex items-start gap-3 p-4 rounded-lg border',
          colors.bg,
          colors.border,
          className
        )}
      >
        <div className={colors.icon}>{getIcon()}</div>
        <div className="flex-1 min-w-0">
          <h4 className={cn('font-semibold mb-1', colors.text)}>{formatted.title}</h4>
          <p className={cn('text-sm', colors.text)}>{formatted.message}</p>
          {formatted.suggestion && (
            <p className={cn('text-sm mt-2', colors.text)}>{formatted.suggestion}</p>
          )}
          {formatted.validationErrors && (
            <ul className={cn('text-sm mt-2 space-y-1', colors.text)}>
              {Object.entries(formatted.validationErrors).map(([field, errors]) => (
                <li key={field}>
                  <strong>{field}:</strong> {errors.join(', ')}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="flex items-center gap-2">
          {formatted.isRetryable && onRetry && (
            <button
              onClick={onRetry}
              className={cn(
                'p-1.5 rounded hover:bg-white/50 transition-colors',
                colors.text
              )}
              title="Retry"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className={cn(
                'p-1.5 rounded hover:bg-white/50 transition-colors',
                colors.text
              )}
              title="Dismiss"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </motion.div>
    );
  }

  if (variant === 'card') {
    return (
      <motion.div
        variants={fadeInVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        className={cn(
          'bg-white rounded-lg border-2 p-6 text-center',
          colors.border,
          className
        )}
      >
        <div className={cn('w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4', colors.bg)}>
          <div className={colors.icon}>{getIcon()}</div>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{formatted.title}</h3>
        <p className="text-gray-600 mb-4">{formatted.message}</p>
        {formatted.suggestion && (
          <p className="text-sm text-gray-500 mb-4">{formatted.suggestion}</p>
        )}
        {formatted.validationErrors && (
          <div className="text-left mb-4">
            <ul className="text-sm text-gray-600 space-y-1">
              {Object.entries(formatted.validationErrors).map(([field, errors]) => (
                <li key={field}>
                  <strong>{field}:</strong> {errors.join(', ')}
                </li>
              ))}
            </ul>
          </div>
        )}
        <div className="flex gap-3 justify-center">
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Dismiss
            </button>
          )}
          {formatted.isRetryable && onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          )}
        </div>
      </motion.div>
    );
  }

  // Inline variant
  return (
    <motion.div
      variants={fadeInVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={cn('flex items-start gap-2 text-sm', colors.text, className)}
    >
      <div className="flex-shrink-0 mt-0.5">{getIcon()}</div>
      <div className="flex-1 min-w-0">
        <p className="font-medium">{formatted.message}</p>
        {formatted.suggestion && (
          <p className="mt-1 text-xs opacity-90">{formatted.suggestion}</p>
        )}
      </div>
    </motion.div>
  );
}

/**
 * Field-level validation error display
 */
interface FieldErrorProps {
  error?: string;
  className?: string;
}

export function FieldError({ error, className }: FieldErrorProps) {
  if (!error) return null;

  return (
    <motion.p
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -5 }}
      className={cn('text-xs text-red-600 mt-1', className)}
    >
      {error}
    </motion.p>
  );
}

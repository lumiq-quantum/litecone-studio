import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Clock,
  Calendar,
  User,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Ban,
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import JSONViewer from '@/components/common/JSONViewer';
import { cn } from '@/lib/utils';
import type { StepExecutionResponse } from '@/types';

interface StepDetailsProps {
  step: StepExecutionResponse | null;
  onClose: () => void;
  className?: string;
}

export default function StepDetails({ step, onClose, className }: StepDetailsProps) {
  if (!step) return null;

  // Calculate duration
  const getDuration = () => {
    if (!step.started_at) return 'N/A';

    const startTime = new Date(step.started_at);
    const endTime = step.completed_at ? new Date(step.completed_at) : new Date();

    const durationMs = endTime.getTime() - startTime.getTime();
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);

    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  // Status configuration
  const statusConfig = {
    PENDING: {
      icon: Clock,
      color: 'text-yellow-600',
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      label: 'Pending',
    },
    RUNNING: {
      icon: Loader2,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      label: 'Running',
    },
    COMPLETED: {
      icon: CheckCircle2,
      color: 'text-green-600',
      bg: 'bg-green-50',
      border: 'border-green-200',
      label: 'Completed',
    },
    FAILED: {
      icon: AlertCircle,
      color: 'text-red-600',
      bg: 'bg-red-50',
      border: 'border-red-200',
      label: 'Failed',
    },
    SKIPPED: {
      icon: Ban,
      color: 'text-gray-600',
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      label: 'Skipped',
    },
  };

  const config = statusConfig[step.status];
  const StatusIcon = config.icon;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className={cn(
          'fixed right-0 top-0 h-full w-full md:w-[600px] bg-white shadow-2xl overflow-y-auto z-50',
          className
        )}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-bold text-gray-900 truncate">
              {step.step_name || step.step_id}
            </h2>
            <p className="text-sm text-gray-600 truncate">Step ID: {step.step_id}</p>
          </div>
          <button
            onClick={onClose}
            className="ml-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Status Badge */}
          <div
            className={cn(
              'inline-flex items-center gap-2 px-4 py-2 rounded-lg border',
              config.bg,
              config.border
            )}
          >
            <StatusIcon
              className={cn('w-5 h-5', config.color, step.status === 'RUNNING' && 'animate-spin')}
            />
            <span className={cn('font-semibold', config.color)}>{config.label}</span>
          </div>

          {/* Metadata */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
              Metadata
            </h3>

            <div className="grid grid-cols-1 gap-3">
              {/* Agent Name */}
              <div className="flex items-start gap-3">
                <User className="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <div className="text-xs text-gray-500">Agent</div>
                  <div className="text-sm font-medium text-gray-900">{step.agent_name}</div>
                </div>
              </div>

              {/* Started At */}
              {step.started_at && (
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <div className="text-xs text-gray-500">Started</div>
                    <div className="text-sm font-medium text-gray-900">
                      {format(new Date(step.started_at), 'PPpp')}
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDistanceToNow(new Date(step.started_at), { addSuffix: true })}
                    </div>
                  </div>
                </div>
              )}

              {/* Completed At */}
              {step.completed_at && (
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <div className="text-xs text-gray-500">Completed</div>
                    <div className="text-sm font-medium text-gray-900">
                      {format(new Date(step.completed_at), 'PPpp')}
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDistanceToNow(new Date(step.completed_at), { addSuffix: true })}
                    </div>
                  </div>
                </div>
              )}

              {/* Duration */}
              <div className="flex items-start gap-3">
                <Clock className="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <div className="text-xs text-gray-500">Duration</div>
                  <div className="text-sm font-medium text-gray-900">{getDuration()}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {step.status === 'FAILED' && step.error_message && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
                Error
              </h3>
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm text-red-900 font-medium mb-1">Execution Failed</p>
                    <p className="text-sm text-red-800 whitespace-pre-wrap">
                      {step.error_message}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Input Data */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
              Input Data
            </h3>
            <JSONViewer
              data={step.input_data}
              title="Input"
              collapsible
              defaultCollapsed={false}
            />
          </div>

          {/* Output Data */}
          {step.output_data && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
                Output Data
              </h3>
              <JSONViewer
                data={step.output_data}
                title="Output"
                collapsible
                defaultCollapsed={false}
              />
            </div>
          )}

          {/* No Output Message */}
          {!step.output_data && step.status !== 'PENDING' && step.status !== 'RUNNING' && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
                Output Data
              </h3>
              <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
                <p className="text-sm text-gray-600">No output data available</p>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

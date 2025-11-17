import { memo, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Eye, RotateCcw, Calendar, Clock, Workflow, ArrowRight } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import RunStatusBadge from './RunStatusBadge';
import { cn } from '@/lib/utils';
import { cardHoverVariants, buttonVariants } from '@/lib/animations';
import type { RunResponse } from '@/types';

interface RunCardProps {
  run: RunResponse;
  onView: (run: RunResponse) => void;
  onRetry?: (run: RunResponse) => void;
  className?: string;
}

const RunCard = memo(function RunCard({ run, onView, onRetry, className }: RunCardProps) {
  // Memoize duration calculation
  const duration = useMemo(() => {
    if (!run.created_at) return null;
    
    const startTime = new Date(run.created_at);
    const endTime = run.completed_at
      ? new Date(run.completed_at)
      : run.cancelled_at
      ? new Date(run.cancelled_at)
      : new Date();
    
    const durationMs = endTime.getTime() - startTime.getTime();
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }, [run.created_at, run.completed_at, run.cancelled_at]);

  const canRetry = run.status === 'FAILED';

  // Memoize callbacks
  const handleView = useCallback(() => onView(run), [onView, run]);
  const handleRetry = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onRetry?.(run);
  }, [onRetry, run]);

  return (
    <motion.div
      variants={cardHoverVariants}
      initial="initial"
      whileHover="hover"
      whileTap="tap"
      className={cn(
        'bg-white rounded-lg border border-gray-200 p-4 cursor-pointer',
        className
      )}
      onClick={handleView}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Workflow className="w-4 h-4 text-gray-400 flex-shrink-0" />
            <h3 className="text-sm font-semibold text-gray-900 truncate">
              {run.workflow_name || 'Unknown Workflow'}
            </h3>
            {/* Retry Indicator */}
            {run.original_run_id && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-blue-700 bg-blue-100 rounded-full">
                <RotateCcw className="w-3 h-3" />
                Retry
              </span>
            )}
            {run.retried_by_run_id && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-purple-700 bg-purple-100 rounded-full">
                <ArrowRight className="w-3 h-3" />
                Retried
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 font-mono truncate">
            ID: {run.run_id}
          </p>
        </div>
        <RunStatusBadge status={run.status} size="sm" />
      </div>

      {/* Metadata */}
      <div className="space-y-2 mb-4">
        {/* Start Time */}
        <div className="flex items-center gap-2 text-xs text-gray-600">
          <Calendar className="w-3.5 h-3.5 text-gray-400" />
          <span>
            Started {formatDistanceToNow(new Date(run.created_at), { addSuffix: true })}
          </span>
        </div>

        {/* Duration */}
        <div className="flex items-center gap-2 text-xs text-gray-600">
          <Clock className="w-3.5 h-3.5 text-gray-400" />
          <span>Duration: {duration}</span>
        </div>
      </div>

      {/* Error Message (if failed) */}
      {run.status === 'FAILED' && run.error_message && (
        <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700 line-clamp-2">
          {run.error_message}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-3 border-t border-gray-100">
        <motion.button
          variants={buttonVariants}
          whileHover="hover"
          whileTap="tap"
          onClick={handleView}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-md transition-colors"
        >
          <Eye className="w-3.5 h-3.5" />
          View Details
        </motion.button>

        {canRetry && onRetry && (
          <motion.button
            variants={buttonVariants}
            whileHover="hover"
            whileTap="tap"
            onClick={handleRetry}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Retry
          </motion.button>
        )}
      </div>
    </motion.div>
  );
});

export default RunCard;

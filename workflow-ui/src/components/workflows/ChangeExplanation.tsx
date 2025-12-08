import { motion } from 'framer-motion';
import { FileEdit, Plus, Minus, Edit3, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Props for the ChangeExplanation component
 */
export interface ChangeExplanationProps {
  /** Summary of changes */
  summary: string;
  /** Detailed summary of changes */
  detailedSummary?: string;
  /** Number of added steps */
  addedSteps?: number;
  /** Number of removed steps */
  removedSteps?: number;
  /** Number of modified steps */
  modifiedSteps?: number;
  /** Whether to show detailed view by default */
  showDetails?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * ChangeExplanation Component
 * 
 * Displays a prominent, visually appealing explanation of workflow changes.
 * Shows a summary with icons and optional detailed breakdown.
 * 
 * Requirements: 10.3, 10.4
 */
export default function ChangeExplanation({
  summary,
  detailedSummary,
  addedSteps = 0,
  removedSteps = 0,
  modifiedSteps = 0,
  showDetails = false,
  className = '',
}: ChangeExplanationProps) {
  const hasChanges = addedSteps > 0 || removedSteps > 0 || modifiedSteps > 0;

  if (!hasChanges && summary === 'No significant changes detected') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          'p-3 rounded-lg bg-gray-50 border border-gray-200',
          className
        )}
      >
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-gray-700">{summary}</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={cn(
        'p-4 rounded-xl bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border border-blue-300 shadow-md hover:shadow-lg transition-all duration-200',
        className
      )}
    >
      {/* Header with icon */}
      <div className="flex items-start gap-3 mb-3">
        <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg shadow-sm">
          <FileEdit className="w-5 h-5 text-white flex-shrink-0" />
        </div>
        <div className="flex-1">
          <h4 className="text-sm font-bold text-blue-900 mb-1">
            Workflow Updated
          </h4>
          <p className="text-sm text-blue-800 font-medium">{summary}</p>
        </div>
      </div>

      {/* Change Statistics */}
      {hasChanges && (
        <div className="flex items-center gap-3 mb-3">
          {addedSteps > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-green-100 to-green-200 rounded-full shadow-sm hover:shadow-md transition-all duration-200 hover:scale-105">
              <div className="p-0.5 bg-green-600 rounded-full">
                <Plus className="w-3 h-3 text-white" />
              </div>
              <span className="text-xs font-bold text-green-800">
                {addedSteps} added
              </span>
            </div>
          )}
          {removedSteps > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-red-100 to-red-200 rounded-full shadow-sm hover:shadow-md transition-all duration-200 hover:scale-105">
              <div className="p-0.5 bg-red-600 rounded-full">
                <Minus className="w-3 h-3 text-white" />
              </div>
              <span className="text-xs font-bold text-red-800">
                {removedSteps} removed
              </span>
            </div>
          )}
          {modifiedSteps > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-blue-100 to-blue-200 rounded-full shadow-sm hover:shadow-md transition-all duration-200 hover:scale-105">
              <div className="p-0.5 bg-blue-600 rounded-full">
                <Edit3 className="w-3 h-3 text-white" />
              </div>
              <span className="text-xs font-bold text-blue-800">
                {modifiedSteps} modified
              </span>
            </div>
          )}
        </div>
      )}

      {/* Detailed Summary */}
      {showDetails && detailedSummary && detailedSummary !== 'No changes detected' && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="pt-3 border-t border-blue-300"
        >
          <p className="text-xs font-bold text-blue-900 mb-2">Details:</p>
          <div className="text-xs text-blue-800 whitespace-pre-line font-mono bg-white/70 p-3 rounded-lg shadow-inner">
            {detailedSummary}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowRight, FileJson } from 'lucide-react';
import { cn } from '@/lib/utils';
import JSONEditor from '@/components/common/JSONEditor';

/**
 * Props for the WorkflowComparison component
 */
export interface WorkflowComparisonProps {
  /** Whether the comparison modal is open */
  isOpen: boolean;
  /** Callback to close the modal */
  onClose: () => void;
  /** The original workflow JSON */
  beforeJson: string;
  /** The updated workflow JSON */
  afterJson: string;
  /** Title for the comparison */
  title?: string;
}

/**
 * WorkflowComparison Component
 * 
 * Displays a side-by-side comparison of workflow JSON before and after changes.
 * Shows both versions in read-only JSON editors for easy comparison.
 * 
 * Requirements: 10.5
 */
export default function WorkflowComparison({
  isOpen,
  onClose,
  beforeJson,
  afterJson,
  title = 'Workflow Comparison',
}: WorkflowComparisonProps) {
  const [view, setView] = useState<'side-by-side' | 'before' | 'after'>('side-by-side');

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
            aria-hidden="true"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-4 md:inset-8 lg:inset-16 z-50 flex flex-col bg-white rounded-xl shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="comparison-title"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50 rounded-t-xl">
              <div className="flex items-center gap-3">
                <FileJson className="w-5 h-5 text-blue-600" />
                <h2 id="comparison-title" className="text-lg font-semibold text-gray-900">
                  {title}
                </h2>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Close comparison"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* View Selector */}
            <div className="flex items-center gap-2 px-6 py-3 border-b border-gray-200 bg-gray-50">
              <button
                onClick={() => setView('side-by-side')}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors',
                  view === 'side-by-side'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                )}
              >
                Side by Side
              </button>
              <button
                onClick={() => setView('before')}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors',
                  view === 'before'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                )}
              >
                Before Only
              </button>
              <button
                onClick={() => setView('after')}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors',
                  view === 'after'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                )}
              >
                After Only
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden">
              {view === 'side-by-side' && (
                <div className="flex h-full">
                  {/* Before */}
                  <div className="flex-1 flex flex-col border-r border-gray-200">
                    <div className="px-4 py-2 bg-red-50 border-b border-red-200">
                      <h3 className="text-sm font-semibold text-red-900">Before</h3>
                    </div>
                    <div className="flex-1 overflow-hidden">
                      <JSONEditor
                        value={beforeJson}
                        onChange={() => {}} // Read-only
                        readOnly={true}
                        height="100%"
                        validateSchema={false}
                      />
                    </div>
                  </div>

                  {/* Arrow Divider */}
                  <div className="flex items-center justify-center w-12 bg-gray-100">
                    <ArrowRight className="w-6 h-6 text-gray-400" />
                  </div>

                  {/* After */}
                  <div className="flex-1 flex flex-col">
                    <div className="px-4 py-2 bg-green-50 border-b border-green-200">
                      <h3 className="text-sm font-semibold text-green-900">After</h3>
                    </div>
                    <div className="flex-1 overflow-hidden">
                      <JSONEditor
                        value={afterJson}
                        onChange={() => {}} // Read-only
                        readOnly={true}
                        height="100%"
                        validateSchema={false}
                      />
                    </div>
                  </div>
                </div>
              )}

              {view === 'before' && (
                <div className="h-full flex flex-col">
                  <div className="px-4 py-2 bg-red-50 border-b border-red-200">
                    <h3 className="text-sm font-semibold text-red-900">Before Changes</h3>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <JSONEditor
                      value={beforeJson}
                      onChange={() => {}} // Read-only
                      readOnly={true}
                      height="100%"
                      validateSchema={false}
                    />
                  </div>
                </div>
              )}

              {view === 'after' && (
                <div className="h-full flex flex-col">
                  <div className="px-4 py-2 bg-green-50 border-b border-green-200">
                    <h3 className="text-sm font-semibold text-green-900">After Changes</h3>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <JSONEditor
                      value={afterJson}
                      onChange={() => {}} // Read-only
                      readOnly={true}
                      height="100%"
                      validateSchema={false}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

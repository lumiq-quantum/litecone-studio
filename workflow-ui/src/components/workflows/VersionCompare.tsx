import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, GitCompare, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import { DiffEditor } from '@monaco-editor/react';
import type { WorkflowResponse } from '@/types';

interface VersionCompareProps {
  isOpen: boolean;
  onClose: () => void;
  originalVersion: WorkflowResponse;
  modifiedVersion: WorkflowResponse;
}

export default function VersionCompare({
  isOpen,
  onClose,
  originalVersion,
  modifiedVersion,
}: VersionCompareProps) {
  const [currentChangeIndex, setCurrentChangeIndex] = useState(0);
  const totalChanges = 0; // Monaco diff editor handles change navigation internally

  // Format workflow data for comparison
  const formatWorkflowData = (workflow: WorkflowResponse) => {
    return JSON.stringify(
      {
        name: workflow.name,
        description: workflow.description,
        start_step: workflow.workflow_data.start_step,
        steps: workflow.workflow_data.steps,
      },
      null,
      2
    );
  };

  const originalContent = formatWorkflowData(originalVersion);
  const modifiedContent = formatWorkflowData(modifiedVersion);

  // Calculate if there are any changes
  const hasChanges = originalContent !== modifiedContent;

  const handlePreviousChange = () => {
    if (currentChangeIndex > 0) {
      setCurrentChangeIndex(currentChangeIndex - 1);
    }
  };

  const handleNextChange = () => {
    if (currentChangeIndex < totalChanges - 1) {
      setCurrentChangeIndex(currentChangeIndex + 1);
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
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="bg-white rounded-xl shadow-xl w-full max-w-7xl max-h-[90vh] overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <GitCompare className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">
                      Compare Versions
                    </h3>
                    <p className="text-sm text-gray-600">
                      Version {originalVersion.version} vs Version {modifiedVersion.version}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {/* Change Navigation */}
                  {hasChanges && totalChanges > 0 && (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg">
                      <button
                        onClick={handlePreviousChange}
                        disabled={currentChangeIndex === 0}
                        className="p-1 text-gray-600 hover:text-gray-900 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        aria-label="Previous change"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      <span className="text-sm font-medium text-gray-700">
                        {currentChangeIndex + 1} / {totalChanges}
                      </span>
                      <button
                        onClick={handleNextChange}
                        disabled={currentChangeIndex >= totalChanges - 1}
                        className="p-1 text-gray-600 hover:text-gray-900 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        aria-label="Next change"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  )}

                  <button
                    onClick={onClose}
                    className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
                    aria-label="Close"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Version Info Bar */}
              <div className="grid grid-cols-2 gap-px bg-gray-200">
                <div className="bg-red-50 px-6 py-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-red-900">
                        Version {originalVersion.version} (Original)
                      </p>
                      <p className="text-xs text-red-700">
                        {new Date(originalVersion.created_at).toLocaleString()}
                      </p>
                    </div>
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                      Removed
                    </span>
                  </div>
                </div>
                <div className="bg-green-50 px-6 py-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-green-900">
                        Version {modifiedVersion.version} (Modified)
                      </p>
                      <p className="text-xs text-green-700">
                        {new Date(modifiedVersion.created_at).toLocaleString()}
                      </p>
                    </div>
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                      Added
                    </span>
                  </div>
                </div>
              </div>

              {/* Diff Editor */}
              <div className="flex-1 overflow-hidden">
                {hasChanges ? (
                  <DiffEditor
                    original={originalContent}
                    modified={modifiedContent}
                    language="json"
                    theme="vs"
                    options={{
                      readOnly: true,
                      renderSideBySide: true,
                      minimap: { enabled: true },
                      scrollBeyondLastLine: false,
                      fontSize: 13,
                      lineNumbers: 'on',
                      folding: true,
                      wordWrap: 'on',
                      automaticLayout: true,
                      renderOverviewRuler: true,
                      diffWordWrap: 'on',
                    }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full bg-gray-50">
                    <div className="text-center">
                      <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                      <p className="text-lg font-medium text-gray-900 mb-1">
                        No Changes Detected
                      </p>
                      <p className="text-sm text-gray-600">
                        These versions have identical workflow definitions
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-200">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 bg-red-200 rounded" />
                    <span>Deletions</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 bg-green-200 rounded" />
                    <span>Additions</span>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}

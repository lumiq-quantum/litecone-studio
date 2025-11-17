import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, X, AlertCircle } from 'lucide-react';
import { useWorkflowVersions, useExecuteWorkflow } from '@/hooks/useWorkflows';
import JSONEditor, { ValidationErrors } from '@/components/common/JSONEditor';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import VersionSelector from './VersionSelector';
import { showToast } from '@/lib/toast';
import type { WorkflowResponse } from '@/types';

interface ExecuteWorkflowDialogProps {
  isOpen: boolean;
  onClose: () => void;
  workflow: WorkflowResponse;
}

export default function ExecuteWorkflowDialog({
  isOpen,
  onClose,
  workflow,
}: ExecuteWorkflowDialogProps) {
  const navigate = useNavigate();
  const executeMutation = useExecuteWorkflow();
  const { data: versionsData, isLoading: versionsLoading } = useWorkflowVersions(
    workflow.id,
    { page: 1, page_size: 100 },
    isOpen
  );
  
  // Extract versions array from paginated response
  const versions = versionsData?.items || [];

  const [selectedVersion, setSelectedVersion] = useState(workflow.version);
  const [inputData, setInputData] = useState('{}');
  const [isValid, setIsValid] = useState(true);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Reset state when dialog opens
  useEffect(() => {
    if (isOpen) {
      setSelectedVersion(workflow.version);
      setInputData('{}');
      setIsValid(true);
      setValidationErrors([]);
    }
  }, [isOpen, workflow.version]);

  const handleValidate = (valid: boolean, errors: string[]) => {
    setIsValid(valid);
    setValidationErrors(errors);
  };

  const handleExecute = async () => {
    if (!isValid) {
      showToast.error('Please fix validation errors before executing');
      return;
    }

    try {
      // Parse the input data
      const parsedInput = JSON.parse(inputData);

      // Get the workflow ID for the selected version
      const selectedWorkflow = versions?.find((v) => v.version === selectedVersion);
      if (!selectedWorkflow) {
        showToast.error('Selected version not found');
        return;
      }

      // Execute the workflow
      const result = await executeMutation.mutateAsync({
        workflowId: selectedWorkflow.id,
        data: { input_data: parsedInput },
      });

      // Show success message
      showToast.success(`Workflow execution started (Run ID: ${result.run_id})`);

      // Close dialog
      onClose();

      // Navigate to run detail page
      navigate(`/runs/${result.run_id}`);
    } catch (error) {
      if (error instanceof SyntaxError) {
        showToast.error('Invalid JSON format');
      } else {
        showToast.error('Failed to execute workflow');
        console.error('Execution error:', error);
      }
    }
  };

  const handleClose = () => {
    if (!executeMutation.isPending) {
      onClose();
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
            onClick={handleClose}
            className="fixed inset-0 bg-black/50 z-50"
          />

          {/* Dialog */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="flex items-start justify-between p-6 border-b border-gray-200">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-1">
                    Execute Workflow
                  </h3>
                  <p className="text-sm text-gray-600">
                    {workflow.name}
                  </p>
                </div>
                <button
                  onClick={handleClose}
                  disabled={executeMutation.isPending}
                  className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Close"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Version Selector */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Select Version
                  </label>
                  {versionsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <LoadingSpinner size="md" />
                    </div>
                  ) : versions && versions.length > 0 ? (
                    <VersionSelector
                      versions={versions}
                      selectedVersion={selectedVersion}
                      onVersionSelect={setSelectedVersion}
                      currentVersion={workflow.version}
                    />
                  ) : (
                    <div className="flex items-center gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
                      <p className="text-sm text-yellow-800">
                        No versions available for this workflow
                      </p>
                    </div>
                  )}
                </div>

                {/* Input Data Editor */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Input Data (JSON)
                  </label>
                  <p className="text-sm text-gray-600 mb-3">
                    Provide the input data for the workflow execution in JSON format
                  </p>
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <JSONEditor
                      value={inputData}
                      onChange={setInputData}
                      onValidate={handleValidate}
                      height="300px"
                      validateSchema={false}
                    />
                  </div>
                  {validationErrors.length > 0 && (
                    <ValidationErrors errors={validationErrors} />
                  )}
                </div>

                {/* Info Box */}
                <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 text-sm text-blue-800">
                    <p className="font-medium mb-1">Execution Information</p>
                    <ul className="space-y-1 text-blue-700">
                      <li>• The workflow will be executed with version {selectedVersion}</li>
                      <li>• You will be redirected to the run details page after execution starts</li>
                      <li>• You can monitor the execution progress in real-time</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 border-t border-gray-200">
                <button
                  onClick={handleClose}
                  disabled={executeMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleExecute}
                  disabled={executeMutation.isPending || !isValid || versionsLoading}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {executeMutation.isPending ? (
                    <>
                      <LoadingSpinner size="sm" className="text-white" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Execute Workflow
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}

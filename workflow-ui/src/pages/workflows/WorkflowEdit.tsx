import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Save, FileJson, GitBranch, AlertCircle } from 'lucide-react';
import { useWorkflow, useUpdateWorkflow } from '@/hooks/useWorkflows';
import { useAgents } from '@/hooks/useAgents';
import { WorkflowVisualEditor } from '@/components/workflows';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { showToast } from '@/lib/toast';
import type { WorkflowUpdate } from '@/types';

export default function WorkflowEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const updateMutation = useUpdateWorkflow();
  const { data: workflow, isLoading, error } = useWorkflow(id!);
  const { data: agentsData } = useAgents();

  const [description, setDescription] = useState('');
  const [workflowJson, setWorkflowJson] = useState('');
  const [originalJson, setOriginalJson] = useState('');
  const [isValid, setIsValid] = useState(true);
  const [hasChanges, setHasChanges] = useState(false);
  const [apiErrors, setApiErrors] = useState<string[]>([]);

  const agentNames = agentsData?.items?.map((agent) => agent.name) || [];

  // Initialize form when workflow data loads
  useEffect(() => {
    if (workflow) {
      setDescription(workflow.description || '');
      const jsonStr = JSON.stringify(
        {
          start_step: workflow.workflow_data.start_step,
          steps: workflow.workflow_data.steps,
        },
        null,
        2
      );
      setWorkflowJson(jsonStr);
      setOriginalJson(jsonStr);
    }
  }, [workflow]);

  // Track changes
  useEffect(() => {
    if (workflow) {
      const descChanged = description !== (workflow.description || '');
      const jsonChanged = workflowJson !== originalJson;
      setHasChanges(descChanged || jsonChanged);
      
      // Clear API errors when user makes changes
      if (jsonChanged && apiErrors.length > 0) {
        setApiErrors([]);
      }
    }
  }, [description, workflowJson, originalJson, workflow, apiErrors.length]);

  const handleValidate = (valid: boolean) => {
    setIsValid(valid);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isValid) {
      showToast.error('Please fix validation errors before saving');
      return;
    }

    if (!hasChanges) {
      showToast.error('No changes to save');
      return;
    }

    try {
      const workflowData = JSON.parse(workflowJson);
      
      const payload: WorkflowUpdate = {
        description: description.trim() || undefined,
        start_step: workflowData.start_step,
        steps: workflowData.steps,
      };

      await updateMutation.mutateAsync({ workflowId: id!, data: payload });
      showToast.success('Workflow updated successfully (new version created)');
      setApiErrors([]); // Clear any previous errors
      navigate(`/workflows/${id}`);
    } catch (error: any) {
      if (error instanceof SyntaxError) {
        showToast.error('Invalid JSON format');
        setApiErrors(['Invalid JSON format']);
      } else if (error?.response?.data?.errors) {
        // Extract validation errors from API response
        const errorMessages = error.response.data.errors.map((err: any) => 
          err.message || err.detail || 'Unknown error'
        );
        setApiErrors(errorMessages);
        showToast.error(errorMessages[0] || 'Validation failed');
      } else if (error?.response?.data?.detail) {
        setApiErrors([error.response.data.detail]);
        showToast.error(error.response.data.detail);
      } else {
        setApiErrors(['Failed to update workflow']);
        showToast.error('Failed to update workflow');
      }
    }
  };

  const handleCancel = () => {
    if (hasChanges) {
      const confirmed = window.confirm('You have unsaved changes. Are you sure you want to leave?');
      if (!confirmed) return;
    }
    navigate(`/workflows/${id}`);
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (error || !workflow) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Workflow Not Found</h2>
          <p className="text-gray-600 mb-6">The workflow you're looking for doesn't exist.</p>
          <button
            onClick={() => navigate('/workflows')}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Back to Workflows
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <button
            onClick={handleCancel}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Workflow
          </button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Edit Workflow</h1>
              <p className="text-gray-600">{workflow.name}</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-100 text-blue-800 rounded-lg">
              <GitBranch className="w-4 h-4" />
              <span className="text-sm font-medium">Current: v{workflow.version}</span>
            </div>
          </div>
        </motion.div>

        {/* Version Info Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg"
        >
          <div className="flex items-start gap-3">
            <GitBranch className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-blue-900 mb-1">Version Management</h3>
              <p className="text-sm text-blue-700">
                Saving changes will create a new version (v{workflow.version + 1}). The previous version will remain accessible.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Form */}
        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          onSubmit={handleSubmit}
          className="space-y-6"
        >
          {/* Basic Information Card */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
            
            <div className="space-y-4">
              {/* Name (Read-only) */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  Workflow Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={workflow.name}
                  disabled
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
                />
                <p className="mt-1 text-xs text-gray-500">Workflow name cannot be changed</p>
              </div>

              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what this workflow does..."
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                />
              </div>
            </div>
          </div>

          {/* Workflow Definition Card */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Workflow Definition</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Modify the workflow steps and their connections
                </p>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <FileJson className="w-4 h-4 text-gray-400" />
                <span className={`font-medium ${isValid ? 'text-green-600' : 'text-red-600'}`}>
                  {isValid ? 'Valid JSON' : 'Invalid JSON'}
                </span>
              </div>
            </div>

            <WorkflowVisualEditor
              value={workflowJson}
              onChange={setWorkflowJson}
              onValidate={handleValidate}
              agentNames={agentNames}
              height="600px"
            />

            {/* API Validation Errors */}
            {apiErrors.length > 0 && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-red-900 mb-2">Validation Errors</h4>
                    <ul className="space-y-1">
                      {apiErrors.map((error, index) => (
                        <li key={index} className="text-sm text-red-800">
                          • {error}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Help Text */}
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-semibold text-blue-900">JSON Structure Guide</h4>
                <a
                  href="/help"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-medium text-blue-700 hover:text-blue-900 underline"
                >
                  View Full Documentation →
                </a>
              </div>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• <code className="bg-blue-100 px-1 rounded">start_step</code>: ID of the first step to execute</li>
                <li>• <code className="bg-blue-100 px-1 rounded">steps</code>: Object mapping step IDs to step definitions</li>
                <li>• Each step must have: <code className="bg-blue-100 px-1 rounded">id</code>, <code className="bg-blue-100 px-1 rounded">agent_name</code>, <code className="bg-blue-100 px-1 rounded">next_step</code>, <code className="bg-blue-100 px-1 rounded">input_mapping</code></li>
                <li>• Set <code className="bg-blue-100 px-1 rounded">next_step</code> to <code className="bg-blue-100 px-1 rounded">null</code> for the final step</li>
              </ul>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-4">
            <button
              type="button"
              onClick={handleCancel}
              disabled={updateMutation.isPending}
              className="px-6 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateMutation.isPending || !isValid || !hasChanges}
              className="flex items-center gap-2 px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {updateMutation.isPending ? (
                <>
                  <LoadingSpinner size="sm" className="text-white" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  Save Changes (Create v{workflow.version + 1})
                </>
              )}
            </button>
          </div>
        </motion.form>
      </div>
    </div>
  );
}

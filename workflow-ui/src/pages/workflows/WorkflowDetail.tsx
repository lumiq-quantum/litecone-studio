import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Play,
  Download,
  GitBranch,
  Calendar,
  User,
  AlertCircle,
  FileJson,
  Workflow as WorkflowIcon,
  History,
  Share2,
} from 'lucide-react';
import { useWorkflow, useDeleteWorkflow, useWorkflowVersions } from '@/hooks/useWorkflows';
import { WorkflowVisualEditor, ExecuteWorkflowDialog, VersionHistory } from '@/components/workflows';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { showToast } from '@/lib/toast';
import { cn } from '@/lib/utils';

export default function WorkflowDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: workflow, isLoading, error } = useWorkflow(id!);
  const { data: versionsData, isLoading: versionsLoading } = useWorkflowVersions(id!, { page: 1, page_size: 100 });
  
  // Extract versions array from paginated response
  const versions = versionsData?.items || [];
  const deleteMutation = useDeleteWorkflow();

  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showExecuteDialog, setShowExecuteDialog] = useState(false);
  const [activeTab, setActiveTab] = useState<'definition' | 'versions'>('definition');

  const handleEdit = () => {
    navigate(`/workflows/${id}/edit`);
  };

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(id!);
      showToast.success('Workflow deleted successfully');
      navigate('/workflows');
    } catch (error) {
      showToast.error('Failed to delete workflow');
    }
  };

  const handleExport = () => {
    if (!workflow) return;

    const exportData = {
      name: workflow.name,
      description: workflow.description,
      version: workflow.version,
      workflow_data: workflow.workflow_data,
      created_at: workflow.created_at,
      updated_at: workflow.updated_at,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflow.name.replace(/\s+/g, '-').toLowerCase()}-v${workflow.version}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast.success('Workflow exported successfully');
  };

  const handleShare = async () => {
    if (!workflow) return;

    // Generate shareable URL
    const shareUrl = `${window.location.origin}/workflows/${workflow.id}`;

    try {
      await navigator.clipboard.writeText(shareUrl);
      showToast.success('Link copied to clipboard');
    } catch (error) {
      // Fallback for browsers that don't support clipboard API
      console.error('Failed to copy link:', error);
      showToast.error('Failed to copy link');
    }
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

  const isActive = workflow.status === 'active';
  const stepCount = Object.keys(workflow.workflow_data.steps).length;
  const agentNames = Array.from(
    new Set(Object.values(workflow.workflow_data.steps).map((step) => step.agent_name))
  );

  const workflowJson = JSON.stringify(
    {
      start_step: workflow.workflow_data.start_step,
      steps: workflow.workflow_data.steps,
    },
    null,
    2
  );

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
            onClick={() => navigate('/workflows')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Workflows
          </button>

          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div
                className={cn(
                  'flex-shrink-0 w-16 h-16 rounded-xl flex items-center justify-center',
                  isActive ? 'bg-blue-100' : 'bg-gray-100'
                )}
              >
                <WorkflowIcon className={cn('w-8 h-8', isActive ? 'text-blue-600' : 'text-gray-400')} />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">{workflow.name}</h1>
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={cn(
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                    )}
                  >
                    {isActive ? 'Active' : 'Inactive'}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    <GitBranch className="w-3 h-3" />
                    Version {workflow.version}
                  </span>
                </div>
                {workflow.description && (
                  <p className="text-gray-600 max-w-2xl">{workflow.description}</p>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleShare}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
              <button
                onClick={handleEdit}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Edit className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={() => setShowExecuteDialog(true)}
                disabled={!isActive}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4" />
                Execute
              </button>
              <button
                onClick={() => setShowDeleteDialog(true)}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </motion.div>

        {/* Metadata Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
        >
          {/* Steps Count */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <FileJson className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Steps</p>
                <p className="text-2xl font-bold text-gray-900">{stepCount}</p>
              </div>
            </div>
          </div>

          {/* Agents Used */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <WorkflowIcon className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Agents Used</p>
                <p className="text-2xl font-bold text-gray-900">{agentNames.length}</p>
              </div>
            </div>
          </div>

          {/* Created Date */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Calendar className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Created</p>
                <p className="text-lg font-semibold text-gray-900">
                  {new Date(workflow.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex gap-6">
              <button
                onClick={() => setActiveTab('definition')}
                className={cn(
                  'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
                  activeTab === 'definition'
                    ? 'border-primary-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <div className="flex items-center gap-2">
                  <FileJson className="w-4 h-4" />
                  Workflow Definition
                </div>
              </button>
              <button
                onClick={() => setActiveTab('versions')}
                className={cn(
                  'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
                  activeTab === 'versions'
                    ? 'border-primary-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <div className="flex items-center gap-2">
                  <History className="w-4 h-4" />
                  Version History
                  {versions && versions.length > 0 && (
                    <span className="inline-flex items-center justify-center px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                      {versions.length}
                    </span>
                  )}
                </div>
              </button>
            </nav>
          </div>
        </motion.div>

        {/* Tab Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-8"
        >
          {activeTab === 'definition' && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Workflow Definition</h2>
              <WorkflowVisualEditor value={workflowJson} onChange={() => {}} readOnly height="600px" />
            </div>
          )}

          {activeTab === 'versions' && (
            <>
              {versionsLoading ? (
                <div className="bg-white rounded-xl border border-gray-200 p-12">
                  <LoadingSpinner />
                </div>
              ) : versions && versions.length > 0 ? (
                <VersionHistory
                  versions={versions}
                  currentVersion={workflow.version}
                  onViewVersion={(version) => {
                    // Switch to definition tab and show that version
                    setActiveTab('definition');
                    // Note: In a full implementation, you might want to update the displayed workflow
                    showToast.success(`Viewing version ${version.version}`);
                  }}
                />
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 p-12">
                  <div className="text-center">
                    <History className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-lg font-medium text-gray-900 mb-1">No Version History</p>
                    <p className="text-sm text-gray-600">
                      Version history will appear here as you make changes to the workflow
                    </p>
                  </div>
                </div>
              )}
            </>
          )}
        </motion.div>

        {/* Additional Metadata */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Metadata</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">Created:</span>
              <span className="font-medium text-gray-900">
                {new Date(workflow.created_at).toLocaleString()}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">Updated:</span>
              <span className="font-medium text-gray-900">
                {new Date(workflow.updated_at).toLocaleString()}
              </span>
            </div>
            {workflow.created_by && (
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">Created by:</span>
                <span className="font-medium text-gray-900">{workflow.created_by}</span>
              </div>
            )}
            {workflow.updated_by && (
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">Updated by:</span>
                <span className="font-medium text-gray-900">{workflow.updated_by}</span>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        title="Delete Workflow"
        description={`Are you sure you want to delete "${workflow.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />

      {/* Execute Workflow Dialog */}
      <ExecuteWorkflowDialog
        isOpen={showExecuteDialog}
        onClose={() => setShowExecuteDialog(false)}
        workflow={workflow}
      />
    </div>
  );
}

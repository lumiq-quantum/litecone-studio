import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  RotateCcw,
  Download,
  Ban,
  Calendar,
  Clock,
  Workflow,
  AlertCircle,
  Share2,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import {
  useRun,
  useRunSteps,
  useRetryRun,
  useCancelRun,
  useOriginalRun,
  useRetryAttempts,
} from '@/hooks/useRuns';
import { useWorkflow } from '@/hooks/useWorkflows';
import { useRunPolling, useShouldPoll } from '@/hooks/usePolling';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { RunStatusBadge, ExecutionGraph, StepDetails, RetryHistory } from '@/components/runs';
import { showToast } from '@/lib/toast';

export default function RunDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showRetryDialog, setShowRetryDialog] = useState(false);

  // Helper to check if a string is a valid UUID
  const isValidUUID = (str: string) => {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(str);
  };

  // Fetch run data
  const { data: run, isLoading: runLoading, error: runError } = useRun(id || '');
  const { data: stepsData, isLoading: stepsLoading } = useRunSteps(id || '');
  
  // Only fetch workflow if workflow_id is a valid UUID
  const shouldFetchWorkflow = !!run?.workflow_id && isValidUUID(run.workflow_id);
  const { data: workflow } = useWorkflow(run?.workflow_id || '', shouldFetchWorkflow);

  // Fetch retry relationship data
  const { data: originalRun } = useOriginalRun(run?.original_run_id);
  const { data: retryAttempts = [] } = useRetryAttempts(id || '');

  // Mutations
  const retryMutation = useRetryRun();
  const cancelMutation = useCancelRun();

  // Real-time polling for running workflows
  const shouldPoll = useShouldPoll(run?.status);
  useRunPolling({
    runId: id || '',
    enabled: shouldPoll,
    onComplete: () => {
      showToast.success('Workflow execution completed');
    },
    onError: () => {
      showToast.error('Failed to poll run status');
    },
  });

  // Get selected step details
  const selectedStep = selectedStepId && stepsData?.items
    ? stepsData.items.find((s) => s.step_id === selectedStepId)
    : null;

  // Calculate duration
  const getDuration = () => {
    if (!run?.created_at) return 'N/A';

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
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const handleRetry = async () => {
    if (!id) return;

    try {
      const result = await retryMutation.mutateAsync({ runId: id });
      showToast.success('Workflow retry initiated');
      setShowRetryDialog(false);
      // Navigate to the new run
      navigate(`/runs/${result.new_run_id}`);
    } catch (error) {
      showToast.error('Failed to retry workflow');
    }
  };

  const handleCancel = async () => {
    if (!id) return;

    try {
      await cancelMutation.mutateAsync({ runId: id, data: { reason: 'Cancelled by user' } });
      showToast.success('Workflow cancelled successfully');
      setShowCancelDialog(false);
    } catch (error) {
      showToast.error('Failed to cancel workflow');
    }
  };

  const handleExport = () => {
    if (!run || !stepsData) return;

    const exportData = {
      run,
      steps: stepsData.items,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `run-${run.run_id}-results.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast.success('Run results exported');
  };

  const handleShare = async () => {
    if (!run) return;

    // Generate shareable URL
    const shareUrl = `${window.location.origin}/runs/${run.run_id}`;

    try {
      await navigator.clipboard.writeText(shareUrl);
      showToast.success('Link copied to clipboard');
    } catch (error) {
      // Fallback for browsers that don't support clipboard API
      console.error('Failed to copy link:', error);
      showToast.error('Failed to copy link');
    }
  };

  // Close step details when clicking outside
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedStepId(null);
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, []);

  if (runLoading || stepsLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (runError || !run) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <EmptyState
          icon={AlertCircle}
          title="Run not found"
          description="The workflow run you're looking for doesn't exist or has been deleted."
          action={
            <button
              onClick={() => navigate('/runs')}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Back to Runs
            </button>
          }
        />
      </div>
    );
  }

  const canRetry = run.status === 'FAILED';
  const canCancel = run.status === 'RUNNING' || run.status === 'PENDING';

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          {/* Back Button */}
          <button
            onClick={() => navigate('/runs')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="text-sm font-medium">Back to Runs</span>
          </button>

          {/* Title and Actions */}
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2">
                <Workflow className="w-8 h-8 text-gray-400" />
                <h1 className="text-3xl font-bold text-gray-900 truncate">
                  {run.workflow_name || 'Unknown Workflow'}
                </h1>
              </div>
              <p className="text-sm text-gray-600 font-mono">Run ID: {run.run_id}</p>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              {canRetry && (
                <button
                  onClick={() => setShowRetryDialog(true)}
                  disabled={retryMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors disabled:opacity-50"
                >
                  <RotateCcw className="w-4 h-4" />
                  Retry
                </button>
              )}

              {canCancel && (
                <button
                  onClick={() => setShowCancelDialog(true)}
                  disabled={cancelMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg shadow-sm transition-colors disabled:opacity-50"
                >
                  <Ban className="w-4 h-4" />
                  Cancel
                </button>
              )}

              <button
                onClick={handleShare}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg shadow-sm transition-colors"
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>

              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg shadow-sm transition-colors"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>

          {/* Status and Metadata */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Status */}
              <div>
                <div className="text-xs text-gray-500 mb-2">Status</div>
                <RunStatusBadge status={run.status} size="md" />
              </div>

              {/* Started */}
              <div>
                <div className="text-xs text-gray-500 mb-2">Started</div>
                <div className="flex items-center gap-2 text-sm text-gray-900">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="font-medium">{format(new Date(run.created_at), 'PPp')}</div>
                    <div className="text-xs text-gray-500">
                      {formatDistanceToNow(new Date(run.created_at), { addSuffix: true })}
                    </div>
                  </div>
                </div>
              </div>

              {/* Duration */}
              <div>
                <div className="text-xs text-gray-500 mb-2">Duration</div>
                <div className="flex items-center gap-2 text-sm font-medium text-gray-900">
                  <Clock className="w-4 h-4 text-gray-400" />
                  {getDuration()}
                </div>
              </div>

              {/* Completed */}
              {run.completed_at && (
                <div>
                  <div className="text-xs text-gray-500 mb-2">Completed</div>
                  <div className="text-sm font-medium text-gray-900">
                    {format(new Date(run.completed_at), 'PPp')}
                  </div>
                </div>
              )}
            </div>

            {/* Error Message */}
            {run.status === 'FAILED' && run.error_message && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm text-red-900 font-medium mb-1">Execution Failed</p>
                    <p className="text-sm text-red-800">{run.error_message}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </motion.div>

        {/* Retry History */}
        {run && (run.original_run_id || run.retried_by_run_id || retryAttempts.length > 0) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <RetryHistory
              currentRun={run}
              originalRun={originalRun}
              retryAttempts={retryAttempts}
            />
          </motion.div>
        )}

        {/* Execution Graph */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden"
        >
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Execution Flow</h2>
                <p className="text-sm text-gray-600">
                  Click on a step to view detailed information
                </p>
              </div>
              {/* Retry Context Badge */}
              {run?.original_run_id && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg">
                  <RotateCcw className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-900">
                    Retry Execution
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="h-[600px]">
            {!shouldFetchWorkflow && stepsData ? (
              <div className="h-full flex items-center justify-center">
                <EmptyState
                  icon={AlertCircle}
                  title="Workflow definition unavailable"
                  description="This run was created with an older workflow format. Step execution details are available below."
                />
              </div>
            ) : workflow && stepsData ? (
              <ExecutionGraph
                workflow={workflow.workflow_data}
                steps={stepsData.items}
                onStepClick={setSelectedStepId}
                selectedStepId={selectedStepId || undefined}
              />
            ) : (
              <div className="h-full flex items-center justify-center">
                <LoadingSpinner />
              </div>
            )}
          </div>
        </motion.div>

        {/* Steps List - Show when workflow definition is unavailable */}
        {!shouldFetchWorkflow && stepsData && stepsData.items.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden mt-6"
          >
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Execution Steps</h2>
              <p className="text-sm text-gray-600">
                {stepsData.items.length} step{stepsData.items.length !== 1 ? 's' : ''} executed
              </p>
            </div>
            <div className="divide-y divide-gray-200">
              {stepsData.items.map((step, index) => (
                <div
                  key={step.id}
                  className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => setSelectedStepId(step.step_id)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 text-gray-700 text-sm font-medium">
                          {index + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {step.step_name || step.step_id}
                          </h3>
                          <p className="text-xs text-gray-500">
                            Agent: {step.agent_name || 'Unknown'}
                          </p>
                        </div>
                      </div>
                      {step.started_at && (
                        <div className="ml-11 text-xs text-gray-500">
                          Started {formatDistanceToNow(new Date(step.started_at), { addSuffix: true })}
                          {step.completed_at && (
                            <>
                              {' • '}
                              Duration: {Math.round((new Date(step.completed_at).getTime() - new Date(step.started_at).getTime()) / 1000)}s
                            </>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex-shrink-0">
                      <RunStatusBadge status={step.status as any} size="sm" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Step Details Panel */}
      {selectedStepId && selectedStep && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={() => setSelectedStepId(null)}
          />
          {/* Panel */}
          <StepDetails step={selectedStep} onClose={() => setSelectedStepId(null)} />
        </>
      )}

      {/* Retry Confirmation */}
      <ConfirmDialog
        isOpen={showRetryDialog}
        onClose={() => setShowRetryDialog(false)}
        onConfirm={handleRetry}
        title="Retry Workflow"
        description={
          <div className="space-y-3">
            <p>Are you sure you want to retry this workflow?</p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
              <p className="font-medium text-blue-900 mb-2">What will happen:</p>
              <ul className="list-disc list-inside space-y-1 text-blue-800">
                <li>A new run will be created</li>
                <li>Execution will resume from the failed step</li>
                <li>Previous successful steps will be skipped</li>
                <li>You'll be redirected to the new run</li>
              </ul>
            </div>
            {stepsData?.items && (
              <div className="text-sm text-gray-600">
                <p>
                  Failed step:{' '}
                  <span className="font-mono font-medium">
                    {stepsData.items.find((s) => s.status === 'FAILED')?.step_id || 'Unknown'}
                  </span>
                </p>
              </div>
            )}
          </div>
        }
        confirmLabel="Retry Workflow"
        variant="info"
        isLoading={retryMutation.isPending}
      />

      {/* Cancel Confirmation */}
      <ConfirmDialog
        isOpen={showCancelDialog}
        onClose={() => setShowCancelDialog(false)}
        onConfirm={handleCancel}
        title="Cancel Workflow"
        description="Are you sure you want to cancel this workflow run? This action cannot be undone."
        confirmLabel="Cancel Run"
        variant="danger"
        isLoading={cancelMutation.isPending}
      />
    </div>
  );
}

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Edit,
  Trash2,
  RefreshCw,
  Clock,
  RotateCw,
  Shield,
  ExternalLink,
  Calendar,
  Activity,
} from 'lucide-react';
import { useAgent, useAgentHealth, useUpdateAgent, useDeleteAgent } from '@/hooks/useAgents';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import AgentForm from '@/components/agents/AgentForm';
import AgentHealthBadge from '@/components/agents/AgentHealthBadge';
import { showToast } from '@/lib/toast';
import { cn } from '@/lib/utils';
import type { AgentUpdate } from '@/types';

export default function AgentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const { data: agent, isLoading, error } = useAgent(id || '', !!id);
  const {
    data: healthData,
    isLoading: isHealthLoading,
    refetch: refetchHealth,
  } = useAgentHealth(id || '', !!id);

  const updateMutation = useUpdateAgent();
  const deleteMutation = useDeleteAgent();

  const handleEdit = async (data: AgentUpdate) => {
    try {
      await updateMutation.mutateAsync({ agentId: id!, data });
      showToast.success('Agent updated successfully');
      setIsEditModalOpen(false);
    } catch (error) {
      showToast.error('Failed to update agent');
      throw error;
    }
  };

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(id!);
      showToast.success('Agent deleted successfully');
      navigate('/agents');
    } catch (error) {
      showToast.error('Failed to delete agent');
    }
  };

  const handleRefreshHealth = async () => {
    try {
      await refetchHealth();
      showToast.success('Health check completed');
    } catch (error) {
      showToast.error('Health check failed');
    }
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (error || !agent) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <EmptyState
          icon={Activity}
          title="Agent not found"
          description="The agent you're looking for doesn't exist or has been deleted."
          action={
            <button
              onClick={() => navigate('/agents')}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Back to Agents
            </button>
          }
        />
      </div>
    );
  }

  const isActive = agent.status === 'active';

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <button
            onClick={() => navigate('/agents')}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Agents
          </button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{agent.name}</h1>
              <div className="flex items-center gap-3">
                <span
                  className={cn(
                    'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
                    isActive
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-600'
                  )}
                >
                  {isActive ? 'Active' : 'Inactive'}
                </span>
                <AgentHealthBadge
                  health={healthData}
                  isLoading={isHealthLoading}
                  showResponseTime
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleRefreshHealth}
                disabled={isHealthLoading}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={cn('w-4 h-4', isHealthLoading && 'animate-spin')} />
                Refresh Health
              </button>
              <button
                onClick={() => setIsEditModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <Edit className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={() => setIsDeleteDialogOpen(true)}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </motion.div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2 space-y-6"
          >
            {/* Basic Information */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">URL</label>
                  <a
                    href={agent.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-blue-600 hover:text-blue-700 hover:underline group"
                  >
                    <span className="break-all">{agent.url}</span>
                    <ExternalLink className="w-4 h-4 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </a>
                </div>

                {agent.description && (
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">
                      Description
                    </label>
                    <p className="text-gray-900">{agent.description}</p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">
                      Created At
                    </label>
                    <div className="flex items-center gap-2 text-gray-900">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      {new Date(agent.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">
                      Updated At
                    </label>
                    <div className="flex items-center gap-2 text-gray-900">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      {new Date(agent.updated_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Configuration */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h2>
              <div className="grid grid-cols-2 gap-6">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Clock className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">
                      Timeout
                    </label>
                    <p className="text-lg font-semibold text-gray-900">
                      {agent.timeout_ms / 1000}s
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <RotateCw className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">
                      Max Retries
                    </label>
                    <p className="text-lg font-semibold text-gray-900">
                      {agent.retry_config.max_retries}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Retry Configuration */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Retry Configuration</h2>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">
                    Initial Delay
                  </label>
                  <p className="text-gray-900">{agent.retry_config.initial_delay_ms}ms</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">
                    Max Delay
                  </label>
                  <p className="text-gray-900">{agent.retry_config.max_delay_ms}ms</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">
                    Backoff Multiplier
                  </label>
                  <p className="text-gray-900">{agent.retry_config.backoff_multiplier}x</p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Sidebar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            {/* Authentication */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <Shield className="w-5 h-5 text-green-600" />
                </div>
                <h2 className="text-lg font-semibold text-gray-900">Authentication</h2>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">Type</label>
                <p className="text-gray-900 capitalize">
                  {agent.auth_type === 'none' ? 'None' : agent.auth_type}
                </p>
              </div>
              {agent.auth_type !== 'none' && (
                <div className="mt-3">
                  <label className="block text-sm font-medium text-gray-500 mb-1">
                    Configuration
                  </label>
                  <p className="text-sm text-gray-600">
                    {agent.auth_type === 'bearer'
                      ? 'Bearer token configured'
                      : agent.auth_type === 'apikey'
                        ? `API key in header: ${(agent.auth_config as any)?.header_name || 'N/A'}`
                        : 'Configured'}
                  </p>
                </div>
              )}
            </div>

            {/* Health Status */}
            {healthData && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className={cn(
                      'w-10 h-10 rounded-lg flex items-center justify-center',
                      healthData.status === 'healthy' ? 'bg-green-100' : 'bg-red-100'
                    )}
                  >
                    <Activity
                      className={cn(
                        'w-5 h-5',
                        healthData.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                      )}
                    />
                  </div>
                  <h2 className="text-lg font-semibold text-gray-900">Health Status</h2>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">Status</label>
                    <p
                      className={cn(
                        'text-lg font-semibold capitalize',
                        healthData.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                      )}
                    >
                      {healthData.status}
                    </p>
                  </div>
                  {healthData.response_time_ms !== undefined && (
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Response Time
                      </label>
                      <p className="text-gray-900">{healthData.response_time_ms}ms</p>
                    </div>
                  )}
                  {healthData.message && (
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Message
                      </label>
                      <p className="text-sm text-gray-600">{healthData.message}</p>
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">
                      Last Checked
                    </label>
                    <p className="text-sm text-gray-600">
                      {new Date(healthData.timestamp).toLocaleString()}
                    </p>
                  </div>
                  
                  {/* Agent Card Information */}
                  {healthData.agent_card && (
                    <div className="pt-4 border-t border-gray-200">
                      <label className="block text-sm font-medium text-gray-900 mb-3">
                        Agent Capabilities
                      </label>
                      <div className="space-y-2">
                        {healthData.agent_card.version && (
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">Version:</span>
                            <span className="font-medium text-gray-900">{healthData.agent_card.version}</span>
                          </div>
                        )}
                        {healthData.agent_card.capabilities && healthData.agent_card.capabilities.length > 0 && (
                          <div>
                            <span className="text-sm text-gray-600 block mb-2">Capabilities:</span>
                            <div className="flex flex-wrap gap-2">
                              {healthData.agent_card.capabilities.map((capability, index) => (
                                <span
                                  key={index}
                                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                                >
                                  {capability}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>

      {/* Edit Modal */}
      <AgentForm
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSubmit={handleEdit}
        agent={agent}
        isLoading={updateMutation.isPending}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleDelete}
        title="Delete Agent"
        description={`Are you sure you want to delete "${agent.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}

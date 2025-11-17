import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Search, Filter, Bot } from 'lucide-react';
import { useAgents, useCreateAgent, useDeleteAgent } from '@/hooks/useAgents';
import { useQueryClient } from '@tanstack/react-query';
import { agentKeys } from '@/hooks/useAgents';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import AgentCard from '@/components/agents/AgentCard';
import AgentForm from '@/components/agents/AgentForm';
import { showToast } from '@/lib/toast';
import type { AgentCreate, AgentUpdate, AgentResponse } from '@/types';

export default function AgentsList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<AgentResponse | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  const { data: agentsData, isLoading, error } = useAgents();
  const createMutation = useCreateAgent();
  const deleteMutation = useDeleteAgent();

  // Filter and search agents
  const filteredAgents = useMemo(() => {
    if (!agentsData?.items) return [];

    let filtered = agentsData.items;

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((agent) => agent.status === statusFilter);
    }

    // Apply search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (agent) =>
          agent.name.toLowerCase().includes(query) ||
          agent.url.toLowerCase().includes(query) ||
          agent.description?.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [agentsData?.items, statusFilter, searchQuery]);

  // Pagination
  const totalPages = Math.ceil(filteredAgents.length / itemsPerPage);
  const paginatedAgents = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredAgents.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredAgents, currentPage]);

  const handleCreate = async (data: AgentCreate) => {
    try {
      const newAgent = await createMutation.mutateAsync(data);
      showToast.success('Agent created successfully');
      setIsCreateModalOpen(false);
      // Navigate to the new agent's detail page
      navigate(`/agents/${newAgent.id}`);
    } catch (error) {
      showToast.error('Failed to create agent');
      throw error;
    }
  };

  const handleEdit = (agent: AgentResponse) => {
    navigate(`/agents/${agent.id}`);
  };

  const handleDelete = async () => {
    if (!agentToDelete) return;

    try {
      await deleteMutation.mutateAsync(agentToDelete.id);
      showToast.success('Agent deleted successfully');
      setAgentToDelete(null);
    } catch (error) {
      showToast.error('Failed to delete agent');
    }
  };

  const handleTestHealth = async (agent: AgentResponse) => {
    try {
      // Refetch health for this specific agent
      await queryClient.invalidateQueries({ queryKey: agentKeys.health(agent.id) });
      showToast.success('Health check initiated');
    } catch (error) {
      showToast.error('Failed to check health');
    }
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <EmptyState
          icon={Bot}
          title="Failed to load agents"
          description="There was an error loading the agents. Please try again."
          action={
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Retry
            </button>
          }
        />
      </div>
    );
  }

  const hasAgents = agentsData?.items && agentsData.items.length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Agents</h1>
              <p className="text-gray-600">
                Manage external services that execute workflow tasks
              </p>
            </div>
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
            >
              <Plus className="w-5 h-5" />
              Add Agent
            </button>
          </div>

          {/* Filters and Search */}
          {hasAgents && (
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search agents by name, URL, or description..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setCurrentPage(1); // Reset to first page on search
                  }}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              {/* Status Filter */}
              <div className="flex items-center gap-2">
                <Filter className="w-5 h-5 text-gray-400" />
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value as 'all' | 'active' | 'inactive');
                    setCurrentPage(1); // Reset to first page on filter
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>
          )}
        </motion.div>

        {/* Results Count */}
        {hasAgents && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-4 text-sm text-gray-600"
          >
            Showing {paginatedAgents.length} of {filteredAgents.length} agent
            {filteredAgents.length !== 1 ? 's' : ''}
            {searchQuery && ` matching "${searchQuery}"`}
          </motion.div>
        )}

        {/* Agents Grid */}
        {!hasAgents ? (
          <EmptyState
            icon={Bot}
            title="No agents yet"
            description="Get started by creating your first agent to execute workflow tasks."
            action={
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create First Agent
              </button>
            }
          />
        ) : filteredAgents.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No agents found"
            description="Try adjusting your search or filter criteria."
            action={
              <button
                onClick={() => {
                  setSearchQuery('');
                  setStatusFilter('all');
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Clear Filters
              </button>
            }
          />
        ) : (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8"
            >
              <AnimatePresence mode="popLayout">
                {paginatedAgents.map((agent, index) => (
                  <motion.div
                    key={agent.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ delay: index * 0.05 }}
                    layout
                  >
                    <AgentCard
                      agent={agent}
                      onEdit={handleEdit}
                      onDelete={(agent) => setAgentToDelete(agent)}
                      onTestHealth={handleTestHealth}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>

            {/* Pagination */}
            {totalPages > 1 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center justify-center gap-2"
              >
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <div className="flex items-center gap-1">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                        currentPage === page
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </motion.div>
            )}
          </>
        )}
      </div>

      {/* Floating Action Button (Mobile) */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsCreateModalOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center lg:hidden transition-colors"
      >
        <Plus className="w-6 h-6" />
      </motion.button>

      {/* Create Modal */}
      <AgentForm
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreate as (data: AgentCreate | AgentUpdate) => Promise<void>}
        isLoading={createMutation.isPending}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!agentToDelete}
        onClose={() => setAgentToDelete(null)}
        onConfirm={handleDelete}
        title="Delete Agent"
        description={`Are you sure you want to delete "${agentToDelete?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}

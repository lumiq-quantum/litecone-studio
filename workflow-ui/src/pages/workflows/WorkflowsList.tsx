import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Search, Filter, Workflow } from 'lucide-react';
import { useWorkflows, useDeleteWorkflow } from '@/hooks/useWorkflows';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import WorkflowCard from '@/components/workflows/WorkflowCard';
import { ExecuteWorkflowDialog } from '@/components/workflows';
import { showToast } from '@/lib/toast';
import type { WorkflowResponse } from '@/types';

export default function WorkflowsList() {
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [workflowToDelete, setWorkflowToDelete] = useState<WorkflowResponse | null>(null);
  const [workflowToExecute, setWorkflowToExecute] = useState<WorkflowResponse | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  const { data: workflowsData, isLoading, error } = useWorkflows();
  const deleteMutation = useDeleteWorkflow();

  // Filter and search workflows
  const filteredWorkflows = useMemo(() => {
    if (!workflowsData?.items) return [];

    let filtered = workflowsData.items;

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((workflow) => workflow.status === statusFilter);
    }

    // Apply search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (workflow) =>
          workflow.name.toLowerCase().includes(query) ||
          workflow.description?.toLowerCase().includes(query) ||
          workflow.workflow_data.name?.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [workflowsData?.items, statusFilter, searchQuery]);

  // Pagination
  const totalPages = Math.ceil(filteredWorkflows.length / itemsPerPage);
  const paginatedWorkflows = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredWorkflows.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredWorkflows, currentPage]);

  const handleView = (workflow: WorkflowResponse) => {
    navigate(`/workflows/${workflow.id}`);
  };

  const handleEdit = (workflow: WorkflowResponse) => {
    navigate(`/workflows/${workflow.id}/edit`);
  };

  const handleExecute = (workflow: WorkflowResponse) => {
    setWorkflowToExecute(workflow);
  };

  const handleDelete = async () => {
    if (!workflowToDelete) return;

    try {
      await deleteMutation.mutateAsync(workflowToDelete.id);
      showToast.success('Workflow deleted successfully');
      setWorkflowToDelete(null);
    } catch (error) {
      showToast.error('Failed to delete workflow');
    }
  };

  const handleCreate = () => {
    navigate('/workflows/create');
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <EmptyState
          icon={Workflow}
          title="Failed to load workflows"
          description="There was an error loading the workflows. Please try again."
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

  const hasWorkflows = workflowsData?.items && workflowsData.items.length > 0;

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
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Workflows</h1>
              <p className="text-gray-600">
                Create and manage workflow definitions with multiple steps
              </p>
            </div>
            <button
              onClick={handleCreate}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
            >
              <Plus className="w-5 h-5" />
              Create Workflow
            </button>
          </div>

          {/* Filters and Search */}
          {hasWorkflows && (
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search workflows by name or description..."
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
        {hasWorkflows && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-4 text-sm text-gray-600"
          >
            Showing {paginatedWorkflows.length} of {filteredWorkflows.length} workflow
            {filteredWorkflows.length !== 1 ? 's' : ''}
            {searchQuery && ` matching "${searchQuery}"`}
          </motion.div>
        )}

        {/* Workflows Grid */}
        {!hasWorkflows ? (
          <EmptyState
            icon={Workflow}
            title="No workflows yet"
            description="Get started by creating your first workflow to orchestrate multiple agents."
            action={
              <button
                onClick={handleCreate}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create First Workflow
              </button>
            }
          />
        ) : filteredWorkflows.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No workflows found"
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
                {paginatedWorkflows.map((workflow, index) => (
                  <motion.div
                    key={workflow.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ delay: index * 0.05 }}
                    layout
                  >
                    <WorkflowCard
                      workflow={workflow}
                      onView={handleView}
                      onEdit={handleEdit}
                      onExecute={handleExecute}
                      onDelete={(workflow) => setWorkflowToDelete(workflow)}
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
        onClick={handleCreate}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center lg:hidden transition-colors"
      >
        <Plus className="w-6 h-6" />
      </motion.button>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!workflowToDelete}
        onClose={() => setWorkflowToDelete(null)}
        onConfirm={handleDelete}
        title="Delete Workflow"
        description={`Are you sure you want to delete "${workflowToDelete?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />

      {/* Execute Workflow Dialog */}
      {workflowToExecute && (
        <ExecuteWorkflowDialog
          isOpen={!!workflowToExecute}
          onClose={() => setWorkflowToExecute(null)}
          workflow={workflowToExecute}
        />
      )}
    </div>
  );
}

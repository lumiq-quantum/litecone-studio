import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, PlayCircle, Calendar, X } from 'lucide-react';
import { useRuns, useRetryRun } from '@/hooks/useRuns';
import { useWorkflows } from '@/hooks/useWorkflows';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { RunCard } from '@/components/runs';
import { showToast } from '@/lib/toast';
import type { RunResponse, RunStatus } from '@/types';

export default function RunsList() {
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<RunStatus | 'all'>('all');
  const [workflowFilter, setWorkflowFilter] = useState<string>('all');
  const [dateRangeFilter, setDateRangeFilter] = useState<'all' | 'today' | 'week' | 'month'>(
    'all'
  );
  const [sortBy, setSortBy] = useState<'created_at' | 'updated_at' | 'status'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [runToRetry, setRunToRetry] = useState<RunResponse | null>(null);
  const itemsPerPage = 12;

  // Fetch runs with filters
  const { data: runsData, isLoading, error } = useRuns({
    status: statusFilter !== 'all' ? statusFilter : undefined,
    workflow_id: workflowFilter !== 'all' ? workflowFilter : undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  // Fetch workflows for filter dropdown
  const { data: workflowsData } = useWorkflows();

  const retryMutation = useRetryRun();

  // Filter and search runs
  const filteredRuns = useMemo(() => {
    if (!runsData?.items) return [];

    let filtered = runsData.items;

    // Apply search by run ID
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (run) =>
          run.run_id.toLowerCase().includes(query) ||
          run.workflow_name?.toLowerCase().includes(query)
      );
    }

    // Apply date range filter
    if (dateRangeFilter !== 'all') {
      const now = new Date();
      const filterDate = new Date();

      switch (dateRangeFilter) {
        case 'today':
          filterDate.setHours(0, 0, 0, 0);
          break;
        case 'week':
          filterDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          filterDate.setMonth(now.getMonth() - 1);
          break;
      }

      filtered = filtered.filter((run) => new Date(run.created_at) >= filterDate);
    }

    return filtered;
  }, [runsData?.items, searchQuery, dateRangeFilter]);

  // Pagination
  const totalPages = Math.ceil(filteredRuns.length / itemsPerPage);
  const paginatedRuns = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredRuns.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredRuns, currentPage]);

  const handleView = (run: RunResponse) => {
    navigate(`/runs/${run.id}`);
  };

  const handleRetry = async () => {
    if (!runToRetry) return;

    try {
      const result = await retryMutation.mutateAsync({ runId: runToRetry.id });
      showToast.success('Workflow retry initiated');
      setRunToRetry(null);
      // Navigate to the new run
      navigate(`/runs/${result.new_run_id}`);
    } catch (error) {
      showToast.error('Failed to retry workflow');
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
    setWorkflowFilter('all');
    setDateRangeFilter('all');
    setCurrentPage(1);
  };

  const hasActiveFilters =
    searchQuery || statusFilter !== 'all' || workflowFilter !== 'all' || dateRangeFilter !== 'all';

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <EmptyState
          icon={PlayCircle}
          title="Failed to load runs"
          description="There was an error loading the workflow runs. Please try again."
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

  const hasRuns = runsData?.items && runsData.items.length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Workflow Runs</h1>
            <p className="text-gray-600">Monitor and manage workflow execution runs</p>
          </div>

          {/* Filters and Search */}
          {hasRuns && (
            <div className="space-y-4">
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by run ID or workflow name..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              {/* Filter Row */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
                  <Filter className="w-5 h-5 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">Filters:</span>
                </div>

                {/* Status Filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value as RunStatus | 'all');
                    setCurrentPage(1);
                  }}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="all">All Status</option>
                  <option value="PENDING">Pending</option>
                  <option value="RUNNING">Running</option>
                  <option value="COMPLETED">Completed</option>
                  <option value="FAILED">Failed</option>
                  <option value="CANCELLED">Cancelled</option>
                </select>

                {/* Workflow Filter */}
                <select
                  value={workflowFilter}
                  onChange={(e) => {
                    setWorkflowFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="all">All Workflows</option>
                  {workflowsData?.items?.map((workflow) => (
                    <option key={workflow.id} value={workflow.id}>
                      {workflow.name}
                    </option>
                  ))}
                </select>

                {/* Date Range Filter */}
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <select
                    value={dateRangeFilter}
                    onChange={(e) => {
                      setDateRangeFilter(e.target.value as 'all' | 'today' | 'week' | 'month');
                      setCurrentPage(1);
                    }}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="all">All Time</option>
                    <option value="today">Today</option>
                    <option value="week">Last 7 Days</option>
                    <option value="month">Last 30 Days</option>
                  </select>
                </div>

                {/* Sort Options */}
                <select
                  value={`${sortBy}-${sortOrder}`}
                  onChange={(e) => {
                    const [newSortBy, newSortOrder] = e.target.value.split('-');
                    setSortBy(newSortBy as 'created_at' | 'updated_at' | 'status');
                    setSortOrder(newSortOrder as 'asc' | 'desc');
                    setCurrentPage(1);
                  }}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="created_at-desc">Newest First</option>
                  <option value="created_at-asc">Oldest First</option>
                  <option value="updated_at-desc">Recently Updated</option>
                  <option value="status-asc">Status (A-Z)</option>
                </select>

                {/* Clear Filters */}
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <X className="w-4 h-4" />
                    Clear Filters
                  </button>
                )}
              </div>
            </div>
          )}
        </motion.div>

        {/* Results Count */}
        {hasRuns && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-4 text-sm text-gray-600"
          >
            Showing {paginatedRuns.length} of {filteredRuns.length} run
            {filteredRuns.length !== 1 ? 's' : ''}
            {searchQuery && ` matching "${searchQuery}"`}
          </motion.div>
        )}

        {/* Runs Grid */}
        {!hasRuns ? (
          <EmptyState
            icon={PlayCircle}
            title="No runs yet"
            description="Workflow runs will appear here once you execute a workflow."
            action={
              <button
                onClick={() => navigate('/workflows')}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                View Workflows
              </button>
            }
          />
        ) : filteredRuns.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No runs found"
            description="Try adjusting your search or filter criteria."
            action={
              <button
                onClick={clearFilters}
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
                {paginatedRuns.map((run, index) => (
                  <motion.div
                    key={run.run_id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ delay: index * 0.05 }}
                    layout
                  >
                    <RunCard
                      run={run}
                      onView={handleView}
                      onRetry={(run) => setRunToRetry(run)}
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
                  {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                    // Show first page, last page, current page, and pages around current
                    let page: number;
                    if (totalPages <= 7) {
                      page = i + 1;
                    } else if (currentPage <= 4) {
                      page = i + 1;
                    } else if (currentPage >= totalPages - 3) {
                      page = totalPages - 6 + i;
                    } else {
                      page = currentPage - 3 + i;
                    }

                    return (
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
                    );
                  })}
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

      {/* Retry Confirmation */}
      <ConfirmDialog
        isOpen={!!runToRetry}
        onClose={() => setRunToRetry(null)}
        onConfirm={handleRetry}
        title="Retry Workflow"
        description={`Are you sure you want to retry this workflow run? A new run will be created and executed from the failed step.`}
        confirmLabel="Retry"
        variant="info"
        isLoading={retryMutation.isPending}
      />
    </div>
  );
}

import { Bot, Workflow, PlayCircle, TrendingUp, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { StatCard } from '@/components/common/StatCard';
import { SuccessRateChart, StatusDistributionChart } from '@/components/common/MiniChart';
import { ActivityFeed } from '@/components/common/ActivityFeed';
import { useAgents } from '@/hooks/useAgents';
import { useWorkflows } from '@/hooks/useWorkflows';
import { useRuns } from '@/hooks/useRuns';
import { useMemo } from 'react';

export default function Dashboard() {
  const navigate = useNavigate();

  // Fetch data for dashboard
  const { data: agentsData, isLoading: agentsLoading } = useAgents({ page_size: 100 });
  const { data: workflowsData, isLoading: workflowsLoading } = useWorkflows({ page_size: 100 });
  const { data: runsData, isLoading: runsLoading } = useRuns({ page_size: 50, sort_by: 'created_at', sort_order: 'desc' });

  // Calculate statistics
  const stats = useMemo(() => {
    const agents = agentsData?.items || [];
    const workflows = workflowsData?.items || [];
    const runs = runsData?.items || [];

    const activeAgents = agents.filter((a) => a.status === 'active').length;
    const totalWorkflows = workflows.length;
    const uniqueWorkflows = new Set(workflows.map((w) => w.name)).size;
    
    const recentRuns = runs.length;
    const completedRuns = runs.filter((r) => r.status === 'COMPLETED').length;
    const failedRuns = runs.filter((r) => r.status === 'FAILED').length;
    const runningRuns = runs.filter((r) => r.status === 'RUNNING').length;
    const pendingRuns = runs.filter((r) => r.status === 'PENDING').length;

    const successRate = recentRuns > 0 ? Math.round((completedRuns / recentRuns) * 100) : 0;

    return {
      totalAgents: agents.length,
      activeAgents,
      totalWorkflows,
      uniqueWorkflows,
      recentRuns,
      completedRuns,
      failedRuns,
      runningRuns,
      pendingRuns,
      successRate,
    };
  }, [agentsData, workflowsData, runsData]);

  const isLoading = agentsLoading || workflowsLoading || runsLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome to the Workflow Manager</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/agents/new')}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span className="text-sm font-medium">Add Agent</span>
          </button>
          <button
            onClick={() => navigate('/workflows/new')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span className="text-sm font-medium">Create Workflow</span>
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Agents"
          value={stats.totalAgents}
          subtitle={`${stats.activeAgents} active`}
          icon={Bot}
          iconColor="text-purple-500"
        />
        <StatCard
          title="Workflows"
          value={stats.totalWorkflows}
          subtitle={`${stats.uniqueWorkflows} unique workflows`}
          icon={Workflow}
          iconColor="text-indigo-500"
        />
        <StatCard
          title="Recent Runs"
          value={stats.recentRuns}
          subtitle={`${stats.completedRuns} completed, ${stats.failedRuns} failed`}
          icon={PlayCircle}
          iconColor="text-blue-500"
        />
        <StatCard
          title="Success Rate"
          value={stats.successRate}
          subtitle="Last 50 runs"
          icon={TrendingUp}
          iconColor="text-green-500"
        />
      </div>

      {/* Charts and Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Success Rate Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Success Rate</h3>
          <SuccessRateChart successRate={stats.successRate} />
          <p className="text-sm text-gray-500 text-center mt-4">
            Based on last {stats.recentRuns} runs
          </p>
        </div>

        {/* Status Distribution Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Run Status Distribution</h3>
          <StatusDistributionChart
            data={{
              completed: stats.completedRuns,
              failed: stats.failedRuns,
              running: stats.runningRuns,
              pending: stats.pendingRuns,
            }}
          />
        </div>

        {/* Recent Activity Feed */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 lg:col-span-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="max-h-96 overflow-y-auto">
            <ActivityFeed
              runs={runsData?.items.slice(0, 5)}
              agents={agentsData?.items.slice(0, 2)}
              workflows={workflowsData?.items.slice(0, 2)}
              maxItems={10}
            />
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}
    </div>
  );
}

/**
 * Activity feed component for displaying recent activities
 */
import { motion } from 'framer-motion';
import { Clock, PlayCircle, CheckCircle, XCircle, Workflow, Bot } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import type { RunResponse, AgentResponse, WorkflowResponse } from '@/types';

type ActivityItem = {
  id: string;
  type: 'run' | 'agent' | 'workflow';
  title: string;
  description: string;
  timestamp: string;
  status?: string;
  link?: string;
};

interface ActivityFeedProps {
  runs?: RunResponse[];
  agents?: AgentResponse[];
  workflows?: WorkflowResponse[];
  maxItems?: number;
}

export function ActivityFeed({ runs = [], agents = [], workflows = [], maxItems = 10 }: ActivityFeedProps) {
  const navigate = useNavigate();

  // Combine and sort all activities
  const activities: ActivityItem[] = [
    ...runs.map((run) => ({
      id: run.id,
      type: 'run' as const,
      title: `Workflow executed: ${run.workflow_name}`,
      description: `Status: ${run.status}`,
      timestamp: run.created_at,
      status: run.status,
      link: `/runs/${run.id}`,
    })),
    ...agents.map((agent) => ({
      id: agent.id,
      type: 'agent' as const,
      title: `Agent registered: ${agent.name}`,
      description: agent.description || 'No description',
      timestamp: agent.created_at,
      link: `/agents/${agent.id}`,
    })),
    ...workflows.map((workflow) => ({
      id: workflow.id,
      type: 'workflow' as const,
      title: `Workflow updated: ${workflow.name}`,
      description: `Version ${workflow.version}`,
      timestamp: workflow.updated_at,
      link: `/workflows/${workflow.id}`,
    })),
  ]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, maxItems);

  const getIcon = (type: string, status?: string) => {
    if (type === 'run') {
      switch (status) {
        case 'COMPLETED':
          return <CheckCircle className="w-5 h-5 text-green-500" />;
        case 'FAILED':
          return <XCircle className="w-5 h-5 text-red-500" />;
        case 'RUNNING':
          return <PlayCircle className="w-5 h-5 text-blue-500" />;
        default:
          return <Clock className="w-5 h-5 text-yellow-500" />;
      }
    } else if (type === 'agent') {
      return <Bot className="w-5 h-5 text-purple-500" />;
    } else {
      return <Workflow className="w-5 h-5 text-indigo-500" />;
    }
  };

  if (activities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400">
        <Clock className="w-12 h-12 mb-2" />
        <p className="text-sm">No recent activity</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {activities.map((activity, index) => (
        <motion.div
          key={activity.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
          onClick={() => activity.link && navigate(activity.link)}
          className={`flex items-start gap-3 p-3 rounded-lg border border-gray-200 ${
            activity.link ? 'cursor-pointer hover:bg-gray-50 hover:border-gray-300 transition-colors' : ''
          }`}
        >
          <div className="flex-shrink-0 mt-0.5">{getIcon(activity.type, activity.status)}</div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{activity.title}</p>
            <p className="text-xs text-gray-500 truncate">{activity.description}</p>
            <p className="text-xs text-gray-400 mt-1">
              {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
            </p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

import { useState, memo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Bot, Edit, Trash2, Activity, Clock, RotateCw, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { cardHoverVariants, buttonVariants } from '@/lib/animations';
import type { AgentResponse } from '@/types';
import { useAgentHealth } from '@/hooks/useAgents';

interface AgentCardProps {
  agent: AgentResponse;
  onEdit: (agent: AgentResponse) => void;
  onDelete: (agent: AgentResponse) => void;
  onTestHealth: (agent: AgentResponse) => void;
}

const AgentCard = memo(function AgentCard({ agent, onEdit, onDelete, onTestHealth }: AgentCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const { data: healthData, isLoading: isHealthLoading } = useAgentHealth(agent.id, false);

  const isActive = agent.status === 'active';
  const isHealthy = healthData?.status === 'healthy';

  // Memoize callbacks
  const handleEdit = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(agent);
  }, [onEdit, agent]);

  const handleTestHealth = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onTestHealth(agent);
  }, [onTestHealth, agent]);

  const handleDelete = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(agent);
  }, [onDelete, agent]);

  return (
    <motion.div
      variants={cardHoverVariants}
      initial="initial"
      whileHover="hover"
      whileTap="tap"
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className={cn(
        'relative bg-white rounded-xl border-2 transition-colors duration-300 overflow-hidden cursor-pointer',
        isActive ? 'border-gray-200 hover:border-primary-300' : 'border-gray-100 opacity-75'
      )}
    >
      {/* Status Indicator Bar */}
      <div
        className={cn(
          'absolute top-0 left-0 right-0 h-1',
          isActive ? 'bg-green-500' : 'bg-gray-300'
        )}
      />

      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div
              className={cn(
                'flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center',
                isActive ? 'bg-blue-100' : 'bg-gray-100'
              )}
            >
              <Bot className={cn('w-6 h-6', isActive ? 'text-blue-600' : 'text-gray-400')} />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 truncate">{agent.name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={cn(
                    'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                    isActive
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-600'
                  )}
                >
                  {isActive ? 'Active' : 'Inactive'}
                </span>
                {healthData && (
                  <span
                    className={cn(
                      'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
                      isHealthy
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    )}
                  >
                    <Activity className="w-3 h-3" />
                    {isHealthy ? 'Healthy' : 'Unhealthy'}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* URL */}
        <div className="mb-4">
          <a
            href={agent.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 hover:underline truncate group"
          >
            <span className="truncate">{agent.url}</span>
            <ExternalLink className="w-3 h-3 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
          </a>
        </div>

        {/* Description */}
        {agent.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">{agent.description}</p>
        )}

        {/* Configuration Details */}
        <div className="flex items-center gap-4 mb-4 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            <span>Timeout: {agent.timeout_ms / 1000}s</span>
          </div>
          <div className="flex items-center gap-1">
            <RotateCw className="w-3.5 h-3.5" />
            <span>Retries: {agent.retry_config.max_retries}</span>
          </div>
        </div>

        {/* Health Response Time */}
        {healthData?.response_time_ms && (
          <div className="mb-4 text-xs text-gray-500">
            Response time: {healthData.response_time_ms}ms
          </div>
        )}

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{
            opacity: isHovered ? 1 : 0,
            height: isHovered ? 'auto' : 0,
          }}
          transition={{ duration: 0.2 }}
          className="flex items-center gap-2 pt-4 border-t border-gray-100 overflow-hidden"
        >
          <motion.button
            variants={buttonVariants}
            whileHover="hover"
            whileTap="tap"
            onClick={handleEdit}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Edit className="w-4 h-4" />
            Edit
          </motion.button>
          <motion.button
            variants={buttonVariants}
            whileHover="hover"
            whileTap="tap"
            onClick={handleTestHealth}
            disabled={isHealthLoading}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Activity className="w-4 h-4" />
            Test
          </motion.button>
          <motion.button
            variants={buttonVariants}
            whileHover="hover"
            whileTap="tap"
            onClick={handleDelete}
            className="flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </motion.button>
        </motion.div>
      </div>
    </motion.div>
  );
});

export default AgentCard;

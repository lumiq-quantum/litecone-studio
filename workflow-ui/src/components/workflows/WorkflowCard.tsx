import { useState, memo, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Workflow, Edit, Trash2, Play, Eye, FileJson, GitBranch } from 'lucide-react';
import { cn } from '@/lib/utils';
import { cardHoverVariants, buttonVariants } from '@/lib/animations';
import type { WorkflowResponse } from '@/types';

interface WorkflowCardProps {
  workflow: WorkflowResponse;
  onView: (workflow: WorkflowResponse) => void;
  onEdit: (workflow: WorkflowResponse) => void;
  onExecute: (workflow: WorkflowResponse) => void;
  onDelete: (workflow: WorkflowResponse) => void;
}

const WorkflowCard = memo(function WorkflowCard({
  workflow,
  onView,
  onEdit,
  onExecute,
  onDelete,
}: WorkflowCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  const isActive = workflow.status === 'active';
  
  // Memoize computed values
  const stepCount = useMemo(
    () => Object.keys(workflow.workflow_data.steps).length,
    [workflow.workflow_data.steps]
  );
  
  // Get unique agent names from steps
  const agentNames = useMemo(
    () => Array.from(
      new Set(Object.values(workflow.workflow_data.steps).map((step) => step.agent_name))
    ),
    [workflow.workflow_data.steps]
  );

  // Memoize callbacks
  const handleView = useCallback(() => onView(workflow), [onView, workflow]);
  const handleEdit = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(workflow);
  }, [onEdit, workflow]);
  const handleExecute = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onExecute(workflow);
  }, [onExecute, workflow]);
  const handleDelete = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(workflow);
  }, [onDelete, workflow]);

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
      onClick={handleView}
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
              <Workflow className={cn('w-6 h-6', isActive ? 'text-blue-600' : 'text-gray-400')} />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 truncate">{workflow.name}</h3>
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
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  <GitBranch className="w-3 h-3" />
                  v{workflow.version}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Description */}
        {workflow.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">{workflow.description}</p>
        )}

        {/* Workflow Details */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <FileJson className="w-3.5 h-3.5" />
            <span>{stepCount} step{stepCount !== 1 ? 's' : ''}</span>
          </div>
          
          {agentNames.length > 0 && (
            <div className="flex items-start gap-2 text-xs text-gray-500">
              <Workflow className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
              <div className="flex flex-wrap gap-1">
                {agentNames.slice(0, 3).map((agentName, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 text-gray-700"
                  >
                    {agentName}
                  </span>
                ))}
                {agentNames.length > 3 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                    +{agentNames.length - 3} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className="text-xs text-gray-400 mb-4">
          Created {new Date(workflow.created_at).toLocaleDateString()}
        </div>

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{
            opacity: isHovered ? 1 : 0,
            height: isHovered ? 'auto' : 0,
          }}
          transition={{ duration: 0.2 }}
          className="flex items-center gap-2 pt-4 border-t border-gray-100 overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          <motion.button
            variants={buttonVariants}
            whileHover="hover"
            whileTap="tap"
            onClick={handleView}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Eye className="w-4 h-4" />
            View
          </motion.button>
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
            onClick={handleExecute}
            disabled={!isActive}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="w-4 h-4" />
            Execute
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

export default WorkflowCard;

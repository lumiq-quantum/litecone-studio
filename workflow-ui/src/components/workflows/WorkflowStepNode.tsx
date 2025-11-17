import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Bot, CheckCircle2, XCircle, Clock, Loader2 } from 'lucide-react';
import * as Tooltip from '@radix-ui/react-tooltip';
import { cn } from '@/lib/utils';

export interface WorkflowStepNodeData {
  stepId: string;
  agentName: string;
  status?: 'pending' | 'running' | 'completed' | 'failed';
  hasInput: boolean;
  hasOutput: boolean;
  inputMapping?: Record<string, unknown>;
  error?: string;
}

function WorkflowStepNode({ data, selected }: NodeProps<WorkflowStepNodeData>) {
  const { stepId, agentName, status, hasInput, hasOutput, inputMapping, error } = data;

  // Determine node styling based on status
  const getNodeStyles = () => {
    switch (status) {
      case 'running':
        return {
          border: 'border-blue-500',
          bg: 'bg-blue-50',
          text: 'text-blue-900',
          icon: 'text-blue-600',
        };
      case 'completed':
        return {
          border: 'border-green-500',
          bg: 'bg-green-50',
          text: 'text-green-900',
          icon: 'text-green-600',
        };
      case 'failed':
        return {
          border: 'border-red-500',
          bg: 'bg-red-50',
          text: 'text-red-900',
          icon: 'text-red-600',
        };
      case 'pending':
        return {
          border: 'border-gray-300',
          bg: 'bg-gray-50',
          text: 'text-gray-700',
          icon: 'text-gray-400',
        };
      default:
        return {
          border: 'border-gray-300',
          bg: 'bg-white',
          text: 'text-gray-900',
          icon: 'text-gray-600',
        };
    }
  };

  const styles = getNodeStyles();

  // Get status icon
  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return <Loader2 className={cn('w-4 h-4 animate-spin', styles.icon)} />;
      case 'completed':
        return <CheckCircle2 className={cn('w-4 h-4', styles.icon)} />;
      case 'failed':
        return <XCircle className={cn('w-4 h-4', styles.icon)} />;
      case 'pending':
        return <Clock className={cn('w-4 h-4', styles.icon)} />;
      default:
        return null;
    }
  };

  // Tooltip content
  const tooltipContent = (
    <div className="max-w-xs">
      <div className="font-semibold mb-1">{stepId}</div>
      <div className="text-xs space-y-1">
        <div>
          <span className="text-gray-400">Agent:</span> {agentName}
        </div>
        {status && (
          <div>
            <span className="text-gray-400">Status:</span>{' '}
            <span className="capitalize">{status}</span>
          </div>
        )}
        {inputMapping && Object.keys(inputMapping).length > 0 && (
          <div>
            <span className="text-gray-400">Inputs:</span>{' '}
            {Object.keys(inputMapping).join(', ')}
          </div>
        )}
        {error && (
          <div className="text-red-400 mt-2">
            <span className="font-semibold">Error:</span> {error}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <Tooltip.Provider delayDuration={300}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <div
            className={cn(
              'px-4 py-3 rounded-lg border-2 shadow-sm transition-all min-w-[180px]',
              styles.border,
              styles.bg,
              selected && 'ring-2 ring-primary-500 ring-offset-2',
              status === 'running' && 'animate-pulse'
            )}
          >
            {/* Input Handle */}
            {hasInput && (
              <Handle
                type="target"
                position={Position.Left}
                className="w-3 h-3 !bg-gray-400 border-2 border-white"
              />
            )}

            {/* Node Content */}
            <div className="flex items-start gap-2">
              <div className={cn('flex-shrink-0 mt-0.5', styles.icon)}>
                <Bot className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className={cn('text-sm font-semibold truncate', styles.text)}>
                  {stepId}
                </div>
                <div className="text-xs text-gray-600 truncate mt-0.5">{agentName}</div>
              </div>
              {status && <div className="flex-shrink-0">{getStatusIcon()}</div>}
            </div>

            {/* Output Handle */}
            {hasOutput && (
              <Handle
                type="source"
                position={Position.Right}
                className="w-3 h-3 !bg-gray-400 border-2 border-white"
              />
            )}
          </div>
        </Tooltip.Trigger>

        <Tooltip.Portal>
          <Tooltip.Content
            className="bg-gray-900 text-white text-sm rounded-lg px-3 py-2 shadow-lg z-50"
            sideOffset={5}
          >
            {tooltipContent}
            <Tooltip.Arrow className="fill-gray-900" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}

export default memo(WorkflowStepNode);

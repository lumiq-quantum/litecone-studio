import { useCallback, useMemo, useEffect } from 'react';
import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  MarkerType,
  Handle,
  Position,
  type Node,
  type Edge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { motion } from 'framer-motion';
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { StepExecutionResponse, WorkflowDefinition } from '@/types';

interface ExecutionGraphProps {
  workflow: WorkflowDefinition;
  steps: StepExecutionResponse[];
  onStepClick?: (stepId: string) => void;
  selectedStepId?: string;
  className?: string;
}

interface ExecutionStepNodeData {
  stepId: string;
  stepName: string;
  agentName: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  hasInput: boolean;
  hasOutput: boolean;
  error?: string;
}

// Layout configuration
const HORIZONTAL_SPACING = 280;
const VERTICAL_SPACING = 120;

// Custom node component for execution steps
function ExecutionStepNode({ data }: { data: ExecutionStepNodeData }) {
  const statusConfig = {
    PENDING: {
      bg: 'bg-gray-100 border-gray-300',
      text: 'text-gray-700',
      icon: Clock,
      iconColor: 'text-gray-500',
    },
    RUNNING: {
      bg: 'bg-blue-100 border-blue-400',
      text: 'text-blue-900',
      icon: Loader2,
      iconColor: 'text-blue-600',
    },
    COMPLETED: {
      bg: 'bg-green-100 border-green-400',
      text: 'text-green-900',
      icon: CheckCircle2,
      iconColor: 'text-green-600',
    },
    FAILED: {
      bg: 'bg-red-100 border-red-400',
      text: 'text-red-900',
      icon: XCircle,
      iconColor: 'text-red-600',
    },
    SKIPPED: {
      bg: 'bg-gray-50 border-gray-200',
      text: 'text-gray-500',
      icon: Clock,
      iconColor: 'text-gray-400',
    },
  };

  const config = statusConfig[data.status];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'px-4 py-3 rounded-lg border-2 shadow-md min-w-[200px] cursor-pointer hover:shadow-lg transition-all',
        config.bg
      )}
    >
      <div className="flex items-start gap-2 mb-2">
        <Icon
          className={cn(
            'w-5 h-5 flex-shrink-0 mt-0.5',
            config.iconColor,
            data.status === 'RUNNING' && 'animate-spin'
          )}
        />
        <div className="flex-1 min-w-0">
          <div className={cn('font-semibold text-sm truncate', config.text)}>
            {data.stepName || data.stepId}
          </div>
          <div className="text-xs text-gray-600 truncate">{data.agentName}</div>
        </div>
      </div>

      {data.error && (
        <div className="mt-2 text-xs text-red-700 line-clamp-2 bg-red-50 p-1.5 rounded">
          {data.error}
        </div>
      )}

      {/* ReactFlow connection handles */}
      {data.hasInput && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-3 !h-3 !bg-white !border-2 !border-gray-400"
        />
      )}
      {data.hasOutput && (
        <Handle
          type="source"
          position={Position.Right}
          className="!w-3 !h-3 !bg-white !border-2 !border-gray-400"
        />
      )}
    </motion.div>
  );
}

export default function ExecutionGraph({
  workflow,
  steps,
  onStepClick,
  selectedStepId,
  className = '',
}: ExecutionGraphProps) {
  // Memoize nodeTypes to avoid React Flow warning
  const nodeTypes = useMemo(
    () => ({
      executionStep: ExecutionStepNode,
    }),
    []
  );

  // Create a map of step executions by step ID
  const stepExecutionMap = useMemo(() => {
    const map = new Map<string, StepExecutionResponse>();
    steps.forEach((step) => {
      map.set(step.step_id, step);
    });
    return map;
  }, [steps]);

  // Parse workflow definition to create nodes and edges
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node<ExecutionStepNodeData>[] = [];
    const edges: Edge[] = [];
    const workflowSteps = workflow.steps;

    // Build dependency maps
    const stepDependencies = new Map<string, string[]>();
    const stepChildren = new Map<string, string[]>();

    Object.entries(workflowSteps).forEach(([stepId, step]) => {
      if (step.next_step) {
        if (!stepChildren.has(stepId)) {
          stepChildren.set(stepId, []);
        }
        stepChildren.get(stepId)!.push(step.next_step);

        if (!stepDependencies.has(step.next_step)) {
          stepDependencies.set(step.next_step, []);
        }
        stepDependencies.get(step.next_step)!.push(stepId);
      }
    });

    // Calculate levels for layout
    const stepLevels = new Map<string, number>();
    const calculateLevel = (stepId: string, visited = new Set<string>()): number => {
      if (stepLevels.has(stepId)) {
        return stepLevels.get(stepId)!;
      }

      if (visited.has(stepId)) {
        return 0;
      }

      visited.add(stepId);
      const deps = stepDependencies.get(stepId) || [];
      const level =
        deps.length === 0 ? 0 : Math.max(...deps.map((dep) => calculateLevel(dep, visited))) + 1;
      stepLevels.set(stepId, level);
      return level;
    };

    Object.keys(workflowSteps).forEach((stepId) => calculateLevel(stepId));

    // Group steps by level
    const levelGroups = new Map<number, string[]>();
    stepLevels.forEach((level, stepId) => {
      if (!levelGroups.has(level)) {
        levelGroups.set(level, []);
      }
      levelGroups.get(level)!.push(stepId);
    });

    // Create nodes
    Object.entries(workflowSteps).forEach(([stepId, step]) => {
      const level = stepLevels.get(stepId) || 0;
      const stepsInLevel = levelGroups.get(level) || [];
      const indexInLevel = stepsInLevel.indexOf(stepId);
      const totalInLevel = stepsInLevel.length;

      const x = level * HORIZONTAL_SPACING;
      const y = (indexInLevel - (totalInLevel - 1) / 2) * VERTICAL_SPACING;

      const execution = stepExecutionMap.get(stepId);
      const hasInput = stepId !== workflow.start_step;
      const hasOutput = step.next_step !== null;

      nodes.push({
        id: stepId,
        type: 'executionStep',
        position: { x, y },
        data: {
          stepId,
          stepName: execution?.step_name || stepId,
          agentName: step.agent_name,
          status: execution?.status || 'PENDING',
          hasInput,
          hasOutput,
          error: execution?.error_message,
        },
        selected: stepId === selectedStepId,
      });

      // Create edges
      if (step.next_step) {
        const sourceExecution = stepExecutionMap.get(stepId);
        const status = sourceExecution?.status;

        edges.push({
          id: `${stepId}-${step.next_step}`,
          source: stepId,
          target: step.next_step,
          type: 'smoothstep',
          animated: status === 'RUNNING',
          style: {
            stroke:
              status === 'COMPLETED'
                ? '#10b981'
                : status === 'FAILED'
                ? '#ef4444'
                : status === 'RUNNING'
                ? '#3b82f6'
                : '#9ca3af',
            strokeWidth: 2,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color:
              status === 'COMPLETED'
                ? '#10b981'
                : status === 'FAILED'
                ? '#ef4444'
                : status === 'RUNNING'
                ? '#3b82f6'
                : '#9ca3af',
          },
        });
      }
    });

    return { initialNodes: nodes, initialEdges: edges };
  }, [workflow, stepExecutionMap, selectedStepId]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when steps change (for real-time updates)
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (onStepClick) {
        onStepClick(node.id);
      }
    },
    [onStepClick]
  );

  return (
    <div className={className} style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Strict}
        fitView
        fitViewOptions={{
          padding: 0.2,
          minZoom: 0.5,
          maxZoom: 1.5,
        }}
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
        }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#e5e7eb" gap={16} />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(node) => {
            const data = node.data as ExecutionStepNodeData;
            switch (data.status) {
              case 'RUNNING':
                return '#3b82f6';
              case 'COMPLETED':
                return '#10b981';
              case 'FAILED':
                return '#ef4444';
              case 'PENDING':
                return '#9ca3af';
              case 'SKIPPED':
                return '#d1d5db';
              default:
                return '#6b7280';
            }
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
          style={{
            backgroundColor: '#f9fafb',
          }}
        />
      </ReactFlow>
    </div>
  );
}

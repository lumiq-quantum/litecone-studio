import { useCallback, useMemo } from 'react';
import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  MarkerType,
  type Node,
  type Edge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import WorkflowStepNode from './WorkflowStepNode';
import type { WorkflowStepNodeData } from './WorkflowStepNode';
import type { WorkflowDefinition } from '@/types';

interface WorkflowGraphProps {
  workflow: WorkflowDefinition;
  onStepClick?: (stepId: string) => void;
  selectedStepId?: string;
  stepStatuses?: Record<string, 'pending' | 'running' | 'completed' | 'failed'>;
  stepErrors?: Record<string, string>;
  className?: string;
}

// Custom node types
const nodeTypes = {
  workflowStep: WorkflowStepNode,
};

// Layout configuration
const HORIZONTAL_SPACING = 250;
const VERTICAL_SPACING = 100;

export default function WorkflowGraph({
  workflow,
  onStepClick,
  selectedStepId,
  stepStatuses,
  stepErrors,
  className = '',
}: WorkflowGraphProps) {
  // Parse workflow definition to create nodes and edges
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node<WorkflowStepNodeData>[] = [];
    const edges: Edge[] = [];
    const steps = workflow.steps;

    // Build a map of step dependencies to calculate layout
    const stepDependencies = new Map<string, string[]>();
    const stepChildren = new Map<string, string[]>();

    Object.entries(steps).forEach(([stepId, step]) => {
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

    // Calculate levels for each step (for layout)
    const stepLevels = new Map<string, number>();
    const calculateLevel = (stepId: string, visited = new Set<string>()): number => {
      if (stepLevels.has(stepId)) {
        return stepLevels.get(stepId)!;
      }

      if (visited.has(stepId)) {
        return 0; // Circular dependency, break the cycle
      }

      visited.add(stepId);
      const deps = stepDependencies.get(stepId) || [];
      const level = deps.length === 0 ? 0 : Math.max(...deps.map((dep) => calculateLevel(dep, visited))) + 1;
      stepLevels.set(stepId, level);
      return level;
    };

    // Calculate levels for all steps
    Object.keys(steps).forEach((stepId) => calculateLevel(stepId));

    // Group steps by level
    const levelGroups = new Map<number, string[]>();
    stepLevels.forEach((level, stepId) => {
      if (!levelGroups.has(level)) {
        levelGroups.set(level, []);
      }
      levelGroups.get(level)!.push(stepId);
    });

    // Create nodes with calculated positions
    Object.entries(steps).forEach(([stepId, step]) => {
      const level = stepLevels.get(stepId) || 0;
      const stepsInLevel = levelGroups.get(level) || [];
      const indexInLevel = stepsInLevel.indexOf(stepId);
      const totalInLevel = stepsInLevel.length;

      // Calculate position
      const x = level * HORIZONTAL_SPACING;
      const y = (indexInLevel - (totalInLevel - 1) / 2) * VERTICAL_SPACING;

      const hasInput = stepId !== workflow.start_step;
      const hasOutput = step.next_step !== null;

      nodes.push({
        id: stepId,
        type: 'workflowStep',
        position: { x, y },
        data: {
          stepId,
          agentName: step.agent_name,
          status: stepStatuses?.[stepId],
          hasInput,
          hasOutput,
          inputMapping: step.input_mapping,
          error: stepErrors?.[stepId],
        },
        selected: stepId === selectedStepId,
      });

      // Create edge if there's a next step
      if (step.next_step) {
        edges.push({
          id: `${stepId}-${step.next_step}`,
          source: stepId,
          target: step.next_step,
          type: 'smoothstep',
          animated: stepStatuses?.[stepId] === 'running',
          style: {
            stroke: stepStatuses?.[stepId] === 'completed' ? '#10b981' : 
                    stepStatuses?.[stepId] === 'failed' ? '#ef4444' :
                    stepStatuses?.[stepId] === 'running' ? '#3b82f6' : '#9ca3af',
            strokeWidth: 2,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: stepStatuses?.[stepId] === 'completed' ? '#10b981' : 
                   stepStatuses?.[stepId] === 'failed' ? '#ef4444' :
                   stepStatuses?.[stepId] === 'running' ? '#3b82f6' : '#9ca3af',
          },
        });
      }
    });

    return { initialNodes: nodes, initialEdges: edges };
  }, [workflow, selectedStepId, stepStatuses, stepErrors]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

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
      >
        <Background color="#e5e7eb" gap={16} />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(node) => {
            const data = node.data as WorkflowStepNodeData;
            switch (data.status) {
              case 'running':
                return '#3b82f6';
              case 'completed':
                return '#10b981';
              case 'failed':
                return '#ef4444';
              case 'pending':
                return '#9ca3af';
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

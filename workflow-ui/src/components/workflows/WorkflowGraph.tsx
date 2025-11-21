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
      const stepType = step.type || 'agent';

      // Handle parallel steps
      if (stepType === 'parallel' && step.parallel_steps) {
        // Add edges from parallel block to each parallel step
        step.parallel_steps.forEach((parallelStepId) => {
          if (!stepChildren.has(stepId)) {
            stepChildren.set(stepId, []);
          }
          stepChildren.get(stepId)!.push(parallelStepId);

          if (!stepDependencies.has(parallelStepId)) {
            stepDependencies.set(parallelStepId, []);
          }
          stepDependencies.get(parallelStepId)!.push(stepId);
        });
      }

      // Handle conditional steps
      if (stepType === 'conditional') {
        // Add edges for both branches
        if (step.if_true_step) {
          if (!stepChildren.has(stepId)) {
            stepChildren.set(stepId, []);
          }
          stepChildren.get(stepId)!.push(step.if_true_step);

          if (!stepDependencies.has(step.if_true_step)) {
            stepDependencies.set(step.if_true_step, []);
          }
          stepDependencies.get(step.if_true_step)!.push(stepId);
        }

        if (step.if_false_step) {
          if (!stepChildren.has(stepId)) {
            stepChildren.set(stepId, []);
          }
          stepChildren.get(stepId)!.push(step.if_false_step);

          if (!stepDependencies.has(step.if_false_step)) {
            stepDependencies.set(step.if_false_step, []);
          }
          stepDependencies.get(step.if_false_step)!.push(stepId);
        }
      }

      // Handle loop steps
      if (stepType === 'loop' && step.loop_config?.loop_body) {
        // Add edges from loop block to each loop body step
        step.loop_config.loop_body.forEach((loopStepId) => {
          if (!stepChildren.has(stepId)) {
            stepChildren.set(stepId, []);
          }
          stepChildren.get(stepId)!.push(loopStepId);

          if (!stepDependencies.has(loopStepId)) {
            stepDependencies.set(loopStepId, []);
          }
          stepDependencies.get(loopStepId)!.push(stepId);
        });
      }

      // Handle fork-join steps
      if (stepType === 'fork_join' && step.fork_join_config?.branches) {
        // Add edges from fork-join block to each branch's steps
        Object.values(step.fork_join_config.branches).forEach((branch) => {
          branch.steps.forEach((branchStepId) => {
            if (!stepChildren.has(stepId)) {
              stepChildren.set(stepId, []);
            }
            stepChildren.get(stepId)!.push(branchStepId);

            if (!stepDependencies.has(branchStepId)) {
              stepDependencies.set(branchStepId, []);
            }
            stepDependencies.get(branchStepId)!.push(stepId);
          });
        });
      }

      // Handle next_step for all step types
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

      const stepType = step.type || 'agent';
      const hasInput = stepId !== workflow.start_step;
      const hasOutput = Boolean(
        step.next_step !== null || 
        (stepType === 'parallel' && step.parallel_steps) ||
        (stepType === 'conditional' && (step.if_true_step || step.if_false_step))
      );

      // Determine display name based on step type
      let displayName = '';
      if (stepType === 'parallel') {
        displayName = `Parallel (${step.parallel_steps?.length || 0})`;
      } else if (stepType === 'conditional') {
        displayName = step.condition?.expression || 'Condition';
      } else if (stepType === 'loop') {
        const mode = step.loop_config?.execution_mode || 'sequential';
        displayName = `Loop (${mode})`;
      } else if (stepType === 'fork_join') {
        const branchCount = Object.keys(step.fork_join_config?.branches || {}).length;
        const policy = step.fork_join_config?.join_policy || 'all';
        displayName = `Fork-Join (${branchCount} branches, ${policy})`;
      } else {
        displayName = step.agent_name || '';
      }

      nodes.push({
        id: stepId,
        type: 'workflowStep',
        position: { x, y },
        data: {
          stepId,
          agentName: displayName,
          status: stepStatuses?.[stepId],
          hasInput,
          hasOutput,
          inputMapping: step.input_mapping,
          error: stepErrors?.[stepId],
          isParallel: stepType === 'parallel' ? true : false,
          isConditional: stepType === 'conditional' ? true : false,
          isLoop: stepType === 'loop' ? true : false,
          isForkJoin: stepType === 'fork_join' ? true : false,
        },
        selected: stepId === selectedStepId,
      });

      // Create edges for parallel steps
      if (stepType === 'parallel' && step.parallel_steps) {
        step.parallel_steps.forEach((parallelStepId) => {
          edges.push({
            id: `${stepId}-${parallelStepId}`,
            source: stepId,
            target: parallelStepId,
            type: 'smoothstep',
            animated: stepStatuses?.[stepId] === 'running',
            style: {
              stroke: '#8b5cf6', // Purple for parallel edges
              strokeWidth: 2,
              strokeDasharray: '5,5', // Dashed line for parallel
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: '#8b5cf6',
            },
          });
        });
      }

      // Create edges for conditional steps
      if (stepType === 'conditional') {
        // True branch edge
        if (step.if_true_step) {
          edges.push({
            id: `${stepId}-true-${step.if_true_step}`,
            source: stepId,
            target: step.if_true_step,
            type: 'smoothstep',
            label: 'true',
            labelStyle: { fill: '#10b981', fontWeight: 600, fontSize: 12 },
            labelBgStyle: { fill: '#f0fdf4' },
            animated: stepStatuses?.[stepId] === 'running',
            style: {
              stroke: '#10b981', // Green for true branch
              strokeWidth: 2,
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: '#10b981',
            },
          });
        }

        // False branch edge
        if (step.if_false_step) {
          edges.push({
            id: `${stepId}-false-${step.if_false_step}`,
            source: stepId,
            target: step.if_false_step,
            type: 'smoothstep',
            label: 'false',
            labelStyle: { fill: '#ef4444', fontWeight: 600, fontSize: 12 },
            labelBgStyle: { fill: '#fef2f2' },
            animated: stepStatuses?.[stepId] === 'running',
            style: {
              stroke: '#ef4444', // Red for false branch
              strokeWidth: 2,
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: '#ef4444',
            },
          });
        }
      }

      // Create edges for loop steps
      if (stepType === 'loop' && step.loop_config?.loop_body) {
        step.loop_config.loop_body.forEach((loopStepId) => {
          edges.push({
            id: `${stepId}-${loopStepId}`,
            source: stepId,
            target: loopStepId,
            type: 'smoothstep',
            animated: stepStatuses?.[stepId] === 'running',
            style: {
              stroke: '#f59e0b', // Orange for loop edges
              strokeWidth: 2,
              strokeDasharray: '8,4', // Dashed line for loop
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: '#f59e0b',
            },
          });
        });
      }

      // Create edges for fork-join steps
      if (stepType === 'fork_join' && step.fork_join_config?.branches) {
        Object.entries(step.fork_join_config.branches).forEach(([branchName, branch]) => {
          branch.steps.forEach((branchStepId, index) => {
            edges.push({
              id: `${stepId}-${branchName}-${branchStepId}`,
              source: stepId,
              target: branchStepId,
              type: 'smoothstep',
              label: index === 0 ? branchName : undefined, // Only label first step in branch
              labelStyle: { fill: '#6366f1', fontWeight: 600, fontSize: 11 },
              labelBgStyle: { fill: '#eef2ff' },
              animated: stepStatuses?.[stepId] === 'running',
              style: {
                stroke: '#6366f1', // Indigo for fork-join edges
                strokeWidth: 2,
                strokeDasharray: '6,3', // Dashed line for fork-join
              },
              markerEnd: {
                type: MarkerType.ArrowClosed,
                color: '#6366f1',
              },
            });
          });
        });
      }

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

import { useState, useEffect, useMemo, useRef, useImperativeHandle, forwardRef } from 'react';
import { FileJson, Network, AlertCircle } from 'lucide-react';
import * as Tabs from '@radix-ui/react-tabs';
import JSONEditor, { type JSONEditorRef } from '@/components/common/JSONEditor';
import WorkflowGraph from './WorkflowGraph';
import { cn } from '@/lib/utils';
import type { WorkflowDefinition } from '@/types';

interface WorkflowVisualEditorProps {
  value: string;
  onChange: (value: string) => void;
  onValidate?: (valid: boolean, errors: string[]) => void;
  agentNames?: string[];
  readOnly?: boolean;
  height?: string;
}

export interface WorkflowVisualEditorRef {
  highlightLines: (lineNumbers: number[], duration?: number) => void;
}

const WorkflowVisualEditor = forwardRef<WorkflowVisualEditorRef, WorkflowVisualEditorProps>(({
  value,
  onChange,
  onValidate,
  agentNames,
  readOnly = false,
  height = '600px',
}, ref) => {
  const [activeTab, setActiveTab] = useState<'json' | 'visual' | 'split'>('split');
  const [isValid, setIsValid] = useState(true);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [selectedStepId, setSelectedStepId] = useState<string | undefined>();
  const jsonEditorRef = useRef<JSONEditorRef>(null);

  // Expose methods to parent components
  useImperativeHandle(ref, () => ({
    highlightLines: (lineNumbers: number[], duration?: number) => {
      jsonEditorRef.current?.highlightLines(lineNumbers, duration);
    },
  }));

  // Parse workflow from JSON
  const workflowDefinition = useMemo<WorkflowDefinition | null>(() => {
    try {
      const parsed = JSON.parse(value);
      if (parsed.start_step && parsed.steps) {
        return parsed as WorkflowDefinition;
      }
      return null;
    } catch {
      return null;
    }
  }, [value]);

  const handleValidate = (valid: boolean, errors: string[]) => {
    setIsValid(valid);
    setValidationErrors(errors);
    if (onValidate) {
      onValidate(valid, errors);
    }
  };

  const handleStepClick = (stepId: string) => {
    setSelectedStepId(stepId);
    
    // If in visual mode, switch to split view to show both
    if (activeTab === 'visual' && !readOnly) {
      setActiveTab('split');
    }
  };

  // Update selected step when JSON changes
  useEffect(() => {
    if (workflowDefinition && selectedStepId) {
      // Check if selected step still exists
      if (!workflowDefinition.steps[selectedStepId]) {
        setSelectedStepId(undefined);
      }
    }
  }, [workflowDefinition, selectedStepId]);

  return (
    <div className="flex flex-col border border-gray-200 rounded-lg overflow-hidden bg-white" style={{ height }}>
      <Tabs.Root value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)} className="flex flex-col h-full">
        {/* Tab List */}
        <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 flex-shrink-0">
          <Tabs.List className="flex gap-1 py-2">
            <Tabs.Trigger
              value="json"
              className={cn(
                'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                activeTab === 'json'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              )}
            >
              <FileJson className="w-4 h-4" />
              JSON Editor
            </Tabs.Trigger>
            <Tabs.Trigger
              value="visual"
              className={cn(
                'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                activeTab === 'visual'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              )}
            >
              <Network className="w-4 h-4" />
              Visual Graph
            </Tabs.Trigger>
            <Tabs.Trigger
              value="split"
              className={cn(
                'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                activeTab === 'split'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              )}
            >
              <FileJson className="w-3.5 h-3.5" />
              <Network className="w-3.5 h-3.5" />
              Split View
            </Tabs.Trigger>
          </Tabs.List>

          {/* Validation Status */}
          <div className="flex items-center gap-2 text-sm py-2">
            {isValid ? (
              <span className="flex items-center gap-1.5 text-green-600 font-medium">
                <div className="w-2 h-2 bg-green-600 rounded-full" />
                Valid
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-red-600 font-medium">
                <AlertCircle className="w-4 h-4" />
                {validationErrors.length} Error{validationErrors.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden relative">
          {/* JSON Only */}
          <Tabs.Content 
            value="json" 
            className="absolute inset-0 data-[state=inactive]:hidden"
          >
            <div className="w-full h-full">
              <JSONEditor
                ref={jsonEditorRef}
                value={value}
                onChange={onChange}
                onValidate={handleValidate}
                agentNames={agentNames}
                readOnly={readOnly}
                height="100%"
              />
            </div>
          </Tabs.Content>

          {/* Visual Only */}
          <Tabs.Content 
            value="visual" 
            className="absolute inset-0 data-[state=inactive]:hidden bg-gray-50"
          >
            {workflowDefinition && isValid ? (
              <div className="w-full h-full animate-in fade-in duration-300">
                <WorkflowGraph
                  workflow={workflowDefinition}
                  onStepClick={handleStepClick}
                  selectedStepId={selectedStepId}
                  className="h-full"
                  key={value} // Force re-render with animation when workflow changes
                />
              </div>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center max-w-md px-4">
                  <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {isValid ? 'No Workflow to Display' : 'Invalid Workflow Definition'}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {isValid
                      ? 'Enter a valid workflow definition in the JSON editor to see the visual graph.'
                      : 'Fix the validation errors in the JSON editor to see the visual graph.'}
                  </p>
                  {!isValid && validationErrors.length > 0 && (
                    <div className="mt-4 text-left bg-red-50 border border-red-200 rounded-lg p-3">
                      <p className="text-xs font-semibold text-red-900 mb-2">Errors:</p>
                      <ul className="text-xs text-red-700 space-y-1">
                        {validationErrors.slice(0, 3).map((error, idx) => (
                          <li key={idx}>• {error}</li>
                        ))}
                        {validationErrors.length > 3 && (
                          <li className="text-red-600">
                            ... and {validationErrors.length - 3} more
                          </li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </Tabs.Content>

          {/* Split View */}
          <Tabs.Content 
            value="split" 
            className="absolute inset-0 data-[state=inactive]:hidden"
          >
            <div className="flex w-full h-full">
              {/* JSON Editor - Left Side */}
              <div className="w-1/2 border-r border-gray-200 h-full">
                <JSONEditor
                  ref={jsonEditorRef}
                  value={value}
                  onChange={onChange}
                  onValidate={handleValidate}
                  agentNames={agentNames}
                  readOnly={readOnly}
                  height="100%"
                />
              </div>

              {/* Visual Graph - Right Side */}
              <div className="w-1/2 bg-gray-50 h-full">
                {workflowDefinition && isValid ? (
                  <div className="h-full animate-in fade-in duration-300">
                    <WorkflowGraph
                      workflow={workflowDefinition}
                      onStepClick={handleStepClick}
                      selectedStepId={selectedStepId}
                      className="h-full"
                      key={value} // Force re-render with animation when workflow changes
                    />
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center p-8">
                    <div className="text-center max-w-sm">
                      <AlertCircle className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-600">
                        {isValid
                          ? 'Enter a valid workflow to see the graph'
                          : 'Fix validation errors to see the graph'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Tabs.Content>
        </div>
      </Tabs.Root>
    </div>
  );
});

WorkflowVisualEditor.displayName = 'WorkflowVisualEditor';

export default WorkflowVisualEditor;

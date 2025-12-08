import { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import Editor, { type OnMount, type OnChange } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import { AlertCircle } from 'lucide-react';

interface JSONEditorProps {
  value: string;
  onChange: (value: string) => void;
  onValidate?: (isValid: boolean, errors: string[]) => void;
  readOnly?: boolean;
  height?: string;
  agentNames?: string[];
  className?: string;
  validateSchema?: boolean; // Whether to validate against workflow schema
}

export interface JSONEditorRef {
  highlightLines: (lineNumbers: number[], duration?: number) => void;
  getEditor: () => editor.IStandaloneCodeEditor | null;
}

const JSONEditor = forwardRef<JSONEditorRef, JSONEditorProps>(({
  value,
  onChange,
  onValidate,
  readOnly = false,
  height = '500px',
  agentNames = [],
  className = '',
  validateSchema = true, // Default to true for backward compatibility
}, ref) => {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const validationErrors = useRef<string[]>([]);
  const decorationsRef = useRef<string[]>([]);

  // Expose methods to parent components
  useImperativeHandle(ref, () => ({
    highlightLines: (lineNumbers: number[], duration: number = 2000) => {
      if (!editorRef.current) return;

      const editor = editorRef.current;

      // Create decorations for highlighted lines
      const newDecorations = lineNumbers.map(lineNumber => ({
        range: {
          startLineNumber: lineNumber,
          startColumn: 1,
          endLineNumber: lineNumber,
          endColumn: 1,
        },
        options: {
          isWholeLine: true,
          className: 'line-highlight',
          glyphMarginClassName: 'line-highlight-glyph',
        },
      }));

      // Apply decorations
      const decorationIds = editor.deltaDecorations(decorationsRef.current, newDecorations);
      decorationsRef.current = decorationIds;

      // Remove highlights after duration
      if (duration > 0) {
        setTimeout(() => {
          if (editorRef.current) {
            const clearedIds = editorRef.current.deltaDecorations(decorationsRef.current, []);
            decorationsRef.current = clearedIds;
          }
        }, duration);
      }
    },
    getEditor: () => editorRef.current,
  }));

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Configure JSON validation
    if (validateSchema) {
      monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
        validate: true,
        schemas: [
          {
            uri: 'http://workflow-schema',
            fileMatch: ['*'],
            schema: {
              type: 'object',
              properties: {
                name: {
                  type: 'string',
                  description: 'Workflow name',
                },
                version: {
                  type: 'string',
                  description: 'Workflow version',
                },
                start_step: {
                  type: 'string',
                  description: 'ID of the first step to execute',
                },
                steps: {
                  type: 'object',
                  description: 'Map of step IDs to step definitions',
                  additionalProperties: {
                    type: 'object',
                    properties: {
                      id: {
                        type: 'string',
                        description: 'Step identifier',
                      },
                      type: {
                        type: 'string',
                        description: 'Step type: agent, parallel, conditional, loop, or fork_join',
                        enum: ['agent', 'parallel', 'conditional', 'loop', 'fork_join'],
                      },
                      agent_name: {
                        type: 'string',
                        description: 'Name of the agent to execute this step (required for type=agent)',
                        enum: agentNames.length > 0 ? agentNames : undefined,
                      },
                      next_step: {
                        type: ['string', 'null'],
                        description: 'ID of the next step, or null if this is the final step',
                      },
                      input_mapping: {
                        type: 'object',
                        description: 'Mapping of input data for this step (required for type=agent)',
                      },
                      parallel_steps: {
                        type: 'array',
                        description: 'Array of step IDs to execute in parallel (required for type=parallel)',
                        items: {
                          type: 'string',
                        },
                        minItems: 2,
                      },
                      max_parallelism: {
                        type: 'number',
                        description: 'Maximum number of concurrent executions (optional for type=parallel)',
                        minimum: 1,
                      },
                      condition: {
                        type: 'object',
                        description: 'Condition to evaluate for branching (required for type=conditional)',
                        properties: {
                          expression: {
                            type: 'string',
                            description: 'The condition expression to evaluate',
                          },
                          operator: {
                            type: 'string',
                            description: 'Optional simple operator for basic comparisons',
                          },
                        },
                        required: ['expression'],
                      },
                      if_true_step: {
                        type: 'string',
                        description: 'Step ID to execute if condition is true (optional for type=conditional)',
                      },
                      if_false_step: {
                        type: 'string',
                        description: 'Step ID to execute if condition is false (optional for type=conditional)',
                      },
                      loop_config: {
                        type: 'object',
                        description: 'Loop configuration (required for type=loop)',
                        properties: {
                          collection: {
                            type: 'string',
                            description: 'Variable reference to array/list to iterate over',
                          },
                          loop_body: {
                            type: 'array',
                            description: 'Step IDs to execute for each item',
                            items: {
                              type: 'string',
                            },
                            minItems: 1,
                          },
                          execution_mode: {
                            type: 'string',
                            description: 'Execution mode: sequential or parallel',
                            enum: ['sequential', 'parallel'],
                          },
                          max_parallelism: {
                            type: 'number',
                            description: 'Maximum concurrent iterations (for parallel mode)',
                            minimum: 1,
                          },
                          max_iterations: {
                            type: 'number',
                            description: 'Maximum number of items to process',
                            minimum: 1,
                          },
                          on_error: {
                            type: 'string',
                            description: 'Error handling policy',
                            enum: ['stop', 'continue', 'collect'],
                          },
                        },
                        required: ['collection', 'loop_body'],
                      },
                      fork_join_config: {
                        type: 'object',
                        description: 'Fork-join configuration (required for type=fork_join)',
                        properties: {
                          branches: {
                            type: 'object',
                            description: 'Named branches to execute in parallel',
                            additionalProperties: {
                              type: 'object',
                              properties: {
                                steps: {
                                  type: 'array',
                                  description: 'Step IDs to execute in this branch',
                                  items: {
                                    type: 'string',
                                  },
                                  minItems: 1,
                                },
                                timeout_seconds: {
                                  type: 'number',
                                  description: 'Optional timeout for this branch',
                                  minimum: 1,
                                },
                              },
                              required: ['steps'],
                            },
                            minProperties: 2,
                          },
                          join_policy: {
                            type: 'string',
                            description: 'Policy for determining when to proceed after branches complete',
                            enum: ['all', 'any', 'majority', 'n_of_m'],
                          },
                          n_required: {
                            type: 'number',
                            description: 'Number of branches required to succeed (for join_policy=n_of_m)',
                            minimum: 1,
                          },
                          branch_timeout_seconds: {
                            type: 'number',
                            description: 'Default timeout for all branches',
                            minimum: 1,
                          },
                        },
                        required: ['branches'],
                      },
                    },
                    required: ['id'],
                    // Note: agent_name and input_mapping are conditionally required based on type
                    // Monaco doesn't support conditional schemas well, so we handle this in custom validation
                  },
                },
              },
              required: ['start_step', 'steps'],
            },
          },
        ],
      });
    } else {
      // For non-workflow JSON (like input data), accept any valid JSON object
      // Use a permissive schema that allows any properties
      monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
        validate: true,
        allowComments: false,
        schemas: [
          {
            uri: 'http://any-json-schema',
            fileMatch: ['*'],
            schema: {
              type: 'object',
              additionalProperties: true, // Allow any properties
            },
          },
        ],
      });
    }

    // Set up auto-completion for agent names
    if (agentNames.length > 0) {
      monaco.languages.registerCompletionItemProvider('json', {
        provideCompletionItems: (model, position) => {
          const textUntilPosition = model.getValueInRange({
            startLineNumber: 1,
            startColumn: 1,
            endLineNumber: position.lineNumber,
            endColumn: position.column,
          });

          const word = model.getWordUntilPosition(position);
          const range = {
            startLineNumber: position.lineNumber,
            endLineNumber: position.lineNumber,
            startColumn: word.startColumn,
            endColumn: word.endColumn,
          };

          // Check if we're in an agent_name field
          if (textUntilPosition.includes('"agent_name"')) {
            const suggestions = agentNames.map((name) => ({
              label: name,
              kind: monaco.languages.CompletionItemKind.Value,
              insertText: `"${name}"`,
              documentation: `Agent: ${name}`,
              range,
            }));

            return { suggestions };
          }

          return { suggestions: [] };
        },
      });
    }
  };

  const handleEditorChange: OnChange = (value) => {
    if (value !== undefined) {
      onChange(value);
      validateJSON(value);
    }
  };

  const validateJSON = (jsonString: string) => {
    const errors: string[] = [];
    let isValid = true;

    try {
      if (!jsonString.trim()) {
        errors.push('JSON cannot be empty');
        isValid = false;
      } else {
        const parsed = JSON.parse(jsonString);

        // Only validate workflow schema if validateSchema is true
        if (validateSchema) {
          // Custom validation rules for workflow definitions
          if (!parsed.start_step) {
            errors.push('Missing required field: start_step');
            isValid = false;
          }

          if (!parsed.steps || typeof parsed.steps !== 'object') {
            errors.push('Missing or invalid field: steps');
            isValid = false;
          } else {
            // Validate that start_step exists in steps
            if (!parsed.steps[parsed.start_step]) {
              errors.push(`start_step "${parsed.start_step}" not found in steps`);
              isValid = false;
            }

            // Validate each step
            Object.entries(parsed.steps).forEach(([stepId, step]: [string, any]) => {
              if (!step.id) {
                errors.push(`Step "${stepId}" is missing required field: id`);
                isValid = false;
              }

              const stepType = step.type || 'agent';

              // Validate based on step type
              if (stepType === 'parallel') {
                // Parallel step validation
                if (!step.parallel_steps || !Array.isArray(step.parallel_steps)) {
                  errors.push(`Parallel step "${stepId}" is missing required field: parallel_steps (array)`);
                  isValid = false;
                } else if (step.parallel_steps.length < 2) {
                  errors.push(`Parallel step "${stepId}" must have at least 2 parallel_steps`);
                  isValid = false;
                } else {
                  // Validate that all parallel_steps exist
                  step.parallel_steps.forEach((parallelStepId: string) => {
                    if (!parsed.steps[parallelStepId]) {
                      errors.push(`Parallel step "${stepId}" references non-existent step: "${parallelStepId}"`);
                      isValid = false;
                    }
                  });
                }

                // Validate max_parallelism if present
                if (step.max_parallelism !== undefined) {
                  if (typeof step.max_parallelism !== 'number' || step.max_parallelism < 1) {
                    errors.push(`Parallel step "${stepId}" has invalid max_parallelism (must be a number >= 1)`);
                    isValid = false;
                  }
                }
              } else if (stepType === 'conditional') {
                // Conditional step validation
                if (!step.condition || typeof step.condition !== 'object') {
                  errors.push(`Conditional step "${stepId}" is missing required field: condition (object)`);
                  isValid = false;
                } else if (!step.condition.expression) {
                  errors.push(`Conditional step "${stepId}" condition is missing required field: expression`);
                  isValid = false;
                }

                // At least one branch must be specified
                if (!step.if_true_step && !step.if_false_step) {
                  errors.push(`Conditional step "${stepId}" must have at least one of if_true_step or if_false_step`);
                  isValid = false;
                }

                // Validate branch references if present
                if (step.if_true_step && !parsed.steps[step.if_true_step]) {
                  errors.push(`Conditional step "${stepId}" references non-existent if_true_step: "${step.if_true_step}"`);
                  isValid = false;
                }
                if (step.if_false_step && !parsed.steps[step.if_false_step]) {
                  errors.push(`Conditional step "${stepId}" references non-existent if_false_step: "${step.if_false_step}"`);
                  isValid = false;
                }
              } else if (stepType === 'loop') {
                // Loop step validation
                if (!step.loop_config || typeof step.loop_config !== 'object') {
                  errors.push(`Loop step "${stepId}" is missing required field: loop_config (object)`);
                  isValid = false;
                } else {
                  // Validate collection
                  if (!step.loop_config.collection) {
                    errors.push(`Loop step "${stepId}" loop_config is missing required field: collection`);
                    isValid = false;
                  }

                  // Validate loop_body
                  if (!step.loop_config.loop_body || !Array.isArray(step.loop_config.loop_body)) {
                    errors.push(`Loop step "${stepId}" loop_config is missing required field: loop_body (array)`);
                    isValid = false;
                  } else if (step.loop_config.loop_body.length < 1) {
                    errors.push(`Loop step "${stepId}" loop_body must have at least 1 step`);
                    isValid = false;
                  } else {
                    // Validate that all loop_body steps exist
                    step.loop_config.loop_body.forEach((loopStepId: string) => {
                      if (!parsed.steps[loopStepId]) {
                        errors.push(`Loop step "${stepId}" references non-existent loop_body step: "${loopStepId}"`);
                        isValid = false;
                      }
                    });
                  }

                  // Validate execution_mode if present
                  if (step.loop_config.execution_mode !== undefined) {
                    if (!['sequential', 'parallel'].includes(step.loop_config.execution_mode)) {
                      errors.push(`Loop step "${stepId}" has invalid execution_mode (must be 'sequential' or 'parallel')`);
                      isValid = false;
                    }
                  }

                  // Validate max_parallelism if present
                  if (step.loop_config.max_parallelism !== undefined) {
                    if (typeof step.loop_config.max_parallelism !== 'number' || step.loop_config.max_parallelism < 1) {
                      errors.push(`Loop step "${stepId}" has invalid max_parallelism (must be a number >= 1)`);
                      isValid = false;
                    }
                  }

                  // Validate max_iterations if present
                  if (step.loop_config.max_iterations !== undefined) {
                    if (typeof step.loop_config.max_iterations !== 'number' || step.loop_config.max_iterations < 1) {
                      errors.push(`Loop step "${stepId}" has invalid max_iterations (must be a number >= 1)`);
                      isValid = false;
                    }
                  }

                  // Validate on_error if present
                  if (step.loop_config.on_error !== undefined) {
                    if (!['stop', 'continue', 'collect'].includes(step.loop_config.on_error)) {
                      errors.push(`Loop step "${stepId}" has invalid on_error (must be 'stop', 'continue', or 'collect')`);
                      isValid = false;
                    }
                  }
                }
              } else if (stepType === 'fork_join') {
                // Fork-join step validation
                if (!step.fork_join_config || typeof step.fork_join_config !== 'object') {
                  errors.push(`Fork-join step "${stepId}" is missing required field: fork_join_config (object)`);
                  isValid = false;
                } else {
                  // Validate branches
                  if (!step.fork_join_config.branches || typeof step.fork_join_config.branches !== 'object') {
                    errors.push(`Fork-join step "${stepId}" fork_join_config is missing required field: branches (object)`);
                    isValid = false;
                  } else {
                    const branchCount = Object.keys(step.fork_join_config.branches).length;
                    if (branchCount < 2) {
                      errors.push(`Fork-join step "${stepId}" must have at least 2 branches`);
                      isValid = false;
                    }

                    // Validate each branch
                    Object.entries(step.fork_join_config.branches).forEach(([branchName, branch]: [string, any]) => {
                      if (!branch.steps || !Array.isArray(branch.steps)) {
                        errors.push(`Fork-join step "${stepId}" branch "${branchName}" is missing required field: steps (array)`);
                        isValid = false;
                      } else if (branch.steps.length < 1) {
                        errors.push(`Fork-join step "${stepId}" branch "${branchName}" must have at least 1 step`);
                        isValid = false;
                      } else {
                        // Validate that all branch steps exist
                        branch.steps.forEach((branchStepId: string) => {
                          if (!parsed.steps[branchStepId]) {
                            errors.push(`Fork-join step "${stepId}" branch "${branchName}" references non-existent step: "${branchStepId}"`);
                            isValid = false;
                          }
                        });
                      }

                      // Validate timeout_seconds if present
                      if (branch.timeout_seconds !== undefined) {
                        if (typeof branch.timeout_seconds !== 'number' || branch.timeout_seconds < 1) {
                          errors.push(`Fork-join step "${stepId}" branch "${branchName}" has invalid timeout_seconds (must be a number >= 1)`);
                          isValid = false;
                        }
                      }
                    });
                  }

                  // Validate join_policy if present
                  if (step.fork_join_config.join_policy !== undefined) {
                    if (!['all', 'any', 'majority', 'n_of_m'].includes(step.fork_join_config.join_policy)) {
                      errors.push(`Fork-join step "${stepId}" has invalid join_policy (must be 'all', 'any', 'majority', or 'n_of_m')`);
                      isValid = false;
                    }

                    // Validate n_required for n_of_m policy
                    if (step.fork_join_config.join_policy === 'n_of_m') {
                      if (step.fork_join_config.n_required === undefined) {
                        errors.push(`Fork-join step "${stepId}" with join_policy='n_of_m' must specify n_required`);
                        isValid = false;
                      } else if (typeof step.fork_join_config.n_required !== 'number' || step.fork_join_config.n_required < 1) {
                        errors.push(`Fork-join step "${stepId}" has invalid n_required (must be a number >= 1)`);
                        isValid = false;
                      } else if (step.fork_join_config.branches) {
                        const branchCount = Object.keys(step.fork_join_config.branches).length;
                        if (step.fork_join_config.n_required > branchCount) {
                          errors.push(`Fork-join step "${stepId}" n_required (${step.fork_join_config.n_required}) cannot be greater than number of branches (${branchCount})`);
                          isValid = false;
                        }
                      }
                    }
                  }

                  // Validate branch_timeout_seconds if present
                  if (step.fork_join_config.branch_timeout_seconds !== undefined) {
                    if (typeof step.fork_join_config.branch_timeout_seconds !== 'number' || step.fork_join_config.branch_timeout_seconds < 1) {
                      errors.push(`Fork-join step "${stepId}" has invalid branch_timeout_seconds (must be a number >= 1)`);
                      isValid = false;
                    }
                  }
                }
              } else {
                // Agent step validation (default)
                if (!step.agent_name) {
                  errors.push(`Step "${stepId}" is missing required field: agent_name`);
                  isValid = false;
                }
                if (step.input_mapping === undefined) {
                  errors.push(`Step "${stepId}" is missing required field: input_mapping`);
                  isValid = false;
                }

                // Warn if agent name is not in the list
                if (agentNames.length > 0 && step.agent_name && !agentNames.includes(step.agent_name)) {
                  errors.push(`Warning: Agent "${step.agent_name}" in step "${stepId}" is not registered`);
                }
              }

              // Validate next_step reference (applies to all step types)
              if (step.next_step && !parsed.steps[step.next_step]) {
                errors.push(`Step "${stepId}" references non-existent next_step: "${step.next_step}"`);
                isValid = false;
              }
          });

          // Check for circular dependencies
          const visited = new Set<string>();
          const checkCircular = (stepId: string, path: Set<string>): boolean => {
            if (path.has(stepId)) {
              errors.push(`Circular dependency detected: ${Array.from(path).join(' -> ')} -> ${stepId}`);
              return false;
            }
            if (visited.has(stepId)) return true;

            visited.add(stepId);
            path.add(stepId);

            const step = parsed.steps[stepId];
            if (step?.next_step) {
              checkCircular(step.next_step, new Set(path));
            }

            path.delete(stepId);
            return true;
          };

          if (parsed.start_step) {
            checkCircular(parsed.start_step, new Set());
          }
        }
        }
        // If validateSchema is false, we only check for valid JSON syntax (no additional validation)
      }
    } catch (error) {
      if (error instanceof SyntaxError) {
        errors.push(`JSON Syntax Error: ${error.message}`);
      } else {
        errors.push('Invalid JSON format');
      }
      isValid = false;
    }

    validationErrors.current = errors;
    onValidate?.(isValid, errors);
  };

  // Validate on mount
  useEffect(() => {
    if (value) {
      validateJSON(value);
    }
  }, []);

  return (
    <div 
      className={`w-full ${className}`} 
      style={{ 
        height: height,
        minHeight: height === '100%' ? '100%' : undefined,
      }}
    >
      <Editor
        height="100%"
        defaultLanguage="json"
        value={value}
        onChange={handleEditorChange}
        onMount={handleEditorDidMount}
        theme="vs-light"
        options={{
          readOnly,
          minimap: { enabled: true },
          scrollBeyondLastLine: false,
          fontSize: 14,
          lineNumbers: 'on',
          renderLineHighlight: 'all',
          automaticLayout: true,
          formatOnPaste: true,
          formatOnType: true,
          tabSize: 2,
          wordWrap: 'on',
          folding: true,
          bracketPairColorization: {
            enabled: true,
          },
        }}
        loading={
          <div className="flex items-center justify-center h-full bg-gray-50">
            <div className="text-gray-500">Loading editor...</div>
          </div>
        }
      />
    </div>
  );
});

JSONEditor.displayName = 'JSONEditor';

export default JSONEditor;

// Separate component for displaying validation errors
interface ValidationErrorsProps {
  errors: string[];
}

export function ValidationErrors({ errors }: ValidationErrorsProps) {
  if (errors.length === 0) return null;

  return (
    <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <div className="flex items-start gap-2">
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-red-900 mb-2">Validation Errors</h4>
          <ul className="space-y-1">
            {errors.map((error, index) => (
              <li key={index} className="text-sm text-red-700">
                • {error}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

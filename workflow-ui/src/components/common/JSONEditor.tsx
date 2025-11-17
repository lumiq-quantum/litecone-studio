import { useRef, useEffect } from 'react';
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

export default function JSONEditor({
  value,
  onChange,
  onValidate,
  readOnly = false,
  height = '500px',
  agentNames = [],
  className = '',
  validateSchema = true, // Default to true for backward compatibility
}: JSONEditorProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const validationErrors = useRef<string[]>([]);

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
                      agent_name: {
                        type: 'string',
                        description: 'Name of the agent to execute this step',
                        enum: agentNames.length > 0 ? agentNames : undefined,
                      },
                      next_step: {
                        type: ['string', 'null'],
                        description: 'ID of the next step, or null if this is the final step',
                      },
                      input_mapping: {
                        type: 'object',
                        description: 'Mapping of input data for this step',
                      },
                    },
                    required: ['id', 'agent_name', 'input_mapping'],
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
              if (!step.agent_name) {
                errors.push(`Step "${stepId}" is missing required field: agent_name`);
                isValid = false;
              }
              if (step.input_mapping === undefined) {
                errors.push(`Step "${stepId}" is missing required field: input_mapping`);
                isValid = false;
              }

              // Validate next_step reference
              if (step.next_step && !parsed.steps[step.next_step]) {
                errors.push(`Step "${stepId}" references non-existent next_step: "${step.next_step}"`);
                isValid = false;
              }

            // Warn if agent name is not in the list
            if (agentNames.length > 0 && step.agent_name && !agentNames.includes(step.agent_name)) {
              errors.push(`Warning: Agent "${step.agent_name}" in step "${stepId}" is not registered`);
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
}

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

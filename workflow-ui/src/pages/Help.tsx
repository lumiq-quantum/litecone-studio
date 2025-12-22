import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  FileJson,
  GitBranch,
  Play,
  AlertCircle,
  CheckCircle,
  Code,
  ExternalLink,
  Lightbulb,
  Zap,
  GraduationCap,
} from 'lucide-react';
import { useTutorial } from '@/hooks/useTutorial';
import { showToast } from '@/lib/toast';

export default function Help() {
  const navigate = useNavigate();
  const { resetTutorial } = useTutorial();
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-blue-100 rounded-xl">
              <BookOpen className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Help & Documentation</h1>
              <p className="text-gray-600 mt-1">
                Learn how to create and manage workflows
              </p>
            </div>
          </div>
        </motion.div>

        {/* Quick Links */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        >
          <a
            href="#workflow-structure"
            className="p-4 bg-white rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all group"
          >
            <FileJson className="w-6 h-6 text-blue-600 mb-2" />
            <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
              Workflow Structure
            </h3>
            <p className="text-sm text-gray-600">Learn about workflow JSON format</p>
          </a>

          <a
            href="#step-configuration"
            className="p-4 bg-white rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all group"
          >
            <GitBranch className="w-6 h-6 text-blue-600 mb-2" />
            <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
              Step Configuration
            </h3>
            <p className="text-sm text-gray-600">Configure individual workflow steps</p>
          </a>

          <a
            href="#available-fields"
            className="p-4 bg-white rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all group"
          >
            <Code className="w-6 h-6 text-blue-600 mb-2" />
            <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
              Available Fields
            </h3>
            <p className="text-sm text-gray-600">Fields you can reference from agent outputs</p>
          </a>

          <a
            href="#best-practices"
            className="p-4 bg-white rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all group"
          >
            <Lightbulb className="w-6 h-6 text-blue-600 mb-2" />
            <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
              Best Practices
            </h3>
            <p className="text-sm text-gray-600">Tips for effective workflows</p>
          </a>
        </motion.div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Workflow Structure */}
          <motion.section
            id="workflow-structure"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <FileJson className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Workflow Structure</h2>
            </div>

            <div className="space-y-4">
              <p className="text-gray-700">
                A workflow is defined using JSON format with two main components:
              </p>

              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-2">Basic Structure</h3>
                <pre className="text-sm bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
{`{
  "start_step": "step_id",
  "steps": {
    "step_id": {
      "id": "step_id",
      "agent_name": "agent-name",
      "next_step": "next_step_id",
      "input_mapping": {
        "key": "value"
      }
    }
  }
}`}
                </pre>
              </div>

              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <Code className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-blue-900 mb-1">start_step</h4>
                    <p className="text-sm text-blue-700">
                      The ID of the first step to execute. Must match a key in the steps object.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <Code className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-blue-900 mb-1">steps</h4>
                    <p className="text-sm text-blue-700">
                      An object mapping step IDs to step definitions. Each step defines what agent to
                      call and how to map data.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.section>

          {/* Available Output Fields */}
          <motion.section
            id="available-fields"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <Code className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Available Output Fields</h2>
            </div>

            <div className="space-y-4">
              <p className="text-gray-700">
                When an agent completes execution, these fields are automatically available for input mapping in subsequent steps:
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900 mb-2">Always Available Fields</h3>
                  
                  <div className="border border-green-200 rounded-lg p-3 bg-green-50">
                    <code className="text-sm font-mono text-green-800">${`\${step_id.output.text}`}</code>
                    <p className="text-xs text-green-700 mt-1">Main text response from the agent</p>
                  </div>
                  
                  <div className="border border-green-200 rounded-lg p-3 bg-green-50">
                    <code className="text-sm font-mono text-green-800">${`\${step_id.output.response}`}</code>
                    <p className="text-xs text-green-700 mt-1">Agent's response message</p>
                  </div>
                  
                  <div className="border border-green-200 rounded-lg p-3 bg-green-50">
                    <code className="text-sm font-mono text-green-800">${`\${step_id.output.id}`}</code>
                    <p className="text-xs text-green-700 mt-1">Task/response identifier</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900 mb-2">Structured Data Fields</h3>
                  
                  <div className="border border-blue-200 rounded-lg p-3 bg-blue-50">
                    <code className="text-sm font-mono text-blue-800">${`\${step_id.output.artifacts}`}</code>
                    <p className="text-xs text-blue-700 mt-1">Output artifacts from agent</p>
                  </div>
                  
                  <div className="border border-blue-200 rounded-lg p-3 bg-blue-50">
                    <code className="text-sm font-mono text-blue-800">${`\${step_id.output.metadata}`}</code>
                    <p className="text-xs text-blue-700 mt-1">Agent-specific metadata</p>
                  </div>
                  
                  <div className="border border-blue-200 rounded-lg p-3 bg-blue-50">
                    <code className="text-sm font-mono text-blue-800">${`\${step_id.output.status}`}</code>
                    <p className="text-xs text-blue-700 mt-1">Execution status information</p>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-yellow-900 mb-1">Custom Agent Fields</h4>
                    <p className="text-sm text-yellow-700 mb-2">
                      Some agents may return additional custom fields. Use <code className="bg-yellow-100 px-1 rounded">text</code> or <code className="bg-yellow-100 px-1 rounded">response</code> if you're unsure what fields are available.
                    </p>
                    <p className="text-sm text-yellow-700">
                      <strong>Tip:</strong> Check the run details page after executing a workflow to see all available fields from each step.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">Example: Accessing Nested Fields</h4>
                <pre className="text-xs bg-gray-900 text-gray-100 p-3 rounded overflow-x-auto">
{`"input_mapping": {
  "main_content": "\${extract_data.output.text}",
  "completion_status": "\${extract_data.output.status.state}",
  "processing_time": "\${extract_data.output.metadata.processing_time}",
  "user_context": "\${workflow.input.user_id}"
}`}
                </pre>
              </div>
            </div>
          </motion.section>

          {/* Step Configuration */}
          <motion.section
            id="step-configuration"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <GitBranch className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Step Configuration</h2>
            </div>

            <div className="space-y-4">
              <p className="text-gray-700">Each step in a workflow has the following properties:</p>

              <div className="space-y-3">
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <code className="px-2 py-1 bg-gray-100 text-gray-900 rounded text-sm font-mono">
                      id
                    </code>
                    <span className="text-xs font-semibold text-red-600 uppercase">Required</span>
                  </div>
                  <p className="text-sm text-gray-700">
                    Unique identifier for the step. Must match the key in the steps object.
                  </p>
                  <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono text-gray-800">
                    "id": "fetch_data"
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <code className="px-2 py-1 bg-gray-100 text-gray-900 rounded text-sm font-mono">
                      agent_name
                    </code>
                    <span className="text-xs font-semibold text-red-600 uppercase">Required</span>
                  </div>
                  <p className="text-sm text-gray-700">
                    Name of the agent to execute this step. Must match a registered agent.
                  </p>
                  <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono text-gray-800">
                    "agent_name": "data-processor"
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <code className="px-2 py-1 bg-gray-100 text-gray-900 rounded text-sm font-mono">
                      next_step
                    </code>
                    <span className="text-xs font-semibold text-red-600 uppercase">Required</span>
                  </div>
                  <p className="text-sm text-gray-700">
                    ID of the next step to execute, or <code className="bg-gray-100 px-1 rounded">null</code> if this is the final step.
                  </p>
                  <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono text-gray-800">
                    "next_step": "process_data" // or null for final step
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <code className="px-2 py-1 bg-gray-100 text-gray-900 rounded text-sm font-mono">
                      input_mapping
                    </code>
                    <span className="text-xs font-semibold text-red-600 uppercase">Required</span>
                  </div>
                  <p className="text-sm text-gray-700 mb-2">
                    Object defining how to map data to the agent's input. Uses variable references with ${} syntax.
                  </p>
                  <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono text-gray-800">
{`"input_mapping": {
  "user_id": "\${workflow.input.user_id}",
  "data": "\${fetch_data.output.text}",
  "metadata": "\${fetch_data.output.metadata}"
}`}
                  </div>
                  <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
                    <p className="text-xs text-blue-700">
                      <strong>Variable Reference Syntax:</strong>
                      <br />• <code className="bg-blue-100 px-1 rounded">${`\${workflow.input.*}`}</code> - Access workflow input data
                      <br />• <code className="bg-blue-100 px-1 rounded">${`\${step_id.output.*}`}</code> - Access previous step output
                      <br />• <code className="bg-blue-100 px-1 rounded">${`\${step_id.output.text}`}</code> - Main text response (always available)
                      <br />• <code className="bg-blue-100 px-1 rounded">${`\${step_id.output.response}`}</code> - Agent response message (always available)
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.section>

          {/* Example Workflow */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <Play className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Complete Example</h2>
            </div>

            <div className="space-y-4">
              <p className="text-gray-700">
                Here's a complete example of a three-step workflow:
              </p>

              <pre className="text-sm bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
{`{
  "start_step": "fetch_user",
  "steps": {
    "fetch_user": {
      "id": "fetch_user",
      "agent_name": "user-service",
      "next_step": "enrich_data",
      "input_mapping": {
        "user_id": "\${workflow.input.user_id}"
      }
    },
    "enrich_data": {
      "id": "enrich_data",
      "agent_name": "data-enricher",
      "next_step": "send_notification",
      "input_mapping": {
        "user_data": "\${fetch_user.output.text}",
        "user_metadata": "\${fetch_user.output.metadata}",
        "source": "\${workflow.input.data_source}"
      }
    },
    "send_notification": {
      "id": "send_notification",
      "agent_name": "notification-service",
      "next_step": null,
      "input_mapping": {
        "recipient_info": "\${fetch_user.output.response}",
        "enriched_message": "\${enrich_data.output.text}",
        "notification_type": "\${workflow.input.notification_type}"
      }
    }
  }
}`}
              </pre>
            </div>
          </motion.section>

          {/* Best Practices */}
          <motion.section
            id="best-practices"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <Lightbulb className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Best Practices</h2>
            </div>

            <div className="space-y-3">
              <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg border border-green-200">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-green-900 mb-1">Use Descriptive Step IDs</h4>
                  <p className="text-sm text-green-700">
                    Choose clear, descriptive names like "fetch_user_data" instead of "step1".
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg border border-green-200">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-green-900 mb-1">Keep Steps Focused</h4>
                  <p className="text-sm text-green-700">
                    Each step should do one thing well. Break complex operations into multiple steps.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg border border-green-200">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-green-900 mb-1">Test with Templates</h4>
                  <p className="text-sm text-green-700">
                    Start with a template and customize it to your needs. This ensures proper structure.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-yellow-900 mb-1">Avoid Circular Dependencies</h4>
                  <p className="text-sm text-yellow-700">
                    Ensure your workflow has a clear start and end. Don't create loops with next_step.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-yellow-900 mb-1">Verify Agent Names</h4>
                  <p className="text-sm text-yellow-700">
                    Make sure all agent names in your workflow match registered agents.
                  </p>
                </div>
              </div>
            </div>
          </motion.section>

          {/* Additional Resources */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-gradient-to-r from-primary-50 to-purple-50 rounded-xl border border-primary-200 p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <Zap className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Additional Resources</h2>
            </div>

            <div className="space-y-3">
              <a
                href="/workflows/create"
                className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all group"
              >
                <div className="flex items-center gap-3">
                  <FileJson className="w-5 h-5 text-blue-600" />
                  <div>
                    <h4 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                      Create Your First Workflow
                    </h4>
                    <p className="text-sm text-gray-600">Start building with templates</p>
                  </div>
                </div>
                <ExternalLink className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors" />
              </a>

              <a
                href="/agents"
                className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all group"
              >
                <div className="flex items-center gap-3">
                  <GitBranch className="w-5 h-5 text-blue-600" />
                  <div>
                    <h4 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                      Manage Agents
                    </h4>
                    <p className="text-sm text-gray-600">View and configure available agents</p>
                  </div>
                </div>
                <ExternalLink className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors" />
              </a>

              <button
                onClick={() => {
                  resetTutorial();
                  showToast.success('Tutorial reset! Visit the workflow creation page to see it again.');
                  navigate('/workflows/create');
                }}
                className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all group w-full text-left"
              >
                <div className="flex items-center gap-3">
                  <GraduationCap className="w-5 h-5 text-blue-600" />
                  <div>
                    <h4 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                      Restart Tutorial
                    </h4>
                    <p className="text-sm text-gray-600">See the onboarding tutorial again</p>
                  </div>
                </div>
                <ExternalLink className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors" />
              </button>
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );
}

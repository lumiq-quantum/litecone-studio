import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Save, FileJson, Sparkles } from 'lucide-react';
import { useCreateWorkflow } from '@/hooks/useWorkflows';
import { useAgents } from '@/hooks/useAgents';
import { useTutorial } from '@/hooks/useTutorial';
import { WorkflowVisualEditor, TemplateGallery } from '@/components/workflows';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import OnboardingTutorial from '@/components/common/OnboardingTutorial';
import { showToast } from '@/lib/toast';
import type { WorkflowCreate } from '@/types';
import type { WorkflowTemplate } from '@/data/workflowTemplates';

const DEFAULT_WORKFLOW_JSON = {
  start_step: 'step1',
  steps: {
    step1: {
      id: 'step1',
      agent_name: 'example-agent',
      next_step: null,
      input_mapping: {
        input_key: 'input_value',
      },
    },
  },
};

const tutorialSteps = [
  {
    title: 'Welcome to Workflow Creation!',
    description:
      'This tutorial will guide you through creating your first workflow. Workflows are sequences of steps that execute agents in order to accomplish a task.',
    highlight:
      'Workflows help you automate complex processes by chaining together multiple agents.',
  },
  {
    title: 'Start with a Template',
    description:
      'The easiest way to create a workflow is to start with a template. Click the "Use Template" button to browse pre-built workflow examples.',
    action: 'Click "Use Template" in the top-right corner to see available templates.',
  },
  {
    title: 'Define Your Workflow',
    description:
      'Workflows are defined in JSON format with two main parts: start_step (which step to begin with) and steps (the actual workflow steps).',
    highlight:
      'Each step specifies an agent to call, input data mapping, and which step comes next.',
  },
  {
    title: 'Visual Preview',
    description:
      'As you edit the JSON, you can see a visual representation of your workflow in the graph view. This helps you understand the flow and catch errors.',
    action: 'Try switching between JSON Editor, Visual Graph, and Split View tabs.',
  },
  {
    title: 'Validation & Help',
    description:
      'The editor validates your JSON in real-time and highlights errors. If you need help with the structure, check the documentation link below the editor.',
    action: 'Click "View Full Documentation" to learn more about workflow structure.',
  },
  {
    title: "You're Ready!",
    description:
      'Now you know the basics of creating workflows. Start by choosing a template or writing your own JSON. Good luck!',
    highlight: 'Remember: you can always access help from the sidebar navigation.',
  },
];

export default function WorkflowCreate() {
  const navigate = useNavigate();
  const createMutation = useCreateWorkflow();
  const { data: agentsData } = useAgents();
  const { showTutorial, tutorialCompleted, startTutorial, completeTutorial, skipTutorial } =
    useTutorial();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [workflowJson, setWorkflowJson] = useState(JSON.stringify(DEFAULT_WORKFLOW_JSON, null, 2));
  const [isValid, setIsValid] = useState(true);
  const [showTemplateGallery, setShowTemplateGallery] = useState(false);

  const agentNames = agentsData?.items?.map((agent) => agent.name) || [];

  // Show tutorial on first visit
  useEffect(() => {
    if (!tutorialCompleted) {
      const timer = setTimeout(() => {
        startTutorial();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [tutorialCompleted, startTutorial]);

  const handleSelectTemplate = (template: WorkflowTemplate) => {
    setWorkflowJson(JSON.stringify(template.workflowData, null, 2));
    if (!name) {
      setName(template.name);
    }
    if (!description) {
      setDescription(template.description);
    }
    showToast.success(`Template "${template.name}" loaded`);
  };

  const handleValidate = (valid: boolean) => {
    setIsValid(valid);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      showToast.error('Workflow name is required');
      return;
    }

    if (!isValid) {
      showToast.error('Please fix validation errors before saving');
      return;
    }

    try {
      const workflowData = JSON.parse(workflowJson);
      
      const payload: WorkflowCreate = {
        name: name.trim(),
        description: description.trim() || undefined,
        start_step: workflowData.start_step,
        steps: workflowData.steps,
      };

      const newWorkflow = await createMutation.mutateAsync(payload);
      showToast.success('Workflow created successfully');
      navigate(`/workflows/${newWorkflow.id}`);
    } catch (error) {
      if (error instanceof SyntaxError) {
        showToast.error('Invalid JSON format');
      } else {
        showToast.error('Failed to create workflow');
      }
    }
  };

  const handleCancel = () => {
    navigate('/workflows');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <button
            onClick={handleCancel}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Workflows
          </button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Workflow</h1>
              <p className="text-gray-600">Define a new workflow with steps and agents</p>
            </div>
            <button
              onClick={() => setShowTemplateGallery(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-primary-200 rounded-lg transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              Use Template
            </button>
          </div>
        </motion.div>

        {/* Form */}
        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          onSubmit={handleSubmit}
          className="space-y-6"
        >
          {/* Basic Information Card */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
            
            <div className="space-y-4">
              {/* Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  Workflow Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., User Onboarding Flow"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what this workflow does..."
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                />
              </div>
            </div>
          </div>

          {/* Workflow Definition Card */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Workflow Definition</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Define the workflow steps and their connections in JSON format
                </p>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <FileJson className="w-4 h-4 text-gray-400" />
                <span className={`font-medium ${isValid ? 'text-green-600' : 'text-red-600'}`}>
                  {isValid ? 'Valid JSON' : 'Invalid JSON'}
                </span>
              </div>
            </div>

            <WorkflowVisualEditor
              value={workflowJson}
              onChange={setWorkflowJson}
              onValidate={handleValidate}
              agentNames={agentNames}
              height="600px"
            />

            {/* Help Text */}
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-semibold text-blue-900">JSON Structure Guide</h4>
                <a
                  href="/help"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-medium text-blue-700 hover:text-blue-900 underline"
                >
                  View Full Documentation →
                </a>
              </div>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• <code className="bg-blue-100 px-1 rounded">start_step</code>: ID of the first step to execute</li>
                <li>• <code className="bg-blue-100 px-1 rounded">steps</code>: Object mapping step IDs to step definitions</li>
                <li>• Each step must have: <code className="bg-blue-100 px-1 rounded">id</code>, <code className="bg-blue-100 px-1 rounded">agent_name</code>, <code className="bg-blue-100 px-1 rounded">next_step</code>, <code className="bg-blue-100 px-1 rounded">input_mapping</code></li>
                <li>• Set <code className="bg-blue-100 px-1 rounded">next_step</code> to <code className="bg-blue-100 px-1 rounded">null</code> for the final step</li>
              </ul>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-4">
            <button
              type="button"
              onClick={handleCancel}
              disabled={createMutation.isPending}
              className="px-6 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending || !isValid || !name.trim()}
              className="flex items-center gap-2 px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {createMutation.isPending ? (
                <>
                  <LoadingSpinner size="sm" className="text-white" />
                  Creating...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  Create Workflow
                </>
              )}
            </button>
          </div>
        </motion.form>
      </div>

      {/* Template Gallery Modal */}
      {showTemplateGallery && (
        <TemplateGallery
          onSelectTemplate={handleSelectTemplate}
          onClose={() => setShowTemplateGallery(false)}
        />
      )}

      {/* Onboarding Tutorial */}
      <OnboardingTutorial
        steps={tutorialSteps}
        show={showTutorial}
        onComplete={completeTutorial}
        onSkip={skipTutorial}
      />
    </div>
  );
}

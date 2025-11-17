import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowRight,
  Cloud,
  Database,
  Brain,
  Bell,
  X,
  FileJson,
  Sparkles,
  Filter,
} from 'lucide-react';
import { workflowTemplates, type WorkflowTemplate } from '@/data/workflowTemplates';

interface TemplateGalleryProps {
  onSelectTemplate: (template: WorkflowTemplate) => void;
  onClose: () => void;
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  ArrowRight,
  Cloud,
  Database,
  Brain,
  Bell,
};

const categoryLabels: Record<WorkflowTemplate['category'], string> = {
  'data-processing': 'Data Processing',
  'api-integration': 'API Integration',
  'automation': 'Automation',
  'ml-pipeline': 'ML Pipeline',
};

const difficultyColors: Record<WorkflowTemplate['difficulty'], { bg: string; text: string; border: string }> = {
  beginner: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-200' },
  intermediate: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-200' },
  advanced: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-200' },
};

export default function TemplateGallery({ onSelectTemplate, onClose }: TemplateGalleryProps) {
  const [selectedCategory, setSelectedCategory] = useState<WorkflowTemplate['category'] | 'all'>('all');
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);

  const filteredTemplates =
    selectedCategory === 'all'
      ? workflowTemplates
      : workflowTemplates.filter((t) => t.category === selectedCategory);

  const handleSelectTemplate = (template: WorkflowTemplate) => {
    setSelectedTemplate(template);
  };

  const handleUseTemplate = () => {
    if (selectedTemplate) {
      onSelectTemplate(selectedTemplate);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-200 bg-gradient-to-r from-primary-50 to-purple-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Sparkles className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Workflow Templates</h2>
                <p className="text-sm text-gray-600 mt-0.5">
                  Choose a template to get started quickly
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Category Filter */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Category:</span>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setSelectedCategory('all')}
                className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                  selectedCategory === 'all'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                }`}
              >
                All Templates
              </button>
              {Object.entries(categoryLabels).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setSelectedCategory(key as WorkflowTemplate['category'])}
                  className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                    selectedCategory === key
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Template List */}
          <div className="w-1/2 border-r border-gray-200 overflow-y-auto p-6">
            <div className="space-y-3">
              <AnimatePresence mode="popLayout">
                {filteredTemplates.map((template) => {
                  const Icon = iconMap[template.icon] || ArrowRight;
                  const difficultyStyle = difficultyColors[template.difficulty];
                  const isSelected = selectedTemplate?.id === template.id;

                  return (
                    <motion.button
                      key={template.id}
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      onClick={() => handleSelectTemplate(template)}
                      className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                        isSelected
                          ? 'border-primary-500 bg-blue-50 shadow-md'
                          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={`p-2 rounded-lg ${
                            isSelected ? 'bg-blue-100' : 'bg-gray-100'
                          }`}
                        >
                          <Icon
                            className={`w-5 h-5 ${
                              isSelected ? 'text-blue-600' : 'text-gray-600'
                            }`}
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-gray-900">{template.name}</h3>
                            <span
                              className={`px-2 py-0.5 text-xs font-medium rounded-full ${difficultyStyle.bg} ${difficultyStyle.text} ${difficultyStyle.border} border`}
                            >
                              {template.difficulty}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 line-clamp-2">
                            {template.description}
                          </p>
                          <div className="mt-2 flex items-center gap-2">
                            <span className="text-xs text-gray-500">
                              {categoryLabels[template.category]}
                            </span>
                            <span className="text-xs text-gray-400">•</span>
                            <span className="text-xs text-gray-500">
                              {Object.keys(template.workflowData.steps).length} steps
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.button>
                  );
                })}
              </AnimatePresence>
            </div>
          </div>

          {/* Template Preview */}
          <div className="w-1/2 overflow-y-auto p-6 bg-gray-50">
            {selectedTemplate ? (
              <motion.div
                key={selectedTemplate.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-4"
              >
                {/* Template Info */}
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex items-start gap-3 mb-4">
                    {(() => {
                      const Icon = iconMap[selectedTemplate.icon] || ArrowRight;
                      return (
                        <div className="p-3 bg-blue-100 rounded-lg">
                          <Icon className="w-6 h-6 text-blue-600" />
                        </div>
                      );
                    })()}
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-900 mb-1">
                        {selectedTemplate.name}
                      </h3>
                      <p className="text-sm text-gray-600">{selectedTemplate.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-gray-500">Category:</span>
                      <span className="text-xs font-semibold text-gray-900">
                        {categoryLabels[selectedTemplate.category]}
                      </span>
                    </div>
                    <span className="text-gray-300">•</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-gray-500">Difficulty:</span>
                      <span
                        className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                          difficultyColors[selectedTemplate.difficulty].bg
                        } ${difficultyColors[selectedTemplate.difficulty].text}`}
                      >
                        {selectedTemplate.difficulty}
                      </span>
                    </div>
                    <span className="text-gray-300">•</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-gray-500">Steps:</span>
                      <span className="text-xs font-semibold text-gray-900">
                        {Object.keys(selectedTemplate.workflowData.steps).length}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Workflow Structure */}
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <FileJson className="w-4 h-4 text-gray-500" />
                    <h4 className="text-sm font-semibold text-gray-900">Workflow Structure</h4>
                  </div>
                  <div className="space-y-2">
                    {Object.values(selectedTemplate.workflowData.steps).map((step: any, index) => (
                      <div
                        key={step.id}
                        className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-700 rounded-full text-xs font-bold">
                          {index + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900">{step.id}</div>
                          <div className="text-xs text-gray-500">Agent: {step.agent_name}</div>
                        </div>
                        {step.next_step && (
                          <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* JSON Preview */}
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <FileJson className="w-4 h-4 text-gray-500" />
                    <h4 className="text-sm font-semibold text-gray-900">JSON Preview</h4>
                  </div>
                  <pre className="text-xs bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                    {JSON.stringify(selectedTemplate.workflowData, null, 2)}
                  </pre>
                </div>
              </motion.div>
            ) : (
              <div className="h-full flex items-center justify-center text-center">
                <div>
                  <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">Select a template to preview</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} available
          </p>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleUseTemplate}
              disabled={!selectedTemplate}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              Use Template
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

/**
 * Workflow Templates
 * Pre-defined workflow templates to help users get started quickly
 */

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: 'data-processing' | 'api-integration' | 'automation' | 'ml-pipeline';
  icon: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  workflowData: {
    start_step: string;
    steps: Record<string, any>;
  };
}

export const workflowTemplates: WorkflowTemplate[] = [
  {
    id: 'simple-sequential',
    name: 'Simple Sequential Flow',
    description: 'A basic workflow with three sequential steps. Perfect for getting started with workflow creation.',
    category: 'automation',
    icon: 'ArrowRight',
    difficulty: 'beginner',
    workflowData: {
      start_step: 'fetch_data',
      steps: {
        fetch_data: {
          id: 'fetch_data',
          agent_name: 'data-fetcher',
          next_step: 'process_data',
          input_mapping: {
            source: '$.input.data_source',
            query: '$.input.query',
          },
        },
        process_data: {
          id: 'process_data',
          agent_name: 'data-processor',
          next_step: 'save_results',
          input_mapping: {
            data: '$.steps.fetch_data.output.data',
            operation: 'transform',
          },
        },
        save_results: {
          id: 'save_results',
          agent_name: 'data-storage',
          next_step: null,
          input_mapping: {
            data: '$.steps.process_data.output.result',
            destination: '$.input.output_path',
          },
        },
      },
    },
  },
  {
    id: 'api-integration',
    name: 'API Integration Pipeline',
    description: 'Fetch data from an external API, transform it, and send it to another service. Ideal for API integrations.',
    category: 'api-integration',
    icon: 'Cloud',
    difficulty: 'intermediate',
    workflowData: {
      start_step: 'fetch_from_api',
      steps: {
        fetch_from_api: {
          id: 'fetch_from_api',
          agent_name: 'api-client',
          next_step: 'validate_response',
          input_mapping: {
            url: '$.input.api_url',
            method: 'GET',
            headers: '$.input.headers',
          },
        },
        validate_response: {
          id: 'validate_response',
          agent_name: 'data-validator',
          next_step: 'transform_data',
          input_mapping: {
            data: '$.steps.fetch_from_api.output.response',
            schema: '$.input.validation_schema',
          },
        },
        transform_data: {
          id: 'transform_data',
          agent_name: 'data-transformer',
          next_step: 'send_to_service',
          input_mapping: {
            data: '$.steps.validate_response.output.validated_data',
            mapping: '$.input.transformation_rules',
          },
        },
        send_to_service: {
          id: 'send_to_service',
          agent_name: 'api-client',
          next_step: null,
          input_mapping: {
            url: '$.input.target_url',
            method: 'POST',
            body: '$.steps.transform_data.output.transformed_data',
          },
        },
      },
    },
  },
  {
    id: 'data-enrichment',
    name: 'Data Enrichment Flow',
    description: 'Enrich data by fetching additional information from multiple sources and merging results.',
    category: 'data-processing',
    icon: 'Database',
    difficulty: 'intermediate',
    workflowData: {
      start_step: 'load_base_data',
      steps: {
        load_base_data: {
          id: 'load_base_data',
          agent_name: 'data-loader',
          next_step: 'fetch_user_details',
          input_mapping: {
            source: '$.input.data_source',
            filters: '$.input.filters',
          },
        },
        fetch_user_details: {
          id: 'fetch_user_details',
          agent_name: 'user-service',
          next_step: 'fetch_metadata',
          input_mapping: {
            user_ids: '$.steps.load_base_data.output.user_ids',
          },
        },
        fetch_metadata: {
          id: 'fetch_metadata',
          agent_name: 'metadata-service',
          next_step: 'merge_data',
          input_mapping: {
            entity_ids: '$.steps.load_base_data.output.entity_ids',
          },
        },
        merge_data: {
          id: 'merge_data',
          agent_name: 'data-merger',
          next_step: null,
          input_mapping: {
            base_data: '$.steps.load_base_data.output.data',
            user_data: '$.steps.fetch_user_details.output.users',
            metadata: '$.steps.fetch_metadata.output.metadata',
          },
        },
      },
    },
  },
  {
    id: 'ml-inference',
    name: 'ML Model Inference Pipeline',
    description: 'Load data, preprocess it, run ML model inference, and post-process results. Great for ML workflows.',
    category: 'ml-pipeline',
    icon: 'Brain',
    difficulty: 'advanced',
    workflowData: {
      start_step: 'load_input',
      steps: {
        load_input: {
          id: 'load_input',
          agent_name: 'data-loader',
          next_step: 'preprocess',
          input_mapping: {
            source: '$.input.data_source',
            format: '$.input.format',
          },
        },
        preprocess: {
          id: 'preprocess',
          agent_name: 'ml-preprocessor',
          next_step: 'run_inference',
          input_mapping: {
            data: '$.steps.load_input.output.data',
            normalization: 'standard',
            feature_columns: '$.input.features',
          },
        },
        run_inference: {
          id: 'run_inference',
          agent_name: 'ml-model',
          next_step: 'postprocess',
          input_mapping: {
            features: '$.steps.preprocess.output.features',
            model_version: '$.input.model_version',
          },
        },
        postprocess: {
          id: 'postprocess',
          agent_name: 'ml-postprocessor',
          next_step: 'save_predictions',
          input_mapping: {
            predictions: '$.steps.run_inference.output.predictions',
            threshold: '$.input.confidence_threshold',
          },
        },
        save_predictions: {
          id: 'save_predictions',
          agent_name: 'data-storage',
          next_step: null,
          input_mapping: {
            data: '$.steps.postprocess.output.results',
            destination: '$.input.output_path',
          },
        },
      },
    },
  },
  {
    id: 'notification-workflow',
    name: 'Multi-Channel Notification',
    description: 'Send notifications through multiple channels (email, SMS, push) based on user preferences.',
    category: 'automation',
    icon: 'Bell',
    difficulty: 'beginner',
    workflowData: {
      start_step: 'fetch_user_preferences',
      steps: {
        fetch_user_preferences: {
          id: 'fetch_user_preferences',
          agent_name: 'user-service',
          next_step: 'prepare_message',
          input_mapping: {
            user_id: '$.input.user_id',
          },
        },
        prepare_message: {
          id: 'prepare_message',
          agent_name: 'message-formatter',
          next_step: 'send_notifications',
          input_mapping: {
            template: '$.input.template_id',
            data: '$.input.message_data',
            preferences: '$.steps.fetch_user_preferences.output.preferences',
          },
        },
        send_notifications: {
          id: 'send_notifications',
          agent_name: 'notification-service',
          next_step: null,
          input_mapping: {
            channels: '$.steps.prepare_message.output.channels',
            message: '$.steps.prepare_message.output.message',
            recipient: '$.input.user_id',
          },
        },
      },
    },
  },
];

export const getTemplateById = (id: string): WorkflowTemplate | undefined => {
  return workflowTemplates.find((template) => template.id === id);
};

export const getTemplatesByCategory = (category: WorkflowTemplate['category']): WorkflowTemplate[] => {
  return workflowTemplates.filter((template) => template.category === category);
};

export const getTemplatesByDifficulty = (difficulty: WorkflowTemplate['difficulty']): WorkflowTemplate[] => {
  return workflowTemplates.filter((template) => template.difficulty === difficulty);
};

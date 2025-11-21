/**
 * Form validation utilities
 */

export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  min?: number;
  max?: number;
  custom?: (value: any) => string | null;
}

export interface ValidationRules {
  [field: string]: ValidationRule;
}

export interface ValidationErrors {
  [field: string]: string;
}

/**
 * Validate a single field
 */
export function validateField(value: any, rules: ValidationRule, fieldName: string): string | null {
  // Required check
  if (rules.required && (value === undefined || value === null || value === '')) {
    return `${fieldName} is required`;
  }

  // Skip other validations if value is empty and not required
  if (!value && !rules.required) {
    return null;
  }

  // String validations
  if (typeof value === 'string') {
    if (rules.minLength && value.length < rules.minLength) {
      return `${fieldName} must be at least ${rules.minLength} characters`;
    }
    if (rules.maxLength && value.length > rules.maxLength) {
      return `${fieldName} must be at most ${rules.maxLength} characters`;
    }
    if (rules.pattern && !rules.pattern.test(value)) {
      return `${fieldName} format is invalid`;
    }
  }

  // Number validations
  if (typeof value === 'number') {
    if (rules.min !== undefined && value < rules.min) {
      return `${fieldName} must be at least ${rules.min}`;
    }
    if (rules.max !== undefined && value > rules.max) {
      return `${fieldName} must be at most ${rules.max}`;
    }
  }

  // Custom validation
  if (rules.custom) {
    return rules.custom(value);
  }

  return null;
}

/**
 * Validate an object against rules
 */
export function validateForm(data: Record<string, any>, rules: ValidationRules): ValidationErrors {
  const errors: ValidationErrors = {};

  for (const [field, fieldRules] of Object.entries(rules)) {
    const value = data[field];
    const error = validateField(value, fieldRules, field);
    if (error) {
      errors[field] = error;
    }
  }

  return errors;
}

/**
 * Check if form has errors
 */
export function hasErrors(errors: ValidationErrors): boolean {
  return Object.keys(errors).length > 0;
}

/**
 * Common validation patterns
 */
export const patterns = {
  url: /^https?:\/\/.+/,
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  alphanumeric: /^[a-zA-Z0-9]+$/,
  alphanumericWithDash: /^[a-zA-Z0-9-_]+$/,
  number: /^\d+$/,
  decimal: /^\d+(\.\d+)?$/,
};

/**
 * Common validation rules
 */
export const commonRules = {
  required: { required: true },
  url: {
    required: true,
    pattern: patterns.url,
  },
  email: {
    required: true,
    pattern: patterns.email,
  },
  name: {
    required: true,
    minLength: 2,
    maxLength: 100,
  },
  description: {
    maxLength: 500,
  },
  positiveNumber: {
    required: true,
    min: 0,
  },
  positiveInteger: {
    required: true,
    min: 0,
    custom: (value: any) => {
      if (!Number.isInteger(value)) {
        return 'Must be a whole number';
      }
      return null;
    },
  },
};

/**
 * Validate JSON string
 */
export function validateJSON(jsonString: string): { valid: boolean; error?: string; parsed?: any } {
  try {
    const parsed = JSON.parse(jsonString);
    return { valid: true, parsed };
  } catch (error) {
    if (error instanceof Error) {
      return { valid: false, error: error.message };
    }
    return { valid: false, error: 'Invalid JSON' };
  }
}

/**
 * Validate workflow definition
 */
export function validateWorkflowDefinition(definition: any): string[] {
  const errors: string[] = [];

  if (!definition) {
    errors.push('Workflow definition is required');
    return errors;
  }

  if (!definition.name) {
    errors.push('Workflow name is required');
  }

  if (!definition.steps || typeof definition.steps !== 'object') {
    errors.push('Workflow must have steps');
    return errors;
  }

  const stepIds = Object.keys(definition.steps);
  if (stepIds.length === 0) {
    errors.push('Workflow must have at least one step');
  }

  // Validate each step
  for (const [stepId, step] of Object.entries(definition.steps)) {
    if (typeof step !== 'object' || step === null) {
      errors.push(`Step "${stepId}" is invalid`);
      continue;
    }

    const stepObj = step as any;
    const stepType = stepObj.type || 'agent';

    // Validate based on step type
    if (stepType === 'agent') {
      if (!stepObj.agent_name) {
        errors.push(`Step "${stepId}" must have an agent_name`);
      }
      if (!stepObj.input_mapping) {
        errors.push(`Step "${stepId}" must have an input_mapping`);
      }
    } else if (stepType === 'parallel') {
      if (!stepObj.parallel_steps || !Array.isArray(stepObj.parallel_steps)) {
        errors.push(`Step "${stepId}" must have parallel_steps array`);
      } else if (stepObj.parallel_steps.length < 2) {
        errors.push(`Step "${stepId}" must have at least 2 parallel steps`);
      }
    } else if (stepType === 'conditional') {
      if (!stepObj.condition || !stepObj.condition.expression) {
        errors.push(`Step "${stepId}" must have a condition with an expression`);
      }
      if (!stepObj.if_true_step && !stepObj.if_false_step) {
        errors.push(`Step "${stepId}" must have at least one of if_true_step or if_false_step`);
      }
    }

    // Validate dependencies exist
    if (stepObj.depends_on) {
      const dependencies = Array.isArray(stepObj.depends_on)
        ? stepObj.depends_on
        : [stepObj.depends_on];

      for (const dep of dependencies) {
        if (!stepIds.includes(dep)) {
          errors.push(`Step "${stepId}" depends on non-existent step "${dep}"`);
        }
      }
    }
  }

  // Check for circular dependencies
  const hasCycle = detectCircularDependencies(definition.steps);
  if (hasCycle) {
    errors.push('Workflow has circular dependencies');
  }

  return errors;
}

/**
 * Detect circular dependencies in workflow steps
 */
function detectCircularDependencies(steps: Record<string, any>): boolean {
  const visited = new Set<string>();
  const recursionStack = new Set<string>();

  function hasCycle(stepId: string): boolean {
    visited.add(stepId);
    recursionStack.add(stepId);

    const step = steps[stepId];
    if (step?.depends_on) {
      const dependencies = Array.isArray(step.depends_on) ? step.depends_on : [step.depends_on];

      for (const dep of dependencies) {
        if (!visited.has(dep)) {
          if (hasCycle(dep)) {
            return true;
          }
        } else if (recursionStack.has(dep)) {
          return true;
        }
      }
    }

    recursionStack.delete(stepId);
    return false;
  }

  for (const stepId of Object.keys(steps)) {
    if (!visited.has(stepId)) {
      if (hasCycle(stepId)) {
        return true;
      }
    }
  }

  return false;
}

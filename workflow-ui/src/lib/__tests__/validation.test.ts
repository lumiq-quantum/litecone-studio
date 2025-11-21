import { describe, it, expect } from 'vitest';
import {
  validateField,
  validateForm,
  hasErrors,
  validateJSON,
  validateWorkflowDefinition,
  patterns,
} from '../validation';

describe('validateField', () => {
  it('should return error for required field when value is empty', () => {
    const error = validateField('', { required: true }, 'Name');
    expect(error).toBe('Name is required');
  });

  it('should return null for optional field when value is empty', () => {
    const error = validateField('', { required: false }, 'Description');
    expect(error).toBeNull();
  });

  it('should validate minLength', () => {
    const error = validateField('ab', { minLength: 3 }, 'Username');
    expect(error).toBe('Username must be at least 3 characters');
  });

  it('should validate maxLength', () => {
    const error = validateField('a'.repeat(101), { maxLength: 100 }, 'Name');
    expect(error).toBe('Name must be at most 100 characters');
  });

  it('should validate pattern', () => {
    const error = validateField('invalid-url', { pattern: patterns.url }, 'URL');
    expect(error).toBe('URL format is invalid');
  });

  it('should validate min for numbers', () => {
    const error = validateField(-1, { min: 0 }, 'Timeout');
    expect(error).toBe('Timeout must be at least 0');
  });

  it('should validate max for numbers', () => {
    const error = validateField(101, { max: 100 }, 'Retries');
    expect(error).toBe('Retries must be at most 100');
  });

  it('should use custom validation', () => {
    const error = validateField(5.5, {
      custom: (value) => (Number.isInteger(value) ? null : 'Must be integer'),
    }, 'Count');
    expect(error).toBe('Must be integer');
  });

  it('should return null for valid value', () => {
    const error = validateField('https://example.com', { pattern: patterns.url }, 'URL');
    expect(error).toBeNull();
  });
});

describe('validateForm', () => {
  it('should validate all fields and return errors', () => {
    const data = {
      name: '',
      url: 'invalid',
      timeout: -1,
    };

    const rules = {
      name: { required: true },
      url: { pattern: patterns.url },
      timeout: { min: 0 },
    };

    const errors = validateForm(data, rules);
    expect(errors.name).toBe('name is required');
    expect(errors.url).toBe('url format is invalid');
    expect(errors.timeout).toBe('timeout must be at least 0');
  });

  it('should return empty object for valid data', () => {
    const data = {
      name: 'Test Agent',
      url: 'https://example.com',
      timeout: 30,
    };

    const rules = {
      name: { required: true },
      url: { pattern: patterns.url },
      timeout: { min: 0 },
    };

    const errors = validateForm(data, rules);
    expect(Object.keys(errors)).toHaveLength(0);
  });
});

describe('hasErrors', () => {
  it('should return true when errors exist', () => {
    expect(hasErrors({ name: 'Required' })).toBe(true);
  });

  it('should return false when no errors', () => {
    expect(hasErrors({})).toBe(false);
  });
});

describe('validateJSON', () => {
  it('should validate valid JSON', () => {
    const result = validateJSON('{"name": "test"}');
    expect(result.valid).toBe(true);
    expect(result.parsed).toEqual({ name: 'test' });
  });

  it('should return error for invalid JSON', () => {
    const result = validateJSON('{invalid}');
    expect(result.valid).toBe(false);
    expect(result.error).toBeDefined();
  });

  it('should handle empty string', () => {
    const result = validateJSON('');
    expect(result.valid).toBe(false);
  });
});

describe('validateWorkflowDefinition', () => {
  it('should validate valid workflow', () => {
    const workflow = {
      name: 'Test Workflow',
      steps: {
        'step-1': {
          agent_name: 'agent1',
        },
        'step-2': {
          agent_name: 'agent2',
          depends_on: ['step-1'],
        },
      },
    };

    const errors = validateWorkflowDefinition(workflow);
    expect(errors).toHaveLength(0);
  });

  it('should require workflow definition', () => {
    const errors = validateWorkflowDefinition(null);
    expect(errors).toContain('Workflow definition is required');
  });

  it('should require workflow name', () => {
    const workflow = {
      steps: {},
    };
    const errors = validateWorkflowDefinition(workflow);
    expect(errors).toContain('Workflow name is required');
  });

  it('should require steps', () => {
    const workflow = {
      name: 'Test',
    };
    const errors = validateWorkflowDefinition(workflow);
    expect(errors).toContain('Workflow must have steps');
  });

  it('should require at least one step', () => {
    const workflow = {
      name: 'Test',
      steps: {},
    };
    const errors = validateWorkflowDefinition(workflow);
    expect(errors).toContain('Workflow must have at least one step');
  });

  it('should require agent_name for each step', () => {
    const workflow = {
      name: 'Test',
      steps: {
        'step-1': {},
      },
    };
    const errors = validateWorkflowDefinition(workflow);
    expect(errors).toContain('Step "step-1" must have an agent_name');
  });

  it('should validate dependencies exist', () => {
    const workflow = {
      name: 'Test',
      steps: {
        'step-1': {
          agent_name: 'agent1',
          depends_on: ['non-existent'],
        },
      },
    };
    const errors = validateWorkflowDefinition(workflow);
    expect(errors).toContain('Step "step-1" depends on non-existent step "non-existent"');
  });

  it('should detect circular dependencies', () => {
    const workflow = {
      name: 'Test',
      steps: {
        'step-1': {
          agent_name: 'agent1',
          depends_on: ['step-2'],
        },
        'step-2': {
          agent_name: 'agent2',
          depends_on: ['step-1'],
        },
      },
    };
    const errors = validateWorkflowDefinition(workflow);
    expect(errors).toContain('Workflow has circular dependencies');
  });
});

describe('patterns', () => {
  it('should validate URL pattern', () => {
    expect(patterns.url.test('https://example.com')).toBe(true);
    expect(patterns.url.test('http://example.com')).toBe(true);
    expect(patterns.url.test('invalid')).toBe(false);
  });

  it('should validate email pattern', () => {
    expect(patterns.email.test('test@example.com')).toBe(true);
    expect(patterns.email.test('invalid')).toBe(false);
  });

  it('should validate alphanumeric pattern', () => {
    expect(patterns.alphanumeric.test('abc123')).toBe(true);
    expect(patterns.alphanumeric.test('abc-123')).toBe(false);
  });
});

/**
 * Tests for JSON diff utilities
 */
import { describe, it, expect } from 'vitest';
import { getChangedLines, getChangeSummary } from '../jsonDiff';

describe('jsonDiff', () => {
  describe('getChangedLines', () => {
    it('should return empty array for identical JSON', () => {
      const json1 = JSON.stringify({ name: 'test', value: 123 }, null, 2);
      const json2 = JSON.stringify({ name: 'test', value: 123 }, null, 2);
      
      const changedLines = getChangedLines(json1, json2);
      
      expect(changedLines).toEqual([]);
    });

    it('should detect changed lines when values differ', () => {
      const json1 = JSON.stringify({ name: 'test', value: 123 }, null, 2);
      const json2 = JSON.stringify({ name: 'test', value: 456 }, null, 2);
      
      const changedLines = getChangedLines(json1, json2);
      
      expect(changedLines.length).toBeGreaterThan(0);
    });

    it('should detect added properties', () => {
      const json1 = JSON.stringify({ name: 'test' }, null, 2);
      const json2 = JSON.stringify({ name: 'test', value: 123 }, null, 2);
      
      const changedLines = getChangedLines(json1, json2);
      
      expect(changedLines.length).toBeGreaterThan(0);
    });

    it('should detect removed properties', () => {
      const json1 = JSON.stringify({ name: 'test', value: 123 }, null, 2);
      const json2 = JSON.stringify({ name: 'test' }, null, 2);
      
      const changedLines = getChangedLines(json1, json2);
      
      expect(changedLines.length).toBeGreaterThan(0);
    });

    it('should return empty array for invalid JSON', () => {
      const json1 = 'invalid json';
      const json2 = '{ "valid": true }';
      
      const changedLines = getChangedLines(json1, json2);
      
      expect(changedLines).toEqual([]);
    });
  });

  describe('getChangeSummary', () => {
    it('should detect workflow name change', () => {
      const json1 = JSON.stringify({
        name: 'old-name',
        start_step: 'step1',
        steps: { step1: { id: 'step1', agent_name: 'agent1', input_mapping: {}, next_step: null } }
      }, null, 2);
      
      const json2 = JSON.stringify({
        name: 'new-name',
        start_step: 'step1',
        steps: { step1: { id: 'step1', agent_name: 'agent1', input_mapping: {}, next_step: null } }
      }, null, 2);
      
      const summary = getChangeSummary(json1, json2);
      
      expect(summary).toContain('Name changed');
      expect(summary).toContain('old-name');
      expect(summary).toContain('new-name');
    });

    it('should detect added steps', () => {
      const json1 = JSON.stringify({
        start_step: 'step1',
        steps: { step1: { id: 'step1', agent_name: 'agent1', input_mapping: {}, next_step: null } }
      }, null, 2);
      
      const json2 = JSON.stringify({
        start_step: 'step1',
        steps: {
          step1: { id: 'step1', agent_name: 'agent1', input_mapping: {}, next_step: 'step2' },
          step2: { id: 'step2', agent_name: 'agent2', input_mapping: {}, next_step: null }
        }
      }, null, 2);
      
      const summary = getChangeSummary(json1, json2);
      
      expect(summary).toContain('Added 1 step');
      expect(summary).toContain('step2');
    });

    it('should detect removed steps', () => {
      const json1 = JSON.stringify({
        start_step: 'step1',
        steps: {
          step1: { id: 'step1', agent_name: 'agent1', input_mapping: {}, next_step: 'step2' },
          step2: { id: 'step2', agent_name: 'agent2', input_mapping: {}, next_step: null }
        }
      }, null, 2);
      
      const json2 = JSON.stringify({
        start_step: 'step1',
        steps: { step1: { id: 'step1', agent_name: 'agent1', input_mapping: {}, next_step: null } }
      }, null, 2);
      
      const summary = getChangeSummary(json1, json2);
      
      expect(summary).toContain('Removed 1 step');
      expect(summary).toContain('step2');
    });

    it('should detect modified steps', () => {
      const json1 = JSON.stringify({
        start_step: 'step1',
        steps: { step1: { id: 'step1', agent_name: 'agent1', input_mapping: {}, next_step: null } }
      }, null, 2);
      
      const json2 = JSON.stringify({
        start_step: 'step1',
        steps: { step1: { id: 'step1', agent_name: 'agent2', input_mapping: {}, next_step: null } }
      }, null, 2);
      
      const summary = getChangeSummary(json1, json2);
      
      expect(summary).toContain('Modified 1 step');
      expect(summary).toContain('step1');
    });

    it('should return no changes message for identical workflows', () => {
      const json = JSON.stringify({
        start_step: 'step1',
        steps: { step1: { id: 'step1', agent_name: 'agent1', input_mapping: {}, next_step: null } }
      }, null, 2);
      
      const summary = getChangeSummary(json, json);
      
      expect(summary).toBe('No significant changes detected');
    });

    it('should handle invalid JSON gracefully', () => {
      const summary = getChangeSummary('invalid', '{ "valid": true }');
      
      expect(summary).toBe('Unable to generate change summary');
    });
  });
});

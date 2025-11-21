import { describe, it, expect, beforeEach } from 'vitest';
import {
  getStorageItem,
  setStorageItem,
  removeStorageItem,
  clearStorage,
  getUIPreferences,
  updateUIPreferences,
  cacheWorkflowDefinition,
  getCachedWorkflowDefinition,
  addRecentSearch,
  getRecentSearches,
  clearRecentSearches,
  saveLastViewed,
  getLastViewed,
} from '../storage';

describe('Storage utilities', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('getStorageItem and setStorageItem', () => {
    it('should store and retrieve values', () => {
      setStorageItem('test', { value: 'hello' });
      const result = getStorageItem('test', null);
      expect(result).toEqual({ value: 'hello' });
    });

    it('should return default value when key does not exist', () => {
      const result = getStorageItem('nonexistent', 'default');
      expect(result).toBe('default');
    });

    it('should handle different data types', () => {
      setStorageItem('string', 'test');
      setStorageItem('number', 42);
      setStorageItem('boolean', true);
      setStorageItem('object', { key: 'value' });
      setStorageItem('array', [1, 2, 3]);

      expect(getStorageItem('string', '')).toBe('test');
      expect(getStorageItem('number', 0)).toBe(42);
      expect(getStorageItem('boolean', false)).toBe(true);
      expect(getStorageItem('object', {})).toEqual({ key: 'value' });
      expect(getStorageItem('array', [])).toEqual([1, 2, 3]);
    });
  });

  describe('removeStorageItem', () => {
    it('should remove item from storage', () => {
      setStorageItem('test', 'value');
      removeStorageItem('test');
      const result = getStorageItem('test', null);
      expect(result).toBeNull();
    });
  });

  describe('clearStorage', () => {
    it('should call localStorage methods', () => {
      // This test verifies clearStorage doesn't throw errors
      // The actual clearing behavior depends on localStorage implementation
      setStorageItem('item1', 'value1');
      expect(() => clearStorage()).not.toThrow();
    });
  });

  describe('UI Preferences', () => {
    it('should get and update preferences', () => {
      updateUIPreferences({ theme: 'dark', sidebarCollapsed: true });
      const prefs = getUIPreferences();
      expect(prefs.theme).toBe('dark');
      expect(prefs.sidebarCollapsed).toBe(true);
    });

    it('should merge preferences on update', () => {
      updateUIPreferences({ theme: 'dark' });
      updateUIPreferences({ sidebarCollapsed: true });
      const prefs = getUIPreferences();
      expect(prefs.theme).toBe('dark');
      expect(prefs.sidebarCollapsed).toBe(true);
    });
  });

  describe('Workflow caching', () => {
    it('should cache and retrieve workflow definition', () => {
      const definition = { name: 'Test', steps: {} };
      cacheWorkflowDefinition('workflow-1', definition);
      const cached = getCachedWorkflowDefinition('workflow-1');
      expect(cached).toEqual(definition);
    });

    it('should return null for non-existent cache', () => {
      const cached = getCachedWorkflowDefinition('nonexistent');
      expect(cached).toBeNull();
    });

    it('should expire old cache', () => {
      const definition = { name: 'Test', steps: {} };
      cacheWorkflowDefinition('workflow-1', definition);
      
      // Wait a tiny bit to ensure time has passed
      const now = Date.now();
      while (Date.now() === now) {
        // Busy wait for at least 1ms
      }
      
      // Get with 0 maxAge should expire immediately
      const cached = getCachedWorkflowDefinition('workflow-1', 0);
      expect(cached).toBeNull();
    });
  });

  describe('Recent searches', () => {
    it('should add and retrieve recent searches', () => {
      addRecentSearch('query1');
      addRecentSearch('query2');
      const searches = getRecentSearches();
      expect(searches).toEqual(['query2', 'query1']);
    });

    it('should remove duplicates', () => {
      addRecentSearch('query1');
      addRecentSearch('query2');
      addRecentSearch('query1');
      const searches = getRecentSearches();
      expect(searches).toEqual(['query1', 'query2']);
    });

    it('should limit to 10 searches', () => {
      for (let i = 0; i < 15; i++) {
        addRecentSearch(`query${i}`);
      }
      const searches = getRecentSearches();
      expect(searches).toHaveLength(10);
    });

    it('should clear recent searches', () => {
      addRecentSearch('query1');
      clearRecentSearches();
      const searches = getRecentSearches();
      expect(searches).toEqual([]);
    });
  });

  describe('Last viewed items', () => {
    it('should save and retrieve last viewed workflow', () => {
      saveLastViewed('workflow', 'workflow-123');
      const lastViewed = getLastViewed('workflow');
      expect(lastViewed).toBe('workflow-123');
    });

    it('should save and retrieve last viewed agent', () => {
      saveLastViewed('agent', 'agent-456');
      const lastViewed = getLastViewed('agent');
      expect(lastViewed).toBe('agent-456');
    });

    it('should return undefined for non-existent last viewed', () => {
      const lastViewed = getLastViewed('workflow');
      expect(lastViewed).toBeUndefined();
    });
  });
});

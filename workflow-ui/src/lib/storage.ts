/**
 * Local storage utilities for persisting UI preferences
 */

const STORAGE_PREFIX = 'workflow-ui:';

export interface UIPreferences {
  theme?: 'light' | 'dark';
  sidebarCollapsed?: boolean;
  tutorialCompleted?: boolean;
  defaultPageSize?: number;
  lastViewedWorkflow?: string;
  lastViewedAgent?: string;
  recentSearches?: string[];
}

/**
 * Get a value from local storage
 */
export function getStorageItem<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(STORAGE_PREFIX + key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error(`Error reading from localStorage key "${key}":`, error);
    return defaultValue;
  }
}

/**
 * Set a value in local storage
 */
export function setStorageItem<T>(key: string, value: T): void {
  try {
    localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error writing to localStorage key "${key}":`, error);
  }
}

/**
 * Remove a value from local storage
 */
export function removeStorageItem(key: string): void {
  try {
    localStorage.removeItem(STORAGE_PREFIX + key);
  } catch (error) {
    console.error(`Error removing from localStorage key "${key}":`, error);
  }
}

/**
 * Clear all app-specific items from local storage
 */
export function clearStorage(): void {
  try {
    const keys = Object.keys(localStorage);
    keys.forEach((key) => {
      if (key.startsWith(STORAGE_PREFIX)) {
        localStorage.removeItem(key);
      }
    });
  } catch (error) {
    console.error('Error clearing localStorage:', error);
  }
}

/**
 * Get UI preferences
 */
export function getUIPreferences(): UIPreferences {
  return getStorageItem<UIPreferences>('preferences', {});
}

/**
 * Update UI preferences
 */
export function updateUIPreferences(preferences: Partial<UIPreferences>): void {
  const current = getUIPreferences();
  setStorageItem('preferences', { ...current, ...preferences });
}

/**
 * Cache workflow definition
 */
export function cacheWorkflowDefinition(workflowId: string, definition: any): void {
  const cacheKey = `workflow:${workflowId}`;
  const cacheData = {
    definition,
    timestamp: Date.now(),
  };
  setStorageItem(cacheKey, cacheData);
}

/**
 * Get cached workflow definition
 */
export function getCachedWorkflowDefinition(
  workflowId: string,
  maxAge: number = 5 * 60 * 1000 // 5 minutes default
): any | null {
  const cacheKey = `workflow:${workflowId}`;
  const cacheData = getStorageItem<{ definition: any; timestamp: number } | null>(cacheKey, null);

  if (!cacheData) return null;

  // Check if cache is still valid
  const age = Date.now() - cacheData.timestamp;
  if (age > maxAge) {
    removeStorageItem(cacheKey);
    return null;
  }

  return cacheData.definition;
}

/**
 * Add to recent searches
 */
export function addRecentSearch(query: string): void {
  const preferences = getUIPreferences();
  const recentSearches = preferences.recentSearches || [];
  
  // Remove duplicates and add to front
  const updated = [query, ...recentSearches.filter((s) => s !== query)].slice(0, 10);
  
  updateUIPreferences({ recentSearches: updated });
}

/**
 * Get recent searches
 */
export function getRecentSearches(): string[] {
  const preferences = getUIPreferences();
  return preferences.recentSearches || [];
}

/**
 * Clear recent searches
 */
export function clearRecentSearches(): void {
  updateUIPreferences({ recentSearches: [] });
}

/**
 * Save last viewed item
 */
export function saveLastViewed(type: 'workflow' | 'agent', id: string): void {
  if (type === 'workflow') {
    updateUIPreferences({ lastViewedWorkflow: id });
  } else {
    updateUIPreferences({ lastViewedAgent: id });
  }
}

/**
 * Get last viewed item
 */
export function getLastViewed(type: 'workflow' | 'agent'): string | undefined {
  const preferences = getUIPreferences();
  return type === 'workflow' ? preferences.lastViewedWorkflow : preferences.lastViewedAgent;
}

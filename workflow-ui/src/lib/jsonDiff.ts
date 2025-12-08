/**
 * JSON Diff Utilities
 * 
 * Utilities for comparing JSON strings and detecting changed lines
 */

/**
 * Compare two JSON strings and return the line numbers that changed
 * 
 * @param oldJson - The original JSON string
 * @param newJson - The updated JSON string
 * @returns Array of line numbers (1-indexed) that changed
 */
export function getChangedLines(oldJson: string, newJson: string): number[] {
  const changedLines: number[] = [];

  try {
    // Parse both JSON strings
    const oldObj = JSON.parse(oldJson);
    const newObj = JSON.parse(newJson);

    // Format both with consistent spacing
    const oldFormatted = JSON.stringify(oldObj, null, 2);
    const newFormatted = JSON.stringify(newObj, null, 2);

    // Split into lines
    const oldLines = oldFormatted.split('\n');
    const newLines = newFormatted.split('\n');

    // Compare line by line
    const maxLines = Math.max(oldLines.length, newLines.length);
    for (let i = 0; i < maxLines; i++) {
      const oldLine = oldLines[i] || '';
      const newLine = newLines[i] || '';

      if (oldLine !== newLine) {
        changedLines.push(i + 1); // Monaco uses 1-indexed line numbers
      }
    }
  } catch (error) {
    // If parsing fails, return empty array
    console.error('Error comparing JSON:', error);
    return [];
  }

  return changedLines;
}

/**
 * Get a summary of changes between two workflow JSONs
 * 
 * @param oldJson - The original JSON string
 * @param newJson - The updated JSON string
 * @returns Human-readable summary of changes
 */
export function getChangeSummary(oldJson: string, newJson: string): string {
  try {
    const oldObj = JSON.parse(oldJson);
    const newObj = JSON.parse(newJson);

    const changes: string[] = [];

    // Check for workflow name change
    if (oldObj.name !== newObj.name) {
      changes.push(`Name changed from "${oldObj.name || 'unnamed'}" to "${newObj.name || 'unnamed'}"`);
    }

    // Check for description change
    if (oldObj.description !== newObj.description) {
      changes.push('Description updated');
    }

    // Check for start_step change
    if (oldObj.start_step !== newObj.start_step) {
      changes.push(`Start step changed from "${oldObj.start_step}" to "${newObj.start_step}"`);
    }

    // Check for step changes
    const oldSteps = Object.keys(oldObj.steps || {});
    const newSteps = Object.keys(newObj.steps || {});

    const addedSteps = newSteps.filter(id => !oldSteps.includes(id));
    const removedSteps = oldSteps.filter(id => !newSteps.includes(id));
    const commonSteps = oldSteps.filter(id => newSteps.includes(id));

    if (addedSteps.length > 0) {
      changes.push(`Added ${addedSteps.length} step(s): ${addedSteps.join(', ')}`);
    }

    if (removedSteps.length > 0) {
      changes.push(`Removed ${removedSteps.length} step(s): ${removedSteps.join(', ')}`);
    }

    // Check for modified steps
    const modifiedSteps = commonSteps.filter(id => {
      return JSON.stringify(oldObj.steps[id]) !== JSON.stringify(newObj.steps[id]);
    });

    if (modifiedSteps.length > 0) {
      changes.push(`Modified ${modifiedSteps.length} step(s): ${modifiedSteps.join(', ')}`);
    }

    if (changes.length === 0) {
      return 'No significant changes detected';
    }

    return changes.join('; ');
  } catch (error) {
    return 'Unable to generate change summary';
  }
}

/**
 * Get a detailed summary of changes between two workflow JSONs
 * Includes specific details about what changed in each step
 * 
 * @param oldJson - The original JSON string
 * @param newJson - The updated JSON string
 * @returns Detailed human-readable summary of changes
 */
export function getDetailedChangeSummary(oldJson: string, newJson: string): string {
  try {
    const oldObj = JSON.parse(oldJson);
    const newObj = JSON.parse(newJson);

    const changes: string[] = [];

    // Check for workflow name change
    if (oldObj.name !== newObj.name) {
      changes.push(`• Name: "${oldObj.name || 'unnamed'}" → "${newObj.name || 'unnamed'}"`);
    }

    // Check for description change
    if (oldObj.description !== newObj.description) {
      changes.push(`• Description updated`);
    }

    // Check for start_step change
    if (oldObj.start_step !== newObj.start_step) {
      changes.push(`• Start step: "${oldObj.start_step}" → "${newObj.start_step}"`);
    }

    // Check for step changes
    const oldSteps = Object.keys(oldObj.steps || {});
    const newSteps = Object.keys(newObj.steps || {});

    const addedSteps = newSteps.filter(id => !oldSteps.includes(id));
    const removedSteps = oldSteps.filter(id => !newSteps.includes(id));
    const commonSteps = oldSteps.filter(id => newSteps.includes(id));

    // Detail added steps
    if (addedSteps.length > 0) {
      addedSteps.forEach(stepId => {
        const step = newObj.steps[stepId];
        const stepType = step.type || 'agent';
        const agentInfo = step.agent_name ? ` (${step.agent_name})` : '';
        changes.push(`• Added step "${stepId}"${agentInfo} [${stepType}]`);
      });
    }

    // Detail removed steps
    if (removedSteps.length > 0) {
      removedSteps.forEach(stepId => {
        const step = oldObj.steps[stepId];
        const stepType = step.type || 'agent';
        changes.push(`• Removed step "${stepId}" [${stepType}]`);
      });
    }

    // Detail modified steps
    commonSteps.forEach(stepId => {
      const oldStep = oldObj.steps[stepId];
      const newStep = newObj.steps[stepId];
      
      if (JSON.stringify(oldStep) === JSON.stringify(newStep)) {
        return; // No changes
      }

      const stepChanges: string[] = [];

      // Check agent_name change
      if (oldStep.agent_name !== newStep.agent_name) {
        stepChanges.push(`agent: "${oldStep.agent_name}" → "${newStep.agent_name}"`);
      }

      // Check type change
      if (oldStep.type !== newStep.type) {
        stepChanges.push(`type: "${oldStep.type || 'agent'}" → "${newStep.type || 'agent'}"`);
      }

      // Check next_step change
      if (oldStep.next_step !== newStep.next_step) {
        stepChanges.push(`next: "${oldStep.next_step || 'null'}" → "${newStep.next_step || 'null'}"`);
      }

      // Check input_mapping change
      if (JSON.stringify(oldStep.input_mapping) !== JSON.stringify(newStep.input_mapping)) {
        stepChanges.push('input mapping updated');
      }

      // Check for parallel_steps change
      if (JSON.stringify(oldStep.parallel_steps) !== JSON.stringify(newStep.parallel_steps)) {
        stepChanges.push('parallel steps updated');
      }

      // Check for condition change
      if (JSON.stringify(oldStep.condition) !== JSON.stringify(newStep.condition)) {
        stepChanges.push('condition updated');
      }

      // Check for loop_config change
      if (JSON.stringify(oldStep.loop_config) !== JSON.stringify(newStep.loop_config)) {
        stepChanges.push('loop config updated');
      }

      // Check for fork_join_config change
      if (JSON.stringify(oldStep.fork_join_config) !== JSON.stringify(newStep.fork_join_config)) {
        stepChanges.push('fork-join config updated');
      }

      if (stepChanges.length > 0) {
        changes.push(`• Modified step "${stepId}": ${stepChanges.join(', ')}`);
      }
    });

    if (changes.length === 0) {
      return 'No changes detected';
    }

    return changes.join('\n');
  } catch (error) {
    return 'Unable to generate detailed change summary';
  }
}

/**
 * Compare two workflow JSONs and return structured change information
 * 
 * @param oldJson - The original JSON string
 * @param newJson - The updated JSON string
 * @returns Structured change information
 */
export interface WorkflowChanges {
  hasChanges: boolean;
  addedSteps: string[];
  removedSteps: string[];
  modifiedSteps: string[];
  changedLines: number[];
  summary: string;
  detailedSummary: string;
}

export function getWorkflowChanges(oldJson: string, newJson: string): WorkflowChanges {
  const changedLines = getChangedLines(oldJson, newJson);
  const summary = getChangeSummary(oldJson, newJson);
  const detailedSummary = getDetailedChangeSummary(oldJson, newJson);

  try {
    const oldObj = JSON.parse(oldJson);
    const newObj = JSON.parse(newJson);

    const oldSteps = Object.keys(oldObj.steps || {});
    const newSteps = Object.keys(newObj.steps || {});

    const addedSteps = newSteps.filter(id => !oldSteps.includes(id));
    const removedSteps = oldSteps.filter(id => !newSteps.includes(id));
    const commonSteps = oldSteps.filter(id => newSteps.includes(id));

    const modifiedSteps = commonSteps.filter(id => {
      return JSON.stringify(oldObj.steps[id]) !== JSON.stringify(newObj.steps[id]);
    });

    return {
      hasChanges: changedLines.length > 0,
      addedSteps,
      removedSteps,
      modifiedSteps,
      changedLines,
      summary,
      detailedSummary,
    };
  } catch (error) {
    return {
      hasChanges: false,
      addedSteps: [],
      removedSteps: [],
      modifiedSteps: [],
      changedLines,
      summary,
      detailedSummary,
    };
  }
}

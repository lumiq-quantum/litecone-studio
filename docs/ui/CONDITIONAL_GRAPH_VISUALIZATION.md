# Conditional Logic Graph Visualization

## Overview

This document describes the visual graph updates to support conditional logic in workflow visualizations.

## Changes Made

### 1. WorkflowGraph Component (`src/components/workflows/WorkflowGraph.tsx`)

#### Dependency Tracking
Added conditional step branch tracking:
- Tracks `if_true_step` as a dependency
- Tracks `if_false_step` as a dependency
- Both branches are included in layout calculations

#### Node Display
Updated node data for conditional steps:
- Display name shows the condition expression
- `isConditional` flag set to `true`
- `hasOutput` correctly calculated for conditional branches

#### Edge Creation
Added conditional branch edges:
- **True Branch**: Green edge labeled "true"
- **False Branch**: Red edge labeled "false"
- Both edges use smooth step routing
- Labels have colored backgrounds for visibility

### 2. WorkflowStepNode Component (`src/components/workflows/WorkflowStepNode.tsx`)

#### Visual Styling
Added conditional step icon and styling:
- Uses `GitMerge` icon (amber color) for conditional steps
- Shows "?" prefix before condition expression
- Maintains consistent styling with other step types

#### Type Support
Extended `WorkflowStepNodeData` interface:
- Added `isConditional?: boolean` field
- Conditional rendering based on step type

## Visual Design

### Conditional Step Node
```
┌─────────────────────────┐
│ 🔀 step-2               │
│ ? ${step-1.output...}   │
└─────────────────────────┘
```

- **Icon**: GitMerge (🔀) in amber color
- **Prefix**: "?" to indicate conditional logic
- **Label**: Shows the condition expression

### Branch Edges

**True Branch:**
- Color: Green (#10b981)
- Label: "true" with green text
- Arrow: Green arrow marker

**False Branch:**
- Color: Red (#ef4444)
- Label: "false" with red text
- Arrow: Red arrow marker

### Example Graph Layout

```
┌──────────┐
│  step-1  │
│ Analyzer │
└────┬─────┘
     │
     ▼
┌──────────┐
│  step-2  │  ◄── Conditional Step (diamond-like with GitMerge icon)
│ ? score  │
└─┬──────┬─┘
  │      │
  │true  │false
  │      │
  ▼      ▼
┌────┐ ┌────┐
│ S3 │ │ S4 │  ◄── Branch Steps
└─┬──┘ └─┬──┘
  │      │
  └──┬───┘
     │
     ▼
  ┌────┐
  │ S5 │  ◄── Next Step (after branches)
  └────┘
```

## Color Scheme

| Element | Color | Hex Code | Purpose |
|---------|-------|----------|---------|
| True Branch | Green | #10b981 | Indicates condition is true |
| False Branch | Red | #ef4444 | Indicates condition is false |
| Conditional Icon | Amber | #f59e0b | Distinguishes conditional steps |
| Parallel Icon | Purple | #8b5cf6 | Distinguishes parallel steps |
| Agent Icon | Gray | #6b7280 | Standard agent steps |

## Edge Labels

Labels are positioned on the edges with:
- **Font Weight**: 600 (semi-bold)
- **Font Size**: 12px
- **Background**: Colored background matching branch type
  - True: Light green (#f0fdf4)
  - False: Light red (#fef2f2)

## Layout Algorithm

The layout algorithm:
1. Calculates dependencies including conditional branches
2. Assigns levels based on dependency depth
3. Groups steps by level
4. Positions steps horizontally by level
5. Positions steps vertically within level
6. Creates edges for all connections (next_step, branches)

## Status Visualization

Conditional steps support all standard statuses:
- **Pending**: Gray border and background
- **Running**: Blue border with pulse animation
- **Completed**: Green border and background
- **Failed**: Red border and background

## Interaction

Users can:
- Click on conditional steps to view details
- Hover to see tooltip with:
  - Step ID
  - Condition expression
  - Current status
  - Error messages (if failed)

## Future Enhancements

Potential improvements:
- Diamond-shaped nodes for conditional steps
- Highlight active branch during execution
- Show which branch was taken in run history
- Animated flow along the taken branch
- Condition evaluation preview on hover

## Testing

Test the visualization with:
1. Simple conditional (one branch)
2. Full conditional (both branches)
3. Nested conditionals
4. Conditional after parallel
5. Parallel after conditional

## Example Workflows

See `examples/conditional_workflow_example.json` for a complete example that demonstrates:
- Conditional step after agent step
- Both true and false branches
- Next step after conditional branches
- Proper edge routing and labeling

## Related Documentation

- [Conditional Logic Backend](../docs/conditional_logic.md)
- [Conditional Logic UI](CONDITIONAL_LOGIC_UI.md)
- [Workflow Format Specification](../WORKFLOW_FORMAT.md)

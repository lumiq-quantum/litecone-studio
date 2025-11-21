# Workflow Definition Visualizer & Editor - Complete Implementation

## Overview

The Workflow Definition Visualizer & Editor is a comprehensive component that provides three views for working with workflow definitions:
1. **JSON Editor** - Monaco-based code editor with validation
2. **Visual Graph** - Interactive workflow diagram using React Flow
3. **Split View** - Side-by-side JSON and visual representation

## Architecture

### Component Hierarchy

```
WorkflowVisualEditor (Main Container)
├── Radix UI Tabs (Tab Management)
│   ├── Tab List (JSON Editor | Visual Graph | Split View)
│   └── Tab Content
│       ├── JSON Editor Tab
│       │   └── JSONEditor Component
│       │       └── Monaco Editor
│       ├── Visual Graph Tab
│       │   └── WorkflowGraph Component
│       │       └── React Flow
│       └── Split View Tab
│           ├── JSONEditor Component (Left)
│           └── WorkflowGraph Component (Right)
```

## Key Components

### 1. WorkflowVisualEditor

**Location**: `src/components/workflows/WorkflowVisualEditor.tsx`

**Purpose**: Main container component that manages tabs and coordinates between JSON and visual views.

**Props**:
```typescript
interface WorkflowVisualEditorProps {
  value: string;                    // JSON string of workflow definition
  onChange: (value: string) => void; // Callback when JSON changes
  onValidate?: (valid: boolean, errors: string[]) => void; // Validation callback
  agentNames?: string[];            // List of available agents for autocomplete
  readOnly?: boolean;               // Whether editor is read-only
  height?: string;                  // Container height (default: '600px')
}
```

**Key Features**:
- Three-tab interface (JSON, Visual, Split)
- Real-time validation status indicator
- Synchronized state between JSON and visual views
- Step selection across views
- Responsive layout with proper height management

**State Management**:
```typescript
const [activeTab, setActiveTab] = useState<'json' | 'visual' | 'split'>('split');
const [isValid, setIsValid] = useState(true);
const [validationErrors, setValidationErrors] = useState<string[]>([]);
const [selectedStepId, setSelectedStepId] = useState<string | undefined>();
```

### 2. JSONEditor

**Location**: `src/components/common/JSONEditor.tsx`

**Purpose**: Monaco-based JSON editor with schema validation and autocomplete.

**Props**:
```typescript
interface JSONEditorProps {
  value: string;
  onChange: (value: string) => void;
  onValidate?: (isValid: boolean, errors: string[]) => void;
  readOnly?: boolean;
  height?: string;
  agentNames?: string[];
  className?: string;
}
```

**Key Features**:
- Monaco Editor integration
- JSON schema validation
- Custom workflow validation rules
- Agent name autocomplete
- Syntax highlighting and error markers
- Circular dependency detection
- Real-time validation feedback

**Validation Rules**:
1. **Required Fields**:
   - `start_step`: Must be present
   - `steps`: Must be an object
   - Each step must have: `id`, `agent_name`, `input_mapping`

2. **Reference Validation**:
   - `start_step` must exist in `steps`
   - `next_step` references must be valid
   - Agent names should be registered (warning if not)

3. **Circular Dependency Detection**:
   - Detects cycles in step dependencies
   - Prevents infinite loops

### 3. WorkflowGraph

**Location**: `src/components/workflows/WorkflowGraph.tsx`

**Purpose**: Visual representation of workflow using React Flow.

**Props**:
```typescript
interface WorkflowGraphProps {
  workflow: WorkflowDefinition;
  onStepClick?: (stepId: string) => void;
  selectedStepId?: string;
  stepStatuses?: Record<string, 'pending' | 'running' | 'completed' | 'failed'>;
  stepErrors?: Record<string, string>;
  className?: string;
}
```

**Key Features**:
- Automatic layout calculation
- Level-based positioning
- Interactive nodes
- Animated edges for running steps
- Status-based coloring
- Mini-map for navigation
- Zoom and pan controls

**Layout Algorithm**:
1. Calculate dependency levels for each step
2. Group steps by level
3. Position horizontally by level
4. Position vertically within level
5. Create edges between connected steps

### 4. WorkflowStepNode

**Location**: `src/components/workflows/WorkflowStepNode.tsx`

**Purpose**: Custom React Flow node for workflow steps.

**Features**:
- Status indicators (pending, running, completed, failed)
- Agent name display
- Input/output handles
- Error display
- Hover effects
- Selection state

## Layout & Styling

### Height Management

The component uses a robust height management system:

```typescript
// Parent container
<div style={{ height }}>  // e.g., "600px"
  
  // Tab header (fixed height: 49px)
  <div className="flex-shrink-0">
    {/* Tabs */}
  </div>
  
  // Content area (fills remaining space)
  <div className="flex-1 overflow-hidden relative">
    {/* Tab content with absolute positioning */}
    <Tabs.Content className="absolute inset-0">
      {/* Content fills 100% */}
    </Tabs.Content>
  </div>
</div>
```

### Split View Layout

```
┌─────────────────────────────────────────┐
│  JSON Editor Tab | Visual Graph | Split │  ← Tab Header (49px)
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┬──────────────┐       │
│  │              │              │       │
│  │   JSON       │   Visual     │       │  ← Content Area
│  │   Editor     │   Graph      │       │    (height - 49px)
│  │              │              │       │
│  │   (50%)      │   (50%)      │       │
│  └──────────────┴──────────────┘       │
│                                         │
└─────────────────────────────────────────┘
```

## Data Flow

### 1. JSON Editing Flow

```
User types in Monaco Editor
    ↓
onChange event fires
    ↓
validateJSON() runs
    ↓
Validation results → onValidate callback
    ↓
Parent component updates state
    ↓
workflowDefinition memo recalculates
    ↓
Visual graph updates automatically
```

### 2. Visual Interaction Flow

```
User clicks node in graph
    ↓
onNodeClick event fires
    ↓
handleStepClick() called
    ↓
selectedStepId state updates
    ↓
Node highlights in graph
    ↓
(Optional) Switch to split view
```

## Workflow Definition Schema

```typescript
interface WorkflowDefinition {
  name?: string;
  version?: string;
  start_step: string;
  steps: {
    [stepId: string]: {
      id: string;
      agent_name: string;
      next_step: string | null;
      input_mapping: Record<string, any>;
    };
  };
}
```

### Example Workflow

```json
{
  "name": "Example Workflow",
  "start_step": "step-1",
  "steps": {
    "step-1": {
      "id": "step-1",
      "agent_name": "DataFetcher",
      "next_step": "step-2",
      "input_mapping": {
        "url": "https://api.example.com/data"
      }
    },
    "step-2": {
      "id": "step-2",
      "agent_name": "DataProcessor",
      "next_step": null,
      "input_mapping": {
        "data": "{{step-1.output}}"
      }
    }
  }
}
```

## Usage Examples

### Basic Usage

```tsx
import WorkflowVisualEditor from '@/components/workflows/WorkflowVisualEditor';

function MyComponent() {
  const [workflowJson, setWorkflowJson] = useState('{}');
  const [isValid, setIsValid] = useState(false);

  return (
    <WorkflowVisualEditor
      value={workflowJson}
      onChange={setWorkflowJson}
      onValidate={(valid, errors) => {
        setIsValid(valid);
        console.log('Validation errors:', errors);
      }}
      height="600px"
    />
  );
}
```

### With Agent Names

```tsx
<WorkflowVisualEditor
  value={workflowJson}
  onChange={setWorkflowJson}
  agentNames={['Agent1', 'Agent2', 'Agent3']}
  height="800px"
/>
```

### Read-Only Mode

```tsx
<WorkflowVisualEditor
  value={workflowJson}
  onChange={() => {}}
  readOnly={true}
  height="600px"
/>
```

## Performance Optimizations

1. **Memoization**:
   - `workflowDefinition` is memoized to prevent unnecessary recalculations
   - Graph layout is calculated once per workflow change

2. **Lazy Rendering**:
   - Only active tab content is rendered
   - Inactive tabs use `display: none` via Radix UI

3. **Monaco Editor**:
   - `automaticLayout: true` for responsive resizing
   - Minimap enabled for large files
   - Efficient syntax highlighting

4. **React Flow**:
   - `fitView` on mount for optimal initial view
   - Controlled zoom levels (0.1 - 2.0)
   - Efficient edge rendering

## Accessibility

1. **Keyboard Navigation**:
   - Tab key to switch between tabs
   - Arrow keys to navigate graph nodes
   - Enter/Space to select nodes

2. **Screen Reader Support**:
   - Proper ARIA labels on tabs
   - Role attributes on interactive elements
   - Descriptive text for graph elements

3. **Visual Indicators**:
   - Color-coded status (with icons)
   - High contrast mode support
   - Focus indicators

## Browser Compatibility

- **Chrome/Edge**: ✅ Full support
- **Firefox**: ✅ Full support
- **Safari**: ✅ Full support
- **Mobile**: ⚠️ Limited (touch interactions may vary)

## Known Limitations

1. **Large Workflows**:
   - Performance may degrade with 100+ steps
   - Consider pagination or virtualization for very large workflows

2. **Complex Layouts**:
   - Automatic layout works best for linear/tree structures
   - Highly interconnected graphs may overlap

3. **Mobile Support**:
   - Split view may be cramped on small screens
   - Consider responsive breakpoints for mobile

## Troubleshooting

### Issue: Editor shows only 5px height

**Cause**: Parent container doesn't have explicit height
**Solution**: Ensure parent has `height` style or use `height="100%"` with sized parent

### Issue: Graph doesn't render

**Cause**: Invalid workflow definition or missing required fields
**Solution**: Check validation errors in JSON editor tab

### Issue: Tabs don't switch

**Cause**: Radix UI state management issue
**Solution**: Ensure `data-[state=active]` and `data-[state=inactive]` classes are applied

### Issue: Monaco editor not loading

**Cause**: Monaco worker files not found
**Solution**: Ensure Vite is configured to serve Monaco workers

## Future Enhancements

1. **Drag-and-Drop Editor**:
   - Visual workflow builder
   - Drag nodes to create steps
   - Connect nodes to define flow

2. **Advanced Validation**:
   - Type checking for input/output mappings
   - Schema validation for agent-specific inputs

3. **Collaboration Features**:
   - Real-time collaborative editing
   - Change tracking and history

4. **Export/Import**:
   - Export as PNG/SVG
   - Import from various formats

5. **Templates**:
   - Pre-built workflow templates
   - Template library

## Testing

### Unit Tests

```typescript
describe('WorkflowVisualEditor', () => {
  it('should render all three tabs', () => {
    // Test implementation
  });

  it('should validate workflow definition', () => {
    // Test implementation
  });

  it('should sync selection between views', () => {
    // Test implementation
  });
});
```

### Integration Tests

```typescript
describe('Workflow Editor Integration', () => {
  it('should update graph when JSON changes', () => {
    // Test implementation
  });

  it('should highlight step when clicked in graph', () => {
    // Test implementation
  });
});
```

## Maintenance

### Dependencies

- `@monaco-editor/react`: ^4.7.0
- `reactflow`: ^11.11.4
- `@radix-ui/react-tabs`: ^1.1.13

### Update Checklist

When updating the component:
1. ✅ Test all three tab views
2. ✅ Verify validation works
3. ✅ Check height management
4. ✅ Test with various workflow sizes
5. ✅ Verify accessibility
6. ✅ Check browser compatibility

## Support

For issues or questions:
- Check validation errors in the editor
- Review browser console for errors
- Verify workflow definition schema
- Check Monaco/React Flow documentation

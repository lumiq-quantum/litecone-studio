# Design Document: Workflow Management UI

## Overview

This design implements a modern, beautiful React-based web application for managing the Workflow Orchestration System. The UI provides intuitive interfaces for agent management, workflow creation with JSON editing, visual workflow execution tracking, and comprehensive run result visualization. The design emphasizes user experience with smooth animations, real-time updates, and a clean, modern aesthetic.

## Technology Stack

### Core Framework
- **React 18+**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server

### UI Framework & Styling
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: High-quality, accessible component library
- **Radix UI**: Headless UI primitives for accessibility
- **Lucide React**: Beautiful, consistent icon set
- **Framer Motion**: Smooth animations and transitions

### State Management & Data Fetching
- **TanStack Query (React Query)**: Server state management with caching
- **Zustand**: Lightweight client state management
- **Axios**: HTTP client for API calls

### Workflow Visualization
- **React Flow**: Interactive node-based workflow graphs
- **D3.js**: Custom visualizations and charts

### Code Editing
- **Monaco Editor**: VS Code-powered JSON editor with syntax highlighting
- **JSON Schema Validator**: Real-time JSON validation

### Routing & Navigation
- **React Router v6**: Client-side routing
- **React Helmet**: Dynamic page titles and meta tags

### Utilities
- **date-fns**: Date formatting and manipulation
- **clsx**: Conditional className utility
- **react-hot-toast**: Beautiful toast notifications
- **react-json-view**: Interactive JSON viewer

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              React Application                        │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Pages (Routes)                                 │  │  │
│  │  │  - Dashboard                                    │  │  │
│  │  │  - Agents List/Detail                           │  │  │
│  │  │  - Workflows List/Detail                        │  │  │
│  │  │  - Runs List/Detail                             │  │  │
│  │  └─────────────────┬───────────────────────────────┘  │  │
│  │                    │                                   │  │
│  │  ┌─────────────────▼───────────────────────────────┐  │  │
│  │  │  Components                                     │  │  │
│  │  │  - AgentCard, AgentForm                         │  │  │
│  │  │  - WorkflowEditor, WorkflowGraph                │  │  │
│  │  │  - ExecutionGraph, StepDetails                  │  │  │
│  │  │  - JSONEditor, JSONViewer                       │  │  │
│  │  └─────────────────┬───────────────────────────────┘  │  │
│  │                    │                                   │  │
│  │  ┌─────────────────▼───────────────────────────────┐  │  │
│  │  │  Hooks & Services                               │  │  │
│  │  │  - useAgents, useWorkflows, useRuns             │  │  │
│  │  │  - API Client (Axios)                           │  │  │
│  │  │  - WebSocket/Polling Service                    │  │  │
│  │  └─────────────────┬───────────────────────────────┘  │  │
│  └────────────────────┼───────────────────────────────────┘  │
└───────────────────────┼─────────────────────────────────────┘
                        │ HTTP/REST
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Workflow Management API                        │
│              (FastAPI Backend)                              │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
workflow-ui/
├── public/
│   ├── favicon.ico
│   └── logo.svg
│
├── src/
│   ├── main.tsx                 # Application entry point
│   ├── App.tsx                  # Root component with routing
│   ├── index.css                # Global styles
│   │
│   ├── pages/                   # Page components
│   │   ├── Dashboard.tsx
│   │   ├── agents/
│   │   │   ├── AgentsList.tsx
│   │   │   └── AgentDetail.tsx
│   │   ├── workflows/
│   │   │   ├── WorkflowsList.tsx
│   │   │   ├── WorkflowDetail.tsx
│   │   │   ├── WorkflowCreate.tsx
│   │   │   └── WorkflowEdit.tsx
│   │   └── runs/
│   │       ├── RunsList.tsx
│   │       └── RunDetail.tsx
│   │
│   ├── components/              # Reusable components
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Breadcrumbs.tsx
│   │   ├── agents/
│   │   │   ├── AgentCard.tsx
│   │   │   ├── AgentForm.tsx
│   │   │   └── AgentHealthBadge.tsx
│   │   ├── workflows/
│   │   │   ├── WorkflowCard.tsx
│   │   │   ├── WorkflowGraph.tsx
│   │   │   ├── WorkflowEditor.tsx
│   │   │   └── VersionSelector.tsx
│   │   ├── runs/
│   │   │   ├── RunCard.tsx
│   │   │   ├── ExecutionGraph.tsx
│   │   │   ├── StepDetails.tsx
│   │   │   └── RunStatusBadge.tsx
│   │   ├── common/
│   │   │   ├── JSONEditor.tsx
│   │   │   ├── JSONViewer.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── ConfirmDialog.tsx
│   │   │   └── EmptyState.tsx
│   │   └── ui/                  # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── dialog.tsx
│   │       ├── input.tsx
│   │       ├── select.tsx
│   │       ├── badge.tsx
│   │       └── ...
│   │
│   ├── hooks/                   # Custom React hooks
│   │   ├── useAgents.ts
│   │   ├── useWorkflows.ts
│   │   ├── useRuns.ts
│   │   ├── usePolling.ts
│   │   └── useToast.ts
│   │
│   ├── services/                # API and business logic
│   │   ├── api/
│   │   │   ├── client.ts        # Axios instance
│   │   │   ├── agents.ts
│   │   │   ├── workflows.ts
│   │   │   └── runs.ts
│   │   └── polling.ts           # Real-time polling service
│   │
│   ├── types/                   # TypeScript types
│   │   ├── agent.ts
│   │   ├── workflow.ts
│   │   ├── run.ts
│   │   └── common.ts
│   │
│   ├── utils/                   # Utility functions
│   │   ├── formatters.ts        # Date, duration formatting
│   │   ├── validators.ts        # JSON validation
│   │   ├── colors.ts            # Status colors
│   │   └── constants.ts         # App constants
│   │
│   └── store/                   # Zustand stores
│       ├── uiStore.ts           # UI state (sidebar, theme)
│       └── filterStore.ts       # Filter state
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## Design System

### Color Palette

```typescript
// Primary Colors
const colors = {
  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    500: '#0ea5e9',  // Main brand color
    600: '#0284c7',
    700: '#0369a1',
  },
  
  // Status Colors
  success: '#10b981',  // Green for completed
  warning: '#f59e0b',  // Amber for pending
  error: '#ef4444',    // Red for failed
  info: '#3b82f6',     // Blue for running
  
  // Neutral
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    500: '#6b7280',
    700: '#374151',
    900: '#111827',
  }
}
```

### Typography

```typescript
// Font Stack
fontFamily: {
  sans: ['Inter', 'system-ui', 'sans-serif'],
  mono: ['JetBrains Mono', 'Consolas', 'monospace'],
}

// Font Sizes
fontSize: {
  xs: '0.75rem',    // 12px
  sm: '0.875rem',   // 14px
  base: '1rem',     // 16px
  lg: '1.125rem',   // 18px
  xl: '1.25rem',    // 20px
  '2xl': '1.5rem',  // 24px
  '3xl': '1.875rem',// 30px
}
```

### Spacing & Layout

```typescript
// Consistent spacing scale
spacing: {
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  6: '1.5rem',   // 24px
  8: '2rem',     // 32px
  12: '3rem',    // 48px
}

// Border Radius
borderRadius: {
  sm: '0.25rem',  // 4px
  md: '0.375rem', // 6px
  lg: '0.5rem',   // 8px
  xl: '0.75rem',  // 12px
}
```

## Key Components Design

### 1. Dashboard Page

**Layout:**
- Header with app title and quick actions
- Summary cards showing:
  - Total Agents (with active count)
  - Total Workflows (with versions)
  - Recent Runs (with status breakdown)
  - Success Rate (percentage chart)
- Recent activity feed
- Quick access buttons to create agent/workflow

**Visual Design:**
- Clean, card-based layout
- Animated counters for statistics
- Mini charts using D3.js
- Gradient backgrounds on cards

### 2. Agents List Page

**Layout:**
- Search bar and filter controls
- Grid of agent cards (3-4 columns on desktop)
- "Add Agent" floating action button

**Agent Card Design:**
```
┌─────────────────────────────────┐
│ 🤖 Agent Name          [Active] │
│                                 │
│ https://agent-url.com           │
│ Description text here...        │
│                                 │
│ ⏱️ Timeout: 30s  🔄 Retries: 3 │
│                                 │
│ [Edit] [Delete] [Test Health]  │
└─────────────────────────────────┘
```

**Features:**
- Health status indicator (green dot = healthy)
- Hover effects with elevation
- Quick actions on hover
- Smooth card animations on load

### 3. Workflow Editor

**Layout:**
- Split view: JSON editor (left) + Visual preview (right)
- Top toolbar with Save, Cancel, Validate buttons
- Bottom status bar showing validation errors

**JSON Editor Features:**
- Monaco Editor with JSON schema validation
- Syntax highlighting
- Auto-completion for agent names
- Error squiggles with hover tooltips
- Line numbers and minimap

**Visual Preview:**
- React Flow graph showing step connections
- Color-coded nodes by agent type
- Animated connections between steps
- Zoom and pan controls

### 4. Execution Graph Component

**Design:**
```
Start → [Step 1] → [Step 2] → [Step 3] → End
         ✓ Done     ⟳ Running   ⏸ Pending
```

**Node States:**
- **Pending**: Gray with dashed border
- **Running**: Blue with pulsing animation
- **Completed**: Green with checkmark
- **Failed**: Red with X icon

**Interactions:**
- Click node to view details in side panel
- Hover to see quick info tooltip
- Animated transitions between states
- Progress bar showing overall completion

### 5. Step Details Panel

**Layout:**
```
┌─────────────────────────────────────┐
│ Step: step-1                        │
│ Agent: DataFetcher                  │
│ Status: ✓ Completed                 │
│ Duration: 2.3s                      │
├─────────────────────────────────────┤
│ 📥 Input Data                       │
│ ┌─────────────────────────────────┐ │
│ │ {                               │ │
│ │   "user_id": "12345"            │ │
│ │ }                               │ │
│ └─────────────────────────────────┘ │
│ [Copy]                              │
├─────────────────────────────────────┤
│ 📤 Output Data                      │
│ ┌─────────────────────────────────┐ │
│ │ {                               │ │
│ │   "name": "John Doe",           │ │
│ │   "email": "john@example.com"   │ │
│ │ }                               │ │
│ └─────────────────────────────────┘ │
│ [Copy] [Download]                   │
└─────────────────────────────────────┘
```

**Features:**
- Collapsible sections
- Syntax-highlighted JSON
- Copy to clipboard buttons
- Download as file option
- Timing information with timeline

### 6. Run List Page

**Layout:**
- Filter bar (status, workflow, date range)
- Table view with columns:
  - Run ID (clickable)
  - Workflow Name
  - Status (badge)
  - Started At
  - Duration
  - Actions (View, Retry)
- Pagination controls

**Status Badges:**
- PENDING: Yellow with clock icon
- RUNNING: Blue with spinner
- COMPLETED: Green with checkmark
- FAILED: Red with X icon

### 7. Workflow Version Selector

**Design:**
```
┌─────────────────────────────────────┐
│ Version History                     │
├─────────────────────────────────────┤
│ ● v3 (Current) - 2 hours ago        │
│   Created by: system                │
│   [View] [Execute]                  │
├─────────────────────────────────────┤
│ ○ v2 - 1 day ago                    │
│   Created by: system                │
│   [View] [Execute] [Compare]        │
├─────────────────────────────────────┤
│ ○ v1 - 3 days ago                   │
│   Created by: system                │
│   [View] [Execute] [Compare]        │
└─────────────────────────────────────┘
```

**Features:**
- Timeline view with dots
- Current version highlighted
- Quick actions per version
- Diff view when comparing versions

## API Integration

### API Client Setup

```typescript
// src/services/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for future auth
apiClient.interceptors.request.use((config) => {
  // Add auth token when implemented
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors globally
    if (error.response?.status === 404) {
      toast.error('Resource not found');
    } else if (error.response?.status === 500) {
      toast.error('Server error occurred');
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### React Query Hooks

```typescript
// src/hooks/useAgents.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as agentsApi from '@/services/api/agents';

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: agentsApi.listAgents,
  });
}

export function useAgent(id: string) {
  return useQuery({
    queryKey: ['agents', id],
    queryFn: () => agentsApi.getAgent(id),
    enabled: !!id,
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: agentsApi.createAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      toast.success('Agent created successfully');
    },
    onError: (error) => {
      toast.error('Failed to create agent');
    },
  });
}
```

### Real-time Polling

```typescript
// src/hooks/usePolling.ts
import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export function useRunPolling(runId: string, enabled: boolean) {
  const queryClient = useQueryClient();
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!enabled) return;

    intervalRef.current = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['runs', runId] });
    }, 2000); // Poll every 2 seconds

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [runId, enabled, queryClient]);
}
```

## Animations & Transitions

### Page Transitions

```typescript
// Using Framer Motion
import { motion } from 'framer-motion';

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

function Page() {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.3 }}
    >
      {/* Page content */}
    </motion.div>
  );
}
```

### Loading States

```typescript
// Skeleton loaders for cards
function AgentCardSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
    </div>
  );
}
```

### Status Transitions

```typescript
// Pulsing animation for running status
const pulseAnimation = {
  scale: [1, 1.1, 1],
  opacity: [1, 0.8, 1],
  transition: {
    duration: 1.5,
    repeat: Infinity,
    ease: "easeInOut",
  },
};
```

## Error Handling

### Error Boundary

```typescript
// src/components/common/ErrorBoundary.tsx
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-container">
          <h2>Something went wrong</h2>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Toast Notifications

```typescript
// Using react-hot-toast
import toast from 'react-hot-toast';

// Success
toast.success('Workflow created successfully');

// Error
toast.error('Failed to execute workflow');

// Loading
const toastId = toast.loading('Creating workflow...');
// Later: toast.success('Done!', { id: toastId });
```

## Performance Optimizations

### Code Splitting

```typescript
// Lazy load pages
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const WorkflowDetail = lazy(() => import('@/pages/workflows/WorkflowDetail'));

// Use Suspense
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/workflows/:id" element={<WorkflowDetail />} />
  </Routes>
</Suspense>
```

### Memoization

```typescript
// Memoize expensive computations
const workflowGraph = useMemo(() => {
  return buildGraphFromWorkflow(workflow);
}, [workflow]);

// Memoize callbacks
const handleStepClick = useCallback((stepId: string) => {
  setSelectedStep(stepId);
}, []);
```

### Virtual Scrolling

```typescript
// For large lists of runs
import { useVirtualizer } from '@tanstack/react-virtual';

function RunsList({ runs }) {
  const parentRef = useRef();
  
  const virtualizer = useVirtualizer({
    count: runs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
  });

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      {virtualizer.getVirtualItems().map((virtualRow) => (
        <RunCard key={virtualRow.key} run={runs[virtualRow.index]} />
      ))}
    </div>
  );
}
```

## Accessibility

### Keyboard Navigation

- Tab through interactive elements
- Enter/Space to activate buttons
- Escape to close modals
- Arrow keys for navigation in lists

### ARIA Labels

```typescript
<button
  aria-label="Delete agent"
  aria-describedby="delete-description"
>
  <TrashIcon />
</button>
```

### Focus Management

```typescript
// Auto-focus first input in modals
useEffect(() => {
  if (isOpen) {
    inputRef.current?.focus();
  }
}, [isOpen]);
```

## Testing Strategy

### Unit Tests
- Test utility functions
- Test custom hooks
- Test component logic

### Integration Tests
- Test API integration
- Test form submissions
- Test navigation flows

### E2E Tests (Playwright)
- Test complete workflows
- Test execution visualization
- Test retry functionality

## Deployment

### Environment Variables

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_POLLING_INTERVAL=2000
VITE_APP_NAME=Workflow Manager
```

### Build Configuration

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-select'],
          'editor': ['monaco-editor', 'react-monaco-editor'],
        },
      },
    },
  },
});
```

### Docker Deployment

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

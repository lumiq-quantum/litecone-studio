# API Client and Service Layer

This document describes the API client and service layer implementation for the Workflow Management UI.

## Overview

The API client layer provides a type-safe, organized way to interact with the Workflow Management API. It includes:

- **TypeScript Types**: Complete type definitions for all API entities
- **Axios Client**: Configured HTTP client with interceptors
- **API Services**: Organized service modules for each resource
- **React Query Hooks**: Custom hooks for data fetching and mutations

## Structure

```
src/
├── types/                    # TypeScript type definitions
│   ├── common.ts            # Common types (pagination, errors, etc.)
│   ├── agent.ts             # Agent-related types
│   ├── workflow.ts          # Workflow-related types
│   ├── run.ts               # Run-related types
│   └── index.ts             # Central export
│
├── services/api/            # API service layer
│   ├── client.ts            # Axios client configuration
│   ├── agents.ts            # Agent API methods
│   ├── workflows.ts         # Workflow API methods
│   ├── runs.ts              # Run API methods
│   └── index.ts             # Central export
│
└── hooks/                   # React Query hooks
    ├── useAgents.ts         # Agent hooks
    ├── useWorkflows.ts      # Workflow hooks
    ├── useRuns.ts           # Run hooks
    └── index.ts             # Central export
```

## Usage Examples

### Using API Services Directly

```typescript
import { agentsApi } from '@/services/api';

// List agents
const agents = await agentsApi.listAgents({ page: 1, page_size: 20 });

// Create an agent
const newAgent = await agentsApi.createAgent({
  name: 'my-agent',
  url: 'http://localhost:8080',
  description: 'My test agent',
});

// Get agent details
const agent = await agentsApi.getAgent(agentId);

// Update agent
const updated = await agentsApi.updateAgent(agentId, {
  description: 'Updated description',
});

// Delete agent
await agentsApi.deleteAgent(agentId);

// Check health
const health = await agentsApi.checkAgentHealth(agentId);
```

### Using React Query Hooks (Recommended)

```typescript
import { useAgents, useCreateAgent, useAgent } from '@/hooks';

function AgentsList() {
  // Fetch agents with automatic caching and refetching
  const { data, isLoading, error } = useAgents({ page: 1, page_size: 20 });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data?.items.map((agent) => (
        <div key={agent.id}>{agent.name}</div>
      ))}
    </div>
  );
}

function CreateAgentForm() {
  const createAgent = useCreateAgent();

  const handleSubmit = async (formData) => {
    try {
      await createAgent.mutateAsync(formData);
      // Success! The agent list will automatically refetch
    } catch (error) {
      // Handle error
    }
  };

  return <form onSubmit={handleSubmit}>...</form>;
}

function AgentDetail({ agentId }) {
  // Fetch single agent
  const { data: agent } = useAgent(agentId);

  return <div>{agent?.name}</div>;
}
```

### Workflow Hooks

```typescript
import { useWorkflows, useExecuteWorkflow } from '@/hooks';

function WorkflowsList() {
  const { data } = useWorkflows({ status: 'active' });

  return (
    <div>
      {data?.items.map((workflow) => (
        <div key={workflow.id}>{workflow.name}</div>
      ))}
    </div>
  );
}

function ExecuteWorkflow({ workflowId }) {
  const executeWorkflow = useExecuteWorkflow();

  const handleExecute = async () => {
    const result = await executeWorkflow.mutateAsync({
      workflowId,
      data: {
        input_data: { key: 'value' },
      },
    });
    console.log('Run ID:', result.run_id);
  };

  return <button onClick={handleExecute}>Execute</button>;
}
```

### Run Hooks

```typescript
import { useRuns, useRun, useRunSteps, useRetryRun } from '@/hooks';

function RunsList() {
  const { data } = useRuns({
    status: 'FAILED',
    page: 1,
    page_size: 20,
  });

  return (
    <div>
      {data?.items.map((run) => (
        <div key={run.id}>
          {run.workflow_name} - {run.status}
        </div>
      ))}
    </div>
  );
}

function RunDetail({ runId }) {
  const { data: run } = useRun(runId);
  const { data: steps } = useRunSteps(runId);
  const retryRun = useRetryRun();

  const handleRetry = async () => {
    const result = await retryRun.mutateAsync({ runId });
    console.log('New run ID:', result.new_run_id);
  };

  return (
    <div>
      <h2>{run?.workflow_name}</h2>
      <p>Status: {run?.status}</p>
      {run?.status === 'FAILED' && (
        <button onClick={handleRetry}>Retry</button>
      )}
      <div>
        {steps?.items.map((step) => (
          <div key={step.id}>
            {step.step_name} - {step.status}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Configuration

### Environment Variables

Configure the API base URL in `.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_POLLING_INTERVAL=2000
VITE_APP_NAME=Workflow Manager
```

### React Query Configuration

The QueryClient is configured in `src/main.tsx` with:

- **staleTime**: 60 seconds (data is considered fresh for 1 minute)
- **refetchOnWindowFocus**: false (don't refetch when window regains focus)
- **retry**: 1 (retry failed requests once)

You can customize these settings in `main.tsx`.

## Features

### Automatic Cache Management

React Query hooks automatically:
- Cache API responses
- Deduplicate identical requests
- Invalidate and refetch data after mutations
- Provide loading and error states

### Type Safety

All API calls are fully typed:
- Request payloads are validated at compile time
- Response data has complete type information
- No manual type casting needed

### Error Handling

The Axios client includes:
- Request/response interceptors
- Automatic error logging
- Consistent error format
- HTTP status code handling

### Query Key Management

Each hook module exports a query key factory for consistent cache keys:

```typescript
import { agentKeys } from '@/hooks/useAgents';

// Invalidate all agent queries
queryClient.invalidateQueries({ queryKey: agentKeys.all });

// Invalidate specific agent
queryClient.invalidateQueries({ queryKey: agentKeys.detail(agentId) });
```

## Best Practices

1. **Use hooks in components**: Prefer React Query hooks over direct API calls
2. **Handle loading states**: Always check `isLoading` before rendering data
3. **Handle errors**: Display user-friendly error messages
4. **Optimistic updates**: Use `onMutate` for instant UI feedback
5. **Invalidate queries**: Let React Query handle cache invalidation after mutations

## Next Steps

With the API client layer complete, you can now:
1. Build UI components that consume these hooks
2. Implement forms for creating/editing resources
3. Create list views with pagination
4. Build detail pages with real-time updates
5. Add polling for workflow execution monitoring

## Testing

To test the API client:

1. Start the backend API server
2. Start the development server: `npm run dev`
3. Open the browser console to see API request logs
4. Use the React Query DevTools (add `@tanstack/react-query-devtools` for debugging)

## Troubleshooting

### CORS Errors

If you see CORS errors, make sure:
- The API server is running
- The API URL in `.env` is correct
- The API server has CORS enabled

### Type Errors

If you see TypeScript errors:
- Run `npm run type-check` to see all errors
- Make sure all imports use the `@/` alias
- Check that types are exported from `@/types`

### Network Errors

If API calls fail:
- Check the browser console for error details
- Verify the API server is accessible
- Check the network tab in browser DevTools
- Ensure the API base URL is correct

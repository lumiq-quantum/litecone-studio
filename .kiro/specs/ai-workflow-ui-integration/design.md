# Design Document

## Overview

The AI Workflow Generator UI Integration enhances the existing workflow creation page by adding a collapsible sidebar panel that provides AI-powered workflow generation capabilities. Users can generate workflows from natural language descriptions or PDF documents, then iteratively refine them through an interactive chat interface. The generated workflows automatically populate the existing JSON editor and visual graph components, creating a seamless experience between AI-assisted and manual workflow creation.

### Key Design Goals

1. **Non-Intrusive Integration**: Preserve all existing workflow creation functionality
2. **Seamless Experience**: Smooth transitions between AI generation and manual editing
3. **Real-Time Feedback**: Immediate visual updates when workflows are generated or modified
4. **Session Persistence**: Maintain chat history while user is on the page
5. **Error Resilience**: Graceful handling of API failures and session expiration

## Architecture

### High-Level Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    WorkflowCreate Page                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Header: [Use Template] [AI Generate] [Create]       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────────┐   │
│  │                      │  │                          │   │
│  │   JSON Editor        │  │   AI Generate Sidebar    │   │
│  │   (Monaco)           │  │   (Collapsible)          │   │
│  │                      │  │                          │   │
│  │                      │  │  ┌────────────────────┐  │   │
│  │                      │  │  │ Initial View:      │  │   │
│  │                      │  │  │ - Welcome Message  │  │   │
│  │                      │  │  │ - Text Input       │  │   │
│  │                      │  │  │ - PDF Upload       │  │   │
│  │                      │  │  │ - Generate Button  │  │   │
│  │                      │  │  └────────────────────┘  │   │
│  │                      │  │                          │   │
│  │                      │  │  ┌────────────────────┐  │   │
│  │                      │  │  │ Chat View:         │  │   │
│  │                      │  │  │ - Message History  │  │   │
│  │                      │  │  │ - AI Responses     │  │   │
│  │                      │  │  │ - Input Field      │  │   │
│  │                      │  │  └────────────────────┘  │   │
│  │                      │  │                          │   │
│  └──────────────────────┘  └──────────────────────────┘   │
│                                                              │
│  ┌──────────────────────┐                                   │
│  │   Visual Graph       │                                   │
│  │   (Hidden when       │                                   │
│  │    sidebar open)     │                                   │
│  └──────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
WorkflowCreate
├── Header (existing)
│   ├── Use Template Button (existing)
│   ├── AI Generate Button (new)
│   └── Create Workflow Button (existing)
├── Basic Information Form (existing)
├── Workflow Definition Section (existing)
│   ├── WorkflowVisualEditor (existing)
│   └── AIGenerateSidebar (new)
│       ├── SidebarHeader
│       ├── InitialView (conditional)
│       │   ├── WelcomeMessage
│       │   ├── DescriptionInput
│       │   ├── PDFUpload
│       │   └── GenerateButton
│       └── ChatView (conditional)
│           ├── MessageList
│           │   ├── UserMessage
│           │   ├── AssistantMessage
│           │   └── SystemMessage
│           ├── LoadingIndicator
│           └── ChatInput
└── Actions (existing)
```

## Components and Interfaces

### 1. AIGenerateSidebar Component

**Responsibilities:**
- Manage sidebar open/close state
- Handle chat session lifecycle
- Coordinate between initial view and chat view
- Manage API communication
- Update JSON editor with generated workflows

**Props:**

```typescript
interface AIGenerateSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentWorkflowJson: string;
  onWorkflowUpdate: (json: string, explanation: string) => void;
  agentNames: string[];
}
```

**State:**

```typescript
interface AIGenerateSidebarState {
  view: 'initial' | 'chat';
  sessionId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  description: string;
  uploadedFile: File | null;
}
```

### 2. InitialView Component

**Responsibilities:**
- Display welcome message and instructions
- Handle text description input
- Handle PDF file upload
- Validate inputs before generation
- Trigger initial workflow generation

**Props:**

```typescript
interface InitialViewProps {
  onGenerate: (description: string) => Promise<void>;
  onUpload: (file: File) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}
```

### 3. ChatView Component

**Responsibilities:**
- Display conversation history
- Handle user message input
- Show AI responses with explanations
- Display loading states
- Handle error messages

**Props:**

```typescript
interface ChatViewProps {
  messages: Message[];
  onSendMessage: (message: string) => Promise<void>;
  isLoading: boolean;
  sessionId: string;
}
```

### 4. AI Workflow Service

**Responsibilities:**
- Communicate with AI Workflow API
- Manage chat sessions
- Handle errors and retries
- Format requests and responses

**Interface:**

```typescript
class AIWorkflowService {
  // Create a new chat session
  async createSession(initialDescription?: string): Promise<ChatSession>;
  
  // Send a message to existing session
  async sendMessage(sessionId: string, message: string): Promise<ChatSession>;
  
  // Get session details
  async getSession(sessionId: string): Promise<ChatSession>;
  
  // Upload PDF for workflow generation
  async uploadDocument(file: File): Promise<WorkflowGenerationResult>;
  
  // Delete session
  async deleteSession(sessionId: string): Promise<void>;
  
  // Export workflow JSON
  async exportWorkflow(sessionId: string): Promise<Blob>;
}
```

## Data Models

### Message

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    success?: boolean;
    validation_errors?: string[];
    suggestions?: string[];
    agents_used?: string[];
  };
}
```

### ChatSession

```typescript
interface ChatSession {
  id: string;
  user_id?: string;
  status: 'active' | 'completed' | 'expired';
  created_at: string;
  updated_at: string;
  expires_at: string;
  messages: Message[];
  current_workflow: WorkflowJSON | null;
  workflow_history: WorkflowJSON[];
}
```

### WorkflowGenerationResult

```typescript
interface WorkflowGenerationResult {
  success: boolean;
  workflow_json: WorkflowJSON | null;
  explanation: string;
  validation_errors: string[];
  suggestions: string[];
  agents_used: string[];
}
```

### WorkflowJSON

```typescript
interface WorkflowJSON {
  name: string;
  description?: string;
  start_step: string;
  steps: Record<string, WorkflowStep>;
}

interface WorkflowStep {
  id: string;
  name?: string;
  agent_name: string;
  agent_url?: string;
  input_mapping: Record<string, any>;
  next_step?: string | null;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

**Property 1: Sidebar state preservation**
*For any* sidebar open/close cycle, the chat session and conversation history should be preserved while the user remains on the page
**Validates: Requirements 1.5, 7.2**

**Property 2: JSON editor synchronization**
*For any* AI-generated workflow, the JSON editor content should match the workflow JSON returned by the API
**Validates: Requirements 2.4, 4.4**

**Property 3: Visual graph updates**
*For any* workflow JSON update (AI-generated or manual), the visual graph should re-render to reflect the current JSON state
**Validates: Requirements 2.5, 8.2**

**Property 4: Input validation**
*For any* user input (description or file), the system should validate constraints before sending to the API
**Validates: Requirements 2.2, 3.3**

**Property 5: Loading state consistency**
*For any* API request, loading indicators should be shown during the request and removed when the response is received
**Validates: Requirements 5.1, 5.2, 5.4**

**Property 6: Error message display**
*For any* API error response, the error message and suggestions should be displayed in the chat interface
**Validates: Requirements 6.1, 6.2**

**Property 7: Session expiration handling**
*For any* expired session, the system should detect the expiration and create a new session on the next user interaction
**Validates: Requirements 6.4, 7.5**

**Property 8: Manual edit preservation**
*For any* manual edit to the JSON, subsequent chat messages should use the manually edited version as the base
**Validates: Requirements 8.3, 8.4**

**Property 9: Chat history ordering**
*For any* chat session, messages should be displayed in chronological order with correct role attribution
**Validates: Requirements 4.2, 7.2**

**Property 10: Responsive layout adaptation**
*For any* viewport size change, the sidebar should adjust its layout appropriately
**Validates: Requirements 11.1, 11.2, 11.5**

**Property 11: File upload validation**
*For any* file upload attempt, only PDF files under 10MB should be accepted
**Validates: Requirements 3.2, 3.3**

**Property 12: Workflow save integration**
*For any* workflow save action, the system should use the current JSON editor content regardless of whether it was AI-generated or manually edited
**Validates: Requirements 9.1, 9.2**

## User Interface Design

### Sidebar Layout

**Dimensions:**
- Width: 400px (desktop), 100vw (mobile)
- Height: 100% of workflow definition section
- Position: Fixed right, overlaying visual graph
- Z-index: Higher than visual graph, lower than modals

**Colors:**
- Background: White (#FFFFFF)
- Border: Gray-200 (#E5E7EB)
- Header: Gray-50 (#F9FAFB)
- User messages: Blue-50 (#EFF6FF)
- Assistant messages: Gray-50 (#F9FAFB)
- System messages: Yellow-50 (#FEFCE8)
- Error messages: Red-50 (#FEF2F2)

**Typography:**
- Welcome heading: text-lg font-semibold
- Message content: text-sm
- Input placeholder: text-sm text-gray-500
- Timestamps: text-xs text-gray-400

### Initial View Layout

```
┌─────────────────────────────────────┐
│  ✕  AI Workflow Generator           │ ← Header
├─────────────────────────────────────┤
│                                     │
│  ✨ Generate Workflows with AI      │ ← Welcome
│                                     │
│  Describe your workflow in plain    │
│  English or upload a PDF document.  │
│                                     │
│  Examples:                          │
│  • "Process customer orders..."     │
│  • "Validate data then store..."    │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Describe your workflow...   │   │ ← Text Input
│  │                             │   │
│  │                             │   │
│  └─────────────────────────────┘   │
│  0 / 10,000 characters              │
│                                     │
│  ─────────── OR ───────────         │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  📄 Upload PDF Document     │   │ ← Upload Button
│  └─────────────────────────────┘   │
│  Max 10MB, PDF format only          │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │      Generate Workflow      │   │ ← Generate Button
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### Chat View Layout

```
┌─────────────────────────────────────┐
│  ✕  AI Workflow Generator           │ ← Header
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ You: Create a workflow...   │   │ ← User Message
│  │ 10:30 AM                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ AI: I've created a workflow │   │ ← Assistant Message
│  │ with 3 steps...             │   │
│  │                             │   │
│  │ Agents used:                │   │
│  │ • document-processor        │   │
│  │ • validator                 │   │
│  │ • storage-agent             │   │
│  │ 10:30 AM                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ You: Add error handling     │   │
│  │ 10:31 AM                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ AI: I've added an error...  │   │
│  │ 10:31 AM                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  [Scroll for more messages]         │
│                                     │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │ Type a message...           │   │ ← Chat Input
│  │                          [→]│   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## State Management

### Component State Flow

```
WorkflowCreate (Parent)
├── sidebarOpen: boolean
├── sessionId: string | null
├── workflowJson: string
└── onWorkflowUpdate(json, explanation)
    │
    ├─> Updates JSON editor
    ├─> Triggers visual graph re-render
    └─> Shows toast with explanation

AIGenerateSidebar
├── view: 'initial' | 'chat'
├── messages: Message[]
├── isLoading: boolean
└── API calls
    │
    ├─> createSession()
    ├─> sendMessage()
    └─> uploadDocument()
```

### Session Lifecycle

```
1. User clicks "AI Generate"
   └─> sidebarOpen = true
   └─> view = 'initial'

2. User enters description and clicks "Generate"
   └─> createSession(description)
   └─> sessionId = response.id
   └─> messages = response.messages
   └─> view = 'chat'
   └─> onWorkflowUpdate(workflow_json)

3. User sends chat message
   └─> sendMessage(sessionId, message)
   └─> messages.push(userMessage, aiMessage)
   └─> onWorkflowUpdate(updated_workflow_json)

4. User closes sidebar
   └─> sidebarOpen = false
   └─> sessionId preserved in state

5. User reopens sidebar
   └─> sidebarOpen = true
   └─> view = 'chat' (if sessionId exists)
   └─> messages restored from state

6. User navigates away
   └─> Component unmounts
   └─> Session state cleared
```

## API Integration

### Service Implementation

```typescript
// src/services/api/aiWorkflows.ts

import apiClient from './client';

export interface ChatSessionCreate {
  initial_description?: string;
  user_id?: string;
}

export interface ChatMessageSend {
  message: string;
}

export const aiWorkflowsApi = {
  // Create new chat session
  createSession: async (data?: ChatSessionCreate): Promise<ChatSession> => {
    const response = await apiClient.post<ChatSession>(
      '/ai-workflows/chat/sessions',
      data
    );
    return response.data;
  },

  // Send message to session
  sendMessage: async (
    sessionId: string,
    data: ChatMessageSend
  ): Promise<ChatSession> => {
    const response = await apiClient.post<ChatSession>(
      `/ai-workflows/chat/sessions/${sessionId}/messages`,
      data
    );
    return response.data;
  },

  // Get session details
  getSession: async (sessionId: string): Promise<ChatSession> => {
    const response = await apiClient.get<ChatSession>(
      `/ai-workflows/chat/sessions/${sessionId}`
    );
    return response.data;
  },

  // Upload document
  uploadDocument: async (file: File): Promise<WorkflowGenerationResult> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post<WorkflowGenerationResult>(
      '/ai-workflows/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // Delete session
  deleteSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/ai-workflows/chat/sessions/${sessionId}`);
  },

  // Export workflow
  exportWorkflow: async (sessionId: string): Promise<Blob> => {
    const response = await apiClient.get(
      `/ai-workflows/chat/sessions/${sessionId}/export`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },
};
```

### Error Handling Strategy

```typescript
// Handle API errors with user-friendly messages
const handleAIWorkflowError = (error: any): string => {
  if (error.response?.status === 429) {
    const retryAfter = error.response.headers['retry-after'];
    return `Rate limit exceeded. Please wait ${retryAfter} seconds.`;
  }
  
  if (error.response?.status === 400) {
    return error.response.data.detail || 'Invalid request. Please check your input.';
  }
  
  if (error.response?.status === 404) {
    return 'Session not found or expired. Starting a new session.';
  }
  
  if (error.response?.status === 503) {
    return 'AI service temporarily unavailable. Please try again in a moment.';
  }
  
  return 'An unexpected error occurred. Please try again.';
};
```

## Animation and Transitions

### Sidebar Animations

```css
/* Sidebar slide-in from right */
.ai-sidebar-enter {
  transform: translateX(100%);
  opacity: 0;
}

.ai-sidebar-enter-active {
  transform: translateX(0);
  opacity: 1;
  transition: transform 300ms ease-out, opacity 300ms ease-out;
}

.ai-sidebar-exit {
  transform: translateX(0);
  opacity: 1;
}

.ai-sidebar-exit-active {
  transform: translateX(100%);
  opacity: 0;
  transition: transform 300ms ease-in, opacity 300ms ease-in;
}
```

### Message Animations

```css
/* Message fade-in */
.message-enter {
  opacity: 0;
  transform: translateY(10px);
}

.message-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 200ms ease-out, transform 200ms ease-out;
}
```

### JSON Editor Highlight

```typescript
// Highlight changed lines in Monaco editor
const highlightChanges = (editor: monaco.editor.IStandaloneCodeEditor, changes: number[]) => {
  const decorations = changes.map(lineNumber => ({
    range: new monaco.Range(lineNumber, 1, lineNumber, 1),
    options: {
      isWholeLine: true,
      className: 'line-highlight',
      glyphMarginClassName: 'line-highlight-glyph',
    },
  }));
  
  editor.deltaDecorations([], decorations);
  
  // Remove highlights after 2 seconds
  setTimeout(() => {
    editor.deltaDecorations(decorations.map(d => d.range), []);
  }, 2000);
};
```

## Error Handling

### Error Categories

1. **Validation Errors**
   - Invalid description (too short, too long)
   - Invalid file (wrong format, too large)
   - Invalid JSON in editor
   - **Handling**: Display inline validation messages

2. **API Errors**
   - Session not found (404)
   - Session expired (400)
   - Rate limit exceeded (429)
   - Service unavailable (503)
   - **Handling**: Display in chat as system messages with retry options

3. **Network Errors**
   - Connection timeout
   - Network unavailable
   - **Handling**: Display retry button and offline indicator

4. **Workflow Generation Errors**
   - No suitable agents found
   - Workflow validation failed
   - Ambiguous requirements
   - **Handling**: Display AI suggestions and alternatives in chat

### Error Recovery Flows

```typescript
// Session expiration recovery
const handleSessionExpired = async () => {
  // Show system message
  addSystemMessage('Your session has expired. Creating a new session...');
  
  // Create new session
  const newSession = await aiWorkflowsApi.createSession();
  setSessionId(newSession.id);
  
  // Inform user
  addSystemMessage('New session created. You can continue chatting.');
};

// Rate limit recovery
const handleRateLimit = (retryAfter: number) => {
  // Disable input
  setIsInputDisabled(true);
  
  // Show countdown
  addSystemMessage(`Rate limit exceeded. Retrying in ${retryAfter} seconds...`);
  
  // Re-enable after delay
  setTimeout(() => {
    setIsInputDisabled(false);
    addSystemMessage('You can now send messages again.');
  }, retryAfter * 1000);
};
```

## Testing Strategy

### Unit Testing

Unit tests will verify individual components in isolation:

1. **AIGenerateSidebar Tests**
   - Test sidebar open/close behavior
   - Test view switching (initial → chat)
   - Test session state management
   - Test workflow update callbacks

2. **InitialView Tests**
   - Test description input validation
   - Test file upload validation
   - Test generate button enable/disable logic
   - Test error display

3. **ChatView Tests**
   - Test message rendering
   - Test message ordering
   - Test loading states
   - Test input field behavior

4. **API Service Tests**
   - Test request formatting
   - Test response parsing
   - Test error handling
   - Test retry logic

### Integration Testing

Integration tests will verify end-to-end functionality:

1. **Workflow Generation Flow**
   - Open sidebar → enter description → generate → verify JSON editor updated
   - Open sidebar → upload PDF → generate → verify JSON editor updated

2. **Chat Refinement Flow**
   - Generate workflow → send chat message → verify workflow updated
   - Generate workflow → manual edit → send chat → verify AI uses edited version

3. **Session Persistence Flow**
   - Generate workflow → close sidebar → reopen → verify history restored
   - Generate workflow → navigate away → return → verify fresh session

4. **Error Handling Flow**
   - Trigger rate limit → verify error message → verify retry
   - Expire session → send message → verify new session created

### Test Data Strategy

1. **Mock API Responses**
   - Create fixtures for successful workflow generation
   - Create fixtures for various error scenarios
   - Create fixtures for chat message responses

2. **Test Workflows**
   - Simple sequential workflow
   - Complex workflow with conditionals
   - Workflow with loops
   - Invalid workflow JSON

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**
   - Load sidebar component only when opened
   - Lazy load Monaco editor syntax highlighting for large workflows

2. **Debouncing**
   - Debounce character count updates (300ms)
   - Debounce visual graph updates (200ms)

3. **Memoization**
   - Memoize message list rendering
   - Memoize workflow JSON parsing
   - Memoize agent name validation

4. **Virtual Scrolling**
   - Use virtual scrolling for long chat histories (>50 messages)

### Performance Metrics

- Sidebar open/close: < 300ms
- Message send to display: < 100ms
- Workflow JSON update to visual graph: < 500ms
- File upload to generation: < 5s (depends on file size and API)

## Accessibility

### Keyboard Navigation

- Tab through all interactive elements
- Enter to submit forms
- Escape to close sidebar
- Arrow keys to navigate messages

### Screen Reader Support

- ARIA labels for all buttons and inputs
- ARIA live regions for chat messages
- ARIA busy states for loading indicators
- Semantic HTML structure

### Focus Management

- Focus trap within sidebar when open
- Return focus to "AI Generate" button when closed
- Focus chat input after message sent
- Focus error messages when displayed

## Security Considerations

1. **Input Sanitization**
   - Sanitize user descriptions before sending to API
   - Validate file types and sizes client-side
   - Escape HTML in chat messages

2. **API Security**
   - Use existing API client with CORS configuration
   - Handle authentication tokens (when implemented)
   - Validate API responses before processing

3. **Data Privacy**
   - Don't log sensitive workflow data
   - Clear session data on navigation
   - Don't persist chat history in localStorage

## Future Enhancements

1. **Advanced Features**
   - Workflow templates from chat
   - Multi-turn workflow refinement with branching
   - Workflow comparison view (before/after)
   - Export chat history

2. **UX Improvements**
   - Drag-and-drop PDF upload
   - Voice input for descriptions
   - Workflow preview before applying
   - Undo/redo for AI changes

3. **Collaboration**
   - Share chat sessions
   - Collaborative workflow editing
   - Comment on workflow steps

4. **Analytics**
   - Track generation success rates
   - Monitor common user patterns
   - Identify frequently used agents


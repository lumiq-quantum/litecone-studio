import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AIGenerateSidebar from '../AIGenerateSidebar';
import * as aiWorkflowsApi from '@/services/api/aiWorkflows';

describe('AIGenerateSidebar', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    currentWorkflowJson: '{}',
    lastAIGeneratedJson: null,
    onWorkflowUpdate: vi.fn(),
    agentNames: ['agent1', 'agent2'],
  };

  it('should render when open', () => {
    render(<AIGenerateSidebar {...defaultProps} />);
    
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('AI Workflow Generator')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    render(<AIGenerateSidebar {...defaultProps} isOpen={false} />);
    
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    
    render(<AIGenerateSidebar {...defaultProps} onClose={onClose} />);
    
    const closeButton = screen.getByRole('button', { name: /close ai sidebar/i });
    await user.click(closeButton);
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when backdrop is clicked on mobile', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    
    render(<AIGenerateSidebar {...defaultProps} onClose={onClose} />);
    
    // Find the backdrop (it has aria-hidden="true")
    const backdrop = document.querySelector('[aria-hidden="true"]');
    expect(backdrop).toBeInTheDocument();
    
    if (backdrop) {
      await user.click(backdrop);
      expect(onClose).toHaveBeenCalledTimes(1);
    }
  });

  it('should have proper ARIA attributes', () => {
    render(<AIGenerateSidebar {...defaultProps} />);
    
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'ai-sidebar-title');
  });

  it('should display header with title', () => {
    render(<AIGenerateSidebar {...defaultProps} />);
    
    const title = screen.getByText('AI Workflow Generator');
    expect(title).toHaveAttribute('id', 'ai-sidebar-title');
  });
});

describe('AIGenerateSidebar - Session Persistence', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    currentWorkflowJson: '{}',
    lastAIGeneratedJson: null,
    onWorkflowUpdate: vi.fn(),
    agentNames: ['agent1', 'agent2'],
  };

  const mockSession = {
    id: 'test-session-123',
    status: 'active' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    expires_at: '2024-01-01T01:00:00Z',
    messages: [
      {
        id: 'msg-1',
        role: 'user' as const,
        content: 'Create a workflow',
        timestamp: '2024-01-01T00:00:00Z',
      },
      {
        id: 'msg-2',
        role: 'assistant' as const,
        content: 'I created a workflow for you',
        timestamp: '2024-01-01T00:00:01Z',
      },
    ],
    current_workflow: {
      name: 'Test Workflow',
      start_step: 'step1',
      steps: {
        step1: {
          id: 'step1',
          agent_name: 'test-agent',
          next_step: null,
          input_mapping: {},
        },
      },
    },
    workflow_history: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should preserve session state when sidebar closes and reopens', async () => {
    const user = userEvent.setup();
    
    // Mock the API call
    vi.spyOn(aiWorkflowsApi, 'createChatSession').mockResolvedValue(mockSession);

    // Render with sidebar open
    const { rerender } = render(<AIGenerateSidebar {...defaultProps} />);

    // Generate a workflow to create a session
    const input = screen.getByLabelText(/workflow description/i);
    await user.type(input, 'Create a test workflow');
    
    const generateButton = screen.getByRole('button', { name: /generate workflow/i });
    await user.click(generateButton);

    // Wait for the session to be created and chat view to appear
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/type a message/i)).toBeInTheDocument();
    });

    // Verify chat messages are displayed
    expect(screen.getByText('Create a workflow')).toBeInTheDocument();
    expect(screen.getByText('I created a workflow for you')).toBeInTheDocument();

    // Close the sidebar
    rerender(<AIGenerateSidebar {...defaultProps} isOpen={false} />);

    // Verify sidebar is closed
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    // Reopen the sidebar
    rerender(<AIGenerateSidebar {...defaultProps} isOpen={true} />);

    // Verify chat view is restored with messages
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/type a message/i)).toBeInTheDocument();
    });
    expect(screen.getByText('Create a workflow')).toBeInTheDocument();
    expect(screen.getByText('I created a workflow for you')).toBeInTheDocument();
  });

  it('should restore chat view when reopening with active session', async () => {
    const user = userEvent.setup();
    
    // Mock the API call
    vi.spyOn(aiWorkflowsApi, 'createChatSession').mockResolvedValue(mockSession);

    // Render with sidebar open
    const { rerender } = render(<AIGenerateSidebar {...defaultProps} />);

    // Generate a workflow
    const input = screen.getByLabelText(/workflow description/i);
    await user.type(input, 'Create a test workflow');
    
    const generateButton = screen.getByRole('button', { name: /generate workflow/i });
    await user.click(generateButton);

    // Wait for chat view
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/type a message/i)).toBeInTheDocument();
    });

    // Close sidebar
    rerender(<AIGenerateSidebar {...defaultProps} isOpen={false} />);

    // Reopen sidebar
    rerender(<AIGenerateSidebar {...defaultProps} isOpen={true} />);

    // Should show chat view, not initial view
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/type a message/i)).toBeInTheDocument();
    });
    expect(screen.queryByLabelText(/workflow description/i)).not.toBeInTheDocument();
  });

  it('should show initial view when reopening without session', () => {
    const { rerender } = render(<AIGenerateSidebar {...defaultProps} />);

    // Initial view should be shown
    expect(screen.getByLabelText(/workflow description/i)).toBeInTheDocument();

    // Close sidebar
    rerender(<AIGenerateSidebar {...defaultProps} isOpen={false} />);

    // Reopen sidebar
    rerender(<AIGenerateSidebar {...defaultProps} isOpen={true} />);

    // Should still show initial view
    expect(screen.getByLabelText(/workflow description/i)).toBeInTheDocument();
  });

  it('should clear session state on component unmount', async () => {
    const user = userEvent.setup();
    
    // Mock the API call
    vi.spyOn(aiWorkflowsApi, 'createChatSession').mockResolvedValue(mockSession);

    // Render component
    const { unmount } = render(<AIGenerateSidebar {...defaultProps} />);

    // Generate a workflow to create a session
    const input = screen.getByLabelText(/workflow description/i);
    await user.type(input, 'Create a test workflow');
    
    const generateButton = screen.getByRole('button', { name: /generate workflow/i });
    await user.click(generateButton);

    // Wait for chat view
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/type a message/i)).toBeInTheDocument();
    });

    // Unmount the component
    unmount();

    // Render a new instance
    render(<AIGenerateSidebar {...defaultProps} />);

    // Should show initial view (session was cleared)
    expect(screen.getByLabelText(/workflow description/i)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/type a message/i)).not.toBeInTheDocument();
  });

  it('should handle session expiration gracefully', async () => {
    const user = userEvent.setup();
    
    // Mock successful session creation
    vi.spyOn(aiWorkflowsApi, 'createChatSession').mockResolvedValue(mockSession);
    
    // Mock session expiration error (404)
    const sessionExpiredError = {
      response: {
        status: 404,
        data: { detail: 'Session not found' },
      },
    };
    vi.spyOn(aiWorkflowsApi, 'sendChatMessage').mockRejectedValue(sessionExpiredError);

    // Render component
    render(<AIGenerateSidebar {...defaultProps} />);

    // Generate a workflow
    const input = screen.getByLabelText(/workflow description/i);
    await user.type(input, 'Create a test workflow');
    
    const generateButton = screen.getByRole('button', { name: /generate workflow/i });
    await user.click(generateButton);

    // Wait for chat view
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/type a message/i)).toBeInTheDocument();
    });

    // Try to send a message (will trigger session expiration)
    const chatInput = screen.getByPlaceholderText(/type a message/i);
    await user.type(chatInput, 'Update the workflow');
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    await user.click(sendButton);

    // Should show session expiration message
    await waitFor(() => {
      expect(screen.getByText(/your session has expired/i)).toBeInTheDocument();
    });

    // Should return to initial view
    await waitFor(() => {
      expect(screen.getByLabelText(/workflow description/i)).toBeInTheDocument();
    });
  });

  it('should preserve chat history across multiple close/open cycles', async () => {
    const user = userEvent.setup();
    
    // Mock the API call
    vi.spyOn(aiWorkflowsApi, 'createChatSession').mockResolvedValue(mockSession);

    // Render with sidebar open
    const { rerender } = render(<AIGenerateSidebar {...defaultProps} />);

    // Generate a workflow
    const input = screen.getByLabelText(/workflow description/i);
    await user.type(input, 'Create a test workflow');
    
    const generateButton = screen.getByRole('button', { name: /generate workflow/i });
    await user.click(generateButton);

    // Wait for chat view
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/type a message/i)).toBeInTheDocument();
    });

    // Close and reopen multiple times
    for (let i = 0; i < 3; i++) {
      // Close
      rerender(<AIGenerateSidebar {...defaultProps} isOpen={false} />);
      
      // Reopen
      rerender(<AIGenerateSidebar {...defaultProps} isOpen={true} />);

      // Verify messages are still there
      await waitFor(() => {
        expect(screen.getByText('Create a workflow')).toBeInTheDocument();
        expect(screen.getByText('I created a workflow for you')).toBeInTheDocument();
      });
    }
  });
});

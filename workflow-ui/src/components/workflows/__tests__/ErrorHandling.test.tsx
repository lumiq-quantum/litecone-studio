/**
 * Error Handling Tests for AI Workflow Sidebar
 * 
 * Tests Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AIGenerateSidebar from '../AIGenerateSidebar';
import * as aiWorkflowsApi from '@/services/api/aiWorkflows';

// Mock the API module
vi.mock('@/services/api/aiWorkflows');

// Mock scrollIntoView for testing
Element.prototype.scrollIntoView = vi.fn();

describe('AIGenerateSidebar - Error Handling', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    currentWorkflowJson: '{}',
    lastAIGeneratedJson: null,
    onWorkflowUpdate: vi.fn(),
    agentNames: ['agent1', 'agent2'],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Requirement 6.1: Display API errors as system messages in chat', () => {
    it('should display API error in initial view', async () => {
      const user = userEvent.setup();
      
      // Mock API to throw error
      vi.mocked(aiWorkflowsApi.createChatSession).mockRejectedValue({
        response: {
          status: 500,
          data: {
            message: 'Internal server error',
          },
        },
      });

      render(<AIGenerateSidebar {...defaultProps} />);

      // Enter description and generate
      const textarea = screen.getByLabelText(/workflow description/i);
      await user.type(textarea, 'Create a workflow for processing orders');
      
      const generateButton = screen.getByRole('button', { name: /generate workflow/i });
      await user.click(generateButton);

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText(/server error/i)).toBeInTheDocument();
      });
    });

    it('should display API error as system message in chat view', async () => {
      const user = userEvent.setup();
      
      // Mock successful session creation
      vi.mocked(aiWorkflowsApi.createChatSession).mockResolvedValue({
        id: 'session-123',
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 3600000).toISOString(),
        messages: [
          {
            id: 'msg-1',
            role: 'assistant',
            content: 'Workflow created',
            timestamp: new Date().toISOString(),
          },
        ],
        current_workflow: {
          name: 'Test Workflow',
          start_step: 'step1',
          steps: {},
        },
        workflow_history: [],
      });

      // Mock failed message send
      vi.mocked(aiWorkflowsApi.sendChatMessage).mockRejectedValue({
        response: {
          status: 500,
          data: {
            message: 'Failed to process message',
          },
        },
      });

      render(<AIGenerateSidebar {...defaultProps} />);

      // Generate workflow first
      const textarea = screen.getByLabelText(/workflow description/i);
      await user.type(textarea, 'Create a workflow for processing orders');
      
      const generateButton = screen.getByRole('button', { name: /generate workflow/i });
      await user.click(generateButton);

      // Wait for chat view
      await waitFor(() => {
        expect(screen.getByLabelText(/chat message input/i)).toBeInTheDocument();
      });

      // Send a message
      const chatInput = screen.getByLabelText(/chat message input/i);
      await user.type(chatInput, 'Add error handling');
      
      const sendButton = screen.getByRole('button', { name: /send message/i });
      await user.click(sendButton);

      // Wait for error system message
      await waitFor(() => {
        expect(screen.getByText(/failed to process message/i)).toBeInTheDocument();
      });
    });
  });

  describe('Requirement 6.2: Show validation errors with suggestions', () => {
    it('should display validation errors with suggestions', async () => {
      const user = userEvent.setup();
      
      // Mock API to return validation error with suggestions
      vi.mocked(aiWorkflowsApi.createChatSession).mockRejectedValue({
        response: {
          status: 400,
          data: {
            message: 'Invalid workflow description',
            suggestions: [
              'Be more specific about the workflow steps',
              'Include agent names or capabilities',
            ],
          },
        },
      });

      render(<AIGenerateSidebar {...defaultProps} />);

      // Enter description and generate
      const textarea = screen.getByLabelText(/workflow description/i);
      await user.type(textarea, 'Create a workflow for processing orders');
      
      const generateButton = screen.getByRole('button', { name: /generate workflow/i });
      await user.click(generateButton);

      // Wait for error message first
      await waitFor(() => {
        expect(screen.getByText(/invalid workflow description/i)).toBeInTheDocument();
      });

      // Check that suggestions are displayed (they're formatted with bullets)
      await waitFor(() => {
        const errorElement = screen.getByRole('alert');
        const errorText = errorElement.textContent || '';
        // The suggestions are formatted as "• suggestion" in the error message
        expect(errorText).toContain('specific');
        expect(errorText).toContain('agent');
      });
    });
  });

  describe('Requirement 6.3: Handle rate limit errors with retry countdown', () => {
    it('should display rate limit countdown', async () => {
      const user = userEvent.setup();
      
      // Mock API to return rate limit error
      vi.mocked(aiWorkflowsApi.createChatSession).mockRejectedValue({
        response: {
          status: 429,
          headers: {
            'retry-after': '5',
          },
          data: {
            message: 'Rate limit exceeded',
          },
        },
      });

      render(<AIGenerateSidebar {...defaultProps} />);

      // Enter description and generate
      const textarea = screen.getByLabelText(/workflow description/i);
      await user.type(textarea, 'Create a workflow for processing orders');
      
      const generateButton = screen.getByRole('button', { name: /generate workflow/i });
      await user.click(generateButton);

      // Wait for rate limit message with countdown
      await waitFor(() => {
        expect(screen.getByText(/retrying in 5 second/i)).toBeInTheDocument();
      });
    });

    it('should disable input during rate limit countdown', async () => {
      const user = userEvent.setup();
      
      // Mock successful session creation
      vi.mocked(aiWorkflowsApi.createChatSession).mockResolvedValue({
        id: 'session-123',
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 3600000).toISOString(),
        messages: [
          {
            id: 'msg-1',
            role: 'assistant',
            content: 'Workflow created',
            timestamp: new Date().toISOString(),
          },
        ],
        current_workflow: {
          name: 'Test Workflow',
          start_step: 'step1',
          steps: {},
        },
        workflow_history: [],
      });

      // Mock rate limit error on message send
      vi.mocked(aiWorkflowsApi.sendChatMessage).mockRejectedValue({
        response: {
          status: 429,
          headers: {
            'retry-after': '3',
          },
          data: {
            message: 'Rate limit exceeded',
          },
        },
      });

      render(<AIGenerateSidebar {...defaultProps} />);

      // Generate workflow first
      const textarea = screen.getByLabelText(/workflow description/i);
      await user.type(textarea, 'Create a workflow for processing orders');
      
      const generateButton = screen.getByRole('button', { name: /generate workflow/i });
      await user.click(generateButton);

      // Wait for chat view
      await waitFor(() => {
        expect(screen.getByLabelText(/chat message input/i)).toBeInTheDocument();
      });

      // Send a message to trigger rate limit
      const chatInput = screen.getByLabelText(/chat message input/i);
      await user.type(chatInput, 'Add error handling');
      
      const sendButton = screen.getByRole('button', { name: /send message/i });
      await user.click(sendButton);

      // Wait for rate limit message - check for countdown text
      await waitFor(() => {
        const text = screen.getByText(/you can send messages again in/i);
        expect(text).toBeInTheDocument();
      }, { timeout: 3000 });

      // Check that input is disabled
      const disabledInput = screen.getByLabelText(/chat message input/i);
      expect(disabledInput).toBeDisabled();
    });
  });

  describe('Requirement 6.4: Detect and handle session expiration', () => {
    it('should detect session expiration and notify user', async () => {
      const user = userEvent.setup();
      
      // Mock successful session creation
      vi.mocked(aiWorkflowsApi.createChatSession).mockResolvedValue({
        id: 'session-123',
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 3600000).toISOString(),
        messages: [
          {
            id: 'msg-1',
            role: 'assistant',
            content: 'Workflow created',
            timestamp: new Date().toISOString(),
          },
        ],
        current_workflow: {
          name: 'Test Workflow',
          start_step: 'step1',
          steps: {},
        },
        workflow_history: [],
      });

      // Mock session expired error (404)
      vi.mocked(aiWorkflowsApi.sendChatMessage).mockRejectedValue({
        response: {
          status: 404,
          data: {
            message: 'Session not found or expired',
          },
        },
      });

      render(<AIGenerateSidebar {...defaultProps} />);

      // Generate workflow first
      const textarea = screen.getByLabelText(/workflow description/i);
      await user.type(textarea, 'Create a workflow for processing orders');
      
      const generateButton = screen.getByRole('button', { name: /generate workflow/i });
      await user.click(generateButton);

      // Wait for chat view
      await waitFor(() => {
        expect(screen.getByLabelText(/chat message input/i)).toBeInTheDocument();
      });

      // Send a message to trigger session expiration
      const chatInput = screen.getByLabelText(/chat message input/i);
      await user.type(chatInput, 'Add error handling');
      
      const sendButton = screen.getByRole('button', { name: /send message/i });
      await user.click(sendButton);

      // Wait for session expiration message
      await waitFor(() => {
        expect(screen.getByText(/session has expired/i)).toBeInTheDocument();
      });
    });
  });

  describe('Requirement 6.5: Add retry button for network errors', () => {
    it('should display retry button for network errors', async () => {
      const user = userEvent.setup();
      
      // Mock network error
      vi.mocked(aiWorkflowsApi.createChatSession).mockRejectedValue(
        new Error('Network Error')
      );

      render(<AIGenerateSidebar {...defaultProps} />);

      // Enter description and generate
      const textarea = screen.getByLabelText(/workflow description/i);
      await user.type(textarea, 'Create a workflow for processing orders');
      
      const generateButton = screen.getByRole('button', { name: /generate workflow/i });
      await user.click(generateButton);

      // Wait for error message first
      await waitFor(() => {
        expect(screen.getByText(/unable to connect/i)).toBeInTheDocument();
      });

      // Then check for retry button
      await waitFor(() => {
        const retryButton = screen.queryByRole('button', { name: /retry/i });
        expect(retryButton).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should retry action when retry button is clicked', async () => {
      const user = userEvent.setup();
      
      // Mock network error first, then success
      vi.mocked(aiWorkflowsApi.createChatSession)
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce({
          id: 'session-123',
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          expires_at: new Date(Date.now() + 3600000).toISOString(),
          messages: [
            {
              id: 'msg-1',
              role: 'assistant',
              content: 'Workflow created',
              timestamp: new Date().toISOString(),
            },
          ],
          current_workflow: {
            name: 'Test Workflow',
            start_step: 'step1',
            steps: {},
          },
          workflow_history: [],
        });

      render(<AIGenerateSidebar {...defaultProps} />);

      // Enter description and generate
      const textarea = screen.getByLabelText(/workflow description/i);
      await user.type(textarea, 'Create a workflow for processing orders');
      
      const generateButton = screen.getByRole('button', { name: /generate workflow/i });
      await user.click(generateButton);

      // Wait for error message
      await waitFor(() => {
        expect(screen.getByText(/unable to connect/i)).toBeInTheDocument();
      });

      // Wait for retry button
      await waitFor(() => {
        const retryButton = screen.queryByRole('button', { name: /retry/i });
        expect(retryButton).toBeInTheDocument();
      }, { timeout: 2000 });

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      // Wait for success - should switch to chat view
      await waitFor(() => {
        expect(screen.getByLabelText(/chat message input/i)).toBeInTheDocument();
      }, { timeout: 3000 });

      // Verify API was called twice
      expect(aiWorkflowsApi.createChatSession).toHaveBeenCalledTimes(2);
    });
  });
});

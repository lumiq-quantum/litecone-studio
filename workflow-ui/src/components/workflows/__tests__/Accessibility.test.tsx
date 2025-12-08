/**
 * Accessibility tests for AI workflow components
 * Requirements: 1.3, 4.2, 5.2
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AIGenerateSidebar from '../AIGenerateSidebar';
import InitialView from '../InitialView';
import ChatView from '../ChatView';

describe('Accessibility Features', () => {
  describe('AIGenerateSidebar', () => {
    it('should have proper ARIA attributes', () => {
      const mockOnClose = vi.fn();
      const mockOnWorkflowUpdate = vi.fn();

      render(
        <AIGenerateSidebar
          isOpen={true}
          onClose={mockOnClose}
          currentWorkflowJson="{}"
          lastAIGeneratedJson={null}
          onWorkflowUpdate={mockOnWorkflowUpdate}
          agentNames={[]}
        />
      );

      // Check dialog role and ARIA attributes
      const sidebar = screen.getByRole('dialog');
      expect(sidebar).toHaveAttribute('aria-modal', 'true');
      expect(sidebar).toHaveAttribute('aria-labelledby', 'ai-sidebar-title');
      expect(sidebar).toHaveAttribute('aria-describedby', 'ai-sidebar-description');

      // Check title exists
      expect(screen.getByText('AI Workflow Generator')).toBeInTheDocument();
    });

    it('should close on Escape key press', async () => {
      const mockOnClose = vi.fn();
      const mockOnWorkflowUpdate = vi.fn();

      render(
        <AIGenerateSidebar
          isOpen={true}
          onClose={mockOnClose}
          currentWorkflowJson="{}"
          lastAIGeneratedJson={null}
          onWorkflowUpdate={mockOnWorkflowUpdate}
          agentNames={[]}
        />
      );

      const sidebar = screen.getByRole('dialog');
      fireEvent.keyDown(sidebar, { key: 'Escape' });

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it('should have accessible close button', () => {
      const mockOnClose = vi.fn();
      const mockOnWorkflowUpdate = vi.fn();

      render(
        <AIGenerateSidebar
          isOpen={true}
          onClose={mockOnClose}
          currentWorkflowJson="{}"
          lastAIGeneratedJson={null}
          onWorkflowUpdate={mockOnWorkflowUpdate}
          agentNames={[]}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close ai sidebar/i });
      expect(closeButton).toBeInTheDocument();
      expect(closeButton).toHaveAttribute('aria-label');
    });
  });

  describe('InitialView', () => {
    it('should have accessible textarea with ARIA labels', () => {
      const mockOnGenerate = vi.fn();
      const mockOnUpload = vi.fn();

      render(
        <InitialView
          onGenerate={mockOnGenerate}
          onUpload={mockOnUpload}
          isLoading={false}
          error={null}
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const textarea = screen.getByRole('textbox', { name: /workflow description/i });
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveAttribute('aria-describedby');
      expect(textarea).toHaveAttribute('aria-invalid', 'false');
    });

    it('should support Ctrl+Enter keyboard shortcut', async () => {
      const mockOnGenerate = vi.fn();
      const mockOnUpload = vi.fn();

      render(
        <InitialView
          onGenerate={mockOnGenerate}
          onUpload={mockOnUpload}
          isLoading={false}
          error={null}
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const textarea = screen.getByRole('textbox', { name: /workflow description/i });
      
      // Type enough text to enable the button
      fireEvent.change(textarea, { 
        target: { value: 'This is a test workflow description with enough words' } 
      });

      // Press Ctrl+Enter
      fireEvent.keyDown(textarea, { key: 'Enter', ctrlKey: true });

      await waitFor(() => {
        expect(mockOnGenerate).toHaveBeenCalled();
      });
    });

    it('should have accessible generate button with loading state', () => {
      const mockOnGenerate = vi.fn();
      const mockOnUpload = vi.fn();

      const { rerender } = render(
        <InitialView
          onGenerate={mockOnGenerate}
          onUpload={mockOnUpload}
          isLoading={false}
          error={null}
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const button = screen.getByRole('button', { name: /generate workflow/i });
      expect(button).toHaveAttribute('aria-disabled');
      expect(button).toHaveAttribute('aria-busy', 'false');

      // Rerender with loading state
      rerender(
        <InitialView
          onGenerate={mockOnGenerate}
          onUpload={mockOnUpload}
          isLoading={true}
          error={null}
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const loadingButton = screen.getByRole('button', { name: /generating workflow/i });
      expect(loadingButton).toHaveAttribute('aria-busy', 'true');
    });

    it('should have accessible file upload input', () => {
      const mockOnGenerate = vi.fn();
      const mockOnUpload = vi.fn();

      render(
        <InitialView
          onGenerate={mockOnGenerate}
          onUpload={mockOnUpload}
          isLoading={false}
          error={null}
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toBeInTheDocument();
      expect(fileInput).toHaveAttribute('aria-label');
      expect(fileInput).toHaveAttribute('aria-describedby');
    });
  });

  describe('ChatView', () => {
    it('should have ARIA live region for messages', () => {
      const mockOnSendMessage = vi.fn();

      render(
        <ChatView
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          sessionId="test-session"
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const messageList = screen.getByRole('log');
      expect(messageList).toHaveAttribute('aria-live', 'polite');
      expect(messageList).toHaveAttribute('aria-atomic', 'false');
      expect(messageList).toHaveAttribute('aria-relevant', 'additions');
    });

    it('should have accessible chat input', () => {
      const mockOnSendMessage = vi.fn();

      render(
        <ChatView
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          sessionId="test-session"
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-label');
      expect(input).toHaveAttribute('aria-describedby');
      expect(input).toHaveAttribute('aria-disabled', 'false');
    });

    it('should support Enter key to send message', async () => {
      const mockOnSendMessage = vi.fn();

      render(
        <ChatView
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          sessionId="test-session"
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const input = screen.getByRole('textbox');
      
      // Type a message
      fireEvent.change(input, { target: { value: 'Test message' } });

      // Press Enter
      fireEvent.keyDown(input, { key: 'Enter' });

      await waitFor(() => {
        expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
      });
    });

    it('should have accessible send button with loading state', () => {
      const mockOnSendMessage = vi.fn();

      const { rerender } = render(
        <ChatView
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          sessionId="test-session"
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const button = screen.getByRole('button', { name: /send message/i });
      expect(button).toHaveAttribute('aria-disabled');
      expect(button).toHaveAttribute('aria-busy', 'false');

      // Rerender with loading state
      rerender(
        <ChatView
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={true}
          sessionId="test-session"
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const loadingButton = screen.getByRole('button', { name: /sending message/i });
      expect(loadingButton).toHaveAttribute('aria-busy', 'true');
    });

    it('should announce loading states to screen readers', () => {
      const mockOnSendMessage = vi.fn();

      // Add at least one message so the typing indicator shows
      const messages = [
        {
          id: '1',
          role: 'user' as const,
          content: 'Test message',
          timestamp: new Date().toISOString(),
        },
      ];

      render(
        <ChatView
          messages={messages}
          onSendMessage={mockOnSendMessage}
          isLoading={true}
          sessionId="test-session"
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      // Check for typing indicator with screen reader text
      const typingIndicators = screen.getAllByRole('status');
      expect(typingIndicators.length).toBeGreaterThan(0);
      
      // Find the typing indicator
      const typingIndicator = typingIndicators.find(el => 
        el.getAttribute('aria-label')?.includes('typing')
      );
      expect(typingIndicator).toBeDefined();
      expect(typingIndicator).toHaveAttribute('aria-live', 'polite');
    });

    it('should have accessible message articles', () => {
      const mockOnSendMessage = vi.fn();
      const messages = [
        {
          id: '1',
          role: 'user' as const,
          content: 'Test user message',
          timestamp: new Date().toISOString(),
        },
        {
          id: '2',
          role: 'assistant' as const,
          content: 'Test AI response',
          timestamp: new Date().toISOString(),
        },
      ];

      render(
        <ChatView
          messages={messages}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          sessionId="test-session"
          showProgressMessage={false}
          retryCountdown={null}
        />
      );

      const articles = screen.getAllByRole('article');
      expect(articles).toHaveLength(2);
      
      // Each message should have an aria-label
      articles.forEach((article) => {
        expect(article).toHaveAttribute('aria-label');
      });
    });
  });
});

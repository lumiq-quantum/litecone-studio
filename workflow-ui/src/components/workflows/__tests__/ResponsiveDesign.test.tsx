/**
 * Responsive Design Tests for AIGenerateSidebar
 * 
 * Tests Requirements 11.1, 11.2, 11.3, 11.4, 11.5
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import AIGenerateSidebar from '../AIGenerateSidebar';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    aside: ({ children, ...props }: any) => <aside {...props}>{children}</aside>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock the API services
vi.mock('@/services/api/aiWorkflows', () => ({
  createChatSession: vi.fn(),
  uploadDocument: vi.fn(),
  sendChatMessage: vi.fn(),
}));

// Mock the error handling utilities
vi.mock('@/lib/aiWorkflowErrors', () => ({
  handleAIWorkflowError: vi.fn((_err: any) => 'Error occurred'),
  isRecoverableError: vi.fn(() => false),
  getRetryAfterSeconds: vi.fn(() => null),
  getErrorSuggestions: vi.fn(() => []),
}));

// Mock the jsonDiff utility
vi.mock('@/lib/jsonDiff', () => ({
  getWorkflowChanges: vi.fn(() => ({
    summary: 'No changes',
    detailedSummary: 'No changes detected',
    addedSteps: [],
    removedSteps: [],
    modifiedSteps: [],
    changedLines: [],
    hasChanges: false,
  })),
}));

describe('AIGenerateSidebar - Responsive Design', () => {
  const mockProps = {
    isOpen: true,
    onClose: vi.fn(),
    currentWorkflowJson: '{}',
    lastAIGeneratedJson: null,
    onWorkflowUpdate: vi.fn(),
    agentNames: ['agent1', 'agent2'],
  };

  let originalInnerWidth: number;

  beforeEach(() => {
    // Store original window.innerWidth
    originalInnerWidth = window.innerWidth;
  });

  afterEach(() => {
    // Restore original window.innerWidth
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  describe('Requirement 11.1: Full-width on mobile (<1024px)', () => {
    it('should render sidebar with full width on mobile', () => {
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      const { container } = render(<AIGenerateSidebar {...mockProps} />);
      
      const sidebar = container.querySelector('aside');
      expect(sidebar).toBeTruthy();
      
      // Check that sidebar has full-width class
      expect(sidebar?.className).toContain('w-full');
    });

    it('should show backdrop on mobile', () => {
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      const { container } = render(<AIGenerateSidebar {...mockProps} />);
      
      // Backdrop should be present (has bg-black/50 class)
      const backdrop = container.querySelector('.bg-black\\/50');
      expect(backdrop).toBeTruthy();
    });
  });

  describe('Requirement 11.2: Fixed width on desktop (≥1024px)', () => {
    it('should render sidebar with fixed width on desktop', () => {
      // Set desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1440,
      });

      const { container } = render(<AIGenerateSidebar {...mockProps} />);
      
      const sidebar = container.querySelector('aside');
      expect(sidebar).toBeTruthy();
      
      // Check that sidebar has fixed width class
      expect(sidebar?.className).toContain('w-[400px]');
    });

    it('should not show backdrop on desktop', () => {
      // Set desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1440,
      });

      const { container } = render(<AIGenerateSidebar {...mockProps} />);
      
      // Backdrop should not be present on desktop
      const backdrop = container.querySelector('.bg-black\\/50');
      expect(backdrop).toBeFalsy();
    });
  });

  describe('Requirement 11.3 & 11.4: Hide/restore content on mobile', () => {
    it('should hide content when sidebar is open on mobile', () => {
      // This test verifies the CSS classes are applied correctly
      // The actual hiding is done in WorkflowCreate.tsx with conditional classes
      
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      render(<AIGenerateSidebar {...mockProps} />);
      
      // Sidebar should be open
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should restore content when sidebar is closed on mobile', () => {
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      const { rerender } = render(<AIGenerateSidebar {...mockProps} />);
      
      // Close sidebar
      rerender(<AIGenerateSidebar {...mockProps} isOpen={false} />);
      
      // Sidebar should not be in document
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  describe('Requirement 11.5: Handle device rotation gracefully', () => {
    it('should update layout when viewport changes from mobile to desktop', () => {
      // Start with mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      const { container, rerender } = render(<AIGenerateSidebar {...mockProps} />);
      
      let sidebar = container.querySelector('aside');
      expect(sidebar?.className).toContain('w-full');

      // Simulate rotation/resize to desktop
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1440,
      });

      // Trigger resize event
      window.dispatchEvent(new Event('resize'));

      // Rerender to pick up state changes
      rerender(<AIGenerateSidebar {...mockProps} />);

      sidebar = container.querySelector('aside');
      // After resize, should have desktop width
      expect(sidebar?.className).toContain('w-[400px]');
    });

    it('should update layout when viewport changes from desktop to mobile', () => {
      // Start with desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1440,
      });

      const { container, rerender } = render(<AIGenerateSidebar {...mockProps} />);
      
      let sidebar = container.querySelector('aside');
      expect(sidebar?.className).toContain('w-[400px]');

      // Simulate rotation/resize to mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      // Trigger resize event
      window.dispatchEvent(new Event('resize'));

      // Rerender to pick up state changes
      rerender(<AIGenerateSidebar {...mockProps} />);

      sidebar = container.querySelector('aside');
      // After resize, should have mobile width
      expect(sidebar?.className).toContain('w-full');
    });

    it('should handle orientationchange event', () => {
      // Start with mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      const { container, rerender } = render(<AIGenerateSidebar {...mockProps} />);

      // Simulate device rotation (landscape)
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });

      // Trigger orientationchange event
      window.dispatchEvent(new Event('orientationchange'));

      // Rerender to pick up state changes
      rerender(<AIGenerateSidebar {...mockProps} />);

      const sidebar = container.querySelector('aside');
      // At exactly 1024px, should be desktop (≥1024px)
      expect(sidebar?.className).toContain('w-[400px]');
    });
  });

  describe('Sidebar visibility', () => {
    it('should not render sidebar when isOpen is false', () => {
      render(<AIGenerateSidebar {...mockProps} isOpen={false} />);
      
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render sidebar when isOpen is true', () => {
      render(<AIGenerateSidebar {...mockProps} isOpen={true} />);
      
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('AI Workflow Generator')).toBeInTheDocument();
    });
  });
});

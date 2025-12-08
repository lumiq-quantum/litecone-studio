import { useState, useCallback, useEffect, useRef, useMemo, lazy, Suspense } from 'react';
import { X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { trapFocus, handleKeyboardNavigation, FocusManager } from '@/lib/accessibility';
import { createChatSession, uploadDocument, sendChatMessage } from '@/services/api/aiWorkflows';
import { 
  getErrorInfo,
  isCriticalError,
  retryWithBackoff,
} from '@/lib/aiWorkflowErrors';
import { getWorkflowChanges } from '@/lib/jsonDiff';
import type { Message } from '@/types';

// Lazy load views for better initial load performance (Task 26: Lazy loading)
const InitialView = lazy(() => import('./InitialView'));
const ChatView = lazy(() => import('./ChatView'));
const ErrorFallback = lazy(() => import('./ErrorFallback'));

/**
 * Hook to detect if viewport is mobile size (<1024px)
 * Requirements: 11.1, 11.2, 11.5
 */
function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < 1024;
  });

  useEffect(() => {
    // Handle device rotation and viewport changes (Requirement 11.5)
    const handleResize = () => {
      setIsMobile(window.innerWidth < 1024);
    };

    // Add event listener for resize and orientation change
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);

    // Initial check
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  return isMobile;
}

/**
 * Props for the AIGenerateSidebar component
 */
export interface AIGenerateSidebarProps {
  /** Whether the sidebar is open */
  isOpen: boolean;
  /** Callback to close the sidebar */
  onClose: () => void;
  /** Current workflow JSON string */
  currentWorkflowJson: string;
  /** Last AI-generated workflow JSON (for detecting manual edits) */
  lastAIGeneratedJson: string | null;
  /** Callback when workflow is updated by AI */
  onWorkflowUpdate: (json: string, explanation: string) => void;
  /** List of available agent names */
  agentNames: string[];
}

/**
 * View state type
 */
type ViewState = 'initial' | 'chat';

/**
 * AIGenerateSidebar Component
 * 
 * A collapsible right-side panel that provides AI-powered workflow generation
 * capabilities. Users can generate workflows from natural language descriptions
 * or PDF documents, then iteratively refine them through an interactive chat interface.
 * 
 * Features:
 * - Slide-in/out animation from the right
 * - Responsive layout (full-width on mobile, fixed width on desktop)
 * - Session persistence while sidebar is open
 * - Real-time workflow updates
 * 
 * Requirements: 1.2, 1.3, 1.4, 11.1, 11.2
 */
export default function AIGenerateSidebar({
  isOpen,
  onClose,
  currentWorkflowJson,
  lastAIGeneratedJson,
  onWorkflowUpdate,
  agentNames, // Will be used in future tasks
}: AIGenerateSidebarProps) {
  // State management
  const [view, setView] = useState<ViewState>('initial');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showProgressMessage, setShowProgressMessage] = useState(false);
  const [retryCountdown, setRetryCountdown] = useState<number | null>(null);
  const [lastFailedAction, setLastFailedAction] = useState<(() => Promise<void>) | null>(null);
  const [hasNotifiedManualEdit, setHasNotifiedManualEdit] = useState(false);
  const [latestChanges, setLatestChanges] = useState<{
    summary: string;
    detailedSummary: string;
    addedSteps: number;
    removedSteps: number;
    modifiedSteps: number;
  } | null>(null);
  const [criticalError, setCriticalError] = useState<{
    message: string;
    details?: string;
    suggestions: string[];
  } | null>(null);
  const [autoRetryAttempt, setAutoRetryAttempt] = useState(0);

  // Detect mobile viewport (Requirements 11.1, 11.2, 11.5)
  const isMobile = useIsMobile();

  // Refs for accessibility (Requirements 1.3, 4.2, 5.2)
  const sidebarRef = useRef<HTMLDivElement>(null);
  const focusManagerRef = useRef(new FocusManager());

  // Suppress unused variable warnings - these will be used in subsequent tasks
  void agentNames;

  /**
   * Add a system message to the chat
   * Requirements: 6.1, 6.2
   */
  const addSystemMessage = useCallback((content: string, metadata?: Message['metadata']) => {
    const systemMessage: Message = {
      id: `system-${Date.now()}-${Math.random()}`,
      role: 'system',
      content,
      timestamp: new Date().toISOString(),
      metadata,
    };
    setMessages((prev) => [...prev, systemMessage]);
  }, []);

  /**
   * Detect if the user has manually edited the workflow JSON
   * Requirements: 8.1, 8.3
   */
  const hasManualEdits = useCallback((): boolean => {
    // If we haven't generated anything yet, there are no manual edits
    if (!lastAIGeneratedJson) {
      return false;
    }

    // Normalize JSON for comparison (remove whitespace differences)
    try {
      const currentNormalized = JSON.stringify(JSON.parse(currentWorkflowJson));
      const lastAINormalized = JSON.stringify(JSON.parse(lastAIGeneratedJson));
      return currentNormalized !== lastAINormalized;
    } catch {
      // If JSON is invalid, consider it as manually edited
      return true;
    }
  }, [currentWorkflowJson, lastAIGeneratedJson]);

  /**
   * Get a summary of manual edits for context
   * Requirements: 8.3, 8.4
   * Task 26: Memoize workflow JSON parsing
   */
  const getManualEditContext = useCallback((): string => {
    if (!hasManualEdits()) {
      return '';
    }

    try {
      const current = JSON.parse(currentWorkflowJson);
      const lastAI = lastAIGeneratedJson ? JSON.parse(lastAIGeneratedJson) : null;

      if (!lastAI) {
        return '\n\n[Note: The user has manually edited the workflow JSON in the editor.]';
      }

      // Provide context about what changed
      const currentStepCount = Object.keys(current.steps || {}).length;
      const lastAIStepCount = Object.keys(lastAI.steps || {}).length;

      if (currentStepCount !== lastAIStepCount) {
        return `\n\n[Note: The user has manually edited the workflow. It now has ${currentStepCount} steps (was ${lastAIStepCount} steps).]`;
      }

      return '\n\n[Note: The user has manually edited the workflow JSON in the editor.]';
    } catch {
      return '\n\n[Note: The user has manually edited the workflow JSON in the editor.]';
    }
  }, [currentWorkflowJson, lastAIGeneratedJson, hasManualEdits]);

  /**
   * Memoize parsed workflow JSON to avoid repeated parsing
   * Task 26: Memoize workflow JSON parsing
   * Note: These are prepared for future use in performance-critical operations
   */
  const parsedCurrentWorkflow = useMemo(() => {
    try {
      return JSON.parse(currentWorkflowJson);
    } catch {
      return null;
    }
  }, [currentWorkflowJson]);

  const parsedLastAIWorkflow = useMemo(() => {
    if (!lastAIGeneratedJson) return null;
    try {
      return JSON.parse(lastAIGeneratedJson);
    } catch {
      return null;
    }
  }, [lastAIGeneratedJson]);

  // Suppress unused variable warnings - these are prepared for future performance optimizations
  void parsedCurrentWorkflow;
  void parsedLastAIWorkflow;

  /**
   * Restore session when sidebar reopens
   * Requirements: 1.5, 7.2
   */
  useEffect(() => {
    if (isOpen && sessionId && messages.length > 0) {
      // Restore chat view if we have an active session
      setView('chat');
    } else if (isOpen && !sessionId) {
      // Start fresh if no session exists
      setView('initial');
    }
  }, [isOpen, sessionId, messages.length]);

  /**
   * Notify user when manual edits are detected
   * Requirements: 8.1, 8.2
   */
  useEffect(() => {
    // Only check for manual edits when in chat view with an active session
    if (!isOpen || view !== 'chat' || !sessionId) {
      return;
    }

    // Check if there are manual edits and we haven't notified yet
    if (hasManualEdits() && !hasNotifiedManualEdit) {
      addSystemMessage(
        'I noticed you\'ve manually edited the workflow. When you send your next message, I\'ll use your edited version as the base for any changes.',
        { success: true }
      );
      setHasNotifiedManualEdit(true);
    }

    // Reset notification flag if edits are reverted
    if (!hasManualEdits() && hasNotifiedManualEdit) {
      setHasNotifiedManualEdit(false);
    }
  }, [isOpen, view, sessionId, hasManualEdits, hasNotifiedManualEdit, addSystemMessage]);

  /**
   * Clear session state on component unmount
   * Requirements: 7.3, 7.4
   */
  useEffect(() => {
    return () => {
      // Cleanup on unmount - clear all session state
      setSessionId(null);
      setMessages([]);
      setView('initial');
      setError(null);
      setIsLoading(false);
      setShowProgressMessage(false);
      setRetryCountdown(null);
      setLastFailedAction(null);
    };
  }, []);

  /**
   * Implement focus trap when sidebar is open
   * Requirement 1.3 - Focus trap in sidebar
   */
  useEffect(() => {
    if (!isOpen || !sidebarRef.current) return;

    // Save focus before opening sidebar
    focusManagerRef.current.save();

    // Set up focus trap
    const cleanup = trapFocus(sidebarRef.current);

    return () => {
      cleanup();
      // Restore focus when sidebar closes
      focusManagerRef.current.restore();
    };
  }, [isOpen]);

  /**
   * Handle Escape key to close sidebar
   * Requirement 1.3 - Keyboard navigation (Escape)
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      handleKeyboardNavigation(e, {
        onEscape: () => {
          if (isOpen) {
            onClose();
          }
        },
      });
    },
    [isOpen, onClose]
  );

  /**
   * Handle rate limit countdown
   * Requirement 6.3
   */
  useEffect(() => {
    if (retryCountdown === null || retryCountdown <= 0) {
      return;
    }

    const timer = setTimeout(() => {
      setRetryCountdown((prev) => {
        if (prev === null || prev <= 1) {
          // Countdown complete - re-enable input
          return null;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearTimeout(timer);
  }, [retryCountdown]);

  /**
   * Handle errors with appropriate UI feedback
   * Task 27: Enhanced error handling with recovery mechanisms
   * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.5
   */
  const handleError = useCallback((err: unknown, action?: () => Promise<void>) => {
    const errorInfo = getErrorInfo(err);
    const errorMessage = errorInfo.message;
    const suggestions = errorInfo.suggestions;
    const retryAfter = errorInfo.retryAfter;
    const recoverable = errorInfo.recoverable;
    const category = errorInfo.category;

    // Task 27: Check for critical errors that need fallback UI
    if (isCriticalError(err)) {
      setCriticalError({
        message: errorMessage,
        details: errorInfo.details,
        suggestions,
      });
      return;
    }

    // Task 27: Handle session expiration gracefully (Requirements 6.4, 7.5)
    if (category === 'session_expired' && sessionId) {
      addSystemMessage(
        'Your session has expired. Starting a new session...',
        { success: false }
      );
      
      // Clear session state to force new session creation
      setSessionId(null);
      setMessages([]);
      setView('initial');
      setError(null);
      setCriticalError(null);
      
      // Add a follow-up message to guide the user
      setTimeout(() => {
        addSystemMessage(
          'Session cleared. Please describe your workflow to start a new session.',
          { success: true }
        );
      }, 500);
      
      return;
    }

    // Task 27: Handle rate limit with countdown (Requirement 6.3)
    if (retryAfter !== null && retryAfter !== undefined && retryAfter > 0) {
      setRetryCountdown(retryAfter);
      addSystemMessage(
        `${errorMessage} Retrying in ${retryAfter} seconds...`,
        { success: false, suggestions }
      );
      setError(errorMessage);
      
      // Store the action to retry after countdown
      if (action) {
        setLastFailedAction(() => action);
      }
      return;
    }

    // Task 27: Handle workflow validation errors gracefully (Requirement 6.2)
    let fullMessage = errorMessage;
    if (suggestions.length > 0) {
      fullMessage += '\n\nSuggestions:\n' + suggestions.map(s => `• ${s}`).join('\n');
    }

    // Add system message in chat view (Requirement 6.1)
    if (view === 'chat') {
      addSystemMessage(fullMessage, { 
        success: false,
        suggestions,
        validation_errors: category === 'validation' ? [errorMessage] : undefined,
      });
    }

    // Set error with suggestions for display in initial view too (Requirement 6.2)
    setError(fullMessage);

    // Task 27: Store action for retry if error is recoverable (Requirement 6.5)
    if (recoverable && action) {
      setLastFailedAction(() => action);
    } else {
      setLastFailedAction(null);
    }
  }, [view, sessionId, addSystemMessage]);

  /**
   * Retry the last failed action
   * Task 27: Enhanced retry handler
   * Requirement 6.5
   */
  const handleRetry = useCallback(async () => {
    if (!lastFailedAction) return;

    setError(null);
    setCriticalError(null);
    setLastFailedAction(null);
    await lastFailedAction();
  }, [lastFailedAction]);

  /**
   * Reset the component state after a critical error
   * Task 27: Reset handler for critical errors
   */
  const handleReset = useCallback(() => {
    // Clear all state
    setSessionId(null);
    setMessages([]);
    setView('initial');
    setError(null);
    setCriticalError(null);
    setIsLoading(false);
    setShowProgressMessage(false);
    setRetryCountdown(null);
    setLastFailedAction(null);
    setHasNotifiedManualEdit(false);
    setLatestChanges(null);
    setAutoRetryAttempt(0);
  }, []);

  /**
   * Handle workflow generation from description
   * Task 27: Enhanced with automatic retry for network errors
   * Requirements: 2.3, 2.4, 2.5, 5.1, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5
   */
  const handleGenerate = useCallback(
    async (description: string) => {
      setIsLoading(true);
      setError(null);
      setShowProgressMessage(false);
      setLastFailedAction(null);
      setCriticalError(null);
      setAutoRetryAttempt(0);

      // Show progress message after 5 seconds (Requirement 5.5)
      const progressTimer = setTimeout(() => {
        setShowProgressMessage(true);
      }, 5000);

      try {
        // Task 27: Wrap API call with automatic retry for network errors
        const session = await retryWithBackoff(
          async () => {
            // Show retry attempt in chat if this is a retry
            if (autoRetryAttempt > 0) {
              addSystemMessage(
                `Retrying request (attempt ${autoRetryAttempt + 1}/3)...`,
                { success: false }
              );
            }
            
            return await createChatSession({
              initial_description: description,
            });
          },
          {
            maxAttempts: 3,
            initialDelay: 1000,
            maxDelay: 5000,
            backoffMultiplier: 2,
          }
        );

        // Store session data
        setSessionId(session.id);
        setMessages(session.messages);

        // Update workflow JSON if available
        if (session.current_workflow) {
          const workflowJson = JSON.stringify(session.current_workflow, null, 2);
          
          // Get change information for visual feedback
          const changes = getWorkflowChanges(currentWorkflowJson, workflowJson);
          setLatestChanges({
            summary: changes.summary,
            detailedSummary: changes.detailedSummary,
            addedSteps: changes.addedSteps.length,
            removedSteps: changes.removedSteps.length,
            modifiedSteps: changes.modifiedSteps.length,
          });
          
          // Find the assistant message with explanation
          const assistantMessage = session.messages.find(
            (msg) => msg.role === 'assistant'
          );
          const explanation = assistantMessage?.content || 'Workflow generated successfully';

          onWorkflowUpdate(workflowJson, explanation);
        }

        // Switch to chat view
        setView('chat');
        setAutoRetryAttempt(0);
      } catch (err) {
        // Task 27: Use enhanced error handling with recovery mechanisms
        handleError(err, () => handleGenerate(description));
      } finally {
        clearTimeout(progressTimer);
        setIsLoading(false);
        setShowProgressMessage(false);
      }
    },
    [onWorkflowUpdate, handleError, autoRetryAttempt, addSystemMessage, currentWorkflowJson]
  );

  /**
   * Handle PDF upload
   * Task 27: Enhanced with automatic retry for network errors
   * Requirements: 3.4, 3.5, 5.1, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5
   */
  const handleUpload = useCallback(
    async (file: File) => {
      setIsLoading(true);
      setError(null);
      setShowProgressMessage(false);
      setLastFailedAction(null);
      setCriticalError(null);
      setAutoRetryAttempt(0);

      // Show progress message after 5 seconds (Requirement 5.5)
      const progressTimer = setTimeout(() => {
        setShowProgressMessage(true);
      }, 5000);

      try {
        // Task 27: Wrap API call with automatic retry for network errors
        const result = await retryWithBackoff(
          async () => {
            // Show retry attempt in chat if this is a retry
            if (autoRetryAttempt > 0) {
              addSystemMessage(
                `Retrying upload (attempt ${autoRetryAttempt + 1}/3)...`,
                { success: false }
              );
            }
            
            return await uploadDocument(file);
          },
          {
            maxAttempts: 3,
            initialDelay: 1000,
            maxDelay: 5000,
            backoffMultiplier: 2,
          }
        );

        if (result.success && result.workflow_json) {
          // Update workflow JSON with the PDF-generated workflow
          const workflowJson = JSON.stringify(result.workflow_json, null, 2);
          
          // Get change information for visual feedback
          const changes = getWorkflowChanges(currentWorkflowJson, workflowJson);
          setLatestChanges({
            summary: changes.summary,
            detailedSummary: changes.detailedSummary,
            addedSteps: changes.addedSteps.length,
            removedSteps: changes.removedSteps.length,
            modifiedSteps: changes.modifiedSteps.length,
          });
          
          onWorkflowUpdate(workflowJson, result.explanation);

          // Create a chat session after successful upload for further refinement
          const session = await createChatSession({
            initial_description: `I uploaded a document (${file.name}) and generated a workflow. The workflow is now loaded in the editor.`,
          });

          // Store session data
          setSessionId(session.id);
          
          // Build messages array with validation warnings if present
          const messages = [...session.messages];
          
          // Add validation warnings as system messages if present (Task 28: Better error display)
          if (result.validation_errors && result.validation_errors.length > 0) {
            messages.push({
              id: `validation-warning-${Date.now()}`,
              role: 'system',
              content: `⚠️ Workflow generated with validation warnings:\n\n${result.validation_errors.map(e => `• ${e}`).join('\n')}\n\n${result.suggestions.length > 0 ? `Suggestions:\n${result.suggestions.map(s => `• ${s}`).join('\n')}` : 'You can refine the workflow through chat to address these issues.'}`,
              timestamp: new Date().toISOString(),
              metadata: {
                success: false,
                validation_errors: result.validation_errors,
                suggestions: result.suggestions,
              },
            });
          } else if (!session.current_workflow) {
            // No validation errors - add success message
            messages.push({
              id: `system-${Date.now()}`,
              role: 'system',
              content: `Workflow generated from ${file.name}. You can now refine it through chat.`,
              timestamp: new Date().toISOString(),
              metadata: {
                success: true,
                agents_used: result.agents_used,
              },
            });
          }
          
          setMessages(messages);

          // Switch to chat view (Requirement 3.5)
          setView('chat');
          setAutoRetryAttempt(0);
        } else {
          // Task 27: Handle validation errors gracefully (Requirement 6.2)
          const errorMsg = result.explanation || 'Failed to generate workflow from document';
          const validationInfo = result.validation_errors && result.validation_errors.length > 0
            ? `\n\nValidation Errors:\n${result.validation_errors.map(e => `• ${e}`).join('\n')}`
            : '';
          const suggestionsInfo = result.suggestions && result.suggestions.length > 0
            ? `\n\nSuggestions:\n${result.suggestions.map(s => `• ${s}`).join('\n')}`
            : '';
          
          setError(errorMsg + validationInfo + suggestionsInfo);
        }
      } catch (err) {
        // Task 27: Use enhanced error handling with recovery mechanisms
        handleError(err, () => handleUpload(file));
      } finally {
        clearTimeout(progressTimer);
        setIsLoading(false);
        setShowProgressMessage(false);
      }
    },
    [onWorkflowUpdate, handleError, autoRetryAttempt, addSystemMessage, currentWorkflowJson]
  );

  /**
   * Handle sending chat message
   * Task 27: Enhanced with automatic retry for network errors
   * Requirements: 4.3, 4.4, 4.5, 5.2, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 8.3, 8.4
   */
  const handleSendMessage = useCallback(
    async (message: string) => {
      // Check for session expiration (Requirement 6.4)
      if (!sessionId) {
        addSystemMessage(
          'No active session. Please start a new workflow generation.',
          { success: false }
        );
        setError('No active session. Please start a new workflow generation.');
        return;
      }

      // Add context about manual edits if present (Requirements 8.3, 8.4)
      const manualEditContext = getManualEditContext();
      const messageWithContext = message + manualEditContext;

      // If there are manual edits, also include the current workflow JSON as context
      let fullMessage = messageWithContext;
      if (hasManualEdits()) {
        try {
          // Task 27: Validate that the current JSON is valid before including it
          JSON.parse(currentWorkflowJson);
          fullMessage += `\n\nCurrent workflow JSON:\n\`\`\`json\n${currentWorkflowJson}\n\`\`\``;
        } catch {
          // Task 27: Handle workflow validation errors gracefully (Requirement 8.5)
          fullMessage += '\n\n[Note: The current workflow JSON in the editor has syntax errors. Please help fix them.]';
        }
      }

      // Create user message immediately (Requirement 4.3)
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      };

      // Display user message immediately (Requirement 4.3)
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);
      setShowProgressMessage(false);
      setLastFailedAction(null);
      setCriticalError(null);
      setAutoRetryAttempt(0);

      // Show progress message after 5 seconds (Requirement 5.5)
      const progressTimer = setTimeout(() => {
        setShowProgressMessage(true);
      }, 5000);

      try {
        // Task 27: Wrap API call with automatic retry for network errors
        const updatedSession = await retryWithBackoff(
          async () => {
            // Show retry attempt in chat if this is a retry
            if (autoRetryAttempt > 0) {
              addSystemMessage(
                `Retrying message (attempt ${autoRetryAttempt + 1}/3)...`,
                { success: false }
              );
            }
            
            return await sendChatMessage(sessionId, { message: fullMessage });
          },
          {
            maxAttempts: 3,
            initialDelay: 1000,
            maxDelay: 5000,
            backoffMultiplier: 2,
          }
        );

        // Update messages with the full conversation from the API
        setMessages(updatedSession.messages);

        // Update workflow JSON if available (Requirement 4.4)
        if (updatedSession.current_workflow) {
          const workflowJson = JSON.stringify(updatedSession.current_workflow, null, 2);

          // Get change information for visual feedback
          const changes = getWorkflowChanges(currentWorkflowJson, workflowJson);
          setLatestChanges({
            summary: changes.summary,
            detailedSummary: changes.detailedSummary,
            addedSteps: changes.addedSteps.length,
            removedSteps: changes.removedSteps.length,
            modifiedSteps: changes.modifiedSteps.length,
          });

          // Find the latest assistant message with explanation (Requirement 4.5)
          const latestAssistantMessage = [...updatedSession.messages]
            .reverse()
            .find((msg) => msg.role === 'assistant');

          const explanation = latestAssistantMessage?.content || 'Workflow updated successfully';

          // Update the workflow in the editor (Requirement 8.4)
          onWorkflowUpdate(workflowJson, explanation);
        }

        // Reset manual edit notification flag after successful update
        setHasNotifiedManualEdit(false);
        setAutoRetryAttempt(0);
      } catch (err) {
        // Task 27: Use enhanced error handling with recovery mechanisms
        handleError(err, () => handleSendMessage(message));
      } finally {
        clearTimeout(progressTimer);
        setIsLoading(false);
        setShowProgressMessage(false);
      }
    },
    [sessionId, currentWorkflowJson, hasManualEdits, getManualEditContext, onWorkflowUpdate, handleError, addSystemMessage, autoRetryAttempt]
  );


  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop - only visible on mobile (Requirement 11.1) */}
          {isMobile && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="fixed inset-0 bg-black/50 z-40"
              aria-hidden="true"
            />
          )}

          {/* Sidebar Panel */}
          <motion.aside
            ref={sidebarRef}
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ 
              type: 'spring', 
              damping: 25, 
              stiffness: 200,
              // Smoother animation on mobile (Requirement 11.5)
              mass: isMobile ? 0.8 : 1
            }}
            className={cn(
              'fixed inset-y-0 right-0 z-50 flex flex-col bg-white shadow-xl',
              // Mobile: full width (Requirement 11.1)
              // Desktop: fixed width 400px (Requirement 11.2)
              isMobile ? 'w-full' : 'w-[400px]'
            )}
            role="dialog"
            aria-modal="true"
            aria-labelledby="ai-sidebar-title"
            aria-describedby="ai-sidebar-description"
            onKeyDown={handleKeyDown}
            tabIndex={-1}
          >
            {/* Header */}
            <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
              <div>
                <h2
                  id="ai-sidebar-title"
                  className="text-lg font-semibold text-gray-900"
                >
                  AI Workflow Generator
                </h2>
                <p id="ai-sidebar-description" className="sr-only">
                  Generate and refine workflows using AI. Use Tab to navigate, Enter to activate buttons, and Escape to close.
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-white/60 rounded-lg transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                aria-label="Close AI sidebar (Escape)"
                title="Close sidebar"
              >
                <X className="w-5 h-5" aria-hidden="true" />
              </button>
            </div>

            {/* Content Area - Initial View, Chat View, or Error Fallback */}
            {/* Task 26: Lazy loading with Suspense */}
            {/* Task 27: Show ErrorFallback for critical errors */}
            <div className="flex-1 overflow-hidden">
              <Suspense fallback={
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-sm text-gray-600">Loading...</p>
                  </div>
                </div>
              }>
                {criticalError ? (
                  <ErrorFallback
                    message={criticalError.message}
                    details={criticalError.details}
                    suggestions={criticalError.suggestions}
                    onRetry={lastFailedAction ? handleRetry : undefined}
                    onReset={handleReset}
                    isRetrying={isLoading}
                  />
                ) : view === 'initial' ? (
                  <InitialView
                    onGenerate={handleGenerate}
                    onUpload={handleUpload}
                    isLoading={isLoading}
                    error={error}
                    showProgressMessage={showProgressMessage}
                    onRetry={lastFailedAction ? handleRetry : undefined}
                    retryCountdown={retryCountdown}
                  />
                ) : (
                  <ChatView
                    messages={messages}
                    onSendMessage={handleSendMessage}
                    isLoading={isLoading}
                    sessionId={sessionId || ''}
                    showProgressMessage={showProgressMessage}
                    onRetry={lastFailedAction ? handleRetry : undefined}
                    retryCountdown={retryCountdown}
                    latestChanges={latestChanges}
                  />
                )}
              </Suspense>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

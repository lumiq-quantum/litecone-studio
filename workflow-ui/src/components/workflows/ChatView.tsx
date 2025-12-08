import { useState, useCallback, useEffect, useRef, memo, useMemo } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { handleKeyboardNavigation } from '@/lib/accessibility';
import ChangeExplanation from './ChangeExplanation';
import type { Message } from '@/types';

/**
 * LoadingSkeleton Component
 * 
 * Displays a skeleton loading state in the chat area
 * Requirements: 5.3
 */
const LoadingSkeleton = memo(function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Skeleton message 1 */}
      <div className="p-3 rounded-lg bg-gray-100 mr-8">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="h-3 w-12 bg-gray-300 rounded" />
          <div className="h-3 w-16 bg-gray-300 rounded" />
        </div>
        <div className="space-y-2">
          <div className="h-3 w-full bg-gray-300 rounded" />
          <div className="h-3 w-4/5 bg-gray-300 rounded" />
        </div>
      </div>
      
      {/* Skeleton message 2 */}
      <div className="p-3 rounded-lg bg-gray-100 mr-8">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="h-3 w-12 bg-gray-300 rounded" />
          <div className="h-3 w-16 bg-gray-300 rounded" />
        </div>
        <div className="space-y-2">
          <div className="h-3 w-full bg-gray-300 rounded" />
          <div className="h-3 w-3/4 bg-gray-300 rounded" />
          <div className="h-3 w-5/6 bg-gray-300 rounded" />
        </div>
      </div>
    </div>
  );
});

/**
 * MessageItem Component
 * 
 * Memoized individual message component for better performance
 * Task 26: Memoize message list rendering
 */
interface MessageItemProps {
  message: Message;
  isLatest: boolean;
  latestChanges?: {
    summary: string;
    detailedSummary: string;
    addedSteps: number;
    removedSteps: number;
    modifiedSteps: number;
  } | null;
}

const MessageItem = memo(function MessageItem({ 
  message, 
  isLatest, 
  latestChanges,
}: MessageItemProps) {
  return (
    <motion.div
      key={message.id}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ 
        duration: 0.2,
        ease: 'easeOut',
        delay: 0, // No delay for better performance
      }}
      className={cn(
        'p-4 rounded-xl shadow-sm border transition-all duration-200',
        message.role === 'user' && 'bg-gradient-to-br from-blue-50 to-blue-100/50 ml-8 border-blue-200 hover:shadow-md',
        message.role === 'assistant' && 'bg-gradient-to-br from-gray-50 to-gray-100/50 mr-8 border-gray-200 hover:shadow-md',
        message.role === 'system' && 'bg-gradient-to-br from-yellow-50 to-yellow-100/50 border-yellow-200 hover:shadow-md'
      )}
      role="article"
      aria-label={`${message.role === 'user' ? 'Your' : message.role === 'assistant' ? 'AI' : 'System'} message at ${new Date(message.timestamp).toLocaleTimeString()}`}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <span className="text-xs font-medium text-gray-700">
          {message.role === 'user' ? 'You' : message.role === 'assistant' ? 'AI' : 'System'}
        </span>
        <span className="text-xs text-gray-400">
          {new Date(message.timestamp).toLocaleTimeString()}
        </span>
      </div>
      <p className="text-sm text-gray-900 whitespace-pre-wrap">
        {message.content}
      </p>
      
      {/* Display change explanation for assistant messages with workflow updates */}
      {message.role === 'assistant' && latestChanges && isLatest && (
        <div className="mt-3">
          <ChangeExplanation
            summary={latestChanges.summary}
            detailedSummary={latestChanges.detailedSummary}
            addedSteps={latestChanges.addedSteps}
            removedSteps={latestChanges.removedSteps}
            modifiedSteps={latestChanges.modifiedSteps}
            showDetails={true}
          />
        </div>
      )}
      
      {message.metadata?.agents_used && message.metadata.agents_used.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs font-semibold text-gray-700 mb-2">Agents used:</p>
          <div className="flex flex-wrap gap-2">
            {message.metadata.agents_used.map((agent) => (
              <span
                key={agent}
                className="px-3 py-1 bg-gradient-to-r from-blue-100 to-blue-200 text-blue-700 text-xs font-medium rounded-full shadow-sm hover:shadow-md transition-all duration-200 hover:scale-105"
              >
                {agent}
              </span>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for better memoization
  return (
    prevProps.message.id === nextProps.message.id &&
    prevProps.isLatest === nextProps.isLatest &&
    prevProps.latestChanges === nextProps.latestChanges
  );
});

/**
 * Props for the ChatView component
 */
export interface ChatViewProps {
  /** Array of chat messages */
  messages: Message[];
  /** Callback when user sends a message */
  onSendMessage: (message: string) => Promise<void>;
  /** Whether a message is being sent */
  isLoading: boolean;
  /** Current session ID */
  sessionId: string;
  /** Whether to show progress message for long operations */
  showProgressMessage: boolean;
  /** Callback to retry the last failed action */
  onRetry?: () => Promise<void>;
  /** Countdown in seconds before retry is allowed (for rate limiting) */
  retryCountdown: number | null;
  /** Change information for the latest workflow update */
  latestChanges?: {
    summary: string;
    detailedSummary: string;
    addedSteps: number;
    removedSteps: number;
    modifiedSteps: number;
  } | null;
}

/**
 * ChatView Component
 * 
 * Displays the chat interface for refining workflows through conversation.
 * Shows message history and provides an input field for sending new messages.
 * Includes loading states, typing indicators, progress messages, and error handling.
 * 
 * Requirements: 4.1, 4.2, 5.2, 5.3, 5.4, 5.5, 6.1, 6.3, 6.5
 */
export default function ChatView({
  messages,
  onSendMessage,
  isLoading,
  sessionId,
  showProgressMessage,
  onRetry,
  retryCountdown,
  latestChanges,
}: ChatViewProps) {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageListRef = useRef<HTMLDivElement>(null);

  // Suppress unused variable warning - will be used in task 7
  void sessionId;

  /**
   * Task 26: Virtual scrolling for long chat histories (>50 messages)
   * Only render visible messages plus a buffer for performance
   */
  const VIRTUAL_SCROLL_THRESHOLD = 50;
  const BUFFER_SIZE = 10;
  
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: messages.length });

  const shouldUseVirtualScroll = messages.length > VIRTUAL_SCROLL_THRESHOLD;

  /**
   * Update visible range based on scroll position
   * Task 26: Virtual scrolling implementation
   */
  useEffect(() => {
    if (!shouldUseVirtualScroll || !messageListRef.current) {
      setVisibleRange({ start: 0, end: messages.length });
      return;
    }

    const handleScroll = () => {
      if (!messageListRef.current) return;

      const container = messageListRef.current;
      const scrollTop = container.scrollTop;
      const containerHeight = container.clientHeight;
      const averageMessageHeight = 100; // Approximate height per message

      const startIndex = Math.max(0, Math.floor(scrollTop / averageMessageHeight) - BUFFER_SIZE);
      const endIndex = Math.min(
        messages.length,
        Math.ceil((scrollTop + containerHeight) / averageMessageHeight) + BUFFER_SIZE
      );

      setVisibleRange({ start: startIndex, end: endIndex });
    };

    const container = messageListRef.current;
    container.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial calculation

    return () => {
      container.removeEventListener('scroll', handleScroll);
    };
  }, [messages.length, shouldUseVirtualScroll]);

  /**
   * Memoize visible messages for performance
   * Task 26: Memoize message list rendering
   */
  const visibleMessages = useMemo(() => {
    if (!shouldUseVirtualScroll) {
      return messages;
    }
    return messages.slice(visibleRange.start, visibleRange.end);
  }, [messages, visibleRange, shouldUseVirtualScroll]);

  /**
   * Auto-scroll to latest message when messages change
   * Requirement 4.2 - smooth scrolling in chat
   */
  useEffect(() => {
    if (messagesEndRef.current) {
      // Use smooth scrolling for better UX
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [messages]);

  /**
   * Handle sending a message
   */
  const handleSend = useCallback(async () => {
    const trimmed = inputMessage.trim();
    if (!trimmed || isLoading) return;

    setInputMessage('');
    await onSendMessage(trimmed);
  }, [inputMessage, isLoading, onSendMessage]);

  /**
   * Handle keyboard navigation in chat input
   * Requirement 1.3 - Keyboard navigation (Enter to send)
   */
  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      handleKeyboardNavigation(e, {
        onEnter: () => {
          if (inputMessage.trim() && !isLoading && (retryCountdown === null || retryCountdown <= 0)) {
            handleSend();
          }
        },
      });
    },
    [handleSend, inputMessage, isLoading, retryCountdown]
  );

  return (
    <div className="flex flex-col h-full">
      {/* Message List with ARIA live region (Requirement 4.2) */}
      <div 
        ref={messageListRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
        role="log"
        aria-live="polite"
        aria-atomic="false"
        aria-relevant="additions"
        aria-label="Chat conversation"
      >
        {messages.length === 0 ? (
          // Show loading skeleton when no messages yet (Requirement 5.3)
          isLoading ? (
            <LoadingSkeleton />
          ) : (
            <div className="text-center text-gray-500 text-sm py-8">
              <p>Workflow generated! You can now refine it through chat.</p>
            </div>
          )
        ) : (
          <>
            {/* Task 26: Virtual scrolling - add spacer for scrolled-out messages */}
            {shouldUseVirtualScroll && visibleRange.start > 0 && (
              <div style={{ height: `${visibleRange.start * 100}px` }} aria-hidden="true" />
            )}
            
            <AnimatePresence initial={false}>
              {visibleMessages.map((message, index) => {
                const actualIndex = shouldUseVirtualScroll 
                  ? visibleRange.start + index 
                  : index;
                const isLatest = actualIndex === messages.length - 1;
                
                return (
                  <MessageItem
                    key={message.id}
                    message={message}
                    isLatest={isLatest}
                    latestChanges={latestChanges}
                  />
                );
              })}
            </AnimatePresence>
            
            {/* Task 26: Virtual scrolling - add spacer for scrolled-out messages */}
            {shouldUseVirtualScroll && visibleRange.end < messages.length && (
              <div 
                style={{ height: `${(messages.length - visibleRange.end) * 100}px` }} 
                aria-hidden="true" 
              />
            )}
            {/* Typing indicator while loading (Requirement 5.2) */}
            <AnimatePresence>
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="p-4 rounded-xl bg-gradient-to-br from-gray-50 to-gray-100/50 mr-8 border border-gray-200 shadow-sm"
                  role="status"
                  aria-live="polite"
                  aria-label="AI is typing"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-xs font-semibold text-gray-700">AI</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} aria-hidden="true" />
                    <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} aria-hidden="true" />
                    <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} aria-hidden="true" />
                  </div>
                  <span className="sr-only">AI is typing a response</span>
                </motion.div>
              )}
            </AnimatePresence>
            {/* Progress Message for Long Operations (Requirement 5.5) */}
            <AnimatePresence>
              {isLoading && showProgressMessage && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                  className="p-4 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100/50 border border-blue-200 shadow-sm"
                  role="status"
                  aria-live="polite"
                  aria-atomic="true"
                >
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" aria-hidden="true" />
                    <p className="text-sm text-blue-800 font-medium">
                      The AI is working on your request. This may take a moment...
                    </p>
                  </div>
                  <span className="sr-only">Processing your request, please wait</span>
                </motion.div>
              )}
            </AnimatePresence>
            {/* Invisible element to scroll to */}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Chat Input (Requirement 5.4 - disabled during loading) */}
      <div className="p-4 border-t border-gray-200">
        {/* Rate Limit Countdown (Requirement 6.3) */}
        {retryCountdown !== null && retryCountdown > 0 && (
          <div 
            className="mb-3 p-3 bg-gradient-to-br from-yellow-50 to-yellow-100/50 border border-yellow-200 rounded-xl shadow-sm"
            role="status"
            aria-live="polite"
            aria-atomic="true"
          >
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 text-yellow-600 animate-spin flex-shrink-0" aria-hidden="true" />
              <p className="text-sm text-yellow-800 font-medium">
                Rate limit active. You can send messages again in {retryCountdown} second{retryCountdown !== 1 ? 's' : ''}.
              </p>
            </div>
          </div>
        )}
        
        {/* Retry Button for Network Errors (Requirement 6.5) */}
        {onRetry && retryCountdown === null && (
          <div className="mb-3">
            <button
              onClick={onRetry}
              disabled={isLoading}
              className={cn(
                'w-full px-4 py-2.5 text-sm font-semibold rounded-xl transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                'shadow-md',
                isLoading
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed shadow-none'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg transform hover:scale-[1.02]'
              )}
              aria-label={isLoading ? 'Retrying, please wait' : 'Retry failed action (Enter)'}
              aria-disabled={isLoading}
              aria-busy={isLoading}
            >
              {isLoading ? 'Retrying...' : 'Retry Last Action'}
            </button>
          </div>
        )}
        
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={
              retryCountdown !== null && retryCountdown > 0
                ? `Rate limited. Wait ${retryCountdown}s...`
                : isLoading
                ? "AI is responding..."
                : "Type a message to refine the workflow..."
            }
            disabled={isLoading || (retryCountdown !== null && retryCountdown > 0)}
            className={cn(
              'flex-1 px-4 py-3 text-sm border border-gray-300 rounded-xl',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
              'transition-all duration-200 shadow-sm hover:shadow-md',
              !isLoading && 'hover:border-gray-400'
            )}
            aria-label="Type a message to refine the workflow. Press Enter to send."
            aria-disabled={isLoading || (retryCountdown !== null && retryCountdown > 0)}
            aria-describedby="chat-input-help"
          />
          <span id="chat-input-help" className="sr-only">
            Press Enter to send your message. The AI will respond with workflow updates.
          </span>
          <button
            onClick={handleSend}
            disabled={!inputMessage.trim() || isLoading || (retryCountdown !== null && retryCountdown > 0)}
            className={cn(
              'p-3 rounded-xl transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
              'shadow-md',
              inputMessage.trim() && !isLoading && (retryCountdown === null || retryCountdown <= 0)
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg transform hover:scale-105'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed shadow-none'
            )}
            aria-label={isLoading ? 'Sending message, please wait' : 'Send message (Enter)'}
            aria-disabled={!inputMessage.trim() || isLoading || (retryCountdown !== null && retryCountdown > 0)}
            aria-busy={isLoading}
            title="Send message"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
                <span className="sr-only">Sending message</span>
              </>
            ) : (
              <>
                <Send className="w-5 h-5" aria-hidden="true" />
                <span className="sr-only">Send</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

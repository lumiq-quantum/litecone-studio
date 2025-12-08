# Implementation Plan

- [x] 1. Set up API service and types
  - Create TypeScript types for AI workflow API requests and responses
  - Create aiWorkflows.ts service file with API client methods
  - Add error handling utilities for AI workflow errors
  - Create type definitions for ChatSession, Message, and WorkflowGenerationResult
  - _Requirements: 2.3, 3.4, 4.3, 6.1_

- [x] 2. Create AIGenerateSidebar component structure
  - Create AIGenerateSidebar component with props interface
  - Implement sidebar open/close animation with Framer Motion
  - Add sidebar header with close button
  - Implement responsive layout (desktop and mobile)
  - Add z-index and positioning styles
  - _Requirements: 1.2, 1.3, 1.4, 11.1, 11.2_

- [x] 3. Implement InitialView component
  - Create InitialView component with welcome message
  - Add text input field with character count (10-10,000 chars)
  - Implement input validation (minimum 3 words)
  - Add placeholder text with example descriptions
  - Style the initial view layout
  - _Requirements: 2.1, 2.2, 12.1, 12.3, 12.5_

- [x] 4. Implement PDF upload functionality
  - Add PDF upload button to InitialView
  - Implement file picker with PDF-only filter
  - Add file size validation (max 10MB)
  - Display upload progress indicator
  - Add tooltip with format and size information
  - _Requirements: 3.1, 3.2, 3.3, 12.4_

- [x] 5. Implement initial workflow generation
  - Add generate button with loading state
  - Implement createSession API call with description
  - Handle successful generation response
  - Update parent component with generated workflow JSON
  - Switch sidebar view from initial to chat
  - _Requirements: 2.3, 2.4, 2.5_

- [x] 6. Implement PDF upload workflow generation
  - Handle PDF file upload to API
  - Display loading state during upload and processing
  - Parse API response and extract workflow JSON
  - Update parent component with generated workflow
  - Create chat session after successful upload
  - _Requirements: 3.4, 3.5_

- [x] 7. Create ChatView component
  - Create ChatView component with message list
  - Implement auto-scroll to latest message
  - Add chat input field with send button
  - Style user, assistant, and system messages differently
  - Add timestamp display for each message
  - _Requirements: 4.1, 4.2_

- [x] 8. Implement chat message sending
  - Handle chat input submission
  - Send message to API with session ID
  - Display user message immediately
  - Show typing indicator while waiting for response
  - Display AI response with explanation
  - _Requirements: 4.3, 4.4, 4.5_

- [x] 9. Implement workflow update from chat
  - Parse workflow JSON from AI response
  - Update JSON editor with new workflow
  - Trigger visual graph re-render
  - Highlight changed lines in JSON editor
  - Display AI explanation in chat
  - _Requirements: 4.4, 10.1, 10.2, 10.3_

- [x] 10. Implement loading states
  - Add loading spinner for initial generation
  - Add typing indicator for chat messages
  - Add loading skeleton in chat area
  - Disable input fields during loading
  - Add progress message for long operations (>5s)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 11. Implement error handling in sidebar
  - Display API errors as system messages in chat
  - Show validation errors with suggestions
  - Handle rate limit errors with retry countdown
  - Detect and handle session expiration
  - Add retry button for network errors
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 12. Implement session persistence
  - Store session ID in component state
  - Preserve chat history when sidebar closes
  - Restore session when sidebar reopens
  - Clear session state on component unmount
  - Handle session expiration gracefully
  - _Requirements: 1.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 13. Integrate with existing WorkflowCreate page
  - Add "AI Generate" button next to "Use Template" button
  - Add sidebar state management to WorkflowCreate
  - Pass workflow JSON and update callback to sidebar
  - Ensure existing functionality remains unchanged
  - Handle sidebar overlay on visual graph
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 14. Implement manual edit integration
  - Allow manual JSON editing after AI generation
  - Sync manual edits with visual graph
  - Send manually edited JSON in subsequent chat messages
  - Ensure AI uses edited version as base
  - Display validation errors for invalid manual edits
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 15. Implement workflow save integration
  - Ensure "Create Workflow" button works with AI-generated workflows
  - Use existing workflow save logic
  - Keep chat session active after save
  - Navigate to workflow detail page on success
  - Display save errors in toast notifications
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 16. Add visual feedback for changes
  - Implement line highlighting in JSON editor for changes
  - Add animation to visual graph updates
  - Display change explanations prominently in chat
  - Add summary of modifications for multiple changes
  - Implement before/after comparison option
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 17. Implement responsive design
  - Make sidebar full-width on mobile (<1024px)
  - Hide JSON editor and visual graph when sidebar open on mobile
  - Restore editor and graph when sidebar closes on mobile
  - Handle device rotation gracefully
  - Test on various screen sizes
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 18. Add user guidance and onboarding
  - Create welcome message with feature explanation
  - Add example workflow descriptions
  - Implement placeholder text with examples
  - Add tooltips for PDF upload button
  - Display character count and validation feedback
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 19. Implement animations and transitions
  - Add sidebar slide-in/out animation
  - Add message fade-in animation
  - Implement smooth scrolling in chat
  - Add loading spinner animations
  - Add highlight fade-out for changed lines
  - _Requirements: 1.2, 1.3, 4.2_

- [x] 20. Add accessibility features
  - Implement keyboard navigation (Tab, Enter, Escape)
  - Add ARIA labels for all interactive elements
  - Add ARIA live regions for chat messages
  - Implement focus trap in sidebar
  - Add screen reader support for loading states
  - _Requirements: 1.3, 4.2, 5.2_

- [ ]* 21. Write unit tests for AIGenerateSidebar
  - Test sidebar open/close behavior
  - Test view switching (initial → chat)
  - Test session state management
  - Test workflow update callbacks
  - Test error handling
  - _Requirements: 1.2, 1.3, 1.5, 7.2_

- [ ]* 22. Write unit tests for InitialView
  - Test description input validation
  - Test file upload validation
  - Test generate button enable/disable logic
  - Test error display
  - Test character count display
  - _Requirements: 2.2, 3.2, 3.3_

- [ ]* 23. Write unit tests for ChatView
  - Test message rendering
  - Test message ordering
  - Test loading states
  - Test input field behavior
  - Test auto-scroll functionality
  - _Requirements: 4.2, 5.2_

- [ ]* 24. Write unit tests for API service
  - Test request formatting
  - Test response parsing
  - Test error handling
  - Test retry logic
  - Mock API responses
  - _Requirements: 2.3, 3.4, 4.3, 6.1_

- [ ]* 25. Write integration tests
  - Test workflow generation flow (text input)
  - Test workflow generation flow (PDF upload)
  - Test chat refinement flow
  - Test session persistence flow
  - Test error handling flow
  - _Requirements: 2.4, 3.5, 4.4, 7.2, 6.4_

- [x] 26. Optimize performance
  - Implement lazy loading for sidebar component
  - Add debouncing for character count updates
  - Memoize message list rendering
  - Memoize workflow JSON parsing
  - Add virtual scrolling for long chat histories
  - _Requirements: 4.2, 5.4_

- [x] 27. Add error recovery mechanisms
  - Implement session expiration recovery
  - Implement rate limit recovery with countdown
  - Add network error retry logic
  - Handle workflow validation errors gracefully
  - Add fallback UI for critical errors
  - _Requirements: 6.3, 6.4, 6.5, 7.5_

- [x] 28. Polish UI and styling
  - Apply consistent color scheme
  - Ensure proper spacing and alignment
  - Add hover states for interactive elements
  - Implement smooth transitions
  - Test dark mode compatibility (if applicable)
  - _Requirements: 1.2, 4.1, 12.1_

- [ ] 29. Test cross-browser compatibility
  - Test on Chrome, Firefox, Safari, Edge
  - Test on iOS Safari and Chrome
  - Test on Android Chrome
  - Fix any browser-specific issues
  - Verify animations work across browsers
  - _Requirements: 11.1, 11.2_

- [ ] 30. Create documentation
  - Document component props and interfaces
  - Add JSDoc comments to API service methods
  - Create usage examples for developers
  - Document error handling patterns
  - Add troubleshooting guide
  - _Requirements: All_

- [ ] 31. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


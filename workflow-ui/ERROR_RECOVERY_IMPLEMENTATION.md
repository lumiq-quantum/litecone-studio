# Error Recovery Mechanisms Implementation

**Task 27: Add error recovery mechanisms**

This document describes the enhanced error recovery mechanisms implemented for the AI Workflow Generator UI.

## Overview

The error recovery system provides comprehensive handling for various error scenarios, ensuring users can recover from failures gracefully without losing their work or context.

## Implementation Details

### 1. Session Expiration Recovery (Requirement 6.4, 7.5)

**Location:** `AIGenerateSidebar.tsx` - `handleError` function

**Behavior:**
- Detects when a session has expired (404 error)
- Automatically clears the expired session state
- Notifies the user with a clear message
- Resets to the initial view for a fresh start
- Preserves the workflow JSON in the editor

**User Experience:**
```
User Action: Send a message after session expires
System Response: 
  1. "Your session has expired. Starting a new session..."
  2. Clears session state
  3. "Session cleared. Please describe your workflow to start a new session."
```

### 2. Rate Limit Recovery with Countdown (Requirement 6.3)

**Location:** `AIGenerateSidebar.tsx` - `handleError` function and countdown effect

**Behavior:**
- Detects rate limit errors (429 status)
- Extracts retry-after time from headers or response data
- Displays countdown timer to the user
- Disables input during countdown
- Automatically re-enables input when countdown completes
- Stores the failed action for automatic retry

**User Experience:**
```
User Action: Exceeds rate limit
System Response:
  1. "Rate limit exceeded. Retrying in 60 seconds..."
  2. Shows countdown: "59... 58... 57..."
  3. Input field disabled during countdown
  4. Input re-enabled when countdown reaches 0
```

### 3. Network Error Retry Logic (Requirement 6.5)

**Location:** `aiWorkflowErrors.ts` - `retryWithBackoff` function

**Features:**
- Automatic retry with exponential backoff
- Configurable retry attempts (default: 3)
- Configurable delays (initial: 1s, max: 10s)
- Only retries recoverable errors (network, service unavailable)
- Shows retry attempt number to user

**Configuration:**
```typescript
{
  maxAttempts: 3,
  initialDelay: 1000,    // 1 second
  maxDelay: 10000,       // 10 seconds
  backoffMultiplier: 2,  // Exponential backoff
}
```

**Retry Schedule:**
- Attempt 1: Immediate
- Attempt 2: After 1 second
- Attempt 3: After 2 seconds
- Attempt 4: After 4 seconds (if maxAttempts > 3)

**User Experience:**
```
User Action: Network connection drops during request
System Response:
  1. "Retrying request (attempt 2/3)..."
  2. Waits 1 second
  3. "Retrying request (attempt 3/3)..."
  4. Waits 2 seconds
  5. Either succeeds or shows error with retry button
```

### 4. Workflow Validation Error Handling (Requirement 6.2)

**Location:** `aiWorkflowErrors.ts` - `getErrorInfo` function

**Behavior:**
- Detects validation errors (400 status with validation error code)
- Extracts detailed validation error messages
- Provides actionable suggestions
- Marks errors as recoverable (user can fix input)
- Displays field-level error details when available

**User Experience:**
```
User Action: Submits invalid workflow description
System Response:
  "Validation failed

  Validation errors:
  name: Required
  description: Must be at least 10 characters

  Suggestions:
  • Check your input for errors
  • Ensure all required fields are provided
  • Verify the format of your data"
```

### 5. Fallback UI for Critical Errors (Requirement 6.1)

**Location:** `ErrorFallback.tsx` component

**Features:**
- Displays when non-recoverable errors occur
- Shows clear error message
- Provides technical details (collapsible)
- Lists actionable suggestions
- Offers retry and reset options
- Includes support contact information

**Triggers:**
- Unknown errors that are not recoverable
- Errors that are not user-fixable
- System-level failures

**User Experience:**
```
┌─────────────────────────────────────┐
│         [!] Alert Icon              │
│                                     │
│    Something Went Wrong            │
│                                     │
│  [Error Message Box]                │
│  An unexpected error occurred...    │
│                                     │
│  What you can try:                  │
│  • Try refreshing the page          │
│  • Clear your browser cache         │
│  • Contact support if persists      │
│                                     │
│  [Try Again Button]                 │
│  [Start Over Button]                │
│                                     │
│  Support: support@example.com       │
└─────────────────────────────────────┘
```

## Error Categories

The system categorizes errors for appropriate handling:

1. **Network Errors** - Connection issues, timeouts
   - Recoverable: Yes
   - Auto-retry: Yes
   - User action: Wait for retry or check connection

2. **Rate Limit Errors** - Too many requests
   - Recoverable: Yes
   - Auto-retry: No (countdown instead)
   - User action: Wait for countdown

3. **Session Expired** - Session no longer valid
   - Recoverable: Yes
   - Auto-retry: No (creates new session)
   - User action: Start new workflow generation

4. **Validation Errors** - Invalid input
   - Recoverable: Yes
   - Auto-retry: No
   - User action: Fix input and retry

5. **Service Unavailable** - Backend temporarily down
   - Recoverable: Yes
   - Auto-retry: Yes
   - User action: Wait for retry

6. **Server Errors** - Internal server issues
   - Recoverable: Yes
   - Auto-retry: Yes
   - User action: Wait for retry or contact support

7. **Client Errors** - Bad requests
   - Recoverable: Depends on error
   - Auto-retry: No
   - User action: Fix request and retry

8. **Unknown Errors** - Unexpected failures
   - Recoverable: No
   - Auto-retry: No
   - User action: Refresh page or contact support

## Enhanced Error Information

The `getErrorInfo` function provides structured error information:

```typescript
interface ErrorInfo {
  message: string;           // User-friendly message
  category: ErrorCategory;   // Error category
  recoverable: boolean;      // Can user recover?
  retryAfter?: number;       // Seconds to wait
  suggestions: string[];     // Actionable suggestions
  details?: string;          // Technical details
}
```

## API Integration

All API calls in the following functions now use automatic retry:

1. `handleGenerate` - Workflow generation from description
2. `handleUpload` - PDF document upload
3. `handleSendMessage` - Chat message sending

Each wraps the API call with `retryWithBackoff` for automatic recovery from transient failures.

## Testing

Comprehensive test suite in `aiWorkflowErrors.test.ts`:

- ✅ Error categorization (6 tests)
- ✅ User-friendly messages (2 tests)
- ✅ Recoverability detection (3 tests)
- ✅ Critical error detection (3 tests)
- ✅ Retry-after extraction (3 tests)
- ✅ Suggestion extraction (2 tests)
- ✅ Automatic retry with backoff (4 tests)
- ✅ Auto-retry decision (4 tests)

**Total: 27 tests, all passing**

## User Benefits

1. **Seamless Recovery** - Most errors are handled automatically without user intervention
2. **Clear Communication** - Users always know what's happening and what to do
3. **No Data Loss** - Session state and workflow JSON are preserved during recovery
4. **Reduced Frustration** - Automatic retries eliminate the need for manual retry clicks
5. **Actionable Guidance** - Suggestions help users resolve issues quickly
6. **Graceful Degradation** - Even critical errors provide a path forward

## Requirements Coverage

- ✅ **6.1** - Display API errors as system messages in chat
- ✅ **6.2** - Show validation errors with suggestions
- ✅ **6.3** - Handle rate limit errors with retry countdown
- ✅ **6.4** - Detect and handle session expiration
- ✅ **6.5** - Add retry button for network errors
- ✅ **7.5** - Handle session expiration gracefully

## Future Enhancements

1. **Offline Mode** - Queue actions when offline, execute when online
2. **Error Analytics** - Track error patterns for proactive improvements
3. **Smart Retry** - Adjust retry strategy based on error patterns
4. **User Preferences** - Allow users to configure retry behavior
5. **Error History** - Show recent errors for debugging

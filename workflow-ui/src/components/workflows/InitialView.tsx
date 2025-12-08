import { useState, useCallback, useMemo, useEffect } from 'react';
import { Sparkles, FileText, Upload, Loader2, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Props for the InitialView component
 */
export interface InitialViewProps {
  /** Callback when user generates workflow from description */
  onGenerate: (description: string) => Promise<void>;
  /** Callback when user uploads a PDF file */
  onUpload: (file: File) => Promise<void>;
  /** Whether a generation/upload is in progress */
  isLoading: boolean;
  /** Error message to display */
  error: string | null;
  /** Whether to show progress message for long operations */
  showProgressMessage: boolean;
  /** Callback to retry the last failed action */
  onRetry?: () => Promise<void>;
  /** Countdown in seconds before retry is allowed (for rate limiting) */
  retryCountdown: number | null;
}

/**
 * Validation constants
 */
const MIN_CHARACTERS = 10;
const MAX_CHARACTERS = 10000;
const MIN_WORDS = 3;

/**
 * Example workflow descriptions for placeholder
 */
const EXAMPLE_DESCRIPTIONS = [
  'Process customer orders by validating payment, checking inventory, and sending confirmation emails',
  'Validate data quality, transform records, and store results in the database',
  'Extract text from documents, analyze sentiment, and generate summary reports',
];

/**
 * InitialView Component
 * 
 * Displays the initial workflow generation interface with:
 * - Welcome message and instructions
 * - Text input field with character count
 * - Input validation (minimum 3 words, 10-10,000 characters)
 * - PDF upload button
 * - Generate button
 * - Loading states and progress messages
 * - Error handling with retry button
 * 
 * Requirements: 2.1, 2.2, 5.1, 5.5, 6.1, 6.2, 6.3, 6.5, 12.1, 12.3, 12.5
 */
export default function InitialView({
  onGenerate,
  onUpload,
  isLoading,
  error,
  showProgressMessage,
  onRetry,
  retryCountdown,
}: InitialViewProps) {
  const [description, setDescription] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [uploadingFile, setUploadingFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [showUploadTooltip, setShowUploadTooltip] = useState(false);
  
  // Task 26: Debounced character count for performance
  const [debouncedDescription, setDebouncedDescription] = useState(description);

  /**
   * Debounce description updates for character count
   * Task 26: Add debouncing for character count updates (300ms)
   */
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedDescription(description);
    }, 300);

    return () => clearTimeout(timer);
  }, [description]);

  /**
   * Count words in description
   * Task 26: Use debounced value for word count calculation
   */
  const wordCount = useMemo(() => {
    const trimmed = debouncedDescription.trim();
    if (!trimmed) return 0;
    return trimmed.split(/\s+/).length;
  }, [debouncedDescription]);

  /**
   * Validate description input
   */
  const validateDescription = useCallback((text: string): string | null => {
    const trimmed = text.trim();
    const charCount = trimmed.length;
    const words = trimmed ? trimmed.split(/\s+/).length : 0;

    if (charCount === 0) {
      return 'Please enter a workflow description';
    }

    if (charCount < MIN_CHARACTERS) {
      return `Description must be at least ${MIN_CHARACTERS} characters`;
    }

    if (charCount > MAX_CHARACTERS) {
      return `Description must not exceed ${MAX_CHARACTERS} characters`;
    }

    if (words < MIN_WORDS) {
      return `Description must contain at least ${MIN_WORDS} words`;
    }

    return null;
  }, []);

  /**
   * Handle description input change
   */
  const handleDescriptionChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newValue = e.target.value;
      setDescription(newValue);
      
      // Clear validation error when user starts typing
      if (validationError) {
        setValidationError(null);
      }
    },
    [validationError]
  );

  /**
   * Check if generate button should be enabled
   * Task 26: Memoize button state calculation
   */
  const isGenerateEnabled = useMemo(() => {
    if (isLoading) return false;
    const trimmed = description.trim();
    return (
      trimmed.length >= MIN_CHARACTERS &&
      trimmed.length <= MAX_CHARACTERS &&
      wordCount >= MIN_WORDS
    );
  }, [description, wordCount, isLoading]);

  /**
   * Handle generate button click
   */
  const handleGenerate = useCallback(async () => {
    const error = validateDescription(description);
    
    if (error) {
      setValidationError(error);
      return;
    }

    setValidationError(null);
    await onGenerate(description.trim());
  }, [description, validateDescription, onGenerate]);

  /**
   * Handle keyboard shortcuts in textarea
   * Requirement 1.3 - Keyboard navigation (Enter to submit)
   */
  const handleTextareaKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      // Ctrl/Cmd + Enter to submit
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (isGenerateEnabled) {
          handleGenerate();
        }
      }
    },
    [isGenerateEnabled, handleGenerate]
  );

  /**
   * Handle PDF file upload
   */
  const handleFileUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      // Validate file type
      if (file.type !== 'application/pdf') {
        setValidationError('Please upload a PDF file');
        return;
      }

      // Validate file size (10MB max)
      const maxSize = 10 * 1024 * 1024; // 10MB in bytes
      if (file.size > maxSize) {
        setValidationError('File size must not exceed 10MB');
        return;
      }

      setValidationError(null);
      setUploadingFile(file);
      setUploadProgress(0);

      let progressInterval: NodeJS.Timeout | null = null;
      let resetTimeout: NodeJS.Timeout | null = null;

      try {
        // Simulate upload progress (since we don't have real progress from the API)
        progressInterval = setInterval(() => {
          setUploadProgress((prev) => {
            if (prev >= 90) {
              if (progressInterval) clearInterval(progressInterval);
              return 90; // Stop at 90% until upload completes
            }
            return prev + 10;
          });
        }, 200);

        await onUpload(file);
        
        // Complete the progress
        if (progressInterval) clearInterval(progressInterval);
        setUploadProgress(100);
        
        // Reset after a short delay
        resetTimeout = setTimeout(() => {
          setUploadingFile(null);
          setUploadProgress(0);
        }, 500);
      } catch {
        // Clean up intervals and timeouts
        if (progressInterval) clearInterval(progressInterval);
        if (resetTimeout) clearTimeout(resetTimeout);
        
        // Reset upload state on error
        setUploadingFile(null);
        setUploadProgress(0);
      }
      
      // Reset file input
      e.target.value = '';
    },
    [onUpload]
  );

  /**
   * Get random example description for placeholder
   */
  const placeholderExample = useMemo(() => {
    const randomIndex = Math.floor(Math.random() * EXAMPLE_DESCRIPTIONS.length);
    return EXAMPLE_DESCRIPTIONS[randomIndex];
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Welcome Section (Requirements 12.1, 12.2) */}
      <div className="p-6 border-b border-gray-200 bg-gradient-to-br from-blue-50/50 to-indigo-50/50">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-md">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">
            Generate Workflows with AI
          </h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Describe your workflow in plain English or upload a PDF document. The AI will
          generate a complete workflow definition that you can refine through chat.
        </p>
        
        {/* Feature Explanation */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100/50 border border-blue-200 rounded-xl p-4 mb-4 shadow-sm">
          <p className="text-xs font-semibold text-blue-900 mb-2">How it works:</p>
          <ol className="space-y-2 text-xs text-blue-800">
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-[10px] font-bold">1</span>
              <span>Describe your workflow or upload a PDF with requirements</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-[10px] font-bold">2</span>
              <span>AI generates a complete workflow with steps and agents</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-[10px] font-bold">3</span>
              <span>Refine the workflow through interactive chat</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-[10px] font-bold">4</span>
              <span>Save and execute your workflow</span>
            </li>
          </ol>
        </div>
        
        {/* Examples (Requirement 12.2) */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-semibold text-gray-700 mb-3">Example descriptions:</p>
          <ul className="space-y-2">
            {EXAMPLE_DESCRIPTIONS.map((example, index) => (
              <li key={index} className="text-xs text-gray-600 flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 transition-colors duration-150">
                <span className="text-blue-500 mt-0.5 font-bold">•</span>
                <span>{example}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Input Section */}
      <div className="flex-1 p-6 overflow-y-auto">
        {/* Text Input */}
        <div className="mb-6">
          <label
            htmlFor="workflow-description"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Workflow Description
          </label>
          <textarea
            id="workflow-description"
            value={description}
            onChange={handleDescriptionChange}
            onKeyDown={handleTextareaKeyDown}
            placeholder={`Example: ${placeholderExample}`}
            disabled={isLoading}
            className={cn(
              'w-full h-40 px-4 py-3 text-sm border rounded-xl resize-none',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
              'transition-all duration-200',
              'shadow-sm hover:shadow-md',
              validationError || error
                ? 'border-red-300 focus:ring-red-500'
                : 'border-gray-300 hover:border-gray-400'
            )}
            aria-describedby="char-count validation-error helper-text"
            aria-invalid={validationError || error ? 'true' : 'false'}
            aria-label="Workflow description"
          />
          <p id="helper-text" className="sr-only">
            Press Ctrl+Enter or Cmd+Enter to generate workflow
          </p>
          
          {/* Character Count and Validation Feedback (Requirement 12.5) */}
          <div className="flex items-center justify-between mt-2">
            <p
              id="char-count"
              className={cn(
                'text-xs',
                description.length > MAX_CHARACTERS
                  ? 'text-red-600 font-medium'
                  : description.length >= MIN_CHARACTERS && wordCount >= MIN_WORDS
                  ? 'text-green-600 font-medium'
                  : 'text-gray-500'
              )}
            >
              {description.length} / {MAX_CHARACTERS} characters
              {wordCount > 0 && ` • ${wordCount} word${wordCount !== 1 ? 's' : ''}`}
              {description.length >= MIN_CHARACTERS && wordCount >= MIN_WORDS && (
                <span className="ml-1">✓</span>
              )}
            </p>
            {description.length > 0 && description.length < MIN_CHARACTERS && (
              <p className="text-xs text-amber-600">
                {MIN_CHARACTERS - description.length} more character{MIN_CHARACTERS - description.length !== 1 ? 's' : ''} needed
              </p>
            )}
            {description.length >= MIN_CHARACTERS && wordCount < MIN_WORDS && (
              <p className="text-xs text-amber-600">
                Need {MIN_WORDS - wordCount} more word{MIN_WORDS - wordCount !== 1 ? 's' : ''}
              </p>
            )}
          </div>

          {/* Validation Error */}
          {validationError && (
            <p
              id="validation-error"
              className="mt-2 text-sm text-red-600"
              role="alert"
            >
              {validationError}
            </p>
          )}

          {/* API Error with Retry Button (Requirements 6.1, 6.3, 6.5) */}
          {error && (
            <div
              className="mt-3 p-4 bg-gradient-to-br from-red-50 to-red-100/50 border border-red-200 rounded-xl shadow-sm"
              role="alert"
            >
              <p className="text-sm text-red-800 whitespace-pre-wrap">{error}</p>
              
              {/* Rate Limit Countdown (Requirement 6.3) */}
              {retryCountdown !== null && retryCountdown > 0 && (
                <div className="mt-3 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 text-red-600 animate-spin" />
                  <p className="text-xs text-red-700">
                    Retrying in {retryCountdown} second{retryCountdown !== 1 ? 's' : ''}...
                  </p>
                </div>
              )}
              
              {/* Retry Button for Network Errors (Requirement 6.5) */}
              {onRetry && retryCountdown === null && (
                <button
                  onClick={onRetry}
                  disabled={isLoading}
                  className={cn(
                    'mt-3 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200',
                    'focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2',
                    isLoading
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-red-600 text-white hover:bg-red-700 hover:shadow-md transform hover:scale-105'
                  )}
                  aria-label="Retry failed action"
                >
                  {isLoading ? 'Retrying...' : 'Retry'}
                </button>
              )}
            </div>
          )}

          {/* Progress Message for Long Operations (Requirement 5.5) */}
          {isLoading && showProgressMessage && (
            <div
              className="mt-3 p-4 bg-gradient-to-br from-blue-50 to-blue-100/50 border border-blue-200 rounded-xl shadow-sm"
              role="status"
              aria-live="polite"
            >
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
                <p className="text-sm text-blue-800">
                  The AI is working on your request. This may take a moment...
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200" />
          </div>
          <div className="relative flex justify-center">
            <span className="px-3 bg-white text-xs text-gray-500 uppercase tracking-wider">
              Or
            </span>
          </div>
        </div>

        {/* PDF Upload */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label
              htmlFor="pdf-upload"
              className="block text-sm font-medium text-gray-700"
            >
              Upload PDF Document
            </label>
            
            {/* Tooltip for PDF Upload (Requirement 12.4) */}
            <div className="relative">
              <button
                type="button"
                onMouseEnter={() => setShowUploadTooltip(true)}
                onMouseLeave={() => setShowUploadTooltip(false)}
                onFocus={() => setShowUploadTooltip(true)}
                onBlur={() => setShowUploadTooltip(false)}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors rounded-full hover:bg-gray-100"
                aria-label="PDF upload information"
              >
                <Info className="w-4 h-4" />
              </button>
              
              {/* Tooltip Content */}
              {showUploadTooltip && (
                <div
                  className="absolute right-0 top-full mt-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg z-10"
                  role="tooltip"
                >
                  <div className="space-y-2">
                    <p className="font-medium">Supported Format:</p>
                    <p className="text-gray-300">• PDF documents only</p>
                    <p className="font-medium mt-2">Size Limit:</p>
                    <p className="text-gray-300">• Maximum 10MB per file</p>
                    <p className="font-medium mt-2">What happens:</p>
                    <p className="text-gray-300">
                      The AI will extract text from your PDF and generate a workflow based on the content.
                    </p>
                  </div>
                  {/* Tooltip Arrow */}
                  <div className="absolute -top-1 right-3 w-2 h-2 bg-gray-900 transform rotate-45" />
                </div>
              )}
            </div>
          </div>
          
          {/* Upload Button or Progress Indicator */}
          {uploadingFile ? (
            <div className="w-full px-4 py-3 border-2 border-blue-300 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <FileText className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <span className="text-sm text-gray-700 truncate">
                    {uploadingFile.name}
                  </span>
                </div>
                <Loader2 className="w-4 h-4 text-blue-600 animate-spin flex-shrink-0 ml-2" />
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-blue-200 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-blue-600 h-full transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                  role="progressbar"
                  aria-valuenow={uploadProgress}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label="Upload progress"
                />
              </div>
              
              <p className="mt-2 text-xs text-blue-700">
                Uploading... {uploadProgress}%
              </p>
            </div>
          ) : (
            <label
              htmlFor="pdf-upload"
              className={cn(
                'flex items-center justify-center gap-2 w-full px-4 py-4',
                'border-2 border-dashed rounded-xl cursor-pointer transition-all duration-200',
                'hover:border-blue-400 hover:bg-blue-50 hover:shadow-md',
                isLoading
                  ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
                  : 'border-gray-300 bg-white'
              )}
            >
              <Upload className={cn(
                "w-5 h-5 transition-colors duration-200",
                isLoading ? "text-gray-400" : "text-gray-500 group-hover:text-blue-600"
              )} />
              <span className={cn(
                "text-sm font-medium transition-colors duration-200",
                isLoading ? "text-gray-500" : "text-gray-600 group-hover:text-blue-700"
              )}>
                {isLoading ? 'Processing...' : 'Choose PDF file'}
              </span>
              <input
                id="pdf-upload"
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileUpload}
                disabled={isLoading || uploadingFile !== null}
                className="sr-only"
                aria-label="Upload PDF document (maximum 10MB)"
                aria-describedby="pdf-upload-info"
              />
              <span id="pdf-upload-info" className="sr-only">
                Upload a PDF file to generate a workflow. Maximum file size is 10MB.
              </span>
            </label>
          )}
          
          <p className="mt-2 text-xs text-gray-500">
            Maximum file size: 10MB • PDF format only
          </p>
        </div>
      </div>

      {/* Action Section */}
      <div className="p-6 border-t border-gray-200">
        <button
          onClick={handleGenerate}
          disabled={!isGenerateEnabled}
          className={cn(
            'w-full px-4 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-offset-2',
            'shadow-md',
            isGenerateEnabled
              ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg transform hover:scale-[1.02] focus:ring-blue-500'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed shadow-none'
          )}
          aria-label={isLoading ? 'Generating workflow, please wait' : 'Generate workflow from description (Enter)'}
          aria-disabled={!isGenerateEnabled}
          aria-live="polite"
          aria-busy={isLoading}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
              <span>Generating...</span>
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <Sparkles className="w-4 h-4" aria-hidden="true" />
              <span>Generate Workflow</span>
            </span>
          )}
        </button>
      </div>
    </div>
  );
}

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import InitialView from '../InitialView';

describe('InitialView', () => {
  const defaultProps = {
    onGenerate: vi.fn(),
    onUpload: vi.fn(),
    isLoading: false,
    error: null,
    showProgressMessage: false,
    retryCountdown: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render welcome message and instructions', () => {
      render(<InitialView {...defaultProps} />);
      
      expect(screen.getByText('Generate Workflows with AI')).toBeInTheDocument();
      expect(screen.getByText(/Describe your workflow in plain English/i)).toBeInTheDocument();
    });

    it('should render example descriptions', () => {
      render(<InitialView {...defaultProps} />);
      
      expect(screen.getByText('Example descriptions:')).toBeInTheDocument();
      expect(screen.getByText(/Process customer orders/i)).toBeInTheDocument();
    });

    it('should render text input field', () => {
      render(<InitialView {...defaultProps} />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveAttribute('placeholder');
    });

    it('should render PDF upload button', () => {
      render(<InitialView {...defaultProps} />);
      
      expect(screen.getByText('Choose PDF file')).toBeInTheDocument();
      expect(screen.getByText(/Maximum file size: 10MB/i)).toBeInTheDocument();
    });

    it('should render generate button', () => {
      render(<InitialView {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /Generate workflow/i });
      expect(button).toBeInTheDocument();
    });
  });

  describe('Character Count', () => {
    it('should display character count as user types', async () => {
      const user = userEvent.setup();
      render(<InitialView {...defaultProps} />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      await user.type(textarea, 'Test description');
      
      expect(screen.getByText(/16 \/ 10000 characters/i)).toBeInTheDocument();
    });

    it('should display word count', async () => {
      const user = userEvent.setup();
      render(<InitialView {...defaultProps} />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      await user.type(textarea, 'Test description here');
      
      expect(screen.getByText(/3 words/i)).toBeInTheDocument();
    });

    it('should show warning when character limit is exceeded', async () => {
      const user = userEvent.setup();
      render(<InitialView {...defaultProps} />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      const longText = 'a'.repeat(10001);
      
      // Use paste instead of type for large text to avoid timeout
      await user.click(textarea);
      await user.paste(longText);
      
      await waitFor(() => {
        const charCount = screen.getByText(/10001 \/ 10000 characters/i);
        expect(charCount).toHaveClass('text-red-600');
      });
    });

    it('should show word count warning when below minimum', async () => {
      const user = userEvent.setup();
      render(<InitialView {...defaultProps} />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      await user.type(textarea, 'Short text');
      
      expect(screen.getByText(/Need 1 more word/i)).toBeInTheDocument();
    });
  });

  describe('Input Validation', () => {
    it('should disable generate button when description is empty', () => {
      render(<InitialView {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /Generate workflow/i });
      expect(button).toBeDisabled();
    });

    it('should disable generate button when description is too short', async () => {
      const user = userEvent.setup();
      render(<InitialView {...defaultProps} />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      await user.type(textarea, 'Short');
      
      const button = screen.getByRole('button', { name: /Generate workflow/i });
      expect(button).toBeDisabled();
    });

    it('should disable generate button when word count is below minimum', async () => {
      const user = userEvent.setup();
      render(<InitialView {...defaultProps} />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      await user.type(textarea, 'Two words');
      
      const button = screen.getByRole('button', { name: /Generate workflow/i });
      expect(button).toBeDisabled();
    });

    it('should enable generate button when description is valid', async () => {
      const user = userEvent.setup();
      render(<InitialView {...defaultProps} />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      await user.type(textarea, 'This is a valid workflow description');
      
      const button = screen.getByRole('button', { name: /Generate workflow/i });
      expect(button).toBeEnabled();
    });
  });

  describe('Generate Workflow', () => {
    it('should call onGenerate with trimmed description', async () => {
      const user = userEvent.setup();
      const onGenerate = vi.fn().mockResolvedValue(undefined);
      render(<InitialView {...defaultProps} onGenerate={onGenerate} />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      await user.type(textarea, '  Valid workflow description  ');
      
      const button = screen.getByRole('button', { name: /Generate workflow/i });
      await user.click(button);
      
      expect(onGenerate).toHaveBeenCalledWith('Valid workflow description');
    });

    it('should show loading state during generation', () => {
      render(<InitialView {...defaultProps} isLoading={true} />);
      
      expect(screen.getByText('Generating...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Generate workflow/i })).toBeDisabled();
    });

    it('should disable textarea during loading', () => {
      render(<InitialView {...defaultProps} isLoading={true} />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      expect(textarea).toBeDisabled();
    });
  });

  describe('PDF Upload', () => {
    it('should accept PDF files', async () => {
      const user = userEvent.setup();
      const onUpload = vi.fn().mockResolvedValue(undefined);
      render(<InitialView {...defaultProps} onUpload={onUpload} />);
      
      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const input = screen.getByLabelText('Upload PDF document');
      
      await user.upload(input, file);
      
      expect(onUpload).toHaveBeenCalledWith(file);
    });

    it('should show processing state during upload', () => {
      render(<InitialView {...defaultProps} isLoading={true} />);
      
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should display upload progress indicator during file upload', async () => {
      const user = userEvent.setup();
      const onUpload = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));
      render(<InitialView {...defaultProps} onUpload={onUpload} />);
      
      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const input = screen.getByLabelText('Upload PDF document');
      
      await user.upload(input, file);
      
      // Check that progress indicator appears
      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
        expect(screen.getByText(/Uploading\.\.\./i)).toBeInTheDocument();
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
      });
    });

    it('should show file name during upload', async () => {
      const user = userEvent.setup();
      const onUpload = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));
      render(<InitialView {...defaultProps} onUpload={onUpload} />);
      
      const file = new File(['dummy content'], 'my-workflow.pdf', { type: 'application/pdf' });
      const input = screen.getByLabelText('Upload PDF document');
      
      await user.upload(input, file);
      
      await waitFor(() => {
        expect(screen.getByText('my-workflow.pdf')).toBeInTheDocument();
      });
    });

    it('should validate file size and reject files larger than 10MB', async () => {
      const user = userEvent.setup();
      const onUpload = vi.fn();
      render(<InitialView {...defaultProps} onUpload={onUpload} />);
      
      // Create a file larger than 10MB
      const largeContent = new Array(11 * 1024 * 1024).fill('a').join('');
      const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });
      const input = screen.getByLabelText('Upload PDF document');
      
      await user.upload(input, file);
      
      await waitFor(() => {
        expect(onUpload).not.toHaveBeenCalled();
        expect(screen.getByText('File size must not exceed 10MB')).toBeInTheDocument();
      });
    });
  });

  describe('Error Display', () => {
    it('should display API error message', () => {
      render(<InitialView {...defaultProps} error="API connection failed" />);
      
      expect(screen.getByText('API connection failed')).toBeInTheDocument();
    });

    it('should style error message appropriately', () => {
      render(<InitialView {...defaultProps} error="Test error" />);
      
      const errorElement = screen.getByText('Test error');
      expect(errorElement).toHaveClass('text-red-800');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<InitialView {...defaultProps} />);
      
      expect(screen.getByLabelText('Workflow Description')).toBeInTheDocument();
      expect(screen.getByLabelText('Upload PDF document')).toBeInTheDocument();
      expect(screen.getByLabelText('Generate workflow from description')).toBeInTheDocument();
    });

    it('should mark textarea as invalid when there is a validation error', () => {
      render(<InitialView {...defaultProps} error="Test error" />);
      
      const textarea = screen.getByLabelText('Workflow Description');
      expect(textarea).toHaveAttribute('aria-invalid', 'true');
    });

    it('should have role="alert" for API error messages', () => {
      render(<InitialView {...defaultProps} error="API connection failed" />);
      
      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveTextContent('API connection failed');
    });
  });
});

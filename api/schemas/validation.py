"""Validation utilities and configuration for AI workflow generator."""

from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class ValidationConfig(BaseModel):
    """Configuration for validation limits and rules."""
    
    # Text length limits
    min_description_length: int = Field(default=10, description="Minimum description length")
    max_description_length: int = Field(default=10000, description="Maximum description length")
    min_description_words: int = Field(default=3, description="Minimum words in description")
    
    max_message_length: int = Field(default=5000, description="Maximum chat message length")
    max_workflow_name_length: int = Field(default=255, description="Maximum workflow name length")
    max_workflow_description_length: int = Field(default=1000, description="Maximum workflow description length")
    
    # File upload limits
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    supported_file_types: List[str] = Field(
        default=['pdf', 'docx', 'txt', 'md', 'doc'],
        description="Supported document file types"
    )
    
    # Session limits
    max_session_messages: int = Field(default=100, description="Maximum messages per session")
    session_timeout_minutes: int = Field(default=30, description="Session timeout in minutes")


class ValidationResult(BaseModel):
    """Result of a validation operation."""
    
    valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    
    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.valid = False
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)
    
    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion."""
        self.suggestions.append(suggestion)
    
    @classmethod
    def success(cls, suggestions: Optional[List[str]] = None) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(
            valid=True,
            errors=[],
            warnings=[],
            suggestions=suggestions or []
        )
    
    @classmethod
    def failure(cls, errors: List[str], suggestions: Optional[List[str]] = None) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(
            valid=False,
            errors=errors,
            warnings=[],
            suggestions=suggestions or []
        )


class RequestValidator:
    """Utility class for validating API requests."""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize the request validator.
        
        Args:
            config: Optional validation configuration
        """
        self.config = config or ValidationConfig()
    
    def validate_description(self, description: str) -> ValidationResult:
        """
        Validate a workflow description.
        
        Args:
            description: Description to validate
            
        Returns:
            ValidationResult with any errors or suggestions
        """
        result = ValidationResult(valid=True)
        
        # Check if empty or whitespace
        if not description or not description.strip():
            result.add_error("Description cannot be empty or only whitespace")
            result.add_suggestion("Provide a clear description of what you want the workflow to do")
            return result
        
        description = description.strip()
        
        # Check length
        if len(description) < self.config.min_description_length:
            result.add_error(
                f"Description must be at least {self.config.min_description_length} characters"
            )
            result.add_suggestion("Add more details about the workflow steps and requirements")
        
        if len(description) > self.config.max_description_length:
            result.add_error(
                f"Description exceeds maximum length of {self.config.max_description_length} characters"
            )
            result.add_suggestion("Break down your workflow into smaller, more focused descriptions")
        
        # Check word count
        words = description.split()
        if len(words) < self.config.min_description_words:
            result.add_error(
                f"Description must contain at least {self.config.min_description_words} words"
            )
            result.add_suggestion("Provide more context about what the workflow should accomplish")
        
        # Check for common issues
        if description.lower() == description or description.upper() == description:
            result.add_warning("Description is all lowercase or uppercase")
            result.add_suggestion("Use proper capitalization for better readability")
        
        return result
    
    def validate_workflow_name(self, name: str) -> ValidationResult:
        """
        Validate a workflow name.
        
        Args:
            name: Workflow name to validate
            
        Returns:
            ValidationResult with any errors or suggestions
        """
        import re
        
        result = ValidationResult(valid=True)
        
        # Check if empty or whitespace
        if not name or not name.strip():
            result.add_error("Workflow name cannot be empty or only whitespace")
            result.add_suggestion("Provide a descriptive name for your workflow")
            return result
        
        name = name.strip()
        
        # Check length
        if len(name) > self.config.max_workflow_name_length:
            result.add_error(
                f"Workflow name exceeds maximum length of {self.config.max_workflow_name_length} characters"
            )
            result.add_suggestion("Use a shorter, more concise name")
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
            result.add_error(
                "Workflow name must contain only alphanumeric characters, hyphens, underscores, and spaces"
            )
            result.add_suggestion("Remove special characters from the workflow name")
        
        # Check that it doesn't start or end with special characters
        if name[0] in '-_ ' or name[-1] in '-_ ':
            result.add_error("Workflow name cannot start or end with hyphens, underscores, or spaces")
            result.add_suggestion("Remove leading/trailing special characters")
        
        return result
    
    def validate_file_upload(self, file_size: int, file_type: str) -> ValidationResult:
        """
        Validate a file upload.
        
        Args:
            file_size: File size in bytes
            file_type: File type/extension
            
        Returns:
            ValidationResult with any errors or suggestions
        """
        result = ValidationResult(valid=True)
        
        # Check file size
        max_size_bytes = self.config.max_file_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            result.add_error(
                f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum of {self.config.max_file_size_mb} MB"
            )
            result.add_suggestion("Try uploading a smaller file or splitting the content")
            return result
        
        # Check file type
        file_type_lower = file_type.lower().strip()
        if file_type_lower not in self.config.supported_file_types:
            result.add_error(
                f"Unsupported file type '{file_type}'. Supported types: {', '.join(self.config.supported_file_types)}"
            )
            result.add_suggestion("Convert your file to one of the supported formats")
            return result
        
        return result
    
    def validate_chat_message(self, message: str) -> ValidationResult:
        """
        Validate a chat message.
        
        Args:
            message: Message to validate
            
        Returns:
            ValidationResult with any errors or suggestions
        """
        result = ValidationResult(valid=True)
        
        # Check if empty or whitespace
        if not message or not message.strip():
            result.add_error("Message cannot be empty or only whitespace")
            result.add_suggestion("Provide a message describing what you want to change or ask")
            return result
        
        message = message.strip()
        
        # Check length
        if len(message) > self.config.max_message_length:
            result.add_error(
                f"Message exceeds maximum length of {self.config.max_message_length} characters"
            )
            result.add_suggestion("Break your request into multiple shorter messages")
        
        return result


# Global validator instance
default_validator = RequestValidator()


def validate_description(description: str) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate a description.
    
    Args:
        description: Description to validate
        
    Returns:
        Tuple of (is_valid, errors, suggestions)
    """
    result = default_validator.validate_description(description)
    return result.valid, result.errors, result.suggestions


def validate_workflow_name(name: str) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate a workflow name.
    
    Args:
        name: Workflow name to validate
        
    Returns:
        Tuple of (is_valid, errors, suggestions)
    """
    result = default_validator.validate_workflow_name(name)
    return result.valid, result.errors, result.suggestions


def validate_file_upload(file_size: int, file_type: str) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate a file upload.
    
    Args:
        file_size: File size in bytes
        file_type: File type/extension
        
    Returns:
        Tuple of (is_valid, errors, suggestions)
    """
    result = default_validator.validate_file_upload(file_size, file_type)
    return result.valid, result.errors, result.suggestions


def validate_chat_message(message: str) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate a chat message.
    
    Args:
        message: Message to validate
        
    Returns:
        Tuple of (is_valid, errors, suggestions)
    """
    result = default_validator.validate_chat_message(message)
    return result.valid, result.errors, result.suggestions

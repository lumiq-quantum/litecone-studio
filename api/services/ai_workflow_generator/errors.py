"""Error handling models and utilities for AI workflow generator."""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categories of errors that can occur in the AI workflow generator."""
    
    USER_INPUT = "user_input"
    LLM_SERVICE = "llm_service"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    RESOURCE = "resource"
    INTERNAL = "internal"


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AIWorkflowError(Exception):
    """Base exception for AI workflow generator errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        recoverable: bool = True,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize AI workflow error.
        
        Args:
            message: Human-readable error message
            category: Error category for classification
            severity: Error severity level
            details: Additional error details
            suggestions: List of suggestions to resolve the error
            recoverable: Whether the error is recoverable
            original_error: Original exception if this wraps another error
        """
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.suggestions = suggestions or []
        self.recoverable = recoverable
        self.original_error = original_error
        self.timestamp = datetime.utcnow()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        result = {
            "error_code": f"{self.category.value}_{self.severity.value}",
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat()
        }
        
        if self.details:
            result["details"] = self.details
        
        if self.suggestions:
            result["suggestions"] = self.suggestions
        
        if self.original_error:
            result["original_error"] = str(self.original_error)
        
        return result
    
    def log(self):
        """Log the error with appropriate severity level."""
        # Create log data without reserved fields like 'message'
        log_data = {
            "error_code": f"{self.category.value}_{self.severity.value}",
            "error_message": self.message,  # Use error_message instead of message
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat()
        }
        
        if self.details:
            log_data["details"] = self.details
        
        if self.suggestions:
            log_data["suggestions"] = self.suggestions
        
        if self.original_error:
            log_data["original_error"] = str(self.original_error)
        
        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {self.message}", extra=log_data)
        elif self.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {self.message}", extra=log_data)
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {self.message}", extra=log_data)
        else:
            logger.info(f"Low severity error: {self.message}", extra=log_data)


class UserInputError(AIWorkflowError):
    """Error related to user input."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.LOW,
            details=details,
            suggestions=suggestions or [
                "Check your input format and try again",
                "Provide more specific details in your description"
            ],
            recoverable=True
        )


class LLMServiceError(AIWorkflowError):
    """Error related to LLM service interaction."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        recoverable: bool = True,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.LLM_SERVICE,
            severity=ErrorSeverity.HIGH if not recoverable else ErrorSeverity.MEDIUM,
            details=details,
            suggestions=suggestions or [
                "The AI service may be temporarily unavailable",
                "Try again in a few moments"
            ],
            recoverable=recoverable,
            original_error=original_error
        )


class ValidationError(AIWorkflowError):
    """Error related to workflow validation."""
    
    def __init__(
        self,
        message: str,
        validation_errors: List[str],
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        details = details or {}
        details["validation_errors"] = validation_errors
        
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            suggestions=suggestions or [
                "Review the validation errors",
                "Modify your workflow description to address the issues"
            ],
            recoverable=True
        )


class IntegrationError(AIWorkflowError):
    """Error related to external service integration."""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        original_error: Optional[Exception] = None
    ):
        details = details or {}
        details["service_name"] = service_name
        
        super().__init__(
            message=message,
            category=ErrorCategory.INTEGRATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            suggestions=suggestions or [
                f"The {service_name} service may be temporarily unavailable",
                "Check service status and try again"
            ],
            recoverable=True,
            original_error=original_error
        )


class ResourceError(AIWorkflowError):
    """Error related to resource constraints."""
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        details = details or {}
        details["resource_type"] = resource_type
        
        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            suggestions=suggestions or [
                "Reduce the size of your input",
                "Try breaking your request into smaller parts"
            ],
            recoverable=True
        )


class InternalError(AIWorkflowError):
    """Internal system error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
            details=details,
            suggestions=[
                "An unexpected error occurred",
                "Please contact support if the issue persists"
            ],
            recoverable=False,
            original_error=original_error
        )


class ErrorResponse:
    """Standardized error response model."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: List[str] = None,
        recoverable: bool = True
    ):
        """
        Initialize error response.
        
        Args:
            error_code: Unique error code
            message: Human-readable error message
            details: Additional error details
            suggestions: List of suggestions to resolve the error
            recoverable: Whether the error is recoverable
        """
        self.error_code = error_code
        self.message = message
        self.details = details
        self.suggestions = suggestions or []
        self.recoverable = recoverable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "error_code": self.error_code,
            "message": self.message,
            "recoverable": self.recoverable
        }
        
        if self.details:
            result["details"] = self.details
        
        if self.suggestions:
            result["suggestions"] = self.suggestions
        
        return result
    
    @classmethod
    def from_exception(cls, error: AIWorkflowError) -> "ErrorResponse":
        """Create error response from AIWorkflowError."""
        error_dict = error.to_dict()
        return cls(
            error_code=error_dict["error_code"],
            message=error_dict["message"],
            details=error_dict.get("details"),
            suggestions=error_dict.get("suggestions", []),
            recoverable=error_dict["recoverable"]
        )


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorResponse:
    """
    Handle an error and convert it to a standardized error response.
    
    Args:
        error: Exception to handle
        context: Additional context about where the error occurred
        
    Returns:
        ErrorResponse with appropriate error details
    """
    # If it's already an AIWorkflowError, use it directly
    if isinstance(error, AIWorkflowError):
        error.log()
        return ErrorResponse.from_exception(error)
    
    # Otherwise, wrap it in an InternalError
    internal_error = InternalError(
        message=f"An unexpected error occurred: {str(error)}",
        details=context,
        original_error=error
    )
    internal_error.log()
    
    return ErrorResponse.from_exception(internal_error)

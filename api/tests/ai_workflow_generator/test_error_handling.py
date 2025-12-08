"""Tests for AI workflow generator error handling."""

import pytest
from datetime import datetime

from api.services.ai_workflow_generator.errors import (
    ErrorCategory,
    ErrorSeverity,
    AIWorkflowError,
    UserInputError,
    LLMServiceError,
    ValidationError,
    IntegrationError,
    ResourceError,
    InternalError,
    ErrorResponse,
    handle_error
)


class TestErrorCategories:
    """Test error category and severity enums."""
    
    def test_error_categories_exist(self):
        """Test that all error categories are defined."""
        assert ErrorCategory.USER_INPUT == "user_input"
        assert ErrorCategory.LLM_SERVICE == "llm_service"
        assert ErrorCategory.VALIDATION == "validation"
        assert ErrorCategory.INTEGRATION == "integration"
        assert ErrorCategory.RESOURCE == "resource"
        assert ErrorCategory.INTERNAL == "internal"
    
    def test_error_severities_exist(self):
        """Test that all error severities are defined."""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"


class TestAIWorkflowError:
    """Test base AIWorkflowError class."""
    
    def test_create_basic_error(self):
        """Test creating a basic error."""
        error = AIWorkflowError(
            message="Test error",
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.LOW
        )
        
        assert error.message == "Test error"
        assert error.category == ErrorCategory.USER_INPUT
        assert error.severity == ErrorSeverity.LOW
        assert error.recoverable is True
        assert isinstance(error.timestamp, datetime)
    
    def test_error_with_details(self):
        """Test error with additional details."""
        error = AIWorkflowError(
            message="Test error",
            category=ErrorCategory.VALIDATION,
            details={"field": "workflow_name", "value": "invalid"},
            suggestions=["Use a valid name", "Check the format"]
        )
        
        assert error.details == {"field": "workflow_name", "value": "invalid"}
        assert len(error.suggestions) == 2
    
    def test_error_to_dict(self):
        """Test converting error to dictionary."""
        error = AIWorkflowError(
            message="Test error",
            category=ErrorCategory.LLM_SERVICE,
            severity=ErrorSeverity.HIGH,
            details={"model": "gemini"},
            suggestions=["Retry"],
            recoverable=True
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_code"] == "llm_service_high"
        assert error_dict["message"] == "Test error"
        assert error_dict["category"] == "llm_service"
        assert error_dict["severity"] == "high"
        assert error_dict["recoverable"] is True
        assert "details" in error_dict
        assert "suggestions" in error_dict
        assert "timestamp" in error_dict
    
    def test_error_with_original_exception(self):
        """Test error wrapping another exception."""
        original = ValueError("Original error")
        error = AIWorkflowError(
            message="Wrapped error",
            category=ErrorCategory.INTERNAL,
            original_error=original
        )
        
        assert error.original_error == original
        error_dict = error.to_dict()
        assert error_dict["original_error"] == "Original error"


class TestSpecificErrors:
    """Test specific error types."""
    
    def test_user_input_error(self):
        """Test UserInputError."""
        error = UserInputError(
            message="Invalid input",
            details={"field": "description"},
            suggestions=["Provide more details"]
        )
        
        assert error.category == ErrorCategory.USER_INPUT
        assert error.severity == ErrorSeverity.LOW
        assert error.recoverable is True
        assert len(error.suggestions) >= 1
    
    def test_llm_service_error(self):
        """Test LLMServiceError."""
        error = LLMServiceError(
            message="LLM call failed",
            details={"model": "gemini"},
            recoverable=True
        )
        
        assert error.category == ErrorCategory.LLM_SERVICE
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.recoverable is True
    
    def test_llm_service_error_non_recoverable(self):
        """Test non-recoverable LLMServiceError."""
        error = LLMServiceError(
            message="LLM authentication failed",
            recoverable=False
        )
        
        assert error.severity == ErrorSeverity.HIGH
        assert error.recoverable is False
    
    def test_validation_error(self):
        """Test ValidationError."""
        validation_errors = ["Missing start_step", "Invalid agent reference"]
        error = ValidationError(
            message="Workflow validation failed",
            validation_errors=validation_errors
        )
        
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details["validation_errors"] == validation_errors
    
    def test_integration_error(self):
        """Test IntegrationError."""
        error = IntegrationError(
            message="Agent registry unavailable",
            service_name="agent_registry"
        )
        
        assert error.category == ErrorCategory.INTEGRATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.details["service_name"] == "agent_registry"
    
    def test_resource_error(self):
        """Test ResourceError."""
        error = ResourceError(
            message="File too large",
            resource_type="file_size",
            details={"max_mb": 10, "actual_mb": 15}
        )
        
        assert error.category == ErrorCategory.RESOURCE
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details["resource_type"] == "file_size"
    
    def test_internal_error(self):
        """Test InternalError."""
        error = InternalError(
            message="Unexpected error",
            details={"component": "workflow_generator"}
        )
        
        assert error.category == ErrorCategory.INTERNAL
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.recoverable is False


class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_create_error_response(self):
        """Test creating an error response."""
        response = ErrorResponse(
            error_code="user_input_low",
            message="Invalid input",
            details={"field": "name"},
            suggestions=["Fix the input"],
            recoverable=True
        )
        
        assert response.error_code == "user_input_low"
        assert response.message == "Invalid input"
        assert response.recoverable is True
    
    def test_error_response_to_dict(self):
        """Test converting error response to dictionary."""
        response = ErrorResponse(
            error_code="validation_medium",
            message="Validation failed",
            suggestions=["Fix errors"]
        )
        
        response_dict = response.to_dict()
        
        assert response_dict["error_code"] == "validation_medium"
        assert response_dict["message"] == "Validation failed"
        assert response_dict["recoverable"] is True
        assert "suggestions" in response_dict
    
    def test_error_response_from_exception(self):
        """Test creating error response from AIWorkflowError."""
        error = UserInputError(
            message="Invalid format",
            suggestions=["Use correct format"]
        )
        
        response = ErrorResponse.from_exception(error)
        
        assert response.error_code == "user_input_low"
        assert response.message == "Invalid format"
        assert len(response.suggestions) >= 1


class TestErrorHandling:
    """Test error handling utilities."""
    
    def test_handle_ai_workflow_error(self):
        """Test handling AIWorkflowError."""
        error = UserInputError(message="Test error")
        response = handle_error(error)
        
        assert isinstance(response, ErrorResponse)
        assert response.error_code == "user_input_low"
        assert response.message == "Test error"
    
    def test_handle_generic_exception(self):
        """Test handling generic exception."""
        error = ValueError("Generic error")
        response = handle_error(error, context={"operation": "test"})
        
        assert isinstance(response, ErrorResponse)
        assert response.error_code == "internal_critical"
        assert "unexpected error" in response.message.lower()
        assert response.recoverable is False
    
    def test_handle_error_with_context(self):
        """Test handling error with context."""
        error = RuntimeError("Test error")
        response = handle_error(error, context={"user_id": "123", "operation": "generate"})
        
        assert isinstance(response, ErrorResponse)
        assert response.details is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

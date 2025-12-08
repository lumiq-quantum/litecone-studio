"""Tests for AI workflow generator request schemas and validation."""

import pytest
from pydantic import ValidationError
from uuid import uuid4
from datetime import datetime

from api.schemas.ai_workflow import (
    WorkflowGenerationRequest,
    DocumentUploadRequest,
    ChatSessionCreateRequest,
    ChatMessageRequest,
    WorkflowSaveRequest,
    ErrorResponse,
)
from api.schemas.validation import (
    RequestValidator,
    ValidationConfig,
    validate_description,
    validate_workflow_name,
    validate_file_upload,
    validate_chat_message,
)


class TestWorkflowGenerationRequest:
    """Tests for WorkflowGenerationRequest schema."""
    
    def test_valid_request(self):
        """Test creating a valid workflow generation request."""
        request = WorkflowGenerationRequest(
            description="Create a workflow that processes documents and validates them",
            user_preferences={"style": "simple"}
        )
        
        assert request.description == "Create a workflow that processes documents and validates them"
        assert request.user_preferences == {"style": "simple"}
    
    def test_description_too_short(self):
        """Test that short descriptions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowGenerationRequest(description="short")
        
        errors = exc_info.value.errors()
        # Check that validation error occurred
        assert len(errors) > 0
        # The error should be about string length (Pydantic's min_length check runs first)
        assert any(error["type"] == "string_too_short" for error in errors)
    
    def test_description_whitespace_only(self):
        """Test that whitespace-only descriptions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowGenerationRequest(description="   ")
        
        errors = exc_info.value.errors()
        # Check that validation error occurred
        assert len(errors) > 0
        # The error should be about string length (Pydantic's min_length check runs first)
        assert any(error["type"] == "string_too_short" for error in errors)
    
    def test_description_strips_whitespace(self):
        """Test that descriptions are stripped of leading/trailing whitespace."""
        request = WorkflowGenerationRequest(
            description="  Create a workflow that processes documents  "
        )
        
        assert request.description == "Create a workflow that processes documents"
    
    def test_description_too_long(self):
        """Test that very long descriptions are rejected."""
        long_description = "word " * 3000  # Over 10000 characters
        
        with pytest.raises(ValidationError) as exc_info:
            WorkflowGenerationRequest(description=long_description)
        
        errors = exc_info.value.errors()
        # Check that validation error occurred for length
        assert len(errors) > 0
        assert any("string_too_long" in str(error["type"]) or "max_length" in str(error["type"]) for error in errors)


class TestDocumentUploadRequest:
    """Tests for DocumentUploadRequest schema."""
    
    def test_valid_request(self):
        """Test creating a valid document upload request."""
        request = DocumentUploadRequest(file_type="pdf")
        
        assert request.file_type == "pdf"
    
    def test_supported_file_types(self):
        """Test that all supported file types are accepted."""
        for file_type in ["pdf", "docx", "txt", "md", "doc"]:
            request = DocumentUploadRequest(file_type=file_type)
            assert request.file_type == file_type.lower()
    
    def test_case_insensitive_file_type(self):
        """Test that file types are case-insensitive."""
        request = DocumentUploadRequest(file_type="PDF")
        assert request.file_type == "pdf"
    
    def test_unsupported_file_type(self):
        """Test that unsupported file types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentUploadRequest(file_type="exe")
        
        errors = exc_info.value.errors()
        assert any("unsupported" in str(error["msg"]).lower() for error in errors)


class TestChatSessionCreateRequest:
    """Tests for ChatSessionCreateRequest schema."""
    
    def test_valid_request_with_description(self):
        """Test creating a valid chat session request with initial description."""
        request = ChatSessionCreateRequest(
            initial_description="Create a document processing workflow",
            user_id="user123"
        )
        
        assert request.initial_description == "Create a document processing workflow"
        assert request.user_id == "user123"
    
    def test_valid_request_without_description(self):
        """Test creating a valid chat session request without initial description."""
        request = ChatSessionCreateRequest()
        
        assert request.initial_description is None
        assert request.user_id is None
    
    def test_initial_description_too_short(self):
        """Test that short initial descriptions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSessionCreateRequest(initial_description="hi")
        
        errors = exc_info.value.errors()
        assert any("at least 3 words" in str(error["msg"]).lower() for error in errors)
    
    def test_initial_description_whitespace_becomes_none(self):
        """Test that whitespace-only initial descriptions become None."""
        request = ChatSessionCreateRequest(initial_description="   ")
        assert request.initial_description is None
    
    def test_user_id_validation(self):
        """Test user ID validation."""
        # Valid user IDs
        for user_id in ["user123", "user-123", "user_123"]:
            request = ChatSessionCreateRequest(user_id=user_id)
            assert request.user_id == user_id
        
        # Invalid user IDs
        with pytest.raises(ValidationError) as exc_info:
            ChatSessionCreateRequest(user_id="user@123")
        
        errors = exc_info.value.errors()
        assert any("alphanumeric" in str(error["msg"]).lower() for error in errors)


class TestChatMessageRequest:
    """Tests for ChatMessageRequest schema."""
    
    def test_valid_request(self):
        """Test creating a valid chat message request."""
        request = ChatMessageRequest(message="Add a validation step")
        
        assert request.message == "Add a validation step"
    
    def test_message_whitespace_only(self):
        """Test that whitespace-only messages are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ChatMessageRequest(message="   ")
        
        errors = exc_info.value.errors()
        assert any("whitespace" in str(error["msg"]).lower() for error in errors)
    
    def test_message_strips_whitespace(self):
        """Test that messages are stripped of leading/trailing whitespace."""
        request = ChatMessageRequest(message="  Add a step  ")
        
        assert request.message == "Add a step"
    
    def test_message_too_long(self):
        """Test that very long messages are rejected."""
        long_message = "word " * 2000  # Over 5000 characters
        
        with pytest.raises(ValidationError) as exc_info:
            ChatMessageRequest(message=long_message)
        
        errors = exc_info.value.errors()
        # Check that validation error occurred for length
        assert len(errors) > 0
        assert any("string_too_long" in str(error["type"]) or "max_length" in str(error["type"]) for error in errors)


class TestWorkflowSaveRequest:
    """Tests for WorkflowSaveRequest schema."""
    
    def test_valid_request(self):
        """Test creating a valid workflow save request."""
        request = WorkflowSaveRequest(
            name="document-processing",
            description="A workflow for processing documents"
        )
        
        assert request.name == "document-processing"
        assert request.description == "A workflow for processing documents"
    
    def test_valid_name_formats(self):
        """Test that various valid name formats are accepted."""
        valid_names = [
            "workflow-name",
            "workflow_name",
            "workflow name",
            "Workflow123",
            "my-workflow_v2"
        ]
        
        for name in valid_names:
            request = WorkflowSaveRequest(name=name)
            assert request.name == name
    
    def test_name_whitespace_only(self):
        """Test that whitespace-only names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowSaveRequest(name="   ")
        
        errors = exc_info.value.errors()
        assert any("whitespace" in str(error["msg"]).lower() for error in errors)
    
    def test_name_invalid_characters(self):
        """Test that names with invalid characters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowSaveRequest(name="workflow@name")
        
        errors = exc_info.value.errors()
        assert any("alphanumeric" in str(error["msg"]).lower() for error in errors)
    
    def test_name_starts_with_special_char(self):
        """Test that names starting with special characters are rejected."""
        for name in ["-workflow", "_workflow", " workflow"]:
            with pytest.raises(ValidationError) as exc_info:
                WorkflowSaveRequest(name=name)
            
            errors = exc_info.value.errors()
            # Check that validation error occurred
            assert len(errors) > 0
            # The error should mention start/end or be a value_error
            error_msg = str(errors[0]["msg"]).lower()
            assert "start" in error_msg or "end" in error_msg
    
    def test_name_ends_with_special_char(self):
        """Test that names ending with special characters are rejected."""
        for name in ["workflow-", "workflow_", "workflow "]:
            with pytest.raises(ValidationError) as exc_info:
                WorkflowSaveRequest(name=name)
            
            errors = exc_info.value.errors()
            # Check that validation error occurred
            assert len(errors) > 0
            # The error should mention start/end or be a value_error
            error_msg = str(errors[0]["msg"]).lower()
            assert "start" in error_msg or "end" in error_msg
    
    def test_description_whitespace_becomes_none(self):
        """Test that whitespace-only descriptions become None."""
        request = WorkflowSaveRequest(name="workflow", description="   ")
        assert request.description is None


class TestErrorResponse:
    """Tests for ErrorResponse schema."""
    
    def test_create_error_response(self):
        """Test creating an error response."""
        error = ErrorResponse.create(
            error_code="VALIDATION_ERROR",
            message="Invalid input",
            details={"field": "description"},
            suggestions=["Provide more details"],
            recoverable=True
        )
        
        assert error.error_code == "VALIDATION_ERROR"
        assert error.message == "Invalid input"
        assert error.details == {"field": "description"}
        assert error.suggestions == ["Provide more details"]
        assert error.recoverable is True
    
    def test_from_validation_error(self):
        """Test creating error response from Pydantic validation error."""
        try:
            WorkflowGenerationRequest(description="short")
        except ValidationError as e:
            error = ErrorResponse.from_validation_error(e)
            
            assert error.error_code == "VALIDATION_ERROR"
            assert error.message == "Request validation failed"
            assert len(error.details["errors"]) > 0
            assert len(error.suggestions) > 0


class TestRequestValidator:
    """Tests for RequestValidator utility."""
    
    def test_validate_description_success(self):
        """Test successful description validation."""
        validator = RequestValidator()
        result = validator.validate_description("Create a workflow that processes documents")
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_description_too_short(self):
        """Test description validation with too short input."""
        validator = RequestValidator()
        result = validator.validate_description("hi")
        
        assert result.valid is False
        assert len(result.errors) > 0
        assert len(result.suggestions) > 0
    
    def test_validate_workflow_name_success(self):
        """Test successful workflow name validation."""
        validator = RequestValidator()
        result = validator.validate_workflow_name("my-workflow")
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_workflow_name_invalid_chars(self):
        """Test workflow name validation with invalid characters."""
        validator = RequestValidator()
        result = validator.validate_workflow_name("workflow@name")
        
        assert result.valid is False
        assert len(result.errors) > 0
        assert len(result.suggestions) > 0
    
    def test_validate_file_upload_success(self):
        """Test successful file upload validation."""
        validator = RequestValidator()
        result = validator.validate_file_upload(1024 * 1024, "pdf")  # 1 MB
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_file_upload_too_large(self):
        """Test file upload validation with file too large."""
        validator = RequestValidator()
        result = validator.validate_file_upload(20 * 1024 * 1024, "pdf")  # 20 MB
        
        assert result.valid is False
        assert len(result.errors) > 0
        assert "exceeds maximum" in result.errors[0].lower()
    
    def test_validate_file_upload_unsupported_type(self):
        """Test file upload validation with unsupported file type."""
        validator = RequestValidator()
        result = validator.validate_file_upload(1024, "exe")
        
        assert result.valid is False
        assert len(result.errors) > 0
        assert "unsupported" in result.errors[0].lower()
    
    def test_validate_chat_message_success(self):
        """Test successful chat message validation."""
        validator = RequestValidator()
        result = validator.validate_chat_message("Add a validation step")
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_chat_message_empty(self):
        """Test chat message validation with empty message."""
        validator = RequestValidator()
        result = validator.validate_chat_message("   ")
        
        assert result.valid is False
        assert len(result.errors) > 0


class TestConvenienceFunctions:
    """Tests for convenience validation functions."""
    
    def test_validate_description_function(self):
        """Test validate_description convenience function."""
        valid, errors, suggestions = validate_description("Create a workflow that processes documents")
        
        assert valid is True
        assert len(errors) == 0
    
    def test_validate_workflow_name_function(self):
        """Test validate_workflow_name convenience function."""
        valid, errors, suggestions = validate_workflow_name("my-workflow")
        
        assert valid is True
        assert len(errors) == 0
    
    def test_validate_file_upload_function(self):
        """Test validate_file_upload convenience function."""
        valid, errors, suggestions = validate_file_upload(1024 * 1024, "pdf")
        
        assert valid is True
        assert len(errors) == 0
    
    def test_validate_chat_message_function(self):
        """Test validate_chat_message convenience function."""
        valid, errors, suggestions = validate_chat_message("Add a step")
        
        assert valid is True
        assert len(errors) == 0

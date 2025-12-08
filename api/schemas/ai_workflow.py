"""Pydantic schemas for AI workflow generator API."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from uuid import UUID
import re


class WorkflowGenerationRequest(BaseModel):
    """Request schema for workflow generation from text."""
    
    description: str = Field(
        ...,
        description="Natural language description of the workflow",
        min_length=10,
        max_length=10000,
        examples=["Create a workflow that processes documents, validates them, and stores the results"]
    )
    user_preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional user preferences for generation"
    )
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate that description is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Description cannot be empty or only whitespace")
        
        # Check for minimum meaningful content
        words = v.strip().split()
        if len(words) < 3:
            raise ValueError("Description must contain at least 3 words to be meaningful")
        
        return v.strip()


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload."""
    
    file_type: str = Field(
        ...,
        description="Document type (pdf, docx, txt, md)",
        examples=["pdf", "docx", "txt", "md"]
    )
    user_preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional user preferences for generation"
    )
    
    @field_validator('file_type')
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        """Validate that file type is supported."""
        supported_types = ['pdf', 'docx', 'txt', 'md', 'doc']
        v_lower = v.lower().strip()
        
        if v_lower not in supported_types:
            raise ValueError(
                f"Unsupported file type '{v}'. Supported types are: {', '.join(supported_types)}"
            )
        
        return v_lower


class WorkflowGenerationResponse(BaseModel):
    """Response schema for workflow generation."""
    
    success: bool = Field(..., description="Whether generation was successful")
    workflow_json: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Generated workflow JSON"
    )
    explanation: str = Field(..., description="Explanation of the generated workflow")
    validation_errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )
    agents_used: List[str] = Field(
        default_factory=list,
        description="List of agents used in the workflow"
    )


class ChatSessionCreateRequest(BaseModel):
    """Request schema for creating a chat session."""
    
    initial_description: Optional[str] = Field(
        default=None,
        description="Optional initial workflow description",
        max_length=10000
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Optional user ID",
        max_length=255
    )
    
    @field_validator('initial_description')
    @classmethod
    def validate_initial_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate initial description if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                # If it's just whitespace, treat as None
                return None
            
            # Check for minimum meaningful content
            words = v.split()
            if len(words) < 3:
                raise ValueError("Initial description must contain at least 3 words to be meaningful")
        
        return v
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate user ID format if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            
            # Basic validation - alphanumeric, hyphens, underscores
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError("User ID must contain only alphanumeric characters, hyphens, and underscores")
        
        return v


class ChatMessageRequest(BaseModel):
    """Request schema for sending a chat message."""
    
    message: str = Field(
        ...,
        description="User message",
        min_length=1,
        max_length=5000,
        examples=["Add a validation step before processing", "Can you explain what this workflow does?"]
    )
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate that message is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or only whitespace")
        
        return v.strip()


class ChatMessageResponse(BaseModel):
    """Response schema for chat messages."""
    
    id: UUID = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional message metadata"
    )


class ChatSessionResponse(BaseModel):
    """Response schema for chat session."""
    
    id: UUID = Field(..., description="Session ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    status: str = Field(..., description="Session status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    messages: List[ChatMessageResponse] = Field(
        default_factory=list,
        description="Chat messages"
    )
    current_workflow: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current workflow JSON"
    )
    workflow_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Workflow evolution history"
    )


class WorkflowSaveRequest(BaseModel):
    """Request schema for saving a workflow."""
    
    name: str = Field(
        ...,
        description="Workflow name",
        min_length=1,
        max_length=255,
        examples=["document-processing-workflow", "customer-onboarding"]
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional workflow description",
        max_length=1000
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate workflow name format."""
        if not v or not v.strip():
            raise ValueError("Workflow name cannot be empty or only whitespace")
        
        # Check that it doesn't start or end with special characters BEFORE stripping
        if v[0] in '-_ ' or v[-1] in '-_ ':
            raise ValueError("Workflow name cannot start or end with hyphens, underscores, or spaces")
        
        v = v.strip()
        
        # Check for valid characters (alphanumeric, hyphens, underscores, spaces)
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', v):
            raise ValueError(
                "Workflow name must contain only alphanumeric characters, hyphens, underscores, and spaces"
            )
        
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        
        return v


class WorkflowSaveResponse(BaseModel):
    """Response schema for workflow save."""
    
    workflow_id: UUID = Field(..., description="Created workflow ID")
    name: str = Field(..., description="Workflow name")
    url: str = Field(..., description="URL to view/execute the workflow")


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""
    
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(default=None, description="Invalid value provided")


class AgentSuggestionRequest(BaseModel):
    """Request schema for agent suggestions."""
    
    capability_description: str = Field(
        ...,
        description="Description of the required capability",
        min_length=3,
        max_length=500,
        examples=["process PDF documents", "send email notifications", "validate user input"]
    )
    
    @field_validator('capability_description')
    @classmethod
    def validate_capability_description(cls, v: str) -> str:
        """Validate that capability description is meaningful."""
        if not v or not v.strip():
            raise ValueError("Capability description cannot be empty or only whitespace")
        
        words = v.strip().split()
        if len(words) < 2:
            raise ValueError("Capability description must contain at least 2 words")
        
        return v.strip()


class AgentSuggestionItem(BaseModel):
    """Individual agent suggestion."""
    
    agent_name: str = Field(..., description="Agent name")
    agent_url: str = Field(..., description="Agent URL")
    agent_description: Optional[str] = Field(default=None, description="Agent description")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    relevance_score: float = Field(..., description="Relevance score (0-100)")
    reason: str = Field(..., description="Reason for suggestion")


class AgentSuggestionResponse(BaseModel):
    """Response schema for agent suggestions."""
    
    suggestions: List[AgentSuggestionItem] = Field(
        default_factory=list,
        description="List of suggested agents"
    )
    is_ambiguous: bool = Field(
        ...,
        description="Whether multiple agents are equally suitable"
    )
    requires_user_choice: bool = Field(
        ...,
        description="Whether user needs to choose between options"
    )
    no_match: bool = Field(
        ...,
        description="Whether no suitable agents were found"
    )
    alternatives: List[str] = Field(
        default_factory=list,
        description="Alternative approaches if no match found"
    )
    explanation: str = Field(
        ...,
        description="Explanation of the suggestion result"
    )


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    error_code: str = Field(
        ...,
        description="Error code",
        examples=["INVALID_INPUT", "VALIDATION_ERROR", "SERVICE_UNAVAILABLE"]
    )
    message: str = Field(
        ...,
        description="Error message",
        examples=["Invalid workflow description provided"]
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for resolving the error",
        examples=[["Try providing a more detailed description", "Check that all required fields are filled"]]
    )
    recoverable: bool = Field(
        ...,
        description="Whether the error is recoverable",
        examples=[True]
    )
    
    @classmethod
    def create(
        cls,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        recoverable: bool = True
    ) -> "ErrorResponse":
        """
        Factory method to create error responses with consistent formatting.
        
        Args:
            error_code: Error code identifier
            message: Human-readable error message
            details: Additional error details
            suggestions: List of suggestions for resolving the error
            recoverable: Whether the error can be recovered from
            
        Returns:
            ErrorResponse instance
        """
        return cls(
            error_code=error_code,
            message=message,
            details=details,
            suggestions=suggestions or [],
            recoverable=recoverable
        )
    
    @classmethod
    def from_validation_error(cls, exc: Exception) -> "ErrorResponse":
        """
        Create error response from Pydantic validation error.
        
        Args:
            exc: Pydantic ValidationError exception
            
        Returns:
            ErrorResponse with formatted validation errors
        """
        from pydantic import ValidationError
        
        if not isinstance(exc, ValidationError):
            return cls.create(
                error_code="VALIDATION_ERROR",
                message=str(exc),
                recoverable=True
            )
        
        errors = exc.errors()
        error_details = []
        suggestions = []
        
        for error in errors:
            field = ".".join(str(loc) for loc in error["loc"])
            error_details.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
            
            # Generate helpful suggestions based on error type
            if error["type"] == "string_too_short":
                suggestions.append(f"Field '{field}' requires more content")
            elif error["type"] == "string_too_long":
                suggestions.append(f"Field '{field}' exceeds maximum length")
            elif error["type"] == "value_error":
                suggestions.append(f"Field '{field}': {error['msg']}")
        
        return cls(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": error_details},
            suggestions=suggestions,
            recoverable=True
        )

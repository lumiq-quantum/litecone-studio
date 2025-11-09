"""
Agent schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, HttpUrl, field_validator, field_serializer
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class RetryConfigSchema(BaseModel):
    """Schema for agent retry configuration."""
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum number of retry attempts")
    initial_delay_ms: int = Field(default=1000, ge=100, description="Initial delay in milliseconds")
    max_delay_ms: int = Field(default=30000, ge=1000, description="Maximum delay in milliseconds")
    backoff_multiplier: float = Field(default=2.0, ge=1.0, description="Backoff multiplier for exponential backoff")

    @field_validator('max_delay_ms')
    @classmethod
    def validate_max_delay(cls, v: int, info) -> int:
        """Ensure max_delay_ms is greater than or equal to initial_delay_ms."""
        if 'initial_delay_ms' in info.data and v < info.data['initial_delay_ms']:
            raise ValueError('max_delay_ms must be greater than or equal to initial_delay_ms')
        return v


class AgentCreate(BaseModel):
    """Schema for creating a new agent."""
    name: str = Field(..., min_length=1, max_length=255, description="Unique agent name")
    url: HttpUrl = Field(..., description="Agent endpoint URL")
    description: Optional[str] = Field(None, description="Agent description")
    auth_type: str = Field(default="none", description="Authentication type")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    timeout_ms: int = Field(default=30000, ge=1000, le=300000, description="Request timeout in milliseconds")
    retry_config: RetryConfigSchema = Field(default_factory=RetryConfigSchema, description="Retry configuration")
    
    @field_serializer('url')
    def serialize_url(self, url: HttpUrl, _info):
        """Serialize HttpUrl to string for database storage."""
        return str(url)

    @field_validator('auth_type')
    @classmethod
    def validate_auth_type(cls, v: str) -> str:
        """Validate auth_type is one of the allowed values."""
        allowed_types = {'none', 'bearer', 'apikey'}
        if v.lower() not in allowed_types:
            raise ValueError(f"auth_type must be one of: {', '.join(allowed_types)}")
        return v.lower()

    @field_validator('auth_config')
    @classmethod
    def validate_auth_config(cls, v: Optional[Dict[str, Any]], info) -> Optional[Dict[str, Any]]:
        """Validate auth_config based on auth_type."""
        if 'auth_type' not in info.data:
            return v
        
        auth_type = info.data['auth_type']
        
        if auth_type == 'none' and v is not None:
            raise ValueError("auth_config must be null when auth_type is 'none'")
        
        if auth_type in {'bearer', 'apikey'} and v is None:
            raise ValueError(f"auth_config is required when auth_type is '{auth_type}'")
        
        if auth_type == 'bearer' and v is not None:
            if 'token' not in v:
                raise ValueError("auth_config must contain 'token' field for bearer authentication")
        
        if auth_type == 'apikey' and v is not None:
            if 'key' not in v or 'header_name' not in v:
                raise ValueError("auth_config must contain 'key' and 'header_name' fields for apikey authentication")
        
        return v


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent."""
    url: Optional[HttpUrl] = Field(None, description="Agent endpoint URL")
    description: Optional[str] = Field(None, description="Agent description")
    auth_type: Optional[str] = Field(None, description="Authentication type")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    timeout_ms: Optional[int] = Field(None, ge=1000, le=300000, description="Request timeout in milliseconds")
    retry_config: Optional[RetryConfigSchema] = Field(None, description="Retry configuration")
    status: Optional[str] = Field(None, description="Agent status")
    
    @field_serializer('url')
    def serialize_url(self, url: Optional[HttpUrl], _info):
        """Serialize HttpUrl to string for database storage."""
        return str(url) if url is not None else None

    @field_validator('auth_type')
    @classmethod
    def validate_auth_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate auth_type is one of the allowed values."""
        if v is None:
            return v
        allowed_types = {'none', 'bearer', 'apikey'}
        if v.lower() not in allowed_types:
            raise ValueError(f"auth_type must be one of: {', '.join(allowed_types)}")
        return v.lower()

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status is one of the allowed values."""
        if v is None:
            return v
        allowed_statuses = {'active', 'inactive'}
        if v.lower() not in allowed_statuses:
            raise ValueError(f"status must be one of: {', '.join(allowed_statuses)}")
        return v.lower()


class AgentResponse(BaseModel):
    """Schema for agent response."""
    id: UUID = Field(..., description="Agent unique identifier")
    name: str = Field(..., description="Agent name")
    url: str = Field(..., description="Agent endpoint URL")
    description: Optional[str] = Field(None, description="Agent description")
    auth_type: str = Field(..., description="Authentication type")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    timeout_ms: int = Field(..., description="Request timeout in milliseconds")
    retry_config: RetryConfigSchema = Field(..., description="Retry configuration")
    status: str = Field(..., description="Agent status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="User who created the agent")
    updated_by: Optional[str] = Field(None, description="User who last updated the agent")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "data-processor",
                "url": "http://data-processor:8080",
                "description": "Processes data transformations",
                "auth_type": "bearer",
                "timeout_ms": 30000,
                "retry_config": {
                    "max_retries": 3,
                    "initial_delay_ms": 1000,
                    "max_delay_ms": 30000,
                    "backoff_multiplier": 2.0
                },
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "admin",
                "updated_by": "admin"
            }
        }
    }

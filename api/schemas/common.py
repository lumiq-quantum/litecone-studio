"""
Common schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Generic, TypeVar, Any, Dict
from datetime import datetime


# Generic type for paginated responses
T = TypeVar('T')


class PaginationParams(BaseModel):
    """Schema for pagination query parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")

    @field_validator('page')
    @classmethod
    def validate_page(cls, v: int) -> int:
        """Ensure page is at least 1."""
        if v < 1:
            raise ValueError("page must be at least 1")
        return v

    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        """Ensure page_size is within acceptable range."""
        if v < 1:
            raise ValueError("page_size must be at least 1")
        if v > 100:
            raise ValueError("page_size cannot exceed 100")
        return v

    def get_offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.page_size

    def get_limit(self) -> int:
        """Get the limit for database queries."""
        return self.page_size

    model_config = {
        "json_schema_extra": {
            "example": {
                "page": 1,
                "page_size": 20
            }
        }
    }


class PaginationMetadata(BaseModel):
    """Schema for pagination metadata in responses."""
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def from_params(cls, total: int, params: PaginationParams) -> 'PaginationMetadata':
        """Create pagination metadata from total count and params."""
        total_pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0
        return cls(
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages
        )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }
    }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic schema for paginated list responses."""
    items: List[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def create(cls, items: List[T], total: int, params: PaginationParams) -> 'PaginatedResponse[T]':
        """Create a paginated response from items, total count, and pagination params."""
        total_pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages
        )

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }
    }


class ErrorDetail(BaseModel):
    """Schema for detailed error information."""
    field: Optional[str] = Field(None, description="Field name that caused the error (for validation errors)")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type or code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "field": "email",
                "message": "Invalid email format",
                "type": "value_error"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Schema for consistent error response formatting."""
    error: str = Field(..., description="Error message or summary")
    detail: Optional[str] = Field(None, description="Detailed error description")
    errors: Optional[List[ErrorDetail]] = Field(None, description="List of detailed errors (for validation errors)")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "Validation Error",
                    "detail": "Request validation failed",
                    "errors": [
                        {
                            "field": "name",
                            "message": "Field required",
                            "type": "missing"
                        },
                        {
                            "field": "url",
                            "message": "Invalid URL format",
                            "type": "value_error"
                        }
                    ],
                    "status_code": 422,
                    "timestamp": "2024-01-01T10:00:00Z",
                    "path": "/api/v1/agents",
                    "request_id": "req-123e4567-e89b-12d3-a456-426614174000"
                },
                {
                    "error": "Not Found",
                    "detail": "Agent with id '123e4567-e89b-12d3-a456-426614174000' not found",
                    "errors": None,
                    "status_code": 404,
                    "timestamp": "2024-01-01T10:00:00Z",
                    "path": "/api/v1/agents/123e4567-e89b-12d3-a456-426614174000",
                    "request_id": "req-123e4567-e89b-12d3-a456-426614174001"
                },
                {
                    "error": "Internal Server Error",
                    "detail": "An unexpected error occurred",
                    "errors": None,
                    "status_code": 500,
                    "timestamp": "2024-01-01T10:00:00Z",
                    "path": "/api/v1/workflows",
                    "request_id": "req-123e4567-e89b-12d3-a456-426614174002"
                }
            ]
        }
    }


class HealthStatus(BaseModel):
    """Schema for individual service health status."""
    status: str = Field(..., description="Service status (healthy, unhealthy, degraded)")
    message: Optional[str] = Field(None, description="Additional status information")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "message": "Connected successfully",
                "response_time_ms": 15.3
            }
        }
    }


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Overall system status (healthy, unhealthy, degraded)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: Optional[str] = Field(None, description="API version")
    uptime_seconds: Optional[float] = Field(None, description="System uptime in seconds")
    services: Optional[Dict[str, HealthStatus]] = Field(None, description="Individual service health statuses")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "version": "1.0.0",
                    "uptime_seconds": 3600.5,
                    "services": None
                },
                {
                    "status": "healthy",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "version": "1.0.0",
                    "uptime_seconds": 3600.5,
                    "services": {
                        "database": {
                            "status": "healthy",
                            "message": "PostgreSQL connection active",
                            "response_time_ms": 12.5
                        },
                        "kafka": {
                            "status": "healthy",
                            "message": "Kafka broker reachable",
                            "response_time_ms": 8.3
                        }
                    }
                },
                {
                    "status": "degraded",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "version": "1.0.0",
                    "uptime_seconds": 3600.5,
                    "services": {
                        "database": {
                            "status": "healthy",
                            "message": "PostgreSQL connection active",
                            "response_time_ms": 12.5
                        },
                        "kafka": {
                            "status": "unhealthy",
                            "message": "Connection timeout",
                            "response_time_ms": None
                        }
                    }
                }
            ]
        }
    }


class ReadinessResponse(BaseModel):
    """Schema for readiness check response."""
    ready: bool = Field(..., description="Whether the service is ready to accept requests")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Readiness check timestamp")
    checks: Dict[str, HealthStatus] = Field(..., description="Individual readiness checks")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ready": True,
                    "timestamp": "2024-01-01T10:00:00Z",
                    "checks": {
                        "database": {
                            "status": "healthy",
                            "message": "Database connection pool ready",
                            "response_time_ms": 10.2
                        },
                        "kafka": {
                            "status": "healthy",
                            "message": "Kafka producer initialized",
                            "response_time_ms": 5.1
                        }
                    }
                },
                {
                    "ready": False,
                    "timestamp": "2024-01-01T10:00:00Z",
                    "checks": {
                        "database": {
                            "status": "unhealthy",
                            "message": "Cannot connect to database",
                            "response_time_ms": None
                        },
                        "kafka": {
                            "status": "healthy",
                            "message": "Kafka producer initialized",
                            "response_time_ms": 5.1
                        }
                    }
                }
            ]
        }
    }


class MessageResponse(BaseModel):
    """Schema for simple message responses."""
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional additional data")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Agent deleted successfully",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "data": None
                },
                {
                    "message": "Workflow execution triggered",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "data": {
                        "run_id": "run-123e4567-e89b-12d3-a456-426614174000"
                    }
                }
            ]
        }
    }

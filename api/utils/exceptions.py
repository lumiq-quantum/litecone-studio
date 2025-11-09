"""
Custom exception classes for the Workflow Management API.
"""
from typing import Optional, Any, Dict


class APIException(Exception):
    """Base exception class for API errors."""
    
    def __init__(
        self,
        status_code: int,
        error: str,
        detail: Optional[str] = None,
        errors: Optional[list] = None
    ):
        """
        Initialize API exception.
        
        Args:
            status_code: HTTP status code
            error: Error message or summary
            detail: Detailed error description
            errors: List of detailed errors (for validation errors)
        """
        self.status_code = status_code
        self.error = error
        self.detail = detail
        self.errors = errors
        super().__init__(self.error)


class NotFoundException(APIException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, detail: str = "Resource not found"):
        """Initialize NotFoundException with 404 status code."""
        super().__init__(
            status_code=404,
            error="Not Found",
            detail=detail
        )


class ValidationException(APIException):
    """Exception raised when request validation fails."""
    
    def __init__(self, detail: str, errors: Optional[list] = None):
        """Initialize ValidationException with 422 status code."""
        super().__init__(
            status_code=422,
            error="Validation Error",
            detail=detail,
            errors=errors
        )


class ConflictException(APIException):
    """Exception raised when a resource conflict occurs."""
    
    def __init__(self, detail: str):
        """Initialize ConflictException with 409 status code."""
        super().__init__(
            status_code=409,
            error="Conflict",
            detail=detail
        )


class UnauthorizedException(APIException):
    """Exception raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication required"):
        """Initialize UnauthorizedException with 401 status code."""
        super().__init__(
            status_code=401,
            error="Unauthorized",
            detail=detail
        )


class ForbiddenException(APIException):
    """Exception raised when authorization fails."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        """Initialize ForbiddenException with 403 status code."""
        super().__init__(
            status_code=403,
            error="Forbidden",
            detail=detail
        )


class BadRequestException(APIException):
    """Exception raised when request is malformed or invalid."""
    
    def __init__(self, detail: str):
        """Initialize BadRequestException with 400 status code."""
        super().__init__(
            status_code=400,
            error="Bad Request",
            detail=detail
        )


class InternalServerException(APIException):
    """Exception raised when an internal server error occurs."""
    
    def __init__(self, detail: str = "An unexpected error occurred"):
        """Initialize InternalServerException with 500 status code."""
        super().__init__(
            status_code=500,
            error="Internal Server Error",
            detail=detail
        )


class ServiceUnavailableException(APIException):
    """Exception raised when a service is unavailable."""
    
    def __init__(self, detail: str = "Service temporarily unavailable"):
        """Initialize ServiceUnavailableException with 503 status code."""
        super().__init__(
            status_code=503,
            error="Service Unavailable",
            detail=detail
        )

"""
Global error handling middleware for the Workflow Management API.

This module provides exception handlers for various error types including:
- Custom APIException and its subclasses
- Pydantic ValidationError
- SQLAlchemy database errors
- Generic Python exceptions

All errors are returned in a consistent format using the ErrorResponse schema.
"""
import logging
import uuid
from datetime import datetime
from typing import Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    DatabaseError,
    DataError
)

from api.utils.exceptions import APIException
from api.schemas.common import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)


def create_error_response(
    request: Request,
    status_code: int,
    error: str,
    detail: Union[str, None] = None,
    errors: Union[list, None] = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        request: FastAPI request object
        status_code: HTTP status code
        error: Error message or summary
        detail: Detailed error description
        errors: List of detailed errors (for validation errors)
    
    Returns:
        JSONResponse with ErrorResponse schema
    """
    # Generate unique request ID for tracing
    request_id = str(uuid.uuid4())
    
    # Create error response
    error_response = ErrorResponse(
        error=error,
        detail=detail,
        errors=errors,
        status_code=status_code,
        timestamp=datetime.utcnow(),
        path=str(request.url.path),
        request_id=request_id
    )
    
    # Log the error
    log_message = f"Error {status_code}: {error}"
    if detail:
        log_message += f" - {detail}"
    log_message += f" [Request ID: {request_id}] [Path: {request.url.path}]"
    
    if status_code >= 500:
        logger.error(log_message)
    elif status_code >= 400:
        logger.warning(log_message)
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(mode='json', exclude_none=True)
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Handle custom APIException and its subclasses.
    
    Args:
        request: FastAPI request object
        exc: APIException instance
    
    Returns:
        JSONResponse with error details
    """
    return create_error_response(
        request=request,
        status_code=exc.status_code,
        error=exc.error,
        detail=exc.detail,
        errors=exc.errors
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Converts Pydantic validation errors into a consistent error response format
    with field-level error details.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError or ValidationError instance
    
    Returns:
        JSONResponse with validation error details
    """
    # Extract validation errors
    error_details = []
    for error in exc.errors():
        # Get field path
        field_path = ".".join(str(loc) for loc in error.get("loc", []))
        
        # Create error detail
        error_detail = ErrorDetail(
            field=field_path if field_path else None,
            message=error.get("msg", "Validation error"),
            type=error.get("type", "value_error")
        )
        error_details.append(error_detail.model_dump(exclude_none=True))
    
    return create_error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error="Validation Error",
        detail="Request validation failed",
        errors=error_details
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.
    
    Converts various SQLAlchemy exceptions into appropriate HTTP responses:
    - IntegrityError (unique constraint, foreign key) -> 409 Conflict
    - OperationalError (connection issues) -> 503 Service Unavailable
    - DataError (invalid data) -> 400 Bad Request
    - Other database errors -> 500 Internal Server Error
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemyError instance
    
    Returns:
        JSONResponse with error details
    """
    # Log the full exception for debugging
    logger.error(f"Database error: {str(exc)}", exc_info=True)
    
    # Handle specific SQLAlchemy error types
    if isinstance(exc, IntegrityError):
        # Unique constraint or foreign key violation
        error_msg = "Database integrity constraint violated"
        detail = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        
        # Try to extract more specific information
        if "unique constraint" in detail.lower():
            error_msg = "Resource already exists"
        elif "foreign key" in detail.lower():
            error_msg = "Referenced resource does not exist"
        
        return create_error_response(
            request=request,
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            detail=error_msg
        )
    
    elif isinstance(exc, OperationalError):
        # Database connection or operational issues
        logger.critical(f"Database operational error: {str(exc)}")
        return create_error_response(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="Service Unavailable",
            detail="Database service is temporarily unavailable"
        )
    
    elif isinstance(exc, DataError):
        # Invalid data for database operation
        return create_error_response(
            request=request,
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Bad Request",
            detail="Invalid data provided for database operation"
        )
    
    elif isinstance(exc, DatabaseError):
        # Generic database error
        logger.error(f"Database error: {str(exc)}")
        return create_error_response(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            detail="A database error occurred"
        )
    
    else:
        # Other SQLAlchemy errors
        logger.error(f"Unexpected SQLAlchemy error: {str(exc)}")
        return create_error_response(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            detail="An unexpected database error occurred"
        )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle generic Python exceptions.
    
    This is a catch-all handler for any unhandled exceptions.
    It logs the full exception and returns a generic 500 error to the client.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
    
    Returns:
        JSONResponse with generic error message
    """
    # Log the full exception with traceback
    logger.exception(f"Unhandled exception: {str(exc)}")
    
    return create_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="Internal Server Error",
        detail="An unexpected error occurred. Please try again later."
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    This function should be called during application initialization to set up
    global error handling for all routes.
    
    Args:
        app: FastAPI application instance
    """
    # Custom API exceptions
    app.add_exception_handler(APIException, api_exception_handler)
    
    # Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # SQLAlchemy database errors
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered successfully")

"""Startup validation and initialization for AI Workflow Generator service."""

import logging
from typing import Optional

from .config import ai_workflow_config

logger = logging.getLogger(__name__)


class StartupValidationError(Exception):
    """Raised when startup validation fails."""
    pass


def validate_environment() -> None:
    """Validate environment configuration on startup.
    
    This function performs comprehensive validation of all configuration
    settings required for the AI Workflow Generator service. It should be
    called during application startup before accepting any requests.
    
    Raises:
        StartupValidationError: If any required configuration is missing or invalid
    """
    logger.info("Starting AI Workflow Generator environment validation...")
    
    try:
        # Validate required settings
        ai_workflow_config.validate_required_settings()
        
        # Log configuration (excluding sensitive data)
        ai_workflow_config.log_configuration()
        
        # Validate rate limiting configuration
        _validate_rate_limiting()
        
        # Validate timeout configuration
        _validate_timeouts()
        
        # Validate document processing configuration
        _validate_document_processing()
        
        # Validate retry configuration
        _validate_retry_configuration()
        
        logger.info("✓ AI Workflow Generator environment validation completed successfully")
        
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise StartupValidationError(f"Configuration validation failed: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during startup validation: {e}")
        raise StartupValidationError(f"Startup validation failed: {e}") from e


def _validate_rate_limiting() -> None:
    """Validate rate limiting configuration (Requirements 9.2, 9.3)."""
    logger.info("Validating rate limiting configuration...")
    
    config = ai_workflow_config
    
    # Check that rate limits are reasonable
    if config.max_requests_per_session < 1:
        raise ValueError("max_requests_per_session must be at least 1")
    
    if config.rate_limit_window_seconds < 1:
        raise ValueError("rate_limit_window_seconds must be at least 1")
    
    if config.global_rate_limit_per_minute < 1:
        raise ValueError("global_rate_limit_per_minute must be at least 1")
    
    # Warn if configuration seems unusual
    requests_per_minute = (config.max_requests_per_session * 60) / config.rate_limit_window_seconds
    if requests_per_minute > config.global_rate_limit_per_minute * 2:
        logger.warning(
            f"Per-session rate ({requests_per_minute:.1f} req/min) is much higher than "
            f"global rate ({config.global_rate_limit_per_minute} req/min). "
            "This may cause unexpected throttling."
        )
    
    logger.info(
        f"✓ Rate limiting: {config.max_requests_per_session} requests per "
        f"{config.rate_limit_window_seconds}s window, "
        f"{config.global_rate_limit_per_minute} global req/min"
    )


def _validate_timeouts() -> None:
    """Validate timeout configuration."""
    logger.info("Validating timeout configuration...")
    
    config = ai_workflow_config
    
    # Check that timeouts are reasonable
    if config.gemini_timeout_seconds < 10:
        raise ValueError("gemini_timeout_seconds must be at least 10 seconds")
    
    if config.session_timeout_minutes < 1:
        raise ValueError("session_timeout_minutes must be at least 1 minute")
    
    if config.api_timeout_seconds < 5:
        raise ValueError("api_timeout_seconds must be at least 5 seconds")
    
    # Warn if Gemini timeout is very high
    if config.gemini_timeout_seconds > 120:
        logger.warning(
            f"gemini_timeout_seconds is set to {config.gemini_timeout_seconds}s, "
            "which is quite high. This may cause slow user experience."
        )
    
    logger.info(
        f"✓ Timeouts: Gemini={config.gemini_timeout_seconds}s, "
        f"Session={config.session_timeout_minutes}min, "
        f"API={config.api_timeout_seconds}s"
    )


def _validate_document_processing() -> None:
    """Validate document processing configuration (Requirement 9.4)."""
    logger.info("Validating document processing configuration...")
    
    config = ai_workflow_config
    
    # Check document size limits
    if config.max_document_size_mb < 1:
        raise ValueError("max_document_size_mb must be at least 1 MB")
    
    if config.max_document_size_mb > 100:
        logger.warning(
            f"max_document_size_mb is set to {config.max_document_size_mb} MB, "
            "which is quite large. This may cause memory issues."
        )
    
    # Check chunk size
    if config.document_chunk_size_tokens < 1000:
        raise ValueError("document_chunk_size_tokens must be at least 1000")
    
    if config.document_chunk_size_tokens >= config.gemini_max_tokens:
        raise ValueError(
            f"document_chunk_size_tokens ({config.document_chunk_size_tokens}) must be "
            f"less than gemini_max_tokens ({config.gemini_max_tokens})"
        )
    
    # Check supported formats
    if not config.supported_document_formats:
        raise ValueError("supported_document_formats cannot be empty")
    
    logger.info(
        f"✓ Document processing: Max size={config.max_document_size_mb}MB, "
        f"Chunk size={config.document_chunk_size_tokens} tokens, "
        f"Formats={', '.join(config.supported_document_formats)}"
    )


def _validate_retry_configuration() -> None:
    """Validate retry configuration (Requirement 9.1)."""
    logger.info("Validating retry configuration...")
    
    config = ai_workflow_config
    
    # Check retry settings
    if config.max_retries < 0:
        raise ValueError("max_retries cannot be negative")
    
    if config.initial_retry_delay_ms < 100:
        raise ValueError("initial_retry_delay_ms must be at least 100ms")
    
    if config.max_retry_delay_ms < config.initial_retry_delay_ms:
        raise ValueError(
            "max_retry_delay_ms must be greater than or equal to initial_retry_delay_ms"
        )
    
    if config.retry_backoff_multiplier < 1.0:
        raise ValueError("retry_backoff_multiplier must be at least 1.0")
    
    # Calculate total potential retry time
    total_retry_time_ms = 0
    for attempt in range(config.max_retries):
        total_retry_time_ms += config.get_retry_delay_ms(attempt)
    
    total_retry_time_seconds = total_retry_time_ms / 1000
    
    if total_retry_time_seconds > config.gemini_timeout_seconds:
        logger.warning(
            f"Total retry time ({total_retry_time_seconds:.1f}s) exceeds "
            f"Gemini timeout ({config.gemini_timeout_seconds}s). "
            "Retries may not complete before timeout."
        )
    
    logger.info(
        f"✓ Retry configuration: Max retries={config.max_retries}, "
        f"Initial delay={config.initial_retry_delay_ms}ms, "
        f"Max delay={config.max_retry_delay_ms}ms, "
        f"Multiplier={config.retry_backoff_multiplier}x, "
        f"Total potential retry time={total_retry_time_seconds:.1f}s"
    )


def initialize_service() -> None:
    """Initialize the AI Workflow Generator service.
    
    This function should be called during application startup to:
    1. Validate all configuration
    2. Initialize any required resources
    3. Perform health checks on dependencies
    
    Raises:
        StartupValidationError: If initialization fails
    """
    logger.info("Initializing AI Workflow Generator service...")
    
    try:
        # Validate environment
        validate_environment()
        
        # Additional initialization can be added here:
        # - Initialize caches
        # - Warm up connections
        # - Pre-load schemas
        # - etc.
        
        logger.info("✓ AI Workflow Generator service initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize AI Workflow Generator service: {e}")
        raise


def get_service_info() -> dict:
    """Get information about the service configuration.
    
    Returns:
        Dictionary containing service configuration information
    """
    config = ai_workflow_config
    
    return {
        "service": "AI Workflow Generator",
        "gemini_model": config.gemini_model,
        "max_tokens": config.gemini_max_tokens,
        "session_timeout_minutes": config.session_timeout_minutes,
        "max_document_size_mb": config.max_document_size_mb,
        "supported_formats": config.supported_document_formats,
        "rate_limits": {
            "max_requests_per_session": config.max_requests_per_session,
            "rate_limit_window_seconds": config.rate_limit_window_seconds,
            "global_rate_limit_per_minute": config.global_rate_limit_per_minute,
        },
        "retry_config": {
            "max_retries": config.max_retries,
            "initial_delay_ms": config.initial_retry_delay_ms,
            "max_delay_ms": config.max_retry_delay_ms,
            "backoff_multiplier": config.retry_backoff_multiplier,
        },
        "endpoints": {
            "agent_registry": config.agent_registry_url,
            "workflow_api": config.workflow_api_url,
        },
    }

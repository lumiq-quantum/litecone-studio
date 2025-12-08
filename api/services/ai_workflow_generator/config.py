"""Configuration for AI Workflow Generator service."""

import logging
from typing import Optional, List
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AIWorkflowConfig(BaseSettings):
    """Configuration settings for AI Workflow Generator.
    
    This configuration class handles all settings for the AI Workflow Generator,
    including Gemini API settings, rate limits, timeouts, and document processing limits.
    All settings can be overridden via environment variables.
    """
    
    # Gemini API Configuration
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key (required for production)",
        validation_alias="GEMINI_API_KEY"
    )
    gemini_model: str = Field(
        default="gemini-1.5-pro",
        description="Gemini model to use",
        validation_alias="GEMINI_MODEL"
    )
    gemini_max_tokens: int = Field(
        default=8192,
        ge=1024,
        le=32768,
        description="Maximum tokens for Gemini responses",
        validation_alias="GEMINI_MAX_TOKENS"
    )
    gemini_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for Gemini generation (0.0-2.0)",
        validation_alias="GEMINI_TEMPERATURE"
    )
    gemini_timeout_seconds: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Timeout for Gemini API calls in seconds",
        validation_alias="GEMINI_TIMEOUT_SECONDS"
    )
    
    # Session Configuration
    session_timeout_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Chat session timeout in minutes (5-1440)",
        validation_alias="SESSION_TIMEOUT_MINUTES"
    )
    session_cleanup_interval_minutes: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Interval for cleaning up expired sessions in minutes",
        validation_alias="SESSION_CLEANUP_INTERVAL_MINUTES"
    )
    max_session_history_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Maximum number of messages to keep in session history",
        validation_alias="MAX_SESSION_HISTORY_SIZE"
    )
    
    # Document Processing Configuration
    max_document_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum document size in MB (1-100)",
        validation_alias="MAX_DOCUMENT_SIZE_MB"
    )
    max_document_size_bytes: int = Field(
        default=10485760,  # 10 MB in bytes
        init=False,
        description="Maximum document size in bytes (computed from max_document_size_mb)"
    )
    supported_document_formats: List[str] = Field(
        default=["pdf", "docx", "txt", "md"],
        description="List of supported document formats",
        validation_alias="SUPPORTED_DOCUMENT_FORMATS"
    )
    document_chunk_size_tokens: int = Field(
        default=6000,
        ge=1000,
        le=30000,
        description="Size of document chunks in tokens for LLM processing",
        validation_alias="DOCUMENT_CHUNK_SIZE_TOKENS"
    )
    
    # Cache Configuration
    agent_cache_ttl_seconds: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Agent metadata cache TTL in seconds (60-3600)",
        validation_alias="AGENT_CACHE_TTL_SECONDS"
    )
    workflow_cache_ttl_seconds: int = Field(
        default=60,
        ge=10,
        le=600,
        description="Workflow cache TTL in seconds",
        validation_alias="WORKFLOW_CACHE_TTL_SECONDS"
    )
    
    # Integration Endpoints
    agent_registry_url: str = Field(
        default="http://localhost:8000/api/v1/agents",
        description="Agent registry API URL",
        validation_alias="AGENT_REGISTRY_URL"
    )
    workflow_api_url: str = Field(
        default="http://localhost:8000/api/v1/workflows",
        description="Workflow API URL",
        validation_alias="WORKFLOW_API_URL"
    )
    api_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Timeout for API calls to other services in seconds",
        validation_alias="API_TIMEOUT_SECONDS"
    )
    
    # Rate Limiting Configuration (Requirement 9.2, 9.3)
    max_requests_per_session: int = Field(
        default=50,
        ge=10,
        le=500,
        description="Maximum LLM requests per session (10-500)",
        validation_alias="MAX_REQUESTS_PER_SESSION"
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=10,
        le=3600,
        description="Rate limit window in seconds (10-3600)",
        validation_alias="RATE_LIMIT_WINDOW_SECONDS"
    )
    global_rate_limit_per_minute: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Global rate limit for all sessions per minute",
        validation_alias="GLOBAL_RATE_LIMIT_PER_MINUTE"
    )
    rate_limit_queue_size: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Maximum size of rate limit queue",
        validation_alias="RATE_LIMIT_QUEUE_SIZE"
    )
    
    # Retry Configuration (Requirement 9.1)
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for LLM calls (0-10)",
        validation_alias="MAX_RETRIES"
    )
    initial_retry_delay_ms: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="Initial retry delay in milliseconds (100-5000)",
        validation_alias="INITIAL_RETRY_DELAY_MS"
    )
    max_retry_delay_ms: int = Field(
        default=30000,
        ge=5000,
        le=60000,
        description="Maximum retry delay in milliseconds (5000-60000)",
        validation_alias="MAX_RETRY_DELAY_MS"
    )
    retry_backoff_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Backoff multiplier for retries (1.0-5.0)",
        validation_alias="RETRY_BACKOFF_MULTIPLIER"
    )
    retriable_status_codes: List[int] = Field(
        default=[429, 500, 502, 503, 504],
        description="HTTP status codes that should trigger retries",
        validation_alias="RETRIABLE_STATUS_CODES"
    )
    
    # Validation Configuration
    enable_strict_validation: bool = Field(
        default=True,
        description="Enable strict workflow validation",
        validation_alias="ENABLE_STRICT_VALIDATION"
    )
    enable_auto_correction: bool = Field(
        default=True,
        description="Enable automatic correction of validation errors",
        validation_alias="ENABLE_AUTO_CORRECTION"
    )
    
    # Logging Configuration
    log_llm_prompts: bool = Field(
        default=False,
        description="Log LLM prompts (disable in production for privacy)",
        validation_alias="LOG_LLM_PROMPTS"
    )
    log_llm_responses: bool = Field(
        default=False,
        description="Log LLM responses (disable in production for privacy)",
        validation_alias="LOG_LLM_RESPONSES"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env.api",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("gemini_model")
    @classmethod
    def validate_gemini_model(cls, v: str) -> str:
        """Validate that the Gemini model name is valid."""
        valid_models = [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro",
            "gemini-pro-vision",
            "models/gemini-2.5-pro"
        ]
        if v not in valid_models:
            logger.warning(
                f"Gemini model '{v}' is not in the list of known models: {valid_models}. "
                "Proceeding anyway, but this may cause issues."
            )
        return v
    
    @field_validator("agent_registry_url", "workflow_api_url")
    @classmethod
    def validate_urls(cls, v: str) -> str:
        """Validate that URLs are properly formatted."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"URL must start with 'http://' or 'https://': {v}")
        return v.rstrip("/")  # Remove trailing slash for consistency
    
    @field_validator("supported_document_formats")
    @classmethod
    def validate_document_formats(cls, v: List[str]) -> List[str]:
        """Validate and normalize document formats."""
        valid_formats = ["pdf", "docx", "txt", "md", "doc"]
        normalized = [fmt.lower().strip() for fmt in v]
        for fmt in normalized:
            if fmt not in valid_formats:
                logger.warning(f"Document format '{fmt}' may not be supported")
        return normalized
    
    @model_validator(mode="after")
    def validate_retry_delays(self) -> "AIWorkflowConfig":
        """Validate that max retry delay is greater than initial delay."""
        if self.max_retry_delay_ms <= self.initial_retry_delay_ms:
            raise ValueError(
                f"max_retry_delay_ms ({self.max_retry_delay_ms}) must be greater than "
                f"initial_retry_delay_ms ({self.initial_retry_delay_ms})"
            )
        return self
    
    @model_validator(mode="after")
    def compute_document_size_bytes(self) -> "AIWorkflowConfig":
        """Compute max document size in bytes from MB."""
        self.max_document_size_bytes = self.max_document_size_mb * 1024 * 1024
        return self
    
    @model_validator(mode="after")
    def validate_token_limits(self) -> "AIWorkflowConfig":
        """Validate that document chunk size is less than max tokens."""
        if self.document_chunk_size_tokens >= self.gemini_max_tokens:
            raise ValueError(
                f"document_chunk_size_tokens ({self.document_chunk_size_tokens}) must be "
                f"less than gemini_max_tokens ({self.gemini_max_tokens})"
            )
        return self
    
    def validate_required_settings(self) -> None:
        """Validate that all required settings are present.
        
        This should be called on application startup to ensure critical
        configuration is present before the service starts accepting requests.
        
        Raises:
            ValueError: If required settings are missing or invalid
        """
        errors = []
        
        # Check Gemini API key
        if not self.gemini_api_key or self.gemini_api_key.strip() == "":
            errors.append(
                "GEMINI_API_KEY is required. Please set it in your environment or .env.api file."
            )
        
        # Check API endpoints
        if not self.agent_registry_url:
            errors.append("AGENT_REGISTRY_URL is required")
        
        if not self.workflow_api_url:
            errors.append("WORKFLOW_API_URL is required")
        
        # Validate rate limiting makes sense
        if self.max_requests_per_session > self.global_rate_limit_per_minute:
            logger.warning(
                f"max_requests_per_session ({self.max_requests_per_session}) is greater than "
                f"global_rate_limit_per_minute ({self.global_rate_limit_per_minute}). "
                "This may cause unexpected rate limiting behavior."
            )
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)
        
        logger.info("AI Workflow Generator configuration validated successfully")
    
    def get_retry_delay_ms(self, attempt: int) -> int:
        """Calculate retry delay for a given attempt using exponential backoff.
        
        Args:
            attempt: The retry attempt number (0-indexed)
            
        Returns:
            Delay in milliseconds, capped at max_retry_delay_ms
        """
        delay = self.initial_retry_delay_ms * (self.retry_backoff_multiplier ** attempt)
        return min(int(delay), self.max_retry_delay_ms)
    
    def is_retriable_error(self, status_code: int) -> bool:
        """Check if an HTTP status code should trigger a retry.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            True if the error should be retried
        """
        return status_code in self.retriable_status_codes
    
    def log_configuration(self) -> None:
        """Log the current configuration (excluding sensitive data)."""
        logger.info("AI Workflow Generator Configuration:")
        logger.info(f"  Gemini Model: {self.gemini_model}")
        logger.info(f"  Max Tokens: {self.gemini_max_tokens}")
        logger.info(f"  Temperature: {self.gemini_temperature}")
        logger.info(f"  Timeout: {self.gemini_timeout_seconds}s")
        logger.info(f"  Session Timeout: {self.session_timeout_minutes} minutes")
        logger.info(f"  Max Document Size: {self.max_document_size_mb} MB")
        logger.info(f"  Supported Formats: {', '.join(self.supported_document_formats)}")
        logger.info(f"  Max Requests/Session: {self.max_requests_per_session}")
        logger.info(f"  Rate Limit Window: {self.rate_limit_window_seconds}s")
        logger.info(f"  Max Retries: {self.max_retries}")
        logger.info(f"  Agent Registry: {self.agent_registry_url}")
        logger.info(f"  Workflow API: {self.workflow_api_url}")


# Global AI workflow config instance
ai_workflow_config = AIWorkflowConfig()

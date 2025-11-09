"""Configuration management for the Workflow Management API."""

from typing import Optional, List
from pydantic import Field, field_validator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Settings
    api_title: str = Field(default="Workflow Management API", validation_alias="API_TITLE")
    api_version: str = Field(default="1.0.0", validation_alias="API_VERSION")
    api_description: str = Field(
        default="REST API for managing workflow orchestration",
        validation_alias="API_DESCRIPTION"
    )
    api_prefix: str = Field(default="/api/v1", validation_alias="API_PREFIX")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    port: int = Field(default=8000, validation_alias="API_PORT")
    reload: bool = Field(default=False, validation_alias="API_RELOAD")
    workers: int = Field(default=1, validation_alias="API_WORKERS")
    
    # Database Settings
    database_url: str = Field(
        ...,
        description="PostgreSQL connection URL",
        validation_alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, validation_alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, validation_alias="DATABASE_MAX_OVERFLOW")
    database_echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")
    
    # Kafka Settings
    kafka_brokers: str = Field(
        default="localhost:9092",
        validation_alias="KAFKA_BROKERS"
    )
    kafka_execution_topic: str = Field(
        default="workflow.execution.requests",
        validation_alias="KAFKA_EXECUTION_TOPIC"
    )
    kafka_cancellation_topic: str = Field(
        default="workflow.cancellation.requests",
        validation_alias="KAFKA_CANCELLATION_TOPIC"
    )
    
    # Authentication Settings
    jwt_secret: str = Field(..., validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=60, validation_alias="JWT_EXPIRATION_MINUTES")
    api_key_header: str = Field(default="X-API-Key", validation_alias="API_KEY_HEADER")
    
    # CORS Settings
    cors_origins: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, validation_alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: str = Field(default="*", validation_alias="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field(default="*", validation_alias="CORS_ALLOW_HEADERS")
    
    # Logging Settings
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field(default="json", validation_alias="LOG_FORMAT")
    
    # Pagination Settings
    default_page_size: int = Field(default=20, validation_alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, validation_alias="MAX_PAGE_SIZE")
    
    # Feature Flags
    enable_metrics: bool = Field(default=True, validation_alias="ENABLE_METRICS")
    enable_audit_logging: bool = Field(default=True, validation_alias="ENABLE_AUDIT_LOGGING")
    
    model_config = SettingsConfigDict(
        env_file=".env.api",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate that the database URL is properly formatted."""
        if not v.startswith("postgresql://") and not v.startswith("postgres://"):
            raise ValueError("DATABASE_URL must start with 'postgresql://' or 'postgres://'")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_upper
    
    @field_validator("cors_origins", "cors_allow_methods", "cors_allow_headers")
    @classmethod
    def parse_cors_lists(cls, v):
        """Parse CORS settings from comma-separated string."""
        if isinstance(v, str):
            # Handle empty string or single wildcard
            if not v.strip() or v.strip() == "*":
                return v
            return v
        return v
    
    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins
    
    def get_cors_methods_list(self) -> List[str]:
        """Get CORS methods as a list."""
        if self.cors_allow_methods == "*":
            return ["*"]
        return [method.strip() for method in self.cors_allow_methods.split(",")]
    
    def get_cors_headers_list(self) -> List[str]:
        """Get CORS headers as a list."""
        if self.cors_allow_headers == "*":
            return ["*"]
        return [header.strip() for header in self.cors_allow_headers.split(",")]


# Global settings instance
settings = Settings()

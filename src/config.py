"""Configuration management using pydantic-settings."""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaConfig(BaseSettings):
    """Kafka-related configuration."""
    
    brokers: str = Field(
        default="localhost:9092",
        description="Comma-separated list of Kafka broker addresses",
        validation_alias="KAFKA_BROKERS"
    )
    client_id: str = Field(
        default="executor-service",
        description="Kafka client identifier",
        validation_alias="KAFKA_CLIENT_ID"
    )
    group_id: str = Field(
        default="executor-group",
        description="Kafka consumer group ID",
        validation_alias="KAFKA_GROUP_ID"
    )
    tasks_topic: str = Field(
        default="orchestrator.tasks.http",
        description="Kafka topic for agent tasks",
        validation_alias="KAFKA_TASKS_TOPIC"
    )
    results_topic: str = Field(
        default="results.topic",
        description="Kafka topic for agent results",
        validation_alias="KAFKA_RESULTS_TOPIC"
    )
    monitoring_topic: str = Field(
        default="workflow.monitoring.updates",
        description="Kafka topic for monitoring updates",
        validation_alias="KAFKA_MONITORING_TOPIC"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )


class DatabaseConfig(BaseSettings):
    """Database-related configuration."""
    
    url: str = Field(
        ...,
        description="PostgreSQL connection URL",
        validation_alias="DATABASE_URL"
    )
    pool_size: int = Field(
        default=10,
        description="Number of connections to maintain in the pool",
        validation_alias="DATABASE_POOL_SIZE"
    )
    max_overflow: int = Field(
        default=20,
        description="Maximum number of connections to create beyond pool_size",
        validation_alias="DATABASE_MAX_OVERFLOW"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate that the database URL is properly formatted."""
        if not v.startswith("postgresql://") and not v.startswith("postgres://"):
            raise ValueError("DATABASE_URL must start with 'postgresql://' or 'postgres://'")
        return v


class S3Config(BaseSettings):
    """S3-related configuration (optional, for future use)."""
    
    bucket: Optional[str] = Field(
        default=None,
        description="S3 bucket name for storing large payloads",
        validation_alias="S3_BUCKET"
    )
    region: str = Field(
        default="us-east-1",
        description="AWS region for S3 bucket",
        validation_alias="AWS_REGION"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )


class AgentRegistryConfig(BaseSettings):
    """Agent Registry-related configuration."""
    
    url: str = Field(
        ...,
        description="Base URL of the Agent Registry service",
        validation_alias="AGENT_REGISTRY_URL"
    )
    cache_ttl_seconds: int = Field(
        default=300,
        description="Time-to-live for agent metadata cache in seconds",
        validation_alias="AGENT_REGISTRY_CACHE_TTL"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that the URL is properly formatted."""
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("AGENT_REGISTRY_URL must start with 'http://' or 'https://'")
        return v.rstrip("/")  # Remove trailing slash


class ExecutorConfig(BaseSettings):
    """Centralized Executor-specific configuration."""
    
    run_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this workflow run",
        validation_alias="RUN_ID"
    )
    workflow_plan: Optional[str] = Field(
        default=None,
        description="JSON string of workflow plan or path to JSON file",
        validation_alias="WORKFLOW_PLAN"
    )
    workflow_input: Optional[str] = Field(
        default=None,
        description="JSON string of initial input data or path to JSON file",
        validation_alias="WORKFLOW_INPUT"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )


class BridgeConfig(BaseSettings):
    """External Agent Executor (Bridge)-specific configuration."""
    
    http_timeout_ms: int = Field(
        default=30000,
        description="Default timeout for HTTP requests to agents in milliseconds",
        validation_alias="HTTP_TIMEOUT_MS"
    )
    max_retries: int = Field(
        default=3,
        description="Default maximum number of retry attempts for HTTP calls",
        validation_alias="MAX_RETRIES"
    )
    initial_retry_delay_ms: int = Field(
        default=1000,
        description="Initial delay before first retry in milliseconds",
        validation_alias="INITIAL_RETRY_DELAY_MS"
    )
    max_retry_delay_ms: int = Field(
        default=30000,
        description="Maximum delay between retries in milliseconds",
        validation_alias="MAX_RETRY_DELAY_MS"
    )
    backoff_multiplier: float = Field(
        default=2.0,
        description="Multiplier for exponential backoff",
        validation_alias="BACKOFF_MULTIPLIER"
    )
    worker_concurrency: int = Field(
        default=10,
        description="Number of concurrent workers for processing tasks",
        validation_alias="WORKER_CONCURRENCY"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("http_timeout_ms", "max_retries", "initial_retry_delay_ms", 
                     "max_retry_delay_ms", "worker_concurrency")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Validate that numeric values are positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v
    
    @field_validator("backoff_multiplier")
    @classmethod
    def validate_backoff_multiplier(cls, v: float) -> float:
        """Validate that backoff multiplier is >= 1.0."""
        if v < 1.0:
            raise ValueError("Backoff multiplier must be >= 1.0")
        return v


class LoggingConfig(BaseSettings):
    """Logging-related configuration."""
    
    level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        validation_alias="LOG_LEVEL"
    )
    format: str = Field(
        default="text",
        description="Log format (text or json)",
        validation_alias="LOG_FORMAT"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_upper
    
    @field_validator("format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate that log format is valid."""
        valid_formats = ["text", "json"]
        v_lower = v.lower()
        if v_lower not in valid_formats:
            raise ValueError(f"LOG_FORMAT must be one of: {', '.join(valid_formats)}")
        return v_lower


class Config(BaseSettings):
    """
    Main configuration class that aggregates all configuration sections.
    
    This class loads configuration from environment variables and provides
    validation for all required values.
    
    Usage:
        # Load configuration from environment
        config = Config()
        
        # Access configuration values
        kafka_brokers = config.kafka.brokers
        database_url = config.database.url
        
        # Load from .env file
        config = Config(_env_file='.env')
    """
    
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    database: DatabaseConfig
    s3: S3Config = Field(default_factory=S3Config)
    agent_registry: AgentRegistryConfig
    executor: ExecutorConfig = Field(default_factory=ExecutorConfig)
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        """
        Initialize configuration.
        
        Automatically loads nested configuration objects from environment variables.
        """
        # Load nested configs from environment if not provided
        if "kafka" not in kwargs:
            kwargs["kafka"] = KafkaConfig()
        if "database" not in kwargs:
            kwargs["database"] = DatabaseConfig()
        if "s3" not in kwargs:
            kwargs["s3"] = S3Config()
        if "agent_registry" not in kwargs:
            kwargs["agent_registry"] = AgentRegistryConfig()
        if "executor" not in kwargs:
            kwargs["executor"] = ExecutorConfig()
        if "bridge" not in kwargs:
            kwargs["bridge"] = BridgeConfig()
        if "logging" not in kwargs:
            kwargs["logging"] = LoggingConfig()
        
        super().__init__(**kwargs)
    
    def validate_executor_config(self) -> None:
        """
        Validate that required executor configuration is present.
        
        Raises:
            ValueError: If required executor configuration is missing
        """
        if not self.executor.run_id:
            raise ValueError("RUN_ID is required for executor")
        if not self.executor.workflow_plan:
            raise ValueError("WORKFLOW_PLAN is required for executor")
        if not self.executor.workflow_input:
            raise ValueError("WORKFLOW_INPUT is required for executor")
    
    def get_http_timeout_seconds(self) -> float:
        """Get HTTP timeout in seconds (converted from milliseconds)."""
        return self.bridge.http_timeout_ms / 1000.0
    
    def get_initial_retry_delay_seconds(self) -> float:
        """Get initial retry delay in seconds (converted from milliseconds)."""
        return self.bridge.initial_retry_delay_ms / 1000.0
    
    def get_max_retry_delay_seconds(self) -> float:
        """Get max retry delay in seconds (converted from milliseconds)."""
        return self.bridge.max_retry_delay_ms / 1000.0


def load_config(env_file: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables and optional .env file.
    
    Args:
        env_file: Optional path to .env file to load
        
    Returns:
        Config instance with all configuration loaded
        
    Raises:
        ValueError: If required configuration values are missing or invalid
    """
    if env_file:
        return Config(_env_file=env_file)
    return Config()

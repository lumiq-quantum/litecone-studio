"""Pydantic models for Agent Registry data structures."""

from typing import Optional, Dict
from pydantic import BaseModel, Field


class RetryConfig(BaseModel):
    """Configuration for retry logic with exponential backoff."""
    
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    initial_delay_ms: int = Field(default=1000, description="Initial delay in milliseconds")
    max_delay_ms: int = Field(default=30000, description="Maximum delay in milliseconds")
    backoff_multiplier: float = Field(default=2.0, description="Multiplier for exponential backoff")


class CircuitBreakerConfigModel(BaseModel):
    """Circuit breaker configuration for an agent."""
    
    enabled: bool = Field(default=True, description="Enable circuit breaker for this agent")
    failure_threshold: int = Field(default=5, description="Number of consecutive failures before opening circuit")
    failure_rate_threshold: float = Field(default=0.5, description="Failure rate threshold for opening circuit")
    timeout_seconds: int = Field(default=60, description="Time to keep circuit open before attempting reset")
    half_open_max_calls: int = Field(default=3, description="Maximum test calls allowed in half-open state")
    window_size_seconds: int = Field(default=120, description="Sliding window size for failure rate calculation")


class AgentMetadata(BaseModel):
    """Metadata about an agent retrieved from the Agent Registry."""
    
    name: str = Field(..., description="Name of the agent")
    url: str = Field(..., description="HTTP endpoint URL for the agent")
    auth_config: Optional[Dict[str, str]] = Field(
        None,
        description="Authentication configuration (e.g., {'type': 'bearer', 'token': '...'})"
    )
    timeout: int = Field(default=30000, description="Request timeout in milliseconds")
    retry_config: RetryConfig = Field(
        default_factory=RetryConfig,
        description="Retry configuration for this agent"
    )
    circuit_breaker_config: Optional[CircuitBreakerConfigModel] = Field(
        None,
        description="Circuit breaker configuration for this agent"
    )

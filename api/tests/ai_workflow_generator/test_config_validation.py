"""Tests for AI Workflow Generator configuration validation."""

import os
import pytest
from pydantic import ValidationError

from api.services.ai_workflow_generator.config import AIWorkflowConfig
from api.services.ai_workflow_generator.startup import (
    validate_environment,
    StartupValidationError,
    _validate_rate_limiting,
    _validate_timeouts,
    _validate_document_processing,
    _validate_retry_configuration,
)


@pytest.fixture(autouse=True)
def clear_env_vars(monkeypatch):
    """Clear environment variables before each test."""
    # Clear all AI workflow related env vars
    env_vars = [
        "GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_MAX_TOKENS", "GEMINI_TEMPERATURE",
        "SESSION_TIMEOUT_MINUTES", "MAX_DOCUMENT_SIZE_MB", "AGENT_REGISTRY_URL",
        "WORKFLOW_API_URL", "MAX_REQUESTS_PER_SESSION", "RATE_LIMIT_WINDOW_SECONDS",
        "MAX_RETRIES", "INITIAL_RETRY_DELAY_MS", "MAX_RETRY_DELAY_MS",
        "RETRY_BACKOFF_MULTIPLIER", "DOCUMENT_CHUNK_SIZE_TOKENS"
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


class TestAIWorkflowConfig:
    """Test configuration validation."""
    
    def test_default_config_values(self, monkeypatch):
        """Test that default configuration values are set correctly."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        config = AIWorkflowConfig()
        
        assert config.gemini_model == "gemini-1.5-pro"
        assert config.gemini_max_tokens == 8192
        assert config.gemini_temperature == 0.7
        assert config.session_timeout_minutes == 30
        assert config.max_document_size_mb == 10
        assert config.max_requests_per_session == 50
        assert config.max_retries == 3
    
    def test_document_size_bytes_computed(self, monkeypatch):
        """Test that document size in bytes is computed correctly."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("MAX_DOCUMENT_SIZE_MB", "20")
        config = AIWorkflowConfig()
        assert config.max_document_size_mb == 20
        assert config.max_document_size_bytes == 20 * 1024 * 1024
    
    def test_get_retry_delay_calculation(self, monkeypatch):
        """Test exponential backoff calculation."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("INITIAL_RETRY_DELAY_MS", "1000")
        monkeypatch.setenv("MAX_RETRY_DELAY_MS", "30000")
        monkeypatch.setenv("RETRY_BACKOFF_MULTIPLIER", "2.0")
        config = AIWorkflowConfig()
        
        # First retry: 1000ms
        assert config.get_retry_delay_ms(0) == 1000
        
        # Second retry: 2000ms
        assert config.get_retry_delay_ms(1) == 2000
        
        # Third retry: 4000ms
        assert config.get_retry_delay_ms(2) == 4000
        
        # Large attempt should be capped at max
        assert config.get_retry_delay_ms(10) == 30000
    
    def test_is_retriable_error(self, monkeypatch):
        """Test retriable error detection."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        config = AIWorkflowConfig()
        
        # Retriable errors
        assert config.is_retriable_error(429) is True  # Rate limit
        assert config.is_retriable_error(500) is True  # Server error
        assert config.is_retriable_error(503) is True  # Service unavailable
        
        # Non-retriable errors
        assert config.is_retriable_error(400) is False  # Bad request
        assert config.is_retriable_error(401) is False  # Unauthorized
        assert config.is_retriable_error(404) is False  # Not found
    
    def test_validate_required_settings_missing_api_key(self):
        """Test that validation fails when API key is missing."""
        config = AIWorkflowConfig()
        
        with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
            config.validate_required_settings()
    
    def test_validate_required_settings_empty_api_key(self, monkeypatch):
        """Test that validation fails when API key is empty."""
        monkeypatch.setenv("GEMINI_API_KEY", "   ")
        config = AIWorkflowConfig()
        
        with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
            config.validate_required_settings()
    
    def test_validate_required_settings_success(self, monkeypatch):
        """Test that validation succeeds with all required settings."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
        monkeypatch.setenv("AGENT_REGISTRY_URL", "http://localhost:8000/api/v1/agents")
        monkeypatch.setenv("WORKFLOW_API_URL", "http://localhost:8000/api/v1/workflows")
        config = AIWorkflowConfig()
        
        # Should not raise
        config.validate_required_settings()
    
    def test_url_trailing_slash_removed(self, monkeypatch):
        """Test that trailing slashes are removed from URLs."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("AGENT_REGISTRY_URL", "http://localhost:8000/api/v1/agents/")
        monkeypatch.setenv("WORKFLOW_API_URL", "https://example.com/api/workflows/")
        config = AIWorkflowConfig()
        
        assert config.agent_registry_url == "http://localhost:8000/api/v1/agents"
        assert config.workflow_api_url == "https://example.com/api/workflows"


class TestStartupValidation:
    """Test startup validation functions."""
    
    def test_validate_rate_limiting_success(self, monkeypatch):
        """Test rate limiting validation with valid configuration."""
        # Mock config with valid values
        from api.services.ai_workflow_generator import config as config_module
        
        test_config = AIWorkflowConfig(
            gemini_api_key="test-key",
            max_requests_per_session=50,
            rate_limit_window_seconds=60,
            global_rate_limit_per_minute=100
        )
        monkeypatch.setattr(config_module, "ai_workflow_config", test_config)
        
        # Should not raise
        _validate_rate_limiting()
    
    def test_validate_timeouts_success(self, monkeypatch):
        """Test timeout validation with valid configuration."""
        from api.services.ai_workflow_generator import config as config_module
        
        test_config = AIWorkflowConfig(
            gemini_api_key="test-key",
            gemini_timeout_seconds=60,
            session_timeout_minutes=30,
            api_timeout_seconds=30
        )
        monkeypatch.setattr(config_module, "ai_workflow_config", test_config)
        
        # Should not raise
        _validate_timeouts()
    
    def test_validate_document_processing_success(self, monkeypatch):
        """Test document processing validation with valid configuration."""
        from api.services.ai_workflow_generator import config as config_module
        
        test_config = AIWorkflowConfig(
            gemini_api_key="test-key",
            max_document_size_mb=10,
            document_chunk_size_tokens=6000,
            gemini_max_tokens=8192,
            supported_document_formats=["pdf", "docx", "txt", "md"]
        )
        monkeypatch.setattr(config_module, "ai_workflow_config", test_config)
        
        # Should not raise
        _validate_document_processing()
    
    def test_validate_retry_configuration_success(self, monkeypatch):
        """Test retry configuration validation with valid configuration."""
        from api.services.ai_workflow_generator import config as config_module
        
        test_config = AIWorkflowConfig(
            gemini_api_key="test-key",
            max_retries=3,
            initial_retry_delay_ms=1000,
            max_retry_delay_ms=30000,
            retry_backoff_multiplier=2.0
        )
        monkeypatch.setattr(config_module, "ai_workflow_config", test_config)
        
        # Should not raise
        _validate_retry_configuration()

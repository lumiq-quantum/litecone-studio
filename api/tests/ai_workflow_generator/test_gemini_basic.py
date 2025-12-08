"""Basic unit tests for Gemini LLM service core functionality."""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


def test_exponential_backoff_calculation():
    """Test exponential backoff delay calculation."""
    # Mock the config
    mock_config = MagicMock()
    mock_config.gemini_api_key = "test-key"
    mock_config.gemini_model = "gemini-1.5-pro"
    mock_config.gemini_max_tokens = 8192
    mock_config.gemini_temperature = 0.7
    mock_config.max_retries = 3
    mock_config.initial_retry_delay_ms = 1000
    mock_config.max_retry_delay_ms = 30000
    mock_config.retry_backoff_multiplier = 2.0
    
    with patch('services.ai_workflow_generator.config.ai_workflow_config', mock_config):
        with patch('services.ai_workflow_generator.gemini_service.genai'):
            from services.ai_workflow_generator.gemini_service import GeminiService
            
            service = GeminiService(api_key="test-key")
            
            # First retry should be initial delay
            delay_0 = service._calculate_retry_delay(0)
            assert delay_0 == 1.0  # 1000ms = 1s
            
            # Second retry should be doubled
            delay_1 = service._calculate_retry_delay(1)
            assert delay_1 == 2.0  # 2000ms = 2s
            
            # Third retry should be quadrupled
            delay_2 = service._calculate_retry_delay(2)
            assert delay_2 == 4.0  # 4000ms = 4s
            
            # Should not exceed max delay
            delay_large = service._calculate_retry_delay(100)
            assert delay_large == 30.0  # 30000ms = 30s


def test_token_counting_fallback():
    """Test token counting fallback mechanism."""
    mock_config = MagicMock()
    mock_config.gemini_api_key = "test-key"
    mock_config.gemini_model = "gemini-1.5-pro"
    mock_config.gemini_max_tokens = 8192
    mock_config.gemini_temperature = 0.7
    mock_config.max_retries = 3
    mock_config.initial_retry_delay_ms = 1000
    mock_config.max_retry_delay_ms = 30000
    mock_config.retry_backoff_multiplier = 2.0
    
    with patch('services.ai_workflow_generator.config.ai_workflow_config', mock_config):
        with patch('services.ai_workflow_generator.gemini_service.genai'):
            from services.ai_workflow_generator.gemini_service import GeminiService
            
            service = GeminiService(api_key="test-key")
            
            # Mock the model's count_tokens to raise an exception
            service.model.count_tokens = Mock(side_effect=Exception("API error"))
            
            text = "This is a test string with some words"
            count = service.count_tokens(text)
            
            # Should use fallback approximation (1 token ≈ 4 characters)
            expected = len(text) // 4
            assert count == expected


def test_context_window_checking():
    """Test context window size checking."""
    mock_config = MagicMock()
    mock_config.gemini_api_key = "test-key"
    mock_config.gemini_model = "gemini-1.5-pro"
    mock_config.gemini_max_tokens = 100
    mock_config.gemini_temperature = 0.7
    mock_config.max_retries = 3
    mock_config.initial_retry_delay_ms = 1000
    mock_config.max_retry_delay_ms = 30000
    mock_config.retry_backoff_multiplier = 2.0
    
    with patch('services.ai_workflow_generator.gemini_service.ai_workflow_config', mock_config):
        with patch('services.ai_workflow_generator.gemini_service.genai'):
            from services.ai_workflow_generator.gemini_service import GeminiService
            
            service = GeminiService(api_key="test-key")
            
            # Verify max_tokens was set correctly from config
            assert service.max_tokens == 100
            
            # Mock count_tokens to return specific values
            service.count_tokens = Mock(return_value=50)
            assert service._check_context_window("test") is True
            
            service.count_tokens = Mock(return_value=150)
            assert service._check_context_window("test") is False


def test_agent_formatting():
    """Test agent list formatting for prompts."""
    mock_config = MagicMock()
    mock_config.gemini_api_key = "test-key"
    mock_config.gemini_model = "gemini-1.5-pro"
    mock_config.gemini_max_tokens = 8192
    mock_config.gemini_temperature = 0.7
    mock_config.max_retries = 3
    mock_config.initial_retry_delay_ms = 1000
    mock_config.max_retry_delay_ms = 30000
    mock_config.retry_backoff_multiplier = 2.0
    
    with patch('services.ai_workflow_generator.config.ai_workflow_config', mock_config):
        with patch('services.ai_workflow_generator.gemini_service.genai'):
            from services.ai_workflow_generator.gemini_service import GeminiService
            from services.ai_workflow_generator.agent_query import AgentMetadata
            
            service = GeminiService(api_key="test-key")
            
            agents = [
                AgentMetadata(
                    name="data-processor",
                    description="Processes data files",
                    url="http://localhost:8001",
                    capabilities=["data processing", "file handling"],
                    status="active"
                ),
                AgentMetadata(
                    name="validator",
                    description="Validates data quality",
                    url="http://localhost:8002",
                    capabilities=["validation"],
                    status="active"
                )
            ]
            
            formatted = service._format_agents_for_prompt(agents)
            
            assert "data-processor" in formatted
            assert "validator" in formatted
            assert "Processes data files" in formatted
            assert "data processing" in formatted
            assert "validation" in formatted


def test_agent_formatting_empty():
    """Test agent formatting with empty list."""
    mock_config = MagicMock()
    mock_config.gemini_api_key = "test-key"
    mock_config.gemini_model = "gemini-1.5-pro"
    mock_config.gemini_max_tokens = 8192
    mock_config.gemini_temperature = 0.7
    mock_config.max_retries = 3
    mock_config.initial_retry_delay_ms = 1000
    mock_config.max_retry_delay_ms = 30000
    mock_config.retry_backoff_multiplier = 2.0
    
    with patch('services.ai_workflow_generator.config.ai_workflow_config', mock_config):
        with patch('services.ai_workflow_generator.gemini_service.genai'):
            from services.ai_workflow_generator.gemini_service import GeminiService
            
            service = GeminiService(api_key="test-key")
            formatted = service._format_agents_for_prompt([])
            
            assert formatted == "No agents available"


def test_workflow_response_parsing_valid():
    """Test parsing valid workflow response."""
    mock_config = MagicMock()
    mock_config.gemini_api_key = "test-key"
    mock_config.gemini_model = "gemini-1.5-pro"
    mock_config.gemini_max_tokens = 8192
    mock_config.gemini_temperature = 0.7
    mock_config.max_retries = 3
    mock_config.initial_retry_delay_ms = 1000
    mock_config.max_retry_delay_ms = 30000
    mock_config.retry_backoff_multiplier = 2.0
    
    with patch('services.ai_workflow_generator.config.ai_workflow_config', mock_config):
        with patch('services.ai_workflow_generator.gemini_service.genai'):
            from services.ai_workflow_generator.gemini_service import GeminiService
            
            service = GeminiService(api_key="test-key")
            
            response_text = '{"workflow": {"name": "test", "steps": {}}, "explanation": "Test workflow"}'
            parsed = service._parse_workflow_response(response_text)
            
            assert "workflow" in parsed
            assert "explanation" in parsed
            assert parsed["workflow"]["name"] == "test"


def test_workflow_response_parsing_direct():
    """Test parsing response that is directly a workflow."""
    mock_config = MagicMock()
    mock_config.gemini_api_key = "test-key"
    mock_config.gemini_model = "gemini-1.5-pro"
    mock_config.gemini_max_tokens = 8192
    mock_config.gemini_temperature = 0.7
    mock_config.max_retries = 3
    mock_config.initial_retry_delay_ms = 1000
    mock_config.max_retry_delay_ms = 30000
    mock_config.retry_backoff_multiplier = 2.0
    
    with patch('services.ai_workflow_generator.config.ai_workflow_config', mock_config):
        with patch('services.ai_workflow_generator.gemini_service.genai'):
            from services.ai_workflow_generator.gemini_service import GeminiService
            
            service = GeminiService(api_key="test-key")
            
            response_text = '{"name": "test", "steps": {}, "start_step": "step1"}'
            parsed = service._parse_workflow_response(response_text)
            
            assert "workflow" in parsed
            assert parsed["workflow"]["name"] == "test"
            assert parsed["workflow"]["start_step"] == "step1"


def test_workflow_response_parsing_markdown():
    """Test parsing workflow from markdown code block."""
    mock_config = MagicMock()
    mock_config.gemini_api_key = "test-key"
    mock_config.gemini_model = "gemini-1.5-pro"
    mock_config.gemini_max_tokens = 8192
    mock_config.gemini_temperature = 0.7
    mock_config.max_retries = 3
    mock_config.initial_retry_delay_ms = 1000
    mock_config.max_retry_delay_ms = 30000
    mock_config.retry_backoff_multiplier = 2.0
    
    with patch('services.ai_workflow_generator.config.ai_workflow_config', mock_config):
        with patch('services.ai_workflow_generator.gemini_service.genai'):
            from services.ai_workflow_generator.gemini_service import GeminiService
            
            service = GeminiService(api_key="test-key")
            
            response_text = '''Here's the workflow:
```json
{"workflow": {"name": "test", "steps": {}}, "explanation": "Test"}
```
'''
            parsed = service._parse_workflow_response(response_text)
            
            assert "workflow" in parsed
            assert parsed["workflow"]["name"] == "test"


def test_workflow_response_parsing_invalid():
    """Test parsing invalid workflow response."""
    mock_config = MagicMock()
    mock_config.gemini_api_key = "test-key"
    mock_config.gemini_model = "gemini-1.5-pro"
    mock_config.gemini_max_tokens = 8192
    mock_config.gemini_temperature = 0.7
    mock_config.max_retries = 3
    mock_config.initial_retry_delay_ms = 1000
    mock_config.max_retry_delay_ms = 30000
    mock_config.retry_backoff_multiplier = 2.0
    
    with patch('services.ai_workflow_generator.config.ai_workflow_config', mock_config):
        with patch('services.ai_workflow_generator.gemini_service.genai'):
            from services.ai_workflow_generator.gemini_service import GeminiService
            
            service = GeminiService(api_key="test-key")
            
            response_text = "This is not valid JSON at all"
            parsed = service._parse_workflow_response(response_text)
            
            assert parsed["workflow"] is None
            assert "error" in parsed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

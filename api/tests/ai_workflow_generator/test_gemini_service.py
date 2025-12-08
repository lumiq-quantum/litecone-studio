"""Unit tests for Gemini LLM service."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

# Mock the config before importing the service
with patch('api.services.ai_workflow_generator.config.AIWorkflowConfig') as mock_config:
    mock_config_instance = MagicMock()
    mock_config_instance.gemini_api_key = "test-key"
    mock_config_instance.gemini_model = "gemini-1.5-pro"
    mock_config_instance.gemini_max_tokens = 8192
    mock_config_instance.gemini_temperature = 0.7
    mock_config_instance.max_retries = 3
    mock_config_instance.initial_retry_delay_ms = 1000
    mock_config_instance.max_retry_delay_ms = 30000
    mock_config_instance.retry_backoff_multiplier = 2.0
    
    with patch('api.services.ai_workflow_generator.gemini_service.ai_workflow_config', mock_config_instance):
        from api.services.ai_workflow_generator.gemini_service import GeminiService, LLMResponse
        from api.services.ai_workflow_generator.agent_query import AgentMetadata
        from api.services.ai_workflow_generator.chat_session import Message


class TestGeminiService:
    """Test suite for GeminiService."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing."""
        return "test-api-key-12345"
    
    @pytest.fixture
    def sample_agents(self):
        """Sample agent metadata."""
        return [
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
                capabilities=["validation", "quality checks"],
                status="active"
            )
        ]
    
    @pytest.fixture
    def sample_messages(self):
        """Sample chat messages."""
        return [
            Message(
                id=uuid4(),
                role="user",
                content="Create a workflow to process data",
                timestamp=datetime.now(),
                metadata={}
            ),
            Message(
                id=uuid4(),
                role="assistant",
                content="I'll create a workflow for you",
                timestamp=datetime.now(),
                metadata={}
            )
        ]
    
    def test_initialization(self, mock_api_key):
        """Test GeminiService initialization."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai') as mock_genai:
            service = GeminiService(api_key=mock_api_key)
            
            assert service.api_key == mock_api_key
            assert service.model_name is not None
            assert service.max_retries >= 0
            mock_genai.configure.assert_called_once_with(api_key=mock_api_key)
    
    def test_calculate_retry_delay(self, mock_api_key):
        """Test exponential backoff calculation."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            # First retry should be initial delay
            delay_0 = service._calculate_retry_delay(0)
            assert delay_0 == service.initial_delay_ms / 1000.0
            
            # Second retry should be doubled
            delay_1 = service._calculate_retry_delay(1)
            expected = (service.initial_delay_ms * service.backoff_multiplier) / 1000.0
            assert delay_1 == expected
            
            # Should not exceed max delay
            delay_large = service._calculate_retry_delay(100)
            assert delay_large == service.max_delay_ms / 1000.0
    
    def test_count_tokens(self, mock_api_key):
        """Test token counting."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            # Mock the model's count_tokens method
            mock_result = Mock()
            mock_result.total_tokens = 10
            service.model.count_tokens = Mock(return_value=mock_result)
            
            text = "This is a test"
            count = service.count_tokens(text)
            
            assert count == 10
            service.model.count_tokens.assert_called_once_with(text)
    
    def test_count_tokens_fallback(self, mock_api_key):
        """Test token counting fallback when API fails."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            # Mock the model's count_tokens to raise an exception
            service.model.count_tokens = Mock(side_effect=Exception("API error"))
            
            text = "This is a test"
            count = service.count_tokens(text)
            
            # Should use fallback approximation (1 token ≈ 4 characters)
            expected = len(text) // 4
            assert count == expected
    
    def test_check_context_window(self, mock_api_key):
        """Test context window checking."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            service.max_tokens = 100
            
            # Mock count_tokens
            service.count_tokens = Mock(return_value=50)
            
            assert service._check_context_window("test") is True
            
            service.count_tokens = Mock(return_value=150)
            assert service._check_context_window("test") is False
    
    def test_format_agents_for_prompt(self, mock_api_key, sample_agents):
        """Test agent formatting for prompts."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            formatted = service._format_agents_for_prompt(sample_agents)
            
            assert "data-processor" in formatted
            assert "validator" in formatted
            assert "Processes data files" in formatted
            assert "data processing" in formatted
    
    def test_format_agents_empty_list(self, mock_api_key):
        """Test agent formatting with empty list."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            formatted = service._format_agents_for_prompt([])
            
            assert formatted == "No agents available"
    
    def test_build_workflow_generation_prompt(self, mock_api_key, sample_agents):
        """Test workflow generation prompt building."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            description = "Create a workflow to process and validate data"
            prompt = service._build_workflow_generation_prompt(description, sample_agents)
            
            assert description in prompt
            assert "data-processor" in prompt
            assert "validator" in prompt
            assert "workflow json" in prompt.lower()
            # Check for pattern examples
            assert "pattern" in prompt.lower()
    
    def test_parse_workflow_response_valid_json(self, mock_api_key):
        """Test parsing valid workflow response."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            response_text = '{"workflow": {"name": "test", "steps": {}}, "explanation": "Test workflow"}'
            parsed = service._parse_workflow_response(response_text)
            
            assert "workflow" in parsed
            assert "explanation" in parsed
            assert parsed["workflow"]["name"] == "test"
    
    def test_parse_workflow_response_direct_workflow(self, mock_api_key):
        """Test parsing response that is directly a workflow."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            response_text = '{"name": "test", "steps": {}, "start_step": "step1"}'
            parsed = service._parse_workflow_response(response_text)
            
            assert "workflow" in parsed
            assert parsed["workflow"]["name"] == "test"
    
    def test_parse_workflow_response_markdown(self, mock_api_key):
        """Test parsing workflow from markdown code block."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            response_text = '''Here's the workflow:
```json
{"workflow": {"name": "test", "steps": {}}, "explanation": "Test"}
```
'''
            parsed = service._parse_workflow_response(response_text)
            
            assert "workflow" in parsed
            assert parsed["workflow"]["name"] == "test"
    
    def test_parse_workflow_response_invalid(self, mock_api_key):
        """Test parsing invalid workflow response."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            response_text = "This is not valid JSON"
            parsed = service._parse_workflow_response(response_text)
            
            assert parsed["workflow"] is None
            assert "error" in parsed
    
    @pytest.mark.asyncio
    async def test_generate_workflow_success(self, mock_api_key, sample_agents):
        """Test successful workflow generation."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            # Mock the model response
            mock_response = Mock()
            mock_response.text = '{"workflow": {"name": "test", "steps": {}, "start_step": "step1"}, "explanation": "Generated workflow"}'
            mock_response.finish_reason = "STOP"
            mock_response.usage_metadata = Mock()
            mock_response.usage_metadata.prompt_token_count = 100
            mock_response.usage_metadata.candidates_token_count = 50
            mock_response.usage_metadata.total_token_count = 150
            
            service.model.generate_content = Mock(return_value=mock_response)
            service._check_context_window = Mock(return_value=True)
            
            result = await service.generate_workflow(
                "Create a test workflow",
                sample_agents
            )
            
            assert isinstance(result, LLMResponse)
            assert result.workflow_json is not None
            assert result.workflow_json["name"] == "test"
            assert result.finish_reason == "STOP"
            assert result.usage["total_tokens"] == 150
    
    @pytest.mark.asyncio
    async def test_generate_workflow_with_truncation(self, mock_api_key, sample_agents):
        """Test workflow generation with prompt truncation."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            # Mock the model response
            mock_response = Mock()
            mock_response.text = '{"workflow": {"name": "test", "steps": {}}, "explanation": "Generated"}'
            mock_response.finish_reason = "STOP"
            
            service.model.generate_content = Mock(return_value=mock_response)
            service._check_context_window = Mock(return_value=False)
            service._truncate_to_fit = Mock(return_value="truncated prompt")
            
            result = await service.generate_workflow(
                "Create a very long workflow description" * 1000,
                sample_agents
            )
            
            assert isinstance(result, LLMResponse)
            service._truncate_to_fit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_success(self, mock_api_key, sample_messages):
        """Test successful chat interaction."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            # Mock the model response
            mock_response = Mock()
            mock_response.text = "I can help you with that workflow modification."
            mock_response.finish_reason = "STOP"
            
            service.model.generate_content = Mock(return_value=mock_response)
            service._check_context_window = Mock(return_value=True)
            
            result = await service.chat(
                "Can you add a validation step?",
                sample_messages,
                {"name": "test", "steps": {}}
            )
            
            assert isinstance(result, LLMResponse)
            assert "help you" in result.content
            assert result.finish_reason == "STOP"
    
    @pytest.mark.asyncio
    async def test_explain_workflow_success(self, mock_api_key):
        """Test successful workflow explanation."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            # Mock the model response
            mock_response = Mock()
            mock_response.text = "This workflow processes data in two steps."
            
            service.model.generate_content = Mock(return_value=mock_response)
            service._check_context_window = Mock(return_value=True)
            
            workflow = {
                "name": "test-workflow",
                "steps": {
                    "step1": {"agent": "processor"},
                    "step2": {"agent": "validator"}
                }
            }
            
            result = await service.explain_workflow(workflow)
            
            assert isinstance(result, str)
            assert "workflow" in result.lower()
    
    @pytest.mark.asyncio
    async def test_call_with_retry_success_first_attempt(self, mock_api_key):
        """Test retry logic with successful first attempt."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            mock_func = Mock(return_value="success")
            
            result = await service._call_with_retry(mock_func, "arg1", kwarg1="value1")
            
            assert result == "success"
            mock_func.assert_called_once_with("arg1", kwarg1="value1")
    
    @pytest.mark.asyncio
    async def test_call_with_retry_success_after_retries(self, mock_api_key):
        """Test retry logic with success after retries."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            from google.api_core import exceptions as google_exceptions
            
            service = GeminiService(api_key=mock_api_key)
            service.max_retries = 2
            service.initial_delay_ms = 10  # Fast for testing
            
            # Fail twice, then succeed
            mock_func = Mock(side_effect=[
                google_exceptions.ResourceExhausted("Rate limit"),
                google_exceptions.ServiceUnavailable("Service down"),
                "success"
            ])
            
            result = await service._call_with_retry(mock_func)
            
            assert result == "success"
            assert mock_func.call_count == 3
    
    @pytest.mark.asyncio
    async def test_call_with_retry_exhausted(self, mock_api_key):
        """Test retry logic when all retries are exhausted."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            from google.api_core import exceptions as google_exceptions
            
            service = GeminiService(api_key=mock_api_key)
            service.max_retries = 2
            service.initial_delay_ms = 10  # Fast for testing
            
            # Always fail
            mock_func = Mock(side_effect=google_exceptions.ResourceExhausted("Rate limit"))
            
            with pytest.raises(google_exceptions.ResourceExhausted):
                await service._call_with_retry(mock_func)
            
            assert mock_func.call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_call_with_retry_non_retriable_error(self, mock_api_key):
        """Test retry logic with non-retriable error."""
        with patch('api.services.ai_workflow_generator.gemini_service.genai'):
            service = GeminiService(api_key=mock_api_key)
            
            # Non-retriable error
            mock_func = Mock(side_effect=ValueError("Invalid input"))
            
            with pytest.raises(ValueError):
                await service._call_with_retry(mock_func)
            
            # Should not retry
            mock_func.assert_called_once()

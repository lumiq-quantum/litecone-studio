"""Tests for AI workflow generator logging utilities."""

import pytest
import logging
import time
from unittest.mock import Mock, patch

from api.services.ai_workflow_generator.logging_utils import (
    OperationLogger,
    log_operation,
    log_function_call,
    LLMLogger,
    PerformanceLogger
)


class TestOperationLogger:
    """Test OperationLogger class."""
    
    def test_create_operation_logger(self):
        """Test creating an operation logger."""
        logger = OperationLogger("test_operation")
        
        assert logger.operation_name == "test_operation"
        assert logger.context == {}
        assert logger.start_time is None
    
    def test_operation_logger_with_context(self):
        """Test operation logger with context."""
        context = {"user_id": "123", "session_id": "abc"}
        logger = OperationLogger("test_operation", context)
        
        assert logger.context == context
    
    def test_start_operation(self):
        """Test starting an operation."""
        logger = OperationLogger("test_operation")
        logger.start()
        
        assert logger.start_time is not None
    
    def test_complete_operation(self):
        """Test completing an operation."""
        logger = OperationLogger("test_operation")
        logger.start()
        time.sleep(0.01)  # Small delay
        logger.complete()
        
        assert logger.end_time is not None
        assert logger.end_time > logger.start_time
    
    def test_error_operation(self):
        """Test logging an operation error."""
        logger = OperationLogger("test_operation")
        logger.start()
        
        error = ValueError("Test error")
        logger.error(error)
        
        assert logger.end_time is not None


class TestLogOperationContext:
    """Test log_operation context manager."""
    
    def test_log_operation_success(self):
        """Test successful operation logging."""
        with log_operation("test_operation") as op_logger:
            assert isinstance(op_logger, OperationLogger)
            assert op_logger.operation_name == "test_operation"
    
    def test_log_operation_with_context(self):
        """Test operation logging with context."""
        context = {"user_id": "123"}
        with log_operation("test_operation", context) as op_logger:
            assert op_logger.context == context
    
    def test_log_operation_with_error(self):
        """Test operation logging when error occurs."""
        with pytest.raises(ValueError):
            with log_operation("test_operation"):
                raise ValueError("Test error")


class TestLogFunctionCallDecorator:
    """Test log_function_call decorator."""
    
    def test_decorate_sync_function(self):
        """Test decorating a synchronous function."""
        @log_function_call("test_function")
        def test_func(x, y):
            return x + y
        
        result = test_func(2, 3)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_decorate_async_function(self):
        """Test decorating an asynchronous function."""
        @log_function_call("test_async_function")
        async def test_async_func(x, y):
            return x + y
        
        result = await test_async_func(2, 3)
        assert result == 5
    
    def test_decorator_uses_function_name(self):
        """Test decorator uses function name when operation name not provided."""
        @log_function_call()
        def my_function():
            return "result"
        
        result = my_function()
        assert result == "result"


class TestLLMLogger:
    """Test LLMLogger class."""
    
    def test_sanitize_short_prompt(self):
        """Test sanitizing a short prompt."""
        prompt = "Generate a workflow"
        sanitized = LLMLogger.sanitize_prompt(prompt)
        
        assert sanitized == prompt
    
    def test_sanitize_long_prompt(self):
        """Test sanitizing a long prompt."""
        prompt = "A" * 1000
        sanitized = LLMLogger.sanitize_prompt(prompt, max_length=100)
        
        assert len(sanitized) <= 120  # 100 + "... [truncated]"
        assert sanitized.endswith("... [truncated]")
    
    def test_sanitize_response(self):
        """Test sanitizing a response."""
        response = "B" * 1000
        sanitized = LLMLogger.sanitize_response(response, max_length=100)
        
        assert len(sanitized) <= 120
        assert sanitized.endswith("... [truncated]")
    
    def test_log_llm_call_success(self):
        """Test logging a successful LLM call."""
        # This test just ensures the method doesn't raise an error
        LLMLogger.log_llm_call(
            model="gemini-1.5-pro",
            prompt="Test prompt",
            response="Test response",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            duration_ms=150.5
        )
    
    def test_log_llm_call_failure(self):
        """Test logging a failed LLM call."""
        LLMLogger.log_llm_call(
            model="gemini-1.5-pro",
            prompt="Test prompt",
            error="Rate limit exceeded"
        )


class TestPerformanceLogger:
    """Test PerformanceLogger class."""
    
    def test_log_metric(self):
        """Test logging a performance metric."""
        # This test just ensures the method doesn't raise an error
        PerformanceLogger.log_metric(
            metric_name="test_metric",
            value=123.45,
            unit="ms",
            context={"operation": "test"}
        )
    
    def test_log_workflow_generation_metrics(self):
        """Test logging workflow generation metrics."""
        # This test just ensures the method doesn't raise an error
        PerformanceLogger.log_workflow_generation_metrics(
            total_duration_ms=1000.0,
            llm_duration_ms=800.0,
            validation_duration_ms=150.0,
            agent_query_duration_ms=50.0,
            workflow_size_bytes=2048,
            num_steps=5,
            num_agents=3
        )


class TestLoggingIntegration:
    """Test logging integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_nested_operations(self):
        """Test nested operation logging."""
        with log_operation("outer_operation") as outer:
            outer.log("info", "Starting outer operation")
            
            with log_operation("inner_operation") as inner:
                inner.log("info", "Starting inner operation")
                time.sleep(0.01)
            
            outer.log("info", "Completed inner operation")
    
    def test_operation_with_custom_logging(self):
        """Test operation with custom log messages."""
        with log_operation("custom_operation") as op_logger:
            op_logger.log("info", "Custom info message", extra_field="value")
            op_logger.log("warning", "Custom warning message")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

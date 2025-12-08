"""Logging utilities for AI workflow generator."""

import logging
import json
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class OperationLogger:
    """Logger for tracking operations with structured logging."""
    
    def __init__(self, operation_name: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize operation logger.
        
        Args:
            operation_name: Name of the operation being logged
            context: Additional context to include in all logs
        """
        self.operation_name = operation_name
        self.context = context or {}
        self.start_time = None
        self.end_time = None
    
    def start(self, **kwargs):
        """Log operation start."""
        self.start_time = time.time()
        log_data = {
            "event_type": "operation_started",
            "operation": self.operation_name,
            "timestamp": datetime.utcnow().isoformat(),
            **self.context,
            **kwargs
        }
        logger.info(f"Operation started: {self.operation_name}", extra=log_data)
    
    def complete(self, **kwargs):
        """Log operation completion."""
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000 if self.start_time else 0
        
        log_data = {
            "event_type": "operation_completed",
            "operation": self.operation_name,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.utcnow().isoformat(),
            **self.context,
            **kwargs
        }
        logger.info(
            f"Operation completed: {self.operation_name} ({duration_ms:.2f}ms)",
            extra=log_data
        )
    
    def error(self, error: Exception, **kwargs):
        """Log operation error."""
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000 if self.start_time else 0
        
        log_data = {
            "event_type": "operation_failed",
            "operation": self.operation_name,
            "duration_ms": round(duration_ms, 2),
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat(),
            **self.context,
            **kwargs
        }
        logger.error(
            f"Operation failed: {self.operation_name} - {str(error)}",
            extra=log_data,
            exc_info=True
        )
    
    def log(self, level: str, message: str, **kwargs):
        """Log a message at specified level."""
        log_data = {
            "operation": self.operation_name,
            "timestamp": datetime.utcnow().isoformat(),
            **self.context,
            **kwargs
        }
        
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message, extra=log_data)


@contextmanager
def log_operation(operation_name: str, context: Optional[Dict[str, Any]] = None):
    """
    Context manager for logging operations.
    
    Usage:
        with log_operation("generate_workflow", {"user_id": "123"}):
            # Do work
            pass
    
    Args:
        operation_name: Name of the operation
        context: Additional context
        
    Yields:
        OperationLogger instance
    """
    op_logger = OperationLogger(operation_name, context)
    op_logger.start()
    
    try:
        yield op_logger
        op_logger.complete()
    except Exception as e:
        op_logger.error(e)
        raise


def log_function_call(operation_name: Optional[str] = None):
    """
    Decorator for logging function calls.
    
    Usage:
        @log_function_call("my_operation")
        async def my_function(arg1, arg2):
            pass
    
    Args:
        operation_name: Optional operation name (uses function name if not provided)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            op_logger = OperationLogger(op_name)
            op_logger.start()
            
            try:
                result = await func(*args, **kwargs)
                op_logger.complete()
                return result
            except Exception as e:
                op_logger.error(e)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            op_logger = OperationLogger(op_name)
            op_logger.start()
            
            try:
                result = func(*args, **kwargs)
                op_logger.complete()
                return result
            except Exception as e:
                op_logger.error(e)
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class LLMLogger:
    """Logger for LLM interactions with sanitization."""
    
    @staticmethod
    def sanitize_prompt(prompt: str, max_length: int = 500) -> str:
        """
        Sanitize prompt for logging.
        
        Args:
            prompt: Prompt to sanitize
            max_length: Maximum length to log
            
        Returns:
            Sanitized prompt
        """
        # Truncate if too long
        if len(prompt) > max_length:
            return prompt[:max_length] + "... [truncated]"
        return prompt
    
    @staticmethod
    def sanitize_response(response: str, max_length: int = 500) -> str:
        """
        Sanitize response for logging.
        
        Args:
            response: Response to sanitize
            max_length: Maximum length to log
            
        Returns:
            Sanitized response
        """
        # Truncate if too long
        if len(response) > max_length:
            return response[:max_length] + "... [truncated]"
        return response
    
    @staticmethod
    def log_llm_call(
        model: str,
        prompt: str,
        response: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ):
        """
        Log an LLM API call.
        
        Args:
            model: Model name
            prompt: Prompt sent to LLM
            response: Response from LLM
            usage: Token usage information
            duration_ms: Call duration in milliseconds
            error: Error message if call failed
        """
        log_data = {
            "event_type": "llm_call",
            "model": model,
            "prompt_preview": LLMLogger.sanitize_prompt(prompt),
            "prompt_length": len(prompt),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if response:
            log_data["response_preview"] = LLMLogger.sanitize_response(response)
            log_data["response_length"] = len(response)
        
        if usage:
            log_data["usage"] = usage
        
        if duration_ms is not None:
            log_data["duration_ms"] = round(duration_ms, 2)
        
        if error:
            log_data["error"] = error
            logger.error(f"LLM call failed: {error}", extra=log_data)
        else:
            logger.info(f"LLM call completed: {model}", extra=log_data)


class PerformanceLogger:
    """Logger for performance metrics."""
    
    @staticmethod
    def log_metric(
        metric_name: str,
        value: float,
        unit: str = "ms",
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            context: Additional context
        """
        log_data = {
            "event_type": "performance_metric",
            "metric_name": metric_name,
            "value": round(value, 2),
            "unit": unit,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if context:
            log_data.update(context)
        
        logger.info(f"Performance metric: {metric_name}={value}{unit}", extra=log_data)
    
    @staticmethod
    def log_workflow_generation_metrics(
        total_duration_ms: float,
        llm_duration_ms: float,
        validation_duration_ms: float,
        agent_query_duration_ms: float,
        workflow_size_bytes: int,
        num_steps: int,
        num_agents: int
    ):
        """
        Log comprehensive workflow generation metrics.
        
        Args:
            total_duration_ms: Total generation time
            llm_duration_ms: Time spent in LLM calls
            validation_duration_ms: Time spent in validation
            agent_query_duration_ms: Time spent querying agents
            workflow_size_bytes: Size of generated workflow
            num_steps: Number of workflow steps
            num_agents: Number of agents used
        """
        log_data = {
            "event_type": "workflow_generation_metrics",
            "total_duration_ms": round(total_duration_ms, 2),
            "llm_duration_ms": round(llm_duration_ms, 2),
            "validation_duration_ms": round(validation_duration_ms, 2),
            "agent_query_duration_ms": round(agent_query_duration_ms, 2),
            "workflow_size_bytes": workflow_size_bytes,
            "num_steps": num_steps,
            "num_agents": num_agents,
            "llm_percentage": round((llm_duration_ms / total_duration_ms) * 100, 1) if total_duration_ms > 0 else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Workflow generation metrics: {total_duration_ms:.2f}ms total, "
            f"{num_steps} steps, {num_agents} agents",
            extra=log_data
        )


def configure_logging(log_level: str = "INFO", log_format: str = "json"):
    """
    Configure logging for the AI workflow generator.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json or text)
    """
    # Set log level
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    
    # Configure format
    if log_format == "json":
        # JSON formatter for structured logging
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage()
                }
                
                # Add extra fields
                if hasattr(record, "__dict__"):
                    for key, value in record.__dict__.items():
                        if key not in ["name", "msg", "args", "created", "filename", "funcName",
                                      "levelname", "levelno", "lineno", "module", "msecs",
                                      "message", "pathname", "process", "processName",
                                      "relativeCreated", "thread", "threadName", "exc_info",
                                      "exc_text", "stack_info"]:
                            log_data[key] = value
                
                return json.dumps(log_data)
        
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logging.root.handlers = [handler]
    
    logger.info(f"Logging configured: level={log_level}, format={log_format}")

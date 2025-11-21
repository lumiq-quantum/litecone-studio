"""Structured logging utilities with JSON formatting and correlation ID support."""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable to store correlation ID for the current execution context
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    
    Each log record is formatted as a JSON object with standard fields:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logger: Logger name
    - message: Log message
    - correlation_id: Correlation ID from context (if available)
    - Additional fields from the 'extra' parameter
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a JSON string.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON-formatted log string
        """
        # Build base log entry
        log_entry: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add correlation ID from context if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_entry['correlation_id'] = correlation_id
        
        # Add extra fields from the log record
        # These are fields passed via the 'extra' parameter in logging calls
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                # Skip standard logging fields
                if key not in [
                    'name', 'msg', 'args', 'created', 'filename', 'funcName',
                    'levelname', 'levelno', 'lineno', 'module', 'msecs',
                    'message', 'pathname', 'process', 'processName',
                    'relativeCreated', 'thread', 'threadName', 'exc_info',
                    'exc_text', 'stack_info', 'taskName'
                ]:
                    # Add custom fields
                    log_entry[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add stack info if present
        if record.stack_info:
            log_entry['stack_info'] = self.formatStack(record.stack_info)
        
        # Serialize to JSON
        try:
            return json.dumps(log_entry, default=str)
        except (TypeError, ValueError) as e:
            # Fallback to simple format if JSON serialization fails
            return json.dumps({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': 'ERROR',
                'logger': 'logging',
                'message': f'Failed to serialize log entry: {e}',
                'original_message': str(record.getMessage())
            })


class TextFormatter(logging.Formatter):
    """
    Custom formatter that outputs human-readable text logs with correlation ID.
    
    Format: timestamp - logger - level - [correlation_id] - message
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a human-readable string.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log string
        """
        # Get correlation ID from context
        correlation_id = correlation_id_var.get()
        
        # Build the log message
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        base_msg = f"{timestamp} - {record.name} - {record.levelname} - "
        
        if correlation_id:
            base_msg += f"[{correlation_id}] - "
        
        base_msg += record.getMessage()
        
        # Add exception info if present
        if record.exc_info:
            base_msg += "\n" + self.formatException(record.exc_info)
        
        return base_msg


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    logger_name: Optional[str] = None
) -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ('json' or 'text')
        logger_name: Optional logger name. If None, configures root logger
        
    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Set formatter based on format type
    if log_format.lower() == 'json':
        formatter = StructuredFormatter()
    else:
        formatter = TextFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to avoid duplicate logs
    if logger_name:
        logger.propagate = False
    
    return logger


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID for the current execution context.
    
    This correlation ID will be automatically included in all log messages
    within the current async context.
    
    Args:
        correlation_id: The correlation ID to set
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get the correlation ID from the current execution context.
    
    Returns:
        The correlation ID if set, None otherwise
    """
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """
    Clear the correlation ID from the current execution context.
    """
    correlation_id_var.set(None)


def log_event(
    logger: logging.Logger,
    level: str,
    event_type: str,
    message: str,
    **kwargs
) -> None:
    """
    Log a structured event with additional metadata.
    
    This is a convenience function for logging key events with consistent structure.
    
    Args:
        logger: Logger instance to use
        level: Log level (debug, info, warning, error, critical)
        event_type: Type of event (e.g., 'step_start', 'step_complete', 'agent_call')
        message: Human-readable message
        **kwargs: Additional fields to include in the log entry
    """
    # Extract exc_info if present (it's a reserved logging parameter)
    exc_info = kwargs.pop('exc_info', False)
    
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra={'event_type': event_type, **kwargs}, exc_info=exc_info)

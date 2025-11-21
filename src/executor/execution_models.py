"""Execution models and constants shared across executors."""

from typing import Dict, Any, Optional
from datetime import datetime


class ExecutionStatus:
    """Constants for execution status values."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StepResult:
    """Container for step execution results."""
    
    def __init__(
        self,
        step_id: str,
        status: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        self.step_id = step_id
        self.status = status
        self.input_data = input_data
        self.output_data = output_data
        self.error_message = error_message
        self.timestamp = datetime.utcnow()

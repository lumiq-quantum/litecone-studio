"""Pydantic models for Kafka message schemas."""

from typing import Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AgentTask(BaseModel):
    """Message schema for agent invocation tasks published to orchestrator.tasks.http."""
    
    run_id: str = Field(..., description="Unique identifier for the workflow run")
    task_id: str = Field(..., description="Unique identifier for this specific task")
    agent_name: str = Field(..., description="Name of the agent to invoke")
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full input payload for the agent"
    )
    correlation_id: str = Field(..., description="Correlation ID for tracking request-response pairs")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp when the task was created"
    )
    
    def to_json(self) -> str:
        """Serialize the message to JSON string."""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentTask':
        """Deserialize the message from JSON string."""
        return cls.model_validate_json(json_str)


class AgentResult(BaseModel):
    """Message schema for agent execution results published to results.topic."""
    
    run_id: str = Field(..., description="Unique identifier for the workflow run")
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Execution status: 'SUCCESS' or 'FAILURE'")
    output_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Full output payload from the agent (None if failed)"
    )
    correlation_id: str = Field(..., description="Correlation ID matching the original task")
    error_message: Optional[str] = Field(
        None,
        description="Error message if status is FAILURE"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp when the result was created"
    )
    
    def to_json(self) -> str:
        """Serialize the message to JSON string."""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentResult':
        """Deserialize the message from JSON string."""
        return cls.model_validate_json(json_str)


class MonitoringUpdate(BaseModel):
    """Message schema for workflow monitoring updates published to workflow.monitoring.updates."""
    
    run_id: str = Field(..., description="Unique identifier for the workflow run")
    step_id: str = Field(..., description="Unique identifier for the workflow step")
    step_name: str = Field(..., description="Human-readable name of the step")
    status: str = Field(
        ...,
        description="Step status: 'RUNNING', 'COMPLETED', or 'FAILED'"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp when the update was created"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the step execution"
    )
    
    def to_json(self) -> str:
        """Serialize the message to JSON string."""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MonitoringUpdate':
        """Deserialize the message from JSON string."""
        return cls.model_validate_json(json_str)

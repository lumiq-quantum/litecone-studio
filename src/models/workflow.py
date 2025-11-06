"""Pydantic models for workflow plan structure."""

from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class WorkflowStep(BaseModel):
    """Model representing a single step in a workflow plan."""
    
    id: str = Field(..., description="Unique identifier for the step")
    agent_name: str = Field(..., description="Name of the agent to execute this step")
    next_step: Optional[str] = Field(None, description="ID of the next step in sequence, null for final step")
    input_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of input field names to variable references (e.g., ${workflow.input.field})"
    )
    
    @field_validator('id', 'agent_name')
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Validate that string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator('input_mapping')
    @classmethod
    def validate_input_mapping(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate that input_mapping values are strings."""
        for key, value in v.items():
            if not isinstance(value, str):
                raise ValueError(f"Input mapping value for '{key}' must be a string")
        return v


class WorkflowPlan(BaseModel):
    """Model representing a complete workflow plan."""
    
    workflow_id: str = Field(..., description="Unique identifier for the workflow")
    name: str = Field(..., description="Human-readable name of the workflow")
    version: str = Field(..., description="Version of the workflow plan")
    start_step: str = Field(..., description="ID of the first step to execute")
    steps: Dict[str, WorkflowStep] = Field(
        ...,
        description="Dictionary mapping step IDs to WorkflowStep objects"
    )
    
    @field_validator('workflow_id', 'name', 'version', 'start_step')
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Validate that string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator('steps')
    @classmethod
    def validate_steps_not_empty(cls, v: Dict[str, WorkflowStep]) -> Dict[str, WorkflowStep]:
        """Validate that steps dictionary is not empty."""
        if not v:
            raise ValueError("Workflow must contain at least one step")
        return v
    
    @model_validator(mode='after')
    def validate_workflow_structure(self) -> 'WorkflowPlan':
        """Validate the overall workflow structure."""
        # Validate that start_step exists in steps
        if self.start_step not in self.steps:
            raise ValueError(f"start_step '{self.start_step}' not found in steps dictionary")
        
        # Validate that all step IDs match their dictionary keys
        for step_id, step in self.steps.items():
            if step.id != step_id:
                raise ValueError(
                    f"Step ID mismatch: dictionary key '{step_id}' does not match step.id '{step.id}'"
                )
        
        # Validate that all next_step references point to valid steps
        for step_id, step in self.steps.items():
            if step.next_step is not None and step.next_step not in self.steps:
                raise ValueError(
                    f"Step '{step_id}' references non-existent next_step '{step.next_step}'"
                )
        
        # Validate that there are no circular references
        self._validate_no_cycles()
        
        # Validate that there is at least one terminal step (next_step is None)
        terminal_steps = [step_id for step_id, step in self.steps.items() if step.next_step is None]
        if not terminal_steps:
            raise ValueError("Workflow must have at least one terminal step (with next_step=None)")
        
        return self
    
    def _validate_no_cycles(self) -> None:
        """Validate that the workflow does not contain circular references."""
        visited = set()
        current_step = self.start_step
        
        while current_step is not None:
            if current_step in visited:
                raise ValueError(f"Circular reference detected in workflow at step '{current_step}'")
            
            visited.add(current_step)
            step = self.steps[current_step]
            current_step = step.next_step

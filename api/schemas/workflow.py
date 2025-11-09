"""
Workflow schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class WorkflowStepSchema(BaseModel):
    """Schema for a single workflow step definition."""
    id: str = Field(..., min_length=1, max_length=255, description="Unique step identifier")
    agent_name: str = Field(..., min_length=1, max_length=255, description="Name of the agent to invoke")
    next_step: Optional[str] = Field(None, description="ID of the next step, or null if final step")
    input_mapping: Dict[str, Any] = Field(..., description="Map of input field names to value expressions")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate step ID format."""
        if not v.strip():
            raise ValueError("Step ID cannot be empty or whitespace")
        # Allow alphanumeric, hyphens, underscores
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError("Step ID can only contain alphanumeric characters, hyphens, and underscores")
        return v

    @field_validator('agent_name')
    @classmethod
    def validate_agent_name(cls, v: str) -> str:
        """Validate agent name is not empty."""
        if not v.strip():
            raise ValueError("Agent name cannot be empty or whitespace")
        return v

    @field_validator('input_mapping')
    @classmethod
    def validate_input_mapping(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input mapping is not empty."""
        if not v:
            raise ValueError("Input mapping cannot be empty")
        return v


class WorkflowCreate(BaseModel):
    """Schema for creating a new workflow definition."""
    name: str = Field(..., min_length=1, max_length=255, description="Unique workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    start_step: str = Field(..., min_length=1, description="ID of the first step to execute")
    steps: Dict[str, WorkflowStepSchema] = Field(..., min_items=1, description="Map of step IDs to step definitions")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate workflow name is not empty."""
        if not v.strip():
            raise ValueError("Workflow name cannot be empty or whitespace")
        return v

    @field_validator('start_step')
    @classmethod
    def validate_start_step(cls, v: str) -> str:
        """Validate start_step is not empty."""
        if not v.strip():
            raise ValueError("Start step cannot be empty or whitespace")
        return v

    @model_validator(mode='after')
    def validate_workflow_structure(self) -> 'WorkflowCreate':
        """Validate the complete workflow structure."""
        # Validate start_step exists in steps
        if self.start_step not in self.steps:
            raise ValueError(f"start_step '{self.start_step}' not found in steps")
        
        # Validate each step's ID matches its key in the steps dict
        for step_key, step in self.steps.items():
            if step.id != step_key:
                raise ValueError(
                    f"Step ID mismatch: key '{step_key}' does not match step.id '{step.id}'"
                )
        
        # Validate next_step references
        for step_key, step in self.steps.items():
            if step.next_step is not None and step.next_step not in self.steps:
                raise ValueError(
                    f"Step '{step_key}' references non-existent next_step '{step.next_step}'"
                )
        
        # Validate no circular references (detect cycles)
        self._validate_no_cycles()
        
        # Validate all steps are reachable from start_step
        self._validate_all_steps_reachable()
        
        return self

    def _validate_no_cycles(self) -> None:
        """Detect circular references in the workflow."""
        visited = set()
        current_path = set()
        
        def has_cycle(step_id: str) -> bool:
            """DFS to detect cycles."""
            if step_id in current_path:
                return True
            if step_id in visited:
                return False
            
            visited.add(step_id)
            current_path.add(step_id)
            
            step = self.steps.get(step_id)
            if step and step.next_step:
                if has_cycle(step.next_step):
                    return True
            
            current_path.remove(step_id)
            return False
        
        # Check for cycles starting from each step
        for step_id in self.steps:
            visited.clear()
            current_path.clear()
            if has_cycle(step_id):
                raise ValueError(f"Circular reference detected in workflow at step '{step_id}'")

    def _validate_all_steps_reachable(self) -> None:
        """Validate all steps are reachable from start_step."""
        reachable = set()
        current = self.start_step
        
        # Follow the chain from start_step
        while current and current not in reachable:
            reachable.add(current)
            step = self.steps.get(current)
            current = step.next_step if step else None
        
        # Check if any steps are unreachable
        unreachable = set(self.steps.keys()) - reachable
        if unreachable:
            raise ValueError(
                f"Unreachable steps detected: {', '.join(sorted(unreachable))}. "
                f"All steps must be reachable from start_step '{self.start_step}'"
            )


class WorkflowUpdate(BaseModel):
    """Schema for updating an existing workflow definition."""
    description: Optional[str] = Field(None, description="Workflow description")
    start_step: Optional[str] = Field(None, min_length=1, description="ID of the first step to execute")
    steps: Optional[Dict[str, WorkflowStepSchema]] = Field(None, min_items=1, description="Map of step IDs to step definitions")
    status: Optional[str] = Field(None, description="Workflow status")

    @field_validator('start_step')
    @classmethod
    def validate_start_step(cls, v: Optional[str]) -> Optional[str]:
        """Validate start_step is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("Start step cannot be empty or whitespace")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status is one of the allowed values."""
        if v is None:
            return v
        allowed_statuses = {'active', 'inactive'}
        if v.lower() not in allowed_statuses:
            raise ValueError(f"status must be one of: {', '.join(allowed_statuses)}")
        return v.lower()

    @model_validator(mode='after')
    def validate_workflow_structure(self) -> 'WorkflowUpdate':
        """Validate the workflow structure if steps are provided."""
        # Only validate if both start_step and steps are provided
        if self.start_step is not None and self.steps is not None:
            # Validate start_step exists in steps
            if self.start_step not in self.steps:
                raise ValueError(f"start_step '{self.start_step}' not found in steps")
            
            # Validate each step's ID matches its key
            for step_key, step in self.steps.items():
                if step.id != step_key:
                    raise ValueError(
                        f"Step ID mismatch: key '{step_key}' does not match step.id '{step.id}'"
                    )
            
            # Validate next_step references
            for step_key, step in self.steps.items():
                if step.next_step is not None and step.next_step not in self.steps:
                    raise ValueError(
                        f"Step '{step_key}' references non-existent next_step '{step.next_step}'"
                    )
            
            # Validate no circular references
            self._validate_no_cycles()
            
            # Validate all steps are reachable
            self._validate_all_steps_reachable()
        
        return self

    def _validate_no_cycles(self) -> None:
        """Detect circular references in the workflow."""
        if not self.steps:
            return
        
        visited = set()
        current_path = set()
        
        def has_cycle(step_id: str) -> bool:
            """DFS to detect cycles."""
            if step_id in current_path:
                return True
            if step_id in visited:
                return False
            
            visited.add(step_id)
            current_path.add(step_id)
            
            step = self.steps.get(step_id)
            if step and step.next_step:
                if has_cycle(step.next_step):
                    return True
            
            current_path.remove(step_id)
            return False
        
        # Check for cycles starting from each step
        for step_id in self.steps:
            visited.clear()
            current_path.clear()
            if has_cycle(step_id):
                raise ValueError(f"Circular reference detected in workflow at step '{step_id}'")

    def _validate_all_steps_reachable(self) -> None:
        """Validate all steps are reachable from start_step."""
        if not self.steps or not self.start_step:
            return
        
        reachable = set()
        current = self.start_step
        
        # Follow the chain from start_step
        while current and current not in reachable:
            reachable.add(current)
            step = self.steps.get(current)
            current = step.next_step if step else None
        
        # Check if any steps are unreachable
        unreachable = set(self.steps.keys()) - reachable
        if unreachable:
            raise ValueError(
                f"Unreachable steps detected: {', '.join(sorted(unreachable))}. "
                f"All steps must be reachable from start_step '{self.start_step}'"
            )


class WorkflowResponse(BaseModel):
    """Schema for workflow response."""
    id: UUID = Field(..., description="Workflow unique identifier")
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    version: int = Field(..., description="Workflow version number")
    workflow_data: Dict[str, Any] = Field(..., description="Complete workflow definition")
    status: str = Field(..., description="Workflow status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="User who created the workflow")
    updated_by: Optional[str] = Field(None, description="User who last updated the workflow")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "data-processing-pipeline",
                "description": "ETL pipeline for data processing",
                "version": 1,
                "workflow_data": {
                    "workflow_id": "wf-data-pipeline-001",
                    "name": "data-processing-pipeline",
                    "version": "1.0.0",
                    "start_step": "extract",
                    "steps": {
                        "extract": {
                            "id": "extract",
                            "agent_name": "DataExtractorAgent",
                            "next_step": "transform",
                            "input_mapping": {
                                "source_url": "${workflow.input.data_source}",
                                "format": "json"
                            }
                        },
                        "transform": {
                            "id": "transform",
                            "agent_name": "DataTransformerAgent",
                            "next_step": None,
                            "input_mapping": {
                                "raw_data": "${extract.output.data}",
                                "transformations": ["normalize", "deduplicate"]
                            }
                        }
                    }
                },
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "admin",
                "updated_by": "admin"
            }
        }
    }

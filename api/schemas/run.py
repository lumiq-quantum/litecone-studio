"""
Run schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class WorkflowExecuteRequest(BaseModel):
    """Schema for triggering workflow execution."""
    input_data: Dict[str, Any] = Field(..., description="Input data for the workflow execution")

    @field_validator('input_data')
    @classmethod
    def validate_input_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data is not None."""
        if v is None:
            raise ValueError("input_data cannot be null")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "input_data": {
                    "data_source": "https://api.example.com/data",
                    "output_format": "json",
                    "filters": {
                        "date_range": "2024-01-01:2024-12-31",
                        "status": "active"
                    }
                }
            }
        }
    }


class WorkflowRetryRequest(BaseModel):
    """Schema for retrying a failed workflow execution."""
    resume_from_step: Optional[str] = Field(
        None,
        description="Optional step ID to resume from. If not provided, resumes from last incomplete step"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "resume_from_step": "transform"
            }
        }
    }


class WorkflowCancelRequest(BaseModel):
    """Schema for cancelling a running workflow."""
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional reason for cancellation"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "reason": "User requested cancellation due to incorrect input data"
            }
        }
    }


class RunResponse(BaseModel):
    """Schema for workflow run response."""
    id: str = Field(..., description="Unique run identifier (run_id)")
    run_id: str = Field(..., description="Unique run identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    workflow_name: str = Field(..., description="Workflow name")
    workflow_definition_id: Optional[str] = Field(None, description="UUID reference to workflow definition")
    status: str = Field(..., description="Run status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input data provided for execution")
    triggered_by: Optional[str] = Field(None, description="User or system that triggered the execution")
    created_at: datetime = Field(..., description="Run creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Run completion timestamp")
    cancelled_at: Optional[datetime] = Field(None, description="Run cancellation timestamp")
    cancelled_by: Optional[str] = Field(None, description="User who cancelled the run")
    error_message: Optional[str] = Field(None, description="Error message if run failed")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "run-123e4567-e89b-12d3-a456-426614174000",
                "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
                "workflow_id": "wf-data-pipeline-001",
                "workflow_name": "data-processing-pipeline",
                "workflow_definition_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "COMPLETED",
                "input_data": {
                    "data_source": "https://api.example.com/data",
                    "output_format": "json"
                },
                "triggered_by": "user@example.com",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:05:00Z",
                "completed_at": "2024-01-01T10:05:00Z",
                "cancelled_at": None,
                "cancelled_by": None,
                "error_message": None
            }
        }
    }


class StepExecutionResponse(BaseModel):
    """Schema for step execution response."""
    id: str = Field(..., description="Unique step execution identifier")
    run_id: str = Field(..., description="Parent workflow run identifier")
    step_id: str = Field(..., description="Step identifier from workflow definition")
    step_name: str = Field(..., description="Step name")
    agent_name: str = Field(..., description="Agent that executed the step")
    status: str = Field(..., description="Step status (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED)")
    input_data: Dict[str, Any] = Field(..., description="Input data for the step")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output data from the step")
    started_at: datetime = Field(..., description="Step start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Step completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if step failed")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "step-exec-123e4567-e89b-12d3-a456-426614174000",
                "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
                "step_id": "extract",
                "step_name": "extract",
                "agent_name": "DataExtractorAgent",
                "status": "COMPLETED",
                "input_data": {
                    "source_url": "https://api.example.com/data",
                    "format": "json"
                },
                "output_data": {
                    "data": [{"id": 1, "value": "test"}],
                    "record_count": 1
                },
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:01:00Z",
                "error_message": None
            }
        }
    }


class RunListResponse(BaseModel):
    """Schema for paginated list of workflow runs."""
    items: list[RunResponse] = Field(..., description="List of workflow runs")
    total: int = Field(..., description="Total number of runs matching the query")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "id": "run-123e4567-e89b-12d3-a456-426614174000",
                        "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
                        "workflow_id": "wf-data-pipeline-001",
                        "workflow_name": "data-processing-pipeline",
                        "workflow_definition_id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "COMPLETED",
                        "input_data": {"data_source": "https://api.example.com/data"},
                        "triggered_by": "user@example.com",
                        "created_at": "2024-01-01T10:00:00Z",
                        "updated_at": "2024-01-01T10:05:00Z",
                        "completed_at": "2024-01-01T10:05:00Z",
                        "cancelled_at": None,
                        "cancelled_by": None,
                        "error_message": None
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }
    }


class StepExecutionListResponse(BaseModel):
    """Schema for list of step executions within a run."""
    items: list[StepExecutionResponse] = Field(..., description="List of step executions")
    total: int = Field(..., description="Total number of steps in the run")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "id": "step-exec-123e4567-e89b-12d3-a456-426614174000",
                        "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
                        "step_id": "extract",
                        "step_name": "extract",
                        "agent_name": "DataExtractorAgent",
                        "status": "COMPLETED",
                        "input_data": {"source_url": "https://api.example.com/data"},
                        "output_data": {"data": [{"id": 1}], "record_count": 1},
                        "started_at": "2024-01-01T10:00:00Z",
                        "completed_at": "2024-01-01T10:01:00Z",
                        "error_message": None
                    }
                ],
                "total": 2
            }
        }
    }

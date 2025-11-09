"""
Run management API routes.

This module provides REST endpoints for monitoring and managing workflow runs.
Runs represent specific execution instances of workflow definitions.

Requirements:
- 3.2: Get run details via GET /api/v1/runs/{run_id}
- 3.3: Retry failed run via POST /api/v1/runs/{run_id}/retry
- 3.4: Cancel running workflow via POST /api/v1/runs/{run_id}/cancel
- 4.1: List runs via GET /api/v1/runs with pagination and filtering
- 4.2: Get run details via GET /api/v1/runs/{run_id}
- 4.3: Get step executions via GET /api/v1/runs/{run_id}/steps
- 4.4: Get run logs via GET /api/v1/runs/{run_id}/logs (placeholder)
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.services.execution import ExecutionService
from api.schemas.run import (
    RunResponse,
    StepExecutionResponse,
    WorkflowRetryRequest,
    WorkflowCancelRequest
)
from api.schemas.common import PaginatedResponse, MessageResponse


# Create router with prefix and tags
router = APIRouter(
    prefix="/runs",
    tags=["Runs"]
)


@router.get(
    "",
    response_model=PaginatedResponse[RunResponse],
    summary="List all workflow runs",
    description="Retrieve a paginated list of workflow runs with optional filtering by status, workflow, and date range.",
    responses={
        200: {
            "description": "List of runs retrieved successfully",
            "model": PaginatedResponse[RunResponse]
        }
    }
)
async def list_runs(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of items per page"),
    status: Optional[str] = Query(
        default=None,
        description="Filter by run status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)"
    ),
    workflow_id: Optional[str] = Query(
        default=None,
        description="Filter by workflow_id (e.g., 'wf-data-pipeline-001')"
    ),
    workflow_definition_id: Optional[str] = Query(
        default=None,
        description="Filter by workflow_definition_id (UUID reference)"
    ),
    created_after: Optional[datetime] = Query(
        default=None,
        description="Filter runs created after this timestamp (ISO 8601 format)"
    ),
    created_before: Optional[datetime] = Query(
        default=None,
        description="Filter runs created before this timestamp (ISO 8601 format)"
    ),
    sort_by: str = Query(
        default="created_at",
        description="Field to sort by (created_at, updated_at, completed_at, status)"
    ),
    sort_order: str = Query(
        default="desc",
        description="Sort order (asc or desc)"
    ),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[RunResponse]:
    """
    List workflow runs with pagination, filtering, and sorting.
    
    This endpoint returns a paginated list of workflow runs. You can filter by:
    - Status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
    - Workflow ID (the workflow identifier from the workflow definition)
    - Workflow Definition ID (UUID reference to the workflow definition)
    - Date range (created_after and created_before)
    
    Results can be sorted by various fields and paginated for efficient retrieval.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        status: Optional status filter
        workflow_id: Optional workflow_id filter
        workflow_definition_id: Optional workflow_definition_id filter (UUID)
        created_after: Optional filter for runs created after this datetime
        created_before: Optional filter for runs created before this datetime
        sort_by: Field to sort by (created_at, updated_at, completed_at, status)
        sort_order: Sort order (asc or desc)
        db: Database session (injected)
    
    Returns:
        Paginated list of workflow runs with metadata
    
    Example:
        GET /api/v1/runs?page=1&page_size=20&status=FAILED&sort_by=created_at&sort_order=desc
        
        Response:
        {
            "items": [
                {
                    "id": "run-123e4567-e89b-12d3-a456-426614174000",
                    "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
                    "workflow_id": "wf-data-pipeline-001",
                    "workflow_name": "data-processing-pipeline",
                    "status": "FAILED",
                    ...
                }
            ],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        }
    
    Requirements:
    - 4.1: Returns paginated list with filtering by status, workflow_id, and date range
    """
    execution_service = ExecutionService(db)
    
    # Calculate offset
    skip = (page - 1) * page_size
    
    # Get runs with filtering
    runs = await execution_service.list_runs(
        skip=skip,
        limit=page_size,
        status=status,
        workflow_id=workflow_id,
        workflow_definition_id=workflow_definition_id,
        created_after=created_after,
        created_before=created_before,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Get total count (approximation based on result size)
    # In production, you'd want a separate count query
    total = len(runs) + skip if len(runs) == page_size else skip + len(runs)
    
    # Convert to response models
    run_responses = [
        RunResponse(
            id=run.run_id,
            run_id=run.run_id,
            workflow_id=run.workflow_id,
            workflow_name=run.workflow_name,
            workflow_definition_id=run.workflow_definition_id,
            status=run.status,
            input_data=run.input_data,
            triggered_by=run.triggered_by,
            created_at=run.created_at,
            updated_at=run.updated_at,
            completed_at=run.completed_at,
            cancelled_at=run.cancelled_at,
            cancelled_by=run.cancelled_by,
            error_message=run.error_message
        )
        for run in runs
    ]
    
    # Create paginated response
    from api.schemas.common import PaginationParams
    params = PaginationParams(page=page, page_size=page_size)
    
    return PaginatedResponse.create(
        items=run_responses,
        total=total,
        params=params
    )


@router.get(
    "/{run_id}",
    response_model=RunResponse,
    summary="Get run details",
    description="Retrieve detailed information about a specific workflow run by run_id.",
    responses={
        200: {
            "description": "Run details retrieved successfully",
            "model": RunResponse
        },
        404: {
            "description": "Run not found"
        }
    }
)
async def get_run(
    run_id: str,
    db: AsyncSession = Depends(get_db)
) -> RunResponse:
    """
    Get workflow run details by run_id.
    
    This endpoint retrieves detailed information about a specific workflow run
    including its status, input data, timestamps, error messages, and metadata.
    
    Args:
        run_id: Run identifier (e.g., 'run-123e4567-e89b-12d3-a456-426614174000')
        db: Database session (injected)
    
    Returns:
        Run details
    
    Raises:
        HTTPException: 404 if run not found
    
    Example:
        GET /api/v1/runs/run-123e4567-e89b-12d3-a456-426614174000
        
        Response:
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
            "cancelled_at": null,
            "cancelled_by": null,
            "error_message": null
        }
    
    Requirements:
    - 3.2: Returns complete run details including status, timestamps, and error messages
    - 4.2: Returns complete run details including status, timestamps, and error messages
    """
    execution_service = ExecutionService(db)
    
    run = await execution_service.get_run(run_id)
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id '{run_id}' not found"
        )
    
    return RunResponse(
        id=run.run_id,
        run_id=run.run_id,
        workflow_id=run.workflow_id,
        workflow_name=run.workflow_name,
        workflow_definition_id=run.workflow_definition_id,
        status=run.status,
        input_data=run.input_data,
        triggered_by=run.triggered_by,
        created_at=run.created_at,
        updated_at=run.updated_at,
        completed_at=run.completed_at,
        cancelled_at=run.cancelled_at,
        cancelled_by=run.cancelled_by,
        error_message=run.error_message
    )


@router.get(
    "/{run_id}/steps",
    response_model=list[StepExecutionResponse],
    summary="Get run step executions",
    description="Retrieve all step executions for a specific workflow run, ordered by execution time.",
    responses={
        200: {
            "description": "Step executions retrieved successfully",
            "model": list[StepExecutionResponse]
        },
        404: {
            "description": "Run not found"
        }
    }
)
async def get_run_steps(
    run_id: str,
    db: AsyncSession = Depends(get_db)
) -> list[StepExecutionResponse]:
    """
    Get all step executions for a workflow run.
    
    This endpoint retrieves all step executions for a specific workflow run,
    ordered by their start time. Each step execution includes:
    - Step identifier and name
    - Agent that executed the step
    - Status (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED)
    - Input and output data
    - Timestamps and error messages
    
    Args:
        run_id: Run identifier to get steps for
        db: Database session (injected)
    
    Returns:
        List of step executions ordered by started_at
    
    Raises:
        HTTPException: 404 if run not found
    
    Example:
        GET /api/v1/runs/run-123e4567-e89b-12d3-a456-426614174000/steps
        
        Response:
        [
            {
                "id": "step-exec-123e4567-e89b-12d3-a456-426614174000",
                "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
                "step_id": "extract",
                "step_name": "extract",
                "agent_name": "DataExtractorAgent",
                "status": "COMPLETED",
                "input_data": {"source_url": "https://api.example.com/data"},
                "output_data": {"data": [...], "record_count": 100},
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:01:00Z",
                "error_message": null
            },
            {
                "id": "step-exec-456e7890-e89b-12d3-a456-426614174000",
                "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
                "step_id": "transform",
                "step_name": "transform",
                "agent_name": "DataTransformerAgent",
                "status": "COMPLETED",
                "input_data": {"raw_data": [...]},
                "output_data": {"transformed_data": [...]},
                "started_at": "2024-01-01T10:01:00Z",
                "completed_at": "2024-01-01T10:03:00Z",
                "error_message": null
            }
        ]
    
    Requirements:
    - 4.3: Returns all step executions for the run with their status and output data
    """
    execution_service = ExecutionService(db)
    
    # First verify the run exists
    run = await execution_service.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id '{run_id}' not found"
        )
    
    # Get step executions
    steps = await execution_service.get_run_steps(run_id)
    
    # Convert to response models
    step_responses = [
        StepExecutionResponse(
            id=step.id,
            run_id=step.run_id,
            step_id=step.step_id,
            step_name=step.step_name,
            agent_name=step.agent_name,
            status=step.status,
            input_data=step.input_data or {},
            output_data=step.output_data,
            started_at=step.started_at,
            completed_at=step.completed_at,
            error_message=step.error_message
        )
        for step in steps
    ]
    
    return step_responses


@router.post(
    "/{run_id}/retry",
    response_model=RunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry a failed workflow run",
    description="Retry a failed or cancelled workflow run. The executor will resume from the last incomplete step.",
    responses={
        202: {
            "description": "Workflow retry initiated successfully",
            "model": RunResponse
        },
        404: {
            "description": "Run not found"
        },
        400: {
            "description": "Run cannot be retried (not in FAILED or CANCELLED status)"
        }
    }
)
async def retry_run(
    run_id: str,
    retry_request: Optional[WorkflowRetryRequest] = None,
    db: AsyncSession = Depends(get_db)
) -> RunResponse:
    """
    Retry a failed or cancelled workflow run.
    
    This endpoint triggers a retry of a failed or cancelled workflow run by:
    1. Validating the run exists and can be retried (FAILED or CANCELLED status)
    2. Updating the run status to PENDING
    3. Republishing the execution request to Kafka
    4. The executor service will resume from the last incomplete step
    
    The workflow execution happens asynchronously. Use the returned run details
    to monitor progress via the /api/v1/runs/{run_id} endpoint.
    
    Args:
        run_id: Run identifier to retry
        retry_request: Optional retry configuration (currently unused, reserved for future use)
        db: Database session (injected)
    
    Returns:
        Updated run details with PENDING status
    
    Raises:
        HTTPException: 404 if run not found
        HTTPException: 400 if run cannot be retried (not FAILED or CANCELLED)
    
    Example:
        POST /api/v1/runs/run-123e4567-e89b-12d3-a456-426614174000/retry
        {}
        
        Response:
        {
            "id": "run-123e4567-e89b-12d3-a456-426614174000",
            "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
            "workflow_id": "wf-data-pipeline-001",
            "workflow_name": "data-processing-pipeline",
            "status": "PENDING",
            "input_data": {"data_source": "https://api.example.com/data"},
            "triggered_by": "user@example.com",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:10:00Z",
            "completed_at": null,
            "cancelled_at": null,
            "cancelled_by": null,
            "error_message": null
        }
    
    Requirements:
    - 3.3: Resumes failed workflow from last incomplete step via POST endpoint
    """
    execution_service = ExecutionService(db)
    
    try:
        run = await execution_service.retry_workflow(
            run_id=run_id,
            user_id="system"
        )
        
        return RunResponse(
            id=run.run_id,
            run_id=run.run_id,
            workflow_id=run.workflow_id,
            workflow_name=run.workflow_name,
            workflow_definition_id=run.workflow_definition_id,
            status=run.status,
            input_data=run.input_data,
            triggered_by=run.triggered_by,
            created_at=run.created_at,
            updated_at=run.updated_at,
            completed_at=run.completed_at,
            cancelled_at=run.cancelled_at,
            cancelled_by=run.cancelled_by,
            error_message=run.error_message
        )
    except ValueError as e:
        # Check if it's a not found error or validation error
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry workflow: {str(e)}"
        )


@router.post(
    "/{run_id}/cancel",
    response_model=RunResponse,
    summary="Cancel a running workflow",
    description="Cancel a pending or running workflow. The executor will stop processing further steps.",
    responses={
        200: {
            "description": "Workflow cancelled successfully",
            "model": RunResponse
        },
        404: {
            "description": "Run not found"
        },
        400: {
            "description": "Run cannot be cancelled (not in PENDING or RUNNING status)"
        }
    }
)
async def cancel_run(
    run_id: str,
    cancel_request: Optional[WorkflowCancelRequest] = None,
    db: AsyncSession = Depends(get_db)
) -> RunResponse:
    """
    Cancel a pending or running workflow.
    
    This endpoint cancels a workflow run by:
    1. Validating the run exists and can be cancelled (PENDING or RUNNING status)
    2. Updating the run status to CANCELLED with cancellation metadata
    3. Publishing a cancellation request to Kafka to notify the executor
    4. The executor service will stop processing further steps
    
    Args:
        run_id: Run identifier to cancel
        cancel_request: Optional cancellation request with reason
        db: Database session (injected)
    
    Returns:
        Updated run details with CANCELLED status
    
    Raises:
        HTTPException: 404 if run not found
        HTTPException: 400 if run cannot be cancelled (not PENDING or RUNNING)
    
    Example:
        POST /api/v1/runs/run-123e4567-e89b-12d3-a456-426614174000/cancel
        {
            "reason": "User requested cancellation due to incorrect input data"
        }
        
        Response:
        {
            "id": "run-123e4567-e89b-12d3-a456-426614174000",
            "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
            "workflow_id": "wf-data-pipeline-001",
            "workflow_name": "data-processing-pipeline",
            "status": "CANCELLED",
            "input_data": {"data_source": "https://api.example.com/data"},
            "triggered_by": "user@example.com",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:02:00Z",
            "completed_at": null,
            "cancelled_at": "2024-01-01T10:02:00Z",
            "cancelled_by": "system",
            "error_message": "Cancelled: User requested cancellation due to incorrect input data"
        }
    
    Requirements:
    - 3.4: Marks run as cancelled and stops further step execution via POST endpoint
    """
    execution_service = ExecutionService(db)
    
    # Extract reason from request if provided
    reason = None
    if cancel_request:
        reason = cancel_request.reason
    
    try:
        run = await execution_service.cancel_workflow(
            run_id=run_id,
            user_id="system",
            reason=reason
        )
        
        return RunResponse(
            id=run.run_id,
            run_id=run.run_id,
            workflow_id=run.workflow_id,
            workflow_name=run.workflow_name,
            workflow_definition_id=run.workflow_definition_id,
            status=run.status,
            input_data=run.input_data,
            triggered_by=run.triggered_by,
            created_at=run.created_at,
            updated_at=run.updated_at,
            completed_at=run.completed_at,
            cancelled_at=run.cancelled_at,
            cancelled_by=run.cancelled_by,
            error_message=run.error_message
        )
    except ValueError as e:
        # Check if it's a not found error or validation error
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )


@router.get(
    "/{run_id}/logs",
    summary="Get run logs (placeholder)",
    description="Retrieve execution logs for a workflow run. This is a placeholder endpoint for future implementation.",
    responses={
        200: {
            "description": "Logs retrieved successfully (placeholder)"
        },
        404: {
            "description": "Run not found"
        },
        501: {
            "description": "Not implemented yet"
        }
    }
)
async def get_run_logs(
    run_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get execution logs for a workflow run (placeholder).
    
    This endpoint is a placeholder for future log retrieval functionality.
    In a production system, this would integrate with a logging system
    (e.g., Elasticsearch, CloudWatch, Loki) to retrieve structured logs
    for the workflow run and its steps.
    
    Args:
        run_id: Run identifier to get logs for
        db: Database session (injected)
    
    Returns:
        Placeholder response indicating the feature is not yet implemented
    
    Raises:
        HTTPException: 404 if run not found
        HTTPException: 501 if logs are not available
    
    Example:
        GET /api/v1/runs/run-123e4567-e89b-12d3-a456-426614174000/logs
        
        Response:
        {
            "message": "Log retrieval not yet implemented",
            "run_id": "run-123e4567-e89b-12d3-a456-426614174000",
            "note": "This endpoint will be implemented in a future release"
        }
    
    Requirements:
    - 4.4: Returns execution logs for the run (placeholder implementation)
    """
    execution_service = ExecutionService(db)
    
    # Verify the run exists
    run = await execution_service.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id '{run_id}' not found"
        )
    
    # Return placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "message": "Log retrieval not yet implemented",
            "run_id": run_id,
            "note": "This endpoint will be implemented in a future release to integrate with a logging system"
        }
    )

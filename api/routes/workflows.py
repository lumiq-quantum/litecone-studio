"""
Workflow management API routes.

This module provides REST endpoints for managing workflow definitions in the system.
Workflows are directed acyclic graphs of steps that are executed sequentially.

Requirements:
- 2.1: Create workflow via POST /api/v1/workflows
- 2.2: List workflows via GET /api/v1/workflows with pagination and filtering
- 2.3: Get workflow details via GET /api/v1/workflows/{workflow_id}
- 2.4: Update workflow via PUT /api/v1/workflows/{workflow_id}
- 2.5: Delete workflow via DELETE /api/v1/workflows/{workflow_id}
- 2.6: Get workflow versions via GET /api/v1/workflows/{workflow_id}/versions
- 3.1: Trigger workflow execution via POST /api/v1/workflows/{workflow_id}/execute
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.services.workflow import WorkflowService
from api.services.execution import ExecutionService
from api.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowResponse
from api.schemas.run import WorkflowExecuteRequest, RunResponse
from api.schemas.common import PaginatedResponse, MessageResponse


# Create router with prefix and tags
router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"]
)


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workflow",
    description="Create a new workflow definition. The workflow name must be unique for the first version.",
    responses={
        201: {
            "description": "Workflow created successfully",
            "model": WorkflowResponse
        },
        400: {
            "description": "Invalid request data or validation failed"
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_db)
) -> WorkflowResponse:
    """
    Create a new workflow definition.
    
    This endpoint creates a new workflow definition in the system. Workflows
    define a directed acyclic graph of steps that are executed sequentially.
    The workflow structure is validated to ensure:
    - All referenced agents exist and are active
    - No circular references exist
    - All steps are reachable from the start_step
    
    Args:
        workflow_data: Workflow creation data including name, steps, and configuration
        db: Database session (injected)
    
    Returns:
        Created workflow details
    
    Raises:
        HTTPException: 400 if validation fails (agents not found, invalid structure)
    
    Example:
        POST /api/v1/workflows
        {
            "name": "data-processing-pipeline",
            "description": "ETL pipeline for data processing",
            "start_step": "extract",
            "steps": {
                "extract": {
                    "id": "extract",
                    "agent_name": "DataExtractorAgent",
                    "next_step": "transform",
                    "input_mapping": {
                        "source_url": "${workflow.input.data_source}"
                    }
                },
                "transform": {
                    "id": "transform",
                    "agent_name": "DataTransformerAgent",
                    "next_step": null,
                    "input_mapping": {
                        "raw_data": "${extract.output.data}"
                    }
                }
            }
        }
    
    Requirements:
    - 2.1: Creates workflow record in database via POST endpoint
    """
    service = WorkflowService(db)
    
    try:
        workflow = await service.create_workflow(workflow_data, user_id="system")
        return WorkflowResponse.model_validate(workflow)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=PaginatedResponse[WorkflowResponse],
    summary="List all workflows",
    description="Retrieve a paginated list of workflows with optional filtering and sorting.",
    responses={
        200: {
            "description": "List of workflows retrieved successfully",
            "model": PaginatedResponse[WorkflowResponse]
        }
    }
)
async def list_workflows(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of items per page"),
    status: Optional[str] = Query(
        default=None,
        description="Filter by workflow status (active, inactive, deleted)"
    ),
    name: Optional[str] = Query(
        default=None,
        description="Filter by workflow name (exact match)"
    ),
    sort_by: str = Query(
        default="created_at",
        description="Field to sort by (name, created_at, updated_at, version)"
    ),
    sort_order: str = Query(
        default="desc",
        description="Sort order (asc or desc)"
    ),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[WorkflowResponse]:
    """
    List workflows with pagination, filtering, and sorting.
    
    This endpoint returns a paginated list of workflows. You can filter by status
    and name, control pagination with page and page_size parameters, and sort
    by various fields.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        status: Optional status filter (active, inactive, deleted)
        name: Optional name filter (exact match)
        sort_by: Field to sort by (name, created_at, updated_at, version)
        sort_order: Sort order (asc or desc)
        db: Database session (injected)
    
    Returns:
        Paginated list of workflows with metadata
    
    Example:
        GET /api/v1/workflows?page=1&page_size=20&status=active&sort_by=name&sort_order=asc
    
    Requirements:
    - 2.2: Returns paginated list of workflows via GET endpoint with filtering and sorting
    """
    service = WorkflowService(db)
    
    # Calculate offset
    skip = (page - 1) * page_size
    
    # Get workflows
    workflows = await service.list_workflows(
        skip=skip,
        limit=page_size,
        status=status,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Get total count (for now, we'll use the length of results as an approximation)
    # In production, you'd want a separate count query
    total = len(workflows) + skip if len(workflows) == page_size else skip + len(workflows)
    
    # Convert to response models
    workflow_responses = [WorkflowResponse.model_validate(workflow) for workflow in workflows]
    
    # Create paginated response
    from api.schemas.common import PaginationParams
    params = PaginationParams(page=page, page_size=page_size)
    
    return PaginatedResponse.create(
        items=workflow_responses,
        total=total,
        params=params
    )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow details",
    description="Retrieve detailed information about a specific workflow by ID.",
    responses={
        200: {
            "description": "Workflow details retrieved successfully",
            "model": WorkflowResponse
        },
        404: {
            "description": "Workflow not found"
        }
    }
)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> WorkflowResponse:
    """
    Get workflow by ID.
    
    This endpoint retrieves detailed information about a specific workflow
    including its complete definition, steps, status, and metadata.
    
    Args:
        workflow_id: UUID of the workflow to retrieve
        db: Database session (injected)
    
    Returns:
        Workflow details
    
    Raises:
        HTTPException: 404 if workflow not found
    
    Example:
        GET /api/v1/workflows/123e4567-e89b-12d3-a456-426614174000
    
    Requirements:
    - 2.3: Returns complete workflow definition including all steps via GET endpoint
    """
    service = WorkflowService(db)
    
    workflow = await service.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with id '{workflow_id}' not found"
        )
    
    return WorkflowResponse.model_validate(workflow)


@router.put(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Update a workflow",
    description="Update an existing workflow's configuration. Only provided fields will be updated. Structural changes increment the version.",
    responses={
        200: {
            "description": "Workflow updated successfully",
            "model": WorkflowResponse
        },
        404: {
            "description": "Workflow not found"
        },
        400: {
            "description": "Validation failed"
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db)
) -> WorkflowResponse:
    """
    Update an existing workflow.
    
    This endpoint updates a workflow's configuration. Only the fields provided
    in the request body will be updated; other fields remain unchanged.
    
    If steps or start_step are modified, the version number is automatically
    incremented to track changes. The workflow structure is validated to ensure:
    - All referenced agents exist and are active
    - No circular references exist
    - All steps are reachable from the start_step
    
    Args:
        workflow_id: UUID of the workflow to update
        workflow_data: Workflow update data (partial update)
        db: Database session (injected)
    
    Returns:
        Updated workflow details
    
    Raises:
        HTTPException: 404 if workflow not found
        HTTPException: 400 if validation fails
    
    Example:
        PUT /api/v1/workflows/123e4567-e89b-12d3-a456-426614174000
        {
            "description": "Updated description",
            "status": "inactive"
        }
    
    Requirements:
    - 2.4: Updates workflow definition and increments version via PUT endpoint
    """
    service = WorkflowService(db)
    
    try:
        workflow = await service.update_workflow(workflow_id, workflow_data, user_id="system")
        return WorkflowResponse.model_validate(workflow)
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


@router.delete(
    "/{workflow_id}",
    response_model=MessageResponse,
    summary="Delete a workflow",
    description="Soft delete a workflow. The workflow will be marked as deleted and cannot be used for new executions.",
    responses={
        200: {
            "description": "Workflow deleted successfully",
            "model": MessageResponse
        },
        404: {
            "description": "Workflow not found"
        }
    }
)
async def delete_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Delete a workflow (soft delete).
    
    This endpoint performs a soft delete on a workflow, marking it as deleted
    without removing it from the database. This preserves historical data
    while preventing the workflow from being used in new executions.
    
    Args:
        workflow_id: UUID of the workflow to delete
        db: Database session (injected)
    
    Returns:
        Success message
    
    Raises:
        HTTPException: 404 if workflow not found
    
    Example:
        DELETE /api/v1/workflows/123e4567-e89b-12d3-a456-426614174000
    
    Requirements:
    - 2.5: Soft-deletes workflow via DELETE endpoint
    """
    service = WorkflowService(db)
    
    try:
        await service.delete_workflow(workflow_id, user_id="system")
        return MessageResponse(
            message=f"Workflow '{workflow_id}' deleted successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{workflow_id}/versions",
    response_model=PaginatedResponse[WorkflowResponse],
    summary="Get workflow versions",
    description="Retrieve all versions of a workflow ordered by version number (newest first).",
    responses={
        200: {
            "description": "Workflow versions retrieved successfully",
            "model": PaginatedResponse[WorkflowResponse]
        },
        404: {
            "description": "Workflow not found"
        }
    }
)
async def get_workflow_versions(
    workflow_id: UUID,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[WorkflowResponse]:
    """
    Get all versions of a workflow.
    
    This endpoint retrieves all versions of a workflow by its name,
    ordered by version number (newest first). This allows you to track
    the evolution of a workflow over time.
    
    Args:
        workflow_id: UUID of any version of the workflow
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        db: Database session (injected)
    
    Returns:
        Paginated list of workflow versions
    
    Raises:
        HTTPException: 404 if workflow not found
    
    Example:
        GET /api/v1/workflows/123e4567-e89b-12d3-a456-426614174000/versions?page=1&page_size=10
    
    Requirements:
    - 2.6: Returns all versions of the workflow via GET endpoint
    """
    service = WorkflowService(db)
    
    # Calculate offset
    skip = (page - 1) * page_size
    
    try:
        # Get versions
        versions = await service.get_versions(
            workflow_id=workflow_id,
            skip=skip,
            limit=page_size
        )
        
        # Get total count (approximation)
        total = len(versions) + skip if len(versions) == page_size else skip + len(versions)
        
        # Convert to response models
        version_responses = [WorkflowResponse.model_validate(version) for version in versions]
        
        # Create paginated response
        from api.schemas.common import PaginationParams
        params = PaginationParams(page=page, page_size=page_size)
        
        return PaginatedResponse.create(
            items=version_responses,
            total=total,
            params=params
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{workflow_id}/execute",
    response_model=RunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute a workflow",
    description="Trigger execution of a workflow. Returns immediately with run details without waiting for completion.",
    responses={
        202: {
            "description": "Workflow execution triggered successfully",
            "model": RunResponse
        },
        404: {
            "description": "Workflow not found"
        },
        400: {
            "description": "Workflow is not active or validation failed"
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def execute_workflow(
    workflow_id: UUID,
    execute_request: WorkflowExecuteRequest,
    db: AsyncSession = Depends(get_db)
) -> RunResponse:
    """
    Trigger workflow execution.
    
    This endpoint triggers the execution of a workflow by:
    1. Validating the workflow exists and is active
    2. Creating a workflow run record with PENDING status
    3. Publishing the execution request to Kafka for the executor service
    4. Returning immediately with the run details
    
    The workflow execution happens asynchronously. Use the returned run_id
    to monitor progress via the /api/v1/runs/{run_id} endpoint.
    
    Args:
        workflow_id: UUID of the workflow to execute
        execute_request: Execution request containing input data
        db: Database session (injected)
    
    Returns:
        Created workflow run details with PENDING status
    
    Raises:
        HTTPException: 404 if workflow not found
        HTTPException: 400 if workflow is not active or validation fails
    
    Example:
        POST /api/v1/workflows/123e4567-e89b-12d3-a456-426614174000/execute
        {
            "input_data": {
                "data_source": "https://api.example.com/data",
                "output_format": "json"
            }
        }
        
        Response:
        {
            "id": "run-456e7890-e89b-12d3-a456-426614174000",
            "run_id": "run-456e7890-e89b-12d3-a456-426614174000",
            "workflow_id": "wf-data-pipeline-001",
            "workflow_name": "data-processing-pipeline",
            "status": "PENDING",
            "input_data": {...},
            "triggered_by": "system",
            "created_at": "2024-01-01T10:00:00Z",
            ...
        }
    
    Requirements:
    - 3.1: Creates run record and triggers executor service via POST endpoint
    - 3.2: Returns run_id immediately without waiting for completion
    """
    execution_service = ExecutionService(db)
    
    try:
        run = await execution_service.execute_workflow(
            workflow_id=workflow_id,
            execute_request=execute_request,
            user_id="system"
        )
        
        # Convert to response model
        response = RunResponse(
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
        
        return response
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
            detail=f"Failed to trigger workflow execution: {str(e)}"
        )

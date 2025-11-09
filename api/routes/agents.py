"""
Agent management API routes.

This module provides REST endpoints for managing agents in the workflow system.
Agents are external services that execute tasks via the A2A protocol.

Requirements:
- 1.1: Create agent via POST /api/v1/agents
- 1.2: List agents via GET /api/v1/agents with pagination
- 1.3: Get agent details via GET /api/v1/agents/{agent_id}
- 1.4: Update agent via PUT /api/v1/agents/{agent_id}
- 1.5: Delete agent via DELETE /api/v1/agents/{agent_id}
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.services.agent import AgentService
from api.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from api.schemas.common import PaginatedResponse, MessageResponse


# Create router with prefix and tags
router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Register a new agent in the system. The agent name must be unique.",
    responses={
        201: {
            "description": "Agent created successfully",
            "model": AgentResponse
        },
        400: {
            "description": "Invalid request data or agent name already exists"
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db)
) -> AgentResponse:
    """
    Create a new agent.
    
    This endpoint registers a new agent in the system. Agents are external
    services that execute workflow steps via the A2A protocol.
    
    Args:
        agent_data: Agent creation data including name, URL, and configuration
        db: Database session (injected)
    
    Returns:
        Created agent details
    
    Raises:
        HTTPException: 400 if agent name already exists
    
    Example:
        POST /api/v1/agents
        {
            "name": "data-processor",
            "url": "http://data-processor:8080",
            "description": "Processes data transformations",
            "auth_type": "bearer",
            "auth_config": {"token": "secret-token"},
            "timeout_ms": 30000,
            "retry_config": {
                "max_retries": 3,
                "initial_delay_ms": 1000,
                "max_delay_ms": 30000,
                "backoff_multiplier": 2.0
            }
        }
    
    Requirements:
    - 1.1: Creates agent record in database via POST endpoint
    """
    service = AgentService(db)
    
    try:
        agent = await service.create_agent(agent_data, user_id="system")
        return AgentResponse.model_validate(agent)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=PaginatedResponse[AgentResponse],
    summary="List all agents",
    description="Retrieve a paginated list of agents with optional status filtering.",
    responses={
        200: {
            "description": "List of agents retrieved successfully",
            "model": PaginatedResponse[AgentResponse]
        }
    }
)
async def list_agents(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of items per page"),
    status: Optional[str] = Query(
        default=None,
        description="Filter by agent status (active, inactive, deleted)"
    ),
    name: Optional[str] = Query(
        default=None,
        description="Filter by agent name (exact match)"
    ),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[AgentResponse]:
    """
    List agents with pagination and filtering.
    Updated to support name filtering.
    
    This endpoint returns a paginated list of agents. You can filter by status
    and control pagination with page and page_size parameters.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        status: Optional status filter (active, inactive, deleted)
        db: Database session (injected)
    
    Returns:
        Paginated list of agents with metadata
    
    Example:
        GET /api/v1/agents?page=1&page_size=20&status=active
    
    Requirements:
    - 1.2: Returns paginated list of agents via GET endpoint
    """
    service = AgentService(db)
    
    # If name is provided, use get_agent_by_name instead
    if name:
        agent = await service.get_agent_by_name(name)
        if agent:
            agent_responses = [AgentResponse.model_validate(agent)]
            from api.schemas.common import PaginationParams
            params = PaginationParams(page=1, page_size=1)
            return PaginatedResponse.create(
                items=agent_responses,
                total=1,
                params=params
            )
        else:
            from api.schemas.common import PaginationParams
            params = PaginationParams(page=1, page_size=page_size)
            return PaginatedResponse.create(
                items=[],
                total=0,
                params=params
            )
    
    # Calculate offset
    skip = (page - 1) * page_size
    
    # Get agents
    agents = await service.list_agents(skip=skip, limit=page_size, status=status)
    
    # Get total count (for now, we'll use the length of results as an approximation)
    # In production, you'd want a separate count query
    total = len(agents) + skip if len(agents) == page_size else skip + len(agents)
    
    # Convert to response models
    agent_responses = [AgentResponse.model_validate(agent) for agent in agents]
    
    # Create paginated response
    from api.schemas.common import PaginationParams
    params = PaginationParams(page=page, page_size=page_size)
    
    return PaginatedResponse.create(
        items=agent_responses,
        total=total,
        params=params
    )


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get agent details",
    description="Retrieve detailed information about a specific agent by ID.",
    responses={
        200: {
            "description": "Agent details retrieved successfully",
            "model": AgentResponse
        },
        404: {
            "description": "Agent not found"
        }
    }
)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> AgentResponse:
    """
    Get agent by ID.
    
    This endpoint retrieves detailed information about a specific agent
    including its configuration, status, and metadata.
    
    Args:
        agent_id: UUID of the agent to retrieve
        db: Database session (injected)
    
    Returns:
        Agent details
    
    Raises:
        HTTPException: 404 if agent not found
    
    Example:
        GET /api/v1/agents/123e4567-e89b-12d3-a456-426614174000
    
    Requirements:
    - 1.3: Returns agent details via GET endpoint
    """
    service = AgentService(db)
    
    agent = await service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id '{agent_id}' not found"
        )
    
    return AgentResponse.model_validate(agent)


@router.put(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Update an agent",
    description="Update an existing agent's configuration. Only provided fields will be updated.",
    responses={
        200: {
            "description": "Agent updated successfully",
            "model": AgentResponse
        },
        404: {
            "description": "Agent not found"
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db)
) -> AgentResponse:
    """
    Update an existing agent.
    
    This endpoint updates an agent's configuration. Only the fields provided
    in the request body will be updated; other fields remain unchanged.
    
    Args:
        agent_id: UUID of the agent to update
        agent_data: Agent update data (partial update)
        db: Database session (injected)
    
    Returns:
        Updated agent details
    
    Raises:
        HTTPException: 404 if agent not found
    
    Example:
        PUT /api/v1/agents/123e4567-e89b-12d3-a456-426614174000
        {
            "description": "Updated description",
            "timeout_ms": 60000,
            "status": "inactive"
        }
    
    Requirements:
    - 1.4: Updates agent configuration via PUT endpoint
    """
    service = AgentService(db)
    
    try:
        agent = await service.update_agent(agent_id, agent_data, user_id="system")
        return AgentResponse.model_validate(agent)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete(
    "/{agent_id}",
    response_model=MessageResponse,
    summary="Delete an agent",
    description="Soft delete an agent. The agent will be marked as deleted and cannot be used in new workflows.",
    responses={
        200: {
            "description": "Agent deleted successfully",
            "model": MessageResponse
        },
        404: {
            "description": "Agent not found"
        }
    }
)
async def delete_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Delete an agent (soft delete).
    
    This endpoint performs a soft delete on an agent, marking it as deleted
    without removing it from the database. This preserves historical data
    while preventing the agent from being used in new workflows.
    
    Args:
        agent_id: UUID of the agent to delete
        db: Database session (injected)
    
    Returns:
        Success message
    
    Raises:
        HTTPException: 404 if agent not found
    
    Example:
        DELETE /api/v1/agents/123e4567-e89b-12d3-a456-426614174000
    
    Requirements:
    - 1.5: Soft-deletes agent via DELETE endpoint
    """
    service = AgentService(db)
    
    try:
        await service.delete_agent(agent_id, user_id="system")
        return MessageResponse(
            message=f"Agent '{agent_id}' deleted successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{agent_id}/health",
    summary="Check agent health",
    description="Perform a health check on an agent by calling its /health endpoint.",
    responses={
        200: {
            "description": "Health check completed (check 'healthy' field for status)"
        },
        404: {
            "description": "Agent not found"
        }
    }
)
async def check_agent_health(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Check agent health.
    
    This endpoint performs a health check on an agent by making an HTTP
    request to the agent's /health endpoint. It respects the agent's
    timeout and authentication configuration.
    
    Args:
        agent_id: UUID of the agent to check
        db: Database session (injected)
    
    Returns:
        Health check results including:
        - healthy: bool indicating if agent is healthy
        - status_code: HTTP status code (if request succeeded)
        - response_time_ms: Response time in milliseconds
        - error: Error message (if request failed)
    
    Raises:
        HTTPException: 404 if agent not found
    
    Example:
        GET /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/health
        
        Response:
        {
            "healthy": true,
            "status_code": 200,
            "response_time_ms": 45,
            "error": null
        }
    
    Requirements:
    - 1.5: Provides health check via GET endpoint
    """
    service = AgentService(db)
    
    try:
        health_result = await service.check_agent_health(agent_id)
        return health_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

"""Agent service for managing agent lifecycle and operations."""

from typing import Optional, List
from uuid import UUID
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories.agent import AgentRepository
from api.services.audit import AuditService
from api.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from api.models.agent import Agent


class AgentService:
    """
    Service for managing agents.
    
    This service provides business logic for agent operations including
    creation, retrieval, updates, deletion, and health checks.
    
    Requirements:
    - 1.1: Create agent via POST /api/v1/agents
    - 1.2: List agents via GET /api/v1/agents with pagination
    - 1.3: Get agent details via GET /api/v1/agents/{agent_id}
    - 1.4: Update agent via PUT /api/v1/agents/{agent_id}
    - 1.5: Delete agent via DELETE /api/v1/agents/{agent_id}
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize AgentService with database session.
        
        Args:
            db: Async database session
        """
        self.repository = AgentRepository(db)
        self.audit_service = AuditService(db)
    
    async def create_agent(
        self,
        agent_data: AgentCreate,
        user_id: Optional[str] = None
    ) -> Agent:
        """
        Create a new agent and log the action.
        
        This method creates a new agent in the database and records
        the creation in the audit log.
        
        Args:
            agent_data: Agent creation data
            user_id: Identifier of the user creating the agent
        
        Returns:
            Created Agent instance
        
        Raises:
            ValueError: If an agent with the same name already exists
        
        Example:
            agent = await agent_service.create_agent(
                agent_data=AgentCreate(
                    name="data-processor",
                    url="http://data-processor:8080",
                    description="Processes data transformations"
                ),
                user_id="admin@example.com"
            )
        
        Requirements:
        - 1.1: Creates agent record in database via POST endpoint
        """
        # Check if agent with same name already exists
        existing_agent = await self.repository.get_by_name(agent_data.name)
        if existing_agent:
            raise ValueError(f"Agent with name '{agent_data.name}' already exists")
        
        # Create agent
        agent = await self.repository.create(agent_data)
        
        # Log the creation action
        await self.audit_service.log_action(
            entity_type="agent",
            entity_id=agent.id,
            action="create",
            user_id=user_id,
            changes=agent_data.model_dump()
        )
        
        return agent

    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        """
        Get agent by ID.
        
        Args:
            agent_id: UUID of the agent to retrieve
        
        Returns:
            Agent instance or None if not found
        
        Example:
            agent = await agent_service.get_agent(agent_id)
            if agent:
                print(f"Found agent: {agent.name}")
        
        Requirements:
        - 1.3: Returns agent details via GET endpoint
        """
        return await self.repository.get_by_id(agent_id)
    
    async def get_agent_by_name(self, name: str) -> Optional[Agent]:
        """
        Get agent by name.
        
        Args:
            name: Name of the agent to retrieve
        
        Returns:
            Agent instance or None if not found
        
        Example:
            agent = await agent_service.get_agent_by_name("data-processor")
        """
        return await self.repository.get_by_name(name)
    
    async def list_agents(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Agent]:
        """
        List agents with pagination and optional status filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            status: Optional status filter ('active', 'inactive', 'deleted')
        
        Returns:
            List of Agent instances
        
        Example:
            # Get first page of active agents
            agents = await agent_service.list_agents(
                skip=0,
                limit=20,
                status="active"
            )
        
        Requirements:
        - 1.2: Returns paginated list of agents via GET endpoint
        """
        return await self.repository.list(skip=skip, limit=limit, status=status)
    
    async def update_agent(
        self,
        agent_id: UUID,
        agent_data: AgentUpdate,
        user_id: Optional[str] = None
    ) -> Agent:
        """
        Update an existing agent and log the action.
        
        This method updates an agent's configuration and records
        the changes in the audit log.
        
        Args:
            agent_id: UUID of the agent to update
            agent_data: Agent update data
            user_id: Identifier of the user updating the agent
        
        Returns:
            Updated Agent instance
        
        Raises:
            ValueError: If agent not found
        
        Example:
            updated_agent = await agent_service.update_agent(
                agent_id=agent_id,
                agent_data=AgentUpdate(
                    description="Updated description",
                    timeout_ms=60000
                ),
                user_id="admin@example.com"
            )
        
        Requirements:
        - 1.4: Updates agent configuration via PUT endpoint
        """
        # Check if agent exists
        existing_agent = await self.repository.get_by_id(agent_id)
        if not existing_agent:
            raise ValueError(f"Agent with id '{agent_id}' not found")
        
        # Update agent
        agent = await self.repository.update(agent_id, agent_data)
        
        # Log the update action
        await self.audit_service.log_action(
            entity_type="agent",
            entity_id=agent_id,
            action="update",
            user_id=user_id,
            changes=agent_data.model_dump(exclude_unset=True)
        )
        
        return agent
    
    async def delete_agent(
        self,
        agent_id: UUID,
        user_id: Optional[str] = None
    ) -> None:
        """
        Soft delete an agent and log the action.
        
        This method marks an agent as deleted (soft delete) to prevent
        it from being used in new workflows while preserving historical data.
        
        Args:
            agent_id: UUID of the agent to delete
            user_id: Identifier of the user deleting the agent
        
        Raises:
            ValueError: If agent not found
        
        Example:
            await agent_service.delete_agent(
                agent_id=agent_id,
                user_id="admin@example.com"
            )
        
        Requirements:
        - 1.5: Soft-deletes agent via DELETE endpoint
        """
        # Check if agent exists
        existing_agent = await self.repository.get_by_id(agent_id)
        if not existing_agent:
            raise ValueError(f"Agent with id '{agent_id}' not found")
        
        # Soft delete agent
        await self.repository.soft_delete(agent_id, deleted_by=user_id)
        
        # Log the deletion action
        await self.audit_service.log_action(
            entity_type="agent",
            entity_id=agent_id,
            action="delete",
            user_id=user_id
        )
    
    async def check_agent_health(self, agent_id: UUID) -> dict:
        """
        Check the health of an agent by making an HTTP call to its endpoint.
        
        This method performs a health check by sending a GET request to the
        agent's /health endpoint. It respects the agent's timeout configuration
        and authentication settings.
        
        Args:
            agent_id: UUID of the agent to check
        
        Returns:
            Dictionary containing health check results:
            - healthy: bool indicating if agent is healthy
            - status_code: HTTP status code (if request succeeded)
            - response_time_ms: Response time in milliseconds
            - error: Error message (if request failed)
        
        Raises:
            ValueError: If agent not found
        
        Example:
            health = await agent_service.check_agent_health(agent_id)
            if health["healthy"]:
                print(f"Agent is healthy (response time: {health['response_time_ms']}ms)")
            else:
                print(f"Agent is unhealthy: {health['error']}")
        
        Requirements:
        - 1.5: Provides health check via GET /api/v1/agents/{agent_id}/health
        """
        # Get agent
        agent = await self.repository.get_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent with id '{agent_id}' not found")
        
        # Prepare health check URL
        health_url = f"{agent.url.rstrip('/')}/health"
        
        # Prepare headers based on auth configuration
        headers = {}
        if agent.auth_type == "bearer" and agent.auth_config:
            token = agent.auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif agent.auth_type == "apikey" and agent.auth_config:
            key = agent.auth_config.get("key")
            header_name = agent.auth_config.get("header_name", "X-API-Key")
            if key:
                headers[header_name] = key
        
        # Perform health check
        result = {
            "healthy": False,
            "status_code": None,
            "response_time_ms": None,
            "error": None
        }
        
        try:
            async with httpx.AsyncClient(timeout=agent.timeout_ms / 1000.0) as client:
                import time
                start_time = time.time()
                
                response = await client.get(health_url, headers=headers)
                
                end_time = time.time()
                response_time_ms = int((end_time - start_time) * 1000)
                
                result["status_code"] = response.status_code
                result["response_time_ms"] = response_time_ms
                result["healthy"] = response.status_code == 200
                
                if response.status_code != 200:
                    result["error"] = f"Unhealthy status code: {response.status_code}"
        
        except httpx.TimeoutException:
            result["error"] = f"Request timed out after {agent.timeout_ms}ms"
        except httpx.RequestError as e:
            result["error"] = f"Request failed: {str(e)}"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        return result

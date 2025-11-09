"""Agent repository for database operations on Agent model."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories.base import BaseRepository
from api.models.agent import Agent
from api.schemas.agent import AgentCreate, AgentUpdate


class AgentRepository(BaseRepository[Agent, AgentCreate, AgentUpdate]):
    """
    Repository for Agent model with specialized query methods.
    
    Extends BaseRepository to provide agent-specific operations:
    - Get agent by name
    - List agents with status filtering
    - Soft delete agents
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize AgentRepository with database session.
        
        Args:
            db: Async database session
        """
        super().__init__(Agent, db)
    
    async def get_by_name(self, name: str) -> Optional[Agent]:
        """
        Get an agent by its unique name.
        
        Args:
            name: Agent name to search for
        
        Returns:
            Agent instance or None if not found
        """
        result = await self.db.execute(
            select(Agent).where(Agent.name == name)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Agent]:
        """
        List agents with optional status filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            status: Optional status filter ('active', 'inactive', 'deleted')
        
        Returns:
            List of Agent instances
        """
        query = select(Agent)
        
        # Apply status filter if provided
        if status is not None:
            query = query.where(Agent.status == status)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def soft_delete(self, id: UUID, deleted_by: Optional[str] = None) -> Optional[Agent]:
        """
        Soft delete an agent by setting its status to 'deleted'.
        
        Args:
            id: UUID of the agent to soft delete
            deleted_by: Optional user identifier who performed the deletion
        
        Returns:
            Updated Agent instance or None if not found
        """
        # Get existing agent
        agent = await self.get_by_id(id)
        if not agent:
            return None
        
        # Set status to deleted
        agent.status = 'deleted'
        
        # Set updated_by if deleted_by is provided
        if deleted_by:
            agent.updated_by = deleted_by
        
        # Flush changes
        await self.db.flush()
        await self.db.refresh(agent)
        
        return agent

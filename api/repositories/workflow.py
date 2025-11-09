"""Workflow repository for database operations on WorkflowDefinition model."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories.base import BaseRepository, PaginationResult
from api.models.workflow import WorkflowDefinition
from api.schemas.workflow import WorkflowCreate, WorkflowUpdate


class WorkflowRepository(BaseRepository[WorkflowDefinition, WorkflowCreate, WorkflowUpdate]):
    """
    Repository for WorkflowDefinition model with specialized query methods.
    
    Extends BaseRepository to provide workflow-specific operations:
    - Get workflow by name and version
    - List all versions of a workflow
    - List workflows with filtering and sorting
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize WorkflowRepository with database session.
        
        Args:
            db: Async database session
        """
        super().__init__(WorkflowDefinition, db)
    
    async def get_by_name_and_version(
        self,
        name: str,
        version: int
    ) -> Optional[WorkflowDefinition]:
        """
        Get a workflow by its unique name and version combination.
        
        Args:
            name: Workflow name to search for
            version: Workflow version to search for
        
        Returns:
            WorkflowDefinition instance or None if not found
        """
        result = await self.db.execute(
            select(WorkflowDefinition)
            .where(WorkflowDefinition.name == name)
            .where(WorkflowDefinition.version == version)
        )
        return result.scalar_one_or_none()
    
    async def list_versions(
        self,
        name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowDefinition]:
        """
        List all versions of a workflow by name, ordered by version descending.
        
        Args:
            name: Workflow name to search for
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of WorkflowDefinition instances ordered by version (newest first)
        """
        query = (
            select(WorkflowDefinition)
            .where(WorkflowDefinition.name == name)
            .order_by(desc(WorkflowDefinition.version))
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        name: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[WorkflowDefinition]:
        """
        List workflows with optional filtering and sorting.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            status: Optional status filter ('active', 'inactive', 'deleted')
            name: Optional name filter (exact match)
            sort_by: Field to sort by ('name', 'created_at', 'updated_at', 'version')
            sort_order: Sort order ('asc' or 'desc')
        
        Returns:
            List of WorkflowDefinition instances
        """
        query = select(WorkflowDefinition)
        
        # Apply status filter if provided
        if status is not None:
            query = query.where(WorkflowDefinition.status == status)
        
        # Apply name filter if provided
        if name is not None:
            query = query.where(WorkflowDefinition.name == name)
        
        # Apply sorting
        sort_column = getattr(WorkflowDefinition, sort_by, WorkflowDefinition.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        name: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginationResult[WorkflowDefinition]:
        """
        List workflows with pagination metadata, filtering, and sorting.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Optional status filter ('active', 'inactive', 'deleted')
            name: Optional name filter (exact match)
            sort_by: Field to sort by ('name', 'created_at', 'updated_at', 'version')
            sort_order: Sort order ('asc' or 'desc')
        
        Returns:
            PaginationResult with items and metadata
        """
        # Build filters dictionary
        filters = {}
        if status is not None:
            filters['status'] = status
        if name is not None:
            filters['name'] = name
        
        # Build order_by clause
        sort_column = getattr(WorkflowDefinition, sort_by, WorkflowDefinition.created_at)
        if sort_order.lower() == "asc":
            order_by = [asc(sort_column)]
        else:
            order_by = [desc(sort_column)]
        
        # Use base class list_paginated with filters and ordering
        return await super().list_paginated(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=order_by
        )
    
    async def soft_delete(
        self,
        id: UUID,
        deleted_by: Optional[str] = None
    ) -> Optional[WorkflowDefinition]:
        """
        Soft delete a workflow by setting its status to 'deleted'.
        
        Args:
            id: UUID of the workflow to soft delete
            deleted_by: Optional user identifier who performed the deletion
        
        Returns:
            Updated WorkflowDefinition instance or None if not found
        """
        # Get existing workflow
        workflow = await self.get_by_id(id)
        if not workflow:
            return None
        
        # Set status to deleted
        workflow.status = 'deleted'
        
        # Set updated_by if deleted_by is provided
        if deleted_by:
            workflow.updated_by = deleted_by
        
        # Flush changes
        await self.db.flush()
        await self.db.refresh(workflow)
        
        return workflow

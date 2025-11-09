"""Audit log repository for database operations on AuditLog model."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from api.repositories.base import BaseRepository, PaginationResult
from api.models.audit import AuditLog


# Minimal schemas for audit operations (audit logs are typically write-only)
class AuditLogCreate(BaseModel):
    """Schema for creating audit log entries."""
    entity_type: str
    entity_id: UUID
    action: str
    user_id: Optional[str] = None
    changes: Optional[dict] = None


class AuditLogUpdate(BaseModel):
    """Schema for updating audit log entries (typically not used)."""
    pass


class AuditRepository(BaseRepository[AuditLog, AuditLogCreate, AuditLogUpdate]):
    """
    Repository for AuditLog model with specialized query methods.
    
    Extends BaseRepository to provide audit-specific operations:
    - List audit logs with filtering by entity_type, entity_id, user_id, date range
    - Query audit logs for compliance and debugging
    
    Note: Audit logs are typically write-only and should not be updated or deleted.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize AuditRepository with database session.
        
        Args:
            db: Async database session
        """
        super().__init__(AuditLog, db)
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """
        List audit logs with optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            entity_type: Filter by entity type ('agent', 'workflow', 'run')
            entity_id: Filter by specific entity UUID
            user_id: Filter by user who performed the action
            action: Filter by action type ('create', 'update', 'delete', 'execute')
            start_date: Filter logs created on or after this date
            end_date: Filter logs created on or before this date
        
        Returns:
            List of AuditLog instances
        """
        query = select(AuditLog)
        
        # Build filter conditions
        conditions = []
        
        if entity_type is not None:
            conditions.append(AuditLog.entity_type == entity_type)
        
        if entity_id is not None:
            conditions.append(AuditLog.entity_id == entity_id)
        
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        
        if action is not None:
            conditions.append(AuditLog.action == action)
        
        if start_date is not None:
            conditions.append(AuditLog.created_at >= start_date)
        
        if end_date is not None:
            conditions.append(AuditLog.created_at <= end_date)
        
        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Order by created_at descending (most recent first)
        query = query.order_by(AuditLog.created_at.desc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PaginationResult[AuditLog]:
        """
        List audit logs with pagination metadata and filtering.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            entity_type: Filter by entity type ('agent', 'workflow', 'run')
            entity_id: Filter by specific entity UUID
            user_id: Filter by user who performed the action
            action: Filter by action type ('create', 'update', 'delete', 'execute')
            start_date: Filter logs created on or after this date
            end_date: Filter logs created on or before this date
        
        Returns:
            PaginationResult with items and metadata
        """
        # Build filter dictionary for base method
        filters = {}
        
        # Build filter conditions for query
        conditions = []
        
        if entity_type is not None:
            conditions.append(AuditLog.entity_type == entity_type)
        
        if entity_id is not None:
            conditions.append(AuditLog.entity_id == entity_id)
        
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        
        if action is not None:
            conditions.append(AuditLog.action == action)
        
        if start_date is not None:
            conditions.append(AuditLog.created_at >= start_date)
        
        if end_date is not None:
            conditions.append(AuditLog.created_at <= end_date)
        
        # Build query with filters
        from sqlalchemy import select, func
        query = select(AuditLog)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply ordering (most recent first)
        query = query.order_by(AuditLog.created_at.desc())
        
        # Apply pagination
        skip = (page - 1) * page_size
        query = query.offset(skip).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        
        return PaginationResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get all audit logs for a specific entity.
        
        Args:
            entity_type: Type of entity ('agent', 'workflow', 'run')
            entity_id: UUID of the entity
            limit: Maximum number of records to return
        
        Returns:
            List of AuditLog instances ordered by created_at descending
        """
        return await self.list(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit
        )
    
    async def get_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get all audit logs for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of records to return
        
        Returns:
            List of AuditLog instances ordered by created_at descending
        """
        return await self.list(
            user_id=user_id,
            limit=limit
        )

"""Run repository for database operations on WorkflowRun and StepExecution models."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, desc, asc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.repositories.base import BaseRepository, PaginationResult
from src.database.models import WorkflowRun, StepExecution
from api.schemas.run import WorkflowExecuteRequest, WorkflowRetryRequest


class RunRepository(BaseRepository[WorkflowRun, WorkflowExecuteRequest, WorkflowRetryRequest]):
    """
    Repository for WorkflowRun model with specialized query methods.
    
    Extends BaseRepository to provide run-specific operations:
    - Get run by run_id (string identifier)
    - List runs with filtering by status, workflow_id, date range
    - Get step executions for a run
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize RunRepository with database session.
        
        Args:
            db: Async database session
        """
        super().__init__(WorkflowRun, db)
    
    async def get_by_run_id(self, run_id: str) -> Optional[WorkflowRun]:
        """
        Get a workflow run by its run_id (string identifier).
        
        Args:
            run_id: Run identifier to search for
        
        Returns:
            WorkflowRun instance or None if not found
        """
        result = await self.db.execute(
            select(WorkflowRun)
            .where(WorkflowRun.run_id == run_id)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        workflow_id: Optional[str] = None,
        workflow_definition_id: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[WorkflowRun]:
        """
        List workflow runs with optional filtering and sorting.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            status: Optional status filter (e.g., 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')
            workflow_id: Optional workflow_id filter
            workflow_definition_id: Optional workflow_definition_id filter (UUID reference)
            created_after: Optional filter for runs created after this datetime
            created_before: Optional filter for runs created before this datetime
            sort_by: Field to sort by ('created_at', 'updated_at', 'completed_at', 'status')
            sort_order: Sort order ('asc' or 'desc')
        
        Returns:
            List of WorkflowRun instances
        """
        query = select(WorkflowRun)
        
        # Apply filters
        conditions = []
        
        if status is not None:
            conditions.append(WorkflowRun.status == status)
        
        if workflow_id is not None:
            conditions.append(WorkflowRun.workflow_id == workflow_id)
        
        if workflow_definition_id is not None:
            conditions.append(WorkflowRun.workflow_definition_id == workflow_definition_id)
        
        if created_after is not None:
            conditions.append(WorkflowRun.created_at >= created_after)
        
        if created_before is not None:
            conditions.append(WorkflowRun.created_at <= created_before)
        
        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Apply sorting
        sort_column = getattr(WorkflowRun, sort_by, WorkflowRun.created_at)
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
        workflow_id: Optional[str] = None,
        workflow_definition_id: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginationResult[WorkflowRun]:
        """
        List workflow runs with pagination metadata, filtering, and sorting.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Optional status filter
            workflow_id: Optional workflow_id filter
            workflow_definition_id: Optional workflow_definition_id filter
            created_after: Optional filter for runs created after this datetime
            created_before: Optional filter for runs created before this datetime
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
        
        Returns:
            PaginationResult with items and metadata
        """
        from sqlalchemy import func
        
        # Build base query with filters
        query = select(WorkflowRun)
        
        conditions = []
        
        if status is not None:
            conditions.append(WorkflowRun.status == status)
        
        if workflow_id is not None:
            conditions.append(WorkflowRun.workflow_id == workflow_id)
        
        if workflow_definition_id is not None:
            conditions.append(WorkflowRun.workflow_definition_id == workflow_definition_id)
        
        if created_after is not None:
            conditions.append(WorkflowRun.created_at >= created_after)
        
        if created_before is not None:
            conditions.append(WorkflowRun.created_at <= created_before)
        
        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply sorting
        sort_column = getattr(WorkflowRun, sort_by, WorkflowRun.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
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
    
    async def get_steps(self, run_id: str) -> List[StepExecution]:
        """
        Get all step executions for a workflow run, ordered by started_at.
        
        Args:
            run_id: Run identifier to get steps for
        
        Returns:
            List of StepExecution instances ordered by started_at
        """
        query = (
            select(StepExecution)
            .where(StepExecution.run_id == run_id)
            .order_by(asc(StepExecution.started_at))
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_with_steps(self, run_id: str) -> Optional[WorkflowRun]:
        """
        Get a workflow run with all its step executions eagerly loaded.
        
        Args:
            run_id: Run identifier to search for
        
        Returns:
            WorkflowRun instance with step_executions loaded, or None if not found
        """
        result = await self.db.execute(
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.step_executions))
            .where(WorkflowRun.run_id == run_id)
        )
        return result.scalar_one_or_none()
    
    async def update_status(
        self,
        run_id: str,
        status: str,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None
    ) -> Optional[WorkflowRun]:
        """
        Update the status of a workflow run.
        
        Args:
            run_id: Run identifier to update
            status: New status value
            error_message: Optional error message if status is FAILED
            completed_at: Optional completion timestamp
        
        Returns:
            Updated WorkflowRun instance or None if not found
        """
        run = await self.get_by_run_id(run_id)
        if not run:
            return None
        
        run.status = status
        run.updated_at = datetime.utcnow()
        
        if error_message is not None:
            run.error_message = error_message
        
        if completed_at is not None:
            run.completed_at = completed_at
        
        await self.db.flush()
        await self.db.refresh(run)
        
        return run
    
    async def cancel_run(
        self,
        run_id: str,
        cancelled_by: str
    ) -> Optional[WorkflowRun]:
        """
        Cancel a workflow run by updating its status and cancellation metadata.
        
        Args:
            run_id: Run identifier to cancel
            cancelled_by: User identifier who cancelled the run
        
        Returns:
            Updated WorkflowRun instance or None if not found
        """
        run = await self.get_by_run_id(run_id)
        if not run:
            return None
        
        run.status = 'CANCELLED'
        run.cancelled_at = datetime.utcnow()
        run.cancelled_by = cancelled_by
        run.updated_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(run)
        
        return run

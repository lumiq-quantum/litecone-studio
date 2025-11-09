"""Audit service for logging and querying system actions."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories.audit import AuditRepository, AuditLogCreate
from api.models.audit import AuditLog


class AuditService:
    """
    Service for managing audit logs.
    
    This service provides methods for logging system actions and querying
    audit logs for compliance and debugging purposes.
    
    Requirements:
    - 12.1: Log agent create, update, delete actions
    - 12.2: Log workflow create, update, delete actions
    - 12.3: Log workflow execution triggers
    - 12.4: Support filtering by user, action type, and date range
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize AuditService with database session.
        
        Args:
            db: Async database session
        """
        self.repository = AuditRepository(db)
    
    async def log_action(
        self,
        entity_type: str,
        entity_id: UUID,
        action: str,
        user_id: Optional[str] = None,
        changes: Optional[dict] = None
    ) -> AuditLog:
        """
        Log an action performed on an entity.
        
        This method creates an audit log entry for any action performed
        on agents, workflows, or runs. It captures who performed the action,
        what was changed, and when it occurred.
        
        Args:
            entity_type: Type of entity ('agent', 'workflow', 'run')
            entity_id: UUID of the entity being audited
            action: Action performed ('create', 'update', 'delete', 'execute')
            user_id: Identifier of the user who performed the action
            changes: Dictionary containing the changes made or action details
        
        Returns:
            Created AuditLog instance
        
        Examples:
            # Log agent creation
            await audit_service.log_action(
                entity_type="agent",
                entity_id=agent.id,
                action="create",
                user_id="admin@example.com",
                changes={"name": "my-agent", "url": "http://agent.example.com"}
            )
            
            # Log workflow execution
            await audit_service.log_action(
                entity_type="run",
                entity_id=run.id,
                action="execute",
                user_id="operator@example.com",
                changes={"workflow_id": str(workflow.id), "input_data": {...}}
            )
        
        Requirements:
        - 12.1: Logs agent actions with user, timestamp, and changes
        - 12.2: Logs workflow actions with user, timestamp, and changes
        - 12.3: Logs workflow execution with user, timestamp, and input data
        """
        audit_data = AuditLogCreate(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            changes=changes
        )
        
        return await self.repository.create(audit_data)
    
    async def query_logs(
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
        Query audit logs with filtering.
        
        This method retrieves audit logs with optional filtering by entity type,
        entity ID, user, action type, and date range. Results are ordered by
        created_at descending (most recent first).
        
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
            List of AuditLog instances ordered by created_at descending
        
        Examples:
            # Get all logs for a specific agent
            logs = await audit_service.query_logs(
                entity_type="agent",
                entity_id=agent_id
            )
            
            # Get all actions by a specific user
            logs = await audit_service.query_logs(
                user_id="admin@example.com",
                limit=50
            )
            
            # Get all workflow executions in a date range
            logs = await audit_service.query_logs(
                entity_type="run",
                action="execute",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31)
            )
        
        Requirements:
        - 12.4: Supports filtering by user, action type, and date range
        """
        return await self.repository.list(
            skip=skip,
            limit=limit,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date
        )
    
    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get complete audit history for a specific entity.
        
        This is a convenience method for retrieving all audit logs
        related to a specific entity.
        
        Args:
            entity_type: Type of entity ('agent', 'workflow', 'run')
            entity_id: UUID of the entity
            limit: Maximum number of records to return
        
        Returns:
            List of AuditLog instances ordered by created_at descending
        
        Example:
            # Get all changes to a workflow
            history = await audit_service.get_entity_history(
                entity_type="workflow",
                entity_id=workflow_id
            )
        """
        return await self.repository.get_by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit
        )
    
    async def get_user_actions(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get all actions performed by a specific user.
        
        This is a convenience method for retrieving all audit logs
        for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of records to return
        
        Returns:
            List of AuditLog instances ordered by created_at descending
        
        Example:
            # Get all actions by a user
            actions = await audit_service.get_user_actions(
                user_id="admin@example.com"
            )
        """
        return await self.repository.get_by_user(
            user_id=user_id,
            limit=limit
        )

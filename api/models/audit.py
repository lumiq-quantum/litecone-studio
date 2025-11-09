"""Audit log database model for the Workflow Management API."""

from sqlalchemy import Column, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from api.database import Base


class AuditLog(Base):
    """
    AuditLog model for tracking all system changes and actions.
    
    This model provides a comprehensive audit trail for compliance and debugging.
    All create, update, delete, and execute actions are logged with full context.
    
    Attributes:
        id: Unique identifier (UUID)
        entity_type: Type of entity being audited ('agent', 'workflow', 'run')
        entity_id: UUID of the entity being audited
        action: Action performed ('create', 'update', 'delete', 'execute')
        user_id: Identifier of the user who performed the action
        changes: JSON object containing the changes made or action details
        created_at: Timestamp when the audit log entry was created
        updated_at: Timestamp when the audit log entry was last updated
    """
    
    __tablename__ = "audit_logs"
    
    # Entity identification
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Action details
    action = Column(String(50), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    
    # Change details stored as JSONB for flexibility
    changes = Column(JSONB, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_audit_logs_entity_type", "entity_type"),
        Index("idx_audit_logs_entity_id", "entity_id"),
        Index("idx_audit_logs_entity_type_id", "entity_type", "entity_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        """String representation of AuditLog."""
        return (
            f"<AuditLog(id={self.id}, entity_type='{self.entity_type}', "
            f"entity_id={self.entity_id}, action='{self.action}', "
            f"user_id='{self.user_id}')>"
        )

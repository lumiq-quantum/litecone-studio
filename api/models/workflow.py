"""Workflow database models for the Workflow Management API."""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship
from api.database import Base


class WorkflowDefinition(Base):
    """
    WorkflowDefinition model representing workflow templates/blueprints.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Workflow name (unique with version)
        description: Optional description of the workflow
        version: Version number (incremented on updates)
        workflow_data: Complete workflow JSON structure
        status: Workflow status ('active', 'inactive', 'deleted')
        created_at: Timestamp when workflow was created
        updated_at: Timestamp when workflow was last updated
        created_by: User who created the workflow
        updated_by: User who last updated the workflow
    """
    
    __tablename__ = "workflow_definitions"
    
    # Core fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    
    # Complete workflow data stored as JSONB
    workflow_data = Column(JSONB, nullable=False)
    
    # Status and audit fields
    status = Column(String(50), nullable=False, default="active", index=True)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Relationship to workflow steps
    steps = relationship(
        "WorkflowStep",
        back_populates="workflow_definition",
        cascade="all, delete-orphan"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_workflow_definitions_name", "name"),
        Index("idx_workflow_definitions_status", "status"),
        Index("idx_workflow_definitions_version", "version"),
        Index("idx_workflow_definitions_name_version", "name", "version", unique=True),
    )
    
    def __repr__(self) -> str:
        """String representation of WorkflowDefinition."""
        return f"<WorkflowDefinition(id={self.id}, name='{self.name}', version={self.version}, status='{self.status}')>"


class WorkflowStep(Base):
    """
    WorkflowStep model representing individual steps within a workflow.
    
    Attributes:
        id: Unique identifier (UUID)
        workflow_id: Foreign key to workflow_definitions
        step_id: Step identifier within the workflow
        agent_id: Foreign key to agents table
        next_step_id: ID of the next step in the workflow
        input_mapping: JSON mapping for step inputs
        step_order: Order of step execution
        created_at: Timestamp when step was created
        updated_at: Timestamp when step was last updated
    """
    
    __tablename__ = "workflow_steps"
    
    # Foreign key to workflow definition
    workflow_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Step identification
    step_id = Column(String(255), nullable=False)
    
    # Foreign key to agent
    agent_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=True
    )
    
    # Workflow navigation
    next_step_id = Column(String(255), nullable=True)
    
    # Step configuration
    input_mapping = Column(JSONB, nullable=True)
    step_order = Column(Integer, nullable=True)
    
    # Relationship to workflow definition
    workflow_definition = relationship(
        "WorkflowDefinition",
        back_populates="steps"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_workflow_steps_workflow_id", "workflow_id"),
        Index("idx_workflow_steps_workflow_step", "workflow_id", "step_id", unique=True),
    )
    
    def __repr__(self) -> str:
        """String representation of WorkflowStep."""
        return f"<WorkflowStep(id={self.id}, workflow_id={self.workflow_id}, step_id='{self.step_id}')>"

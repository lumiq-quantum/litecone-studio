"""SQLAlchemy models for workflow execution tracking."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class WorkflowRun(Base):
    """Model for tracking workflow run execution state."""
    
    __tablename__ = 'workflow_runs'
    
    run_id = Column(String(255), primary_key=True)
    workflow_id = Column(String(255), nullable=False)
    workflow_name = Column(String(255), nullable=False)
    workflow_definition_id = Column(String(255), nullable=True)  # UUID reference to workflow_definitions table
    status = Column(String(50), nullable=False)
    input_data = Column(JSONB, nullable=True)  # Input data provided when triggering the workflow
    triggered_by = Column(String(255), nullable=True)  # User or system that triggered the execution
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)  # Timestamp when workflow was cancelled
    cancelled_by = Column(String(255), nullable=True)  # User who cancelled the workflow
    error_message = Column(Text, nullable=True)
    
    # Relationship to step executions
    step_executions = relationship("StepExecution", back_populates="workflow_run", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_run_status', 'status'),
        Index('idx_run_workflow_definition_id', 'workflow_definition_id'),
    )


class StepExecution(Base):
    """Model for tracking individual step execution within a workflow run."""
    
    __tablename__ = 'step_executions'
    
    id = Column(String(255), primary_key=True)
    run_id = Column(String(255), ForeignKey('workflow_runs.run_id'), nullable=False)
    step_id = Column(String(255), nullable=False)
    step_name = Column(String(255), nullable=False)
    agent_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB, nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Parallel execution tracking
    parent_step_id = Column(String(255), nullable=True)  # For parallel/fork-join steps
    branch_name = Column(String(255), nullable=True)  # Branch name for fork-join
    join_policy = Column(String(50), nullable=True)  # Join policy for fork-join
    
    # Relationship to workflow run
    workflow_run = relationship("WorkflowRun", back_populates="step_executions")
    
    __table_args__ = (
        Index('idx_step_run_id', 'run_id'),
        Index('idx_step_status', 'status'),
        Index('idx_step_branch', 'run_id', 'parent_step_id', 'branch_name'),
    )

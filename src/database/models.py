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
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationship to step executions
    step_executions = relationship("StepExecution", back_populates="workflow_run", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_run_status', 'status'),
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
    
    # Relationship to workflow run
    workflow_run = relationship("WorkflowRun", back_populates="step_executions")
    
    __table_args__ = (
        Index('idx_step_run_id', 'run_id'),
        Index('idx_step_status', 'status'),
    )

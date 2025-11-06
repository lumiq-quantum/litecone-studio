"""Repository layer for database operations."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.database.models import WorkflowRun, StepExecution


class WorkflowRepository:
    """Repository for WorkflowRun database operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy Session instance
        """
        self.session = session
    
    def create_run(
        self,
        run_id: str,
        workflow_id: str,
        workflow_name: str,
        status: str = "PENDING"
    ) -> WorkflowRun:
        """
        Create a new workflow run record.
        
        Args:
            run_id: Unique identifier for the workflow run
            workflow_id: Identifier of the workflow definition
            workflow_name: Human-readable name of the workflow
            status: Initial status (default: PENDING)
        
        Returns:
            Created WorkflowRun instance
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        workflow_run = WorkflowRun(
            run_id=run_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(workflow_run)
        self.session.commit()
        self.session.refresh(workflow_run)
        return workflow_run
    
    def update_run_status(
        self,
        run_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[WorkflowRun]:
        """
        Update the status of a workflow run.
        
        Args:
            run_id: Unique identifier for the workflow run
            status: New status value
            error_message: Optional error message if status is FAILED
        
        Returns:
            Updated WorkflowRun instance or None if not found
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        workflow_run = self.session.query(WorkflowRun).filter(
            WorkflowRun.run_id == run_id
        ).first()
        
        if workflow_run:
            workflow_run.status = status
            workflow_run.updated_at = datetime.utcnow()
            
            if status in ("COMPLETED", "FAILED"):
                workflow_run.completed_at = datetime.utcnow()
            
            if error_message:
                workflow_run.error_message = error_message
            
            self.session.commit()
            self.session.refresh(workflow_run)
        
        return workflow_run
    
    def get_run(self, run_id: str) -> Optional[WorkflowRun]:
        """
        Retrieve a workflow run by ID.
        
        Args:
            run_id: Unique identifier for the workflow run
        
        Returns:
            WorkflowRun instance or None if not found
        """
        return self.session.query(WorkflowRun).filter(
            WorkflowRun.run_id == run_id
        ).first()


class StepRepository:
    """Repository for StepExecution database operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy Session instance
        """
        self.session = session
    
    def create_step(
        self,
        step_execution_id: str,
        run_id: str,
        step_id: str,
        step_name: str,
        agent_name: str,
        input_data: Dict[str, Any],
        status: str = "RUNNING"
    ) -> StepExecution:
        """
        Create a new step execution record.
        
        Args:
            step_execution_id: Unique identifier for this step execution
            run_id: Workflow run ID this step belongs to
            step_id: Step identifier from workflow plan
            step_name: Human-readable step name
            agent_name: Name of the agent executing this step
            input_data: Input data for the step (stored as JSONB)
            status: Initial status (default: RUNNING)
        
        Returns:
            Created StepExecution instance
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        step_execution = StepExecution(
            id=step_execution_id,
            run_id=run_id,
            step_id=step_id,
            step_name=step_name,
            agent_name=agent_name,
            status=status,
            input_data=input_data,
            started_at=datetime.utcnow()
        )
        self.session.add(step_execution)
        self.session.commit()
        self.session.refresh(step_execution)
        return step_execution
    
    def update_step(
        self,
        step_execution_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[StepExecution]:
        """
        Update a step execution with results.
        
        Args:
            step_execution_id: Unique identifier for the step execution
            status: New status value
            output_data: Optional output data from the step (stored as JSONB)
            error_message: Optional error message if status is FAILED
        
        Returns:
            Updated StepExecution instance or None if not found
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        step_execution = self.session.query(StepExecution).filter(
            StepExecution.id == step_execution_id
        ).first()
        
        if step_execution:
            step_execution.status = status
            
            if status in ("COMPLETED", "FAILED"):
                step_execution.completed_at = datetime.utcnow()
            
            if output_data is not None:
                step_execution.output_data = output_data
            
            if error_message:
                step_execution.error_message = error_message
            
            self.session.commit()
            self.session.refresh(step_execution)
        
        return step_execution
    
    def get_steps_by_run_id(self, run_id: str) -> List[StepExecution]:
        """
        Retrieve all step executions for a workflow run.
        
        Args:
            run_id: Workflow run ID
        
        Returns:
            List of StepExecution instances ordered by started_at
        """
        return self.session.query(StepExecution).filter(
            StepExecution.run_id == run_id
        ).order_by(StepExecution.started_at).all()
    
    def get_step_by_id(self, step_execution_id: str) -> Optional[StepExecution]:
        """
        Retrieve a specific step execution by ID.
        
        Args:
            step_execution_id: Unique identifier for the step execution
        
        Returns:
            StepExecution instance or None if not found
        """
        return self.session.query(StepExecution).filter(
            StepExecution.id == step_execution_id
        ).first()


class TransactionManager:
    """Manager for atomic database transactions."""
    
    def __init__(self, session: Session):
        """
        Initialize transaction manager with database session.
        
        Args:
            session: SQLAlchemy Session instance
        """
        self.session = session
    
    def begin_transaction(self) -> None:
        """Begin a new transaction."""
        self.session.begin()
    
    def commit_transaction(self) -> None:
        """Commit the current transaction."""
        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise
    
    def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        self.session.rollback()
    
    def execute_in_transaction(self, operations: List[callable]) -> None:
        """
        Execute multiple operations in a single atomic transaction.
        
        Args:
            operations: List of callable functions to execute
        
        Raises:
            SQLAlchemyError: If any operation fails
        """
        try:
            self.begin_transaction()
            for operation in operations:
                operation()
            self.commit_transaction()
        except Exception:
            self.rollback_transaction()
            raise

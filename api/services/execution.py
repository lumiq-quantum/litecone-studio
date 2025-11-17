"""Execution service for managing workflow execution lifecycle."""

import logging
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories.workflow import WorkflowRepository
from api.repositories.run import RunRepository
from api.services.kafka import KafkaService
from api.services.audit import AuditService
from api.schemas.run import WorkflowExecuteRequest
from src.database.models import WorkflowRun, StepExecution

logger = logging.getLogger(__name__)


class ExecutionService:
    """
    Service for managing workflow execution lifecycle.
    
    This service provides business logic for workflow execution operations including
    triggering executions, retrying failed runs, cancelling running workflows,
    and retrieving run information.
    
    Requirements:
    - 3.1: Trigger workflow execution via POST /api/v1/workflows/{workflow_id}/execute
    - 3.2: Return run_id immediately without waiting for completion
    - 3.3: Resume failed workflow from last incomplete step via POST /api/v1/runs/{run_id}/retry
    - 3.4: Cancel running workflow via POST /api/v1/runs/{run_id}/cancel
    - 3.5: Validate input data against workflow definition schema
    - 4.1: List workflow runs with filtering via GET /api/v1/runs
    - 4.2: Get run details via GET /api/v1/runs/{run_id}
    - 4.3: Get step executions via GET /api/v1/runs/{run_id}/steps
    - 11.1: Publish execution request to Kafka for executor service
    - 11.3: Record error and mark run as failed when executor fails
    - 11.5: Queue execution requests when executor is unavailable
    """
    
    def __init__(self, db: AsyncSession, kafka_service: Optional[KafkaService] = None):
        """
        Initialize ExecutionService with database session and Kafka service.
        
        Args:
            db: Async database session
            kafka_service: Optional KafkaService instance for publishing messages
        """
        self.workflow_repository = WorkflowRepository(db)
        self.run_repository = RunRepository(db)
        self.kafka_service = kafka_service or KafkaService()
        self.audit_service = AuditService(db)
        self.db = db
    
    async def execute_workflow(
        self,
        workflow_id: UUID,
        execute_request: WorkflowExecuteRequest,
        user_id: Optional[str] = None
    ) -> WorkflowRun:
        """
        Trigger workflow execution by creating a run and publishing to Kafka.
        
        This method:
        1. Validates the workflow exists and is active
        2. Creates a workflow run record in the database
        3. Publishes execution request to Kafka for the executor service
        4. Logs the execution action
        5. Returns immediately without waiting for completion
        
        Args:
            workflow_id: UUID of the workflow definition to execute
            execute_request: Execution request containing input data
            user_id: Identifier of the user triggering the execution
        
        Returns:
            Created WorkflowRun instance with PENDING status
        
        Raises:
            ValueError: If workflow not found, inactive, or validation fails
            RuntimeError: If Kafka publishing fails
        
        Example:
            run = await execution_service.execute_workflow(
                workflow_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
                execute_request=WorkflowExecuteRequest(
                    input_data={"source": "s3://bucket/data.csv"}
                ),
                user_id="user@example.com"
            )
            print(f"Workflow execution started: {run.run_id}")
        
        Requirements:
        - 3.1: Creates run record and triggers executor service
        - 3.2: Returns run_id immediately without waiting for completion
        - 3.5: Validates input data against workflow definition
        - 11.1: Publishes execution request to Kafka
        """
        # Get workflow definition
        workflow = await self.workflow_repository.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow with id '{workflow_id}' not found")
        
        if workflow.status != 'active':
            raise ValueError(
                f"Workflow '{workflow.name}' is not active (status: {workflow.status})"
            )
        
        # Validate input data (basic validation - executor will do detailed validation)
        if execute_request.input_data is None:
            raise ValueError("input_data cannot be null")
        
        # Generate unique run_id
        run_id = f"run-{uuid4()}"
        
        # Create run record with PENDING status
        run = WorkflowRun(
            run_id=run_id,
            workflow_id=str(workflow_id),  # Use the actual workflow UUID from database
            workflow_name=workflow.name,
            workflow_definition_id=str(workflow_id),
            status='PENDING',
            input_data=execute_request.input_data,
            triggered_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        
        logger.info(
            f"Created workflow run '{run_id}' for workflow '{workflow.name}'",
            extra={
                "run_id": run_id,
                "workflow_id": str(workflow_id),
                "workflow_name": workflow.name,
                "triggered_by": user_id
            }
        )
        
        # Publish to Kafka for executor
        try:
            await self.kafka_service.publish_execution_request(
                run_id=run_id,
                workflow_plan=workflow.workflow_data,
                input_data=execute_request.input_data,
                workflow_name=workflow.name
            )
            
            logger.info(
                f"Published execution request for run '{run_id}' to Kafka",
                extra={
                    "run_id": run_id,
                    "workflow_name": workflow.name
                }
            )
        except Exception as e:
            # Log error but don't fail - executor can pick up PENDING runs
            logger.error(
                f"Failed to publish execution request for run '{run_id}': {e}",
                extra={
                    "run_id": run_id,
                    "workflow_name": workflow.name,
                    "error": str(e)
                }
            )
            # Update run with error but keep PENDING status for retry
            run.error_message = f"Failed to publish to Kafka: {str(e)}"
            await self.db.flush()
            await self.db.refresh(run)
        
        # Log the execution action
        await self.audit_service.log_action(
            entity_type="run",
            entity_id=UUID(run.run_id.replace("run-", "")),
            action="execute",
            user_id=user_id,
            changes={
                "workflow_id": str(workflow_id),
                "workflow_name": workflow.name,
                "input_data": execute_request.input_data
            }
        )
        
        # Commit transaction
        await self.db.commit()
        
        return run
    
    async def retry_workflow(
        self,
        run_id: str,
        user_id: Optional[str] = None
    ) -> WorkflowRun:
        """
        Retry a failed workflow from the last incomplete step.
        
        This method:
        1. Validates the run exists and can be retried (FAILED or CANCELLED status)
        2. Updates the run status to PENDING
        3. Republishes execution request to Kafka (executor will resume from last step)
        4. Logs the retry action
        
        Args:
            run_id: Run identifier to retry
            user_id: Identifier of the user requesting the retry
        
        Returns:
            Updated WorkflowRun instance with PENDING status
        
        Raises:
            ValueError: If run not found or cannot be retried
            RuntimeError: If Kafka publishing fails
        
        Example:
            run = await execution_service.retry_workflow(
                run_id="run-123e4567-e89b-12d3-a456-426614174000",
                user_id="user@example.com"
            )
            print(f"Workflow retry initiated: {run.run_id}")
        
        Requirements:
        - 3.3: Resumes failed workflow from last incomplete step
        - 11.1: Publishes execution request to Kafka for executor
        """
        # Get the run
        run = await self.run_repository.get_by_run_id(run_id)
        if not run:
            raise ValueError(f"Run '{run_id}' not found")
        
        # Validate run can be retried
        if run.status not in ['FAILED', 'CANCELLED']:
            raise ValueError(
                f"Can only retry failed or cancelled runs. Current status: {run.status}"
            )
        
        logger.info(
            f"Retrying workflow run '{run_id}'",
            extra={
                "run_id": run_id,
                "workflow_name": run.workflow_name,
                "previous_status": run.status,
                "user_id": user_id
            }
        )
        
        # Get workflow definition for republishing
        if not run.workflow_definition_id:
            raise ValueError(f"Run '{run_id}' has no workflow_definition_id")
        
        workflow = await self.workflow_repository.get_by_id(UUID(run.workflow_definition_id))
        if not workflow:
            raise ValueError(
                f"Workflow definition '{run.workflow_definition_id}' not found"
            )
        
        # Update run status to PENDING and clear error
        run.status = 'PENDING'
        run.error_message = None
        run.updated_at = datetime.utcnow()
        run.cancelled_at = None
        run.cancelled_by = None
        
        await self.db.flush()
        await self.db.refresh(run)
        
        # Republish to Kafka (executor will resume from last incomplete step)
        try:
            await self.kafka_service.publish_execution_request(
                run_id=run_id,
                workflow_plan=workflow.workflow_data,
                input_data=run.input_data or {},
                workflow_name=run.workflow_name
            )
            
            logger.info(
                f"Published retry request for run '{run_id}' to Kafka",
                extra={
                    "run_id": run_id,
                    "workflow_name": run.workflow_name
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to publish retry request for run '{run_id}': {e}",
                extra={
                    "run_id": run_id,
                    "workflow_name": run.workflow_name,
                    "error": str(e)
                }
            )
            # Update run with error but keep PENDING status
            run.error_message = f"Failed to publish retry to Kafka: {str(e)}"
            await self.db.flush()
            await self.db.refresh(run)
        
        # Log the retry action
        await self.audit_service.log_action(
            entity_type="run",
            entity_id=UUID(run_id.replace("run-", "")),
            action="retry",
            user_id=user_id,
            changes={
                "previous_status": "FAILED" if run.status == "PENDING" else run.status
            }
        )
        
        # Commit transaction
        await self.db.commit()
        
        return run
    
    async def cancel_workflow(
        self,
        run_id: str,
        user_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> WorkflowRun:
        """
        Cancel a running workflow.
        
        This method:
        1. Validates the run exists and can be cancelled (PENDING or RUNNING status)
        2. Updates the run status to CANCELLED with cancellation metadata
        3. Publishes cancellation request to Kafka to stop executor
        4. Logs the cancellation action
        
        Args:
            run_id: Run identifier to cancel
            user_id: Identifier of the user requesting cancellation
            reason: Optional reason for cancellation
        
        Returns:
            Updated WorkflowRun instance with CANCELLED status
        
        Raises:
            ValueError: If run not found or cannot be cancelled
        
        Example:
            run = await execution_service.cancel_workflow(
                run_id="run-123e4567-e89b-12d3-a456-426614174000",
                user_id="user@example.com",
                reason="Incorrect input data"
            )
            print(f"Workflow cancelled: {run.run_id}")
        
        Requirements:
        - 3.4: Marks run as cancelled and stops further step execution
        - 11.4: Notifies executor service via Kafka when workflow is cancelled
        """
        # Get the run
        run = await self.run_repository.get_by_run_id(run_id)
        if not run:
            raise ValueError(f"Run '{run_id}' not found")
        
        # Validate run can be cancelled
        if run.status not in ['PENDING', 'RUNNING']:
            raise ValueError(
                f"Can only cancel pending or running workflows. Current status: {run.status}"
            )
        
        logger.info(
            f"Cancelling workflow run '{run_id}'",
            extra={
                "run_id": run_id,
                "workflow_name": run.workflow_name,
                "previous_status": run.status,
                "user_id": user_id,
                "reason": reason
            }
        )
        
        # Update run status to CANCELLED
        run.status = 'CANCELLED'
        run.cancelled_at = datetime.utcnow()
        run.cancelled_by = user_id
        run.updated_at = datetime.utcnow()
        
        if reason:
            run.error_message = f"Cancelled: {reason}"
        
        await self.db.flush()
        await self.db.refresh(run)
        
        # Publish cancellation request to Kafka
        try:
            await self.kafka_service.publish_cancellation_request(
                run_id=run_id,
                cancelled_by=user_id,
                reason=reason
            )
            
            logger.info(
                f"Published cancellation request for run '{run_id}' to Kafka",
                extra={
                    "run_id": run_id,
                    "workflow_name": run.workflow_name,
                    "cancelled_by": user_id
                }
            )
        except Exception as e:
            # Log error but don't fail - run is already marked as cancelled
            logger.error(
                f"Failed to publish cancellation request for run '{run_id}': {e}",
                extra={
                    "run_id": run_id,
                    "workflow_name": run.workflow_name,
                    "error": str(e)
                }
            )
        
        # Log the cancellation action
        await self.audit_service.log_action(
            entity_type="run",
            entity_id=UUID(run_id.replace("run-", "")),
            action="cancel",
            user_id=user_id,
            changes={
                "reason": reason,
                "previous_status": "RUNNING" if run.status == "CANCELLED" else run.status
            }
        )
        
        # Commit transaction
        await self.db.commit()
        
        return run
    
    async def get_run(self, run_id: str) -> Optional[WorkflowRun]:
        """
        Get workflow run details by run_id.
        
        Args:
            run_id: Run identifier to retrieve
        
        Returns:
            WorkflowRun instance or None if not found
        
        Example:
            run = await execution_service.get_run("run-123e4567-e89b-12d3-a456-426614174000")
            if run:
                print(f"Run status: {run.status}")
        
        Requirements:
        - 4.2: Returns complete run details including status, timestamps, and error messages
        """
        return await self.run_repository.get_by_run_id(run_id)
    
    async def list_runs(
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
        List workflow runs with filtering, sorting, and pagination.
        
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
        
        Example:
            # Get all failed runs for a specific workflow
            runs = await execution_service.list_runs(
                status="FAILED",
                workflow_definition_id="123e4567-e89b-12d3-a456-426614174000",
                limit=50
            )
        
        Requirements:
        - 4.1: Returns paginated list with filtering by status, workflow_id, and date range
        """
        return await self.run_repository.list(
            skip=skip,
            limit=limit,
            status=status,
            workflow_id=workflow_id,
            workflow_definition_id=workflow_definition_id,
            created_after=created_after,
            created_before=created_before,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    async def get_run_steps(self, run_id: str) -> List[StepExecution]:
        """
        Get all step executions for a workflow run.
        
        Args:
            run_id: Run identifier to get steps for
        
        Returns:
            List of StepExecution instances ordered by started_at
        
        Example:
            steps = await execution_service.get_run_steps("run-123e4567-e89b-12d3-a456-426614174000")
            for step in steps:
                print(f"Step {step.step_id}: {step.status}")
        
        Requirements:
        - 4.3: Returns all step executions for the run with their status and output data
        """
        return await self.run_repository.get_steps(run_id)

"""Centralized Executor for workflow orchestration."""

import asyncio
import logging
import uuid
import signal
import sys
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

from src.models.workflow import WorkflowPlan, WorkflowStep
from src.models.kafka_messages import AgentTask, AgentResult, MonitoringUpdate
from src.models.input_resolver import InputMappingResolver
from src.kafka_client.producer import KafkaProducerClient
from src.kafka_client.consumer import KafkaConsumerClient
from src.database.connection import DatabaseConnection
from src.database.repositories import WorkflowRepository, StepRepository
from src.agent_registry.client import AgentRegistryClient
from src.utils.logging import setup_logging, set_correlation_id, log_event
from src.executor.execution_models import ExecutionStatus, StepResult
from src.executor.parallel_executor import ParallelExecutor, ParallelBlock
from src.executor.conditional_executor import ConditionalExecutor
from src.executor.loop_executor import LoopExecutor
from src.executor.fork_join_executor import ForkJoinExecutor

logger = logging.getLogger(__name__)


class CentralizedExecutor:
    """
    Centralized Executor for orchestrating workflow execution.
    
    This executor is ephemeral and spawned per workflow run. It manages
    the execution of workflow steps by publishing tasks to Kafka and
    consuming results, while persisting state to the database.
    """
    
    def __init__(
        self,
        run_id: str,
        workflow_plan: WorkflowPlan,
        initial_input: Dict[str, Any],
        kafka_bootstrap_servers: str,
        database_url: str,
        agent_registry_url: str,
        kafka_client_id: Optional[str] = None,
        kafka_group_id: Optional[str] = None
    ):
        """
        Initialize the Centralized Executor.
        
        Args:
            run_id: Unique identifier for this workflow run
            workflow_plan: The workflow plan to execute
            initial_input: Initial input data for the workflow
            kafka_bootstrap_servers: Comma-separated Kafka broker addresses
            database_url: PostgreSQL connection URL
            agent_registry_url: Base URL of the Agent Registry service
            kafka_client_id: Optional Kafka client ID
            kafka_group_id: Optional Kafka consumer group ID
        """
        self.run_id = run_id
        self.workflow_plan = workflow_plan
        self.initial_input = initial_input
        
        # Kafka configuration
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_client_id = kafka_client_id or f"executor-{run_id}"
        self.kafka_group_id = kafka_group_id or f"executor-group-{run_id}"
        
        # Database configuration
        self.database_url = database_url
        
        # Agent Registry configuration
        self.agent_registry_url = agent_registry_url
        
        # Components (initialized in initialize())
        self.kafka_producer: Optional[KafkaProducerClient] = None
        self.kafka_consumer: Optional[KafkaConsumerClient] = None
        self.database: Optional[DatabaseConnection] = None
        self.workflow_repo: Optional[WorkflowRepository] = None
        self.step_repo: Optional[StepRepository] = None
        self.agent_registry: Optional[AgentRegistryClient] = None
        
        # Execution state
        self.execution_state: Dict[str, StepResult] = {}
        self.step_outputs: Dict[str, Dict[str, Any]] = {}
        
        # Loop context (set when executing loop iterations)
        self.loop_context: Optional[Any] = None
        
        # Parallel executor (initialized after self reference is available)
        self.parallel_executor: Optional[ParallelExecutor] = None
        
        # Conditional executor (initialized after self reference is available)
        self.conditional_executor: Optional[ConditionalExecutor] = None
        
        # Loop executor (initialized after self reference is available)
        self.loop_executor: Optional[Any] = None
        
        # Fork-join executor (initialized after self reference is available)
        self.fork_join_executor: Optional[ForkJoinExecutor] = None
        
        logger.info(
            f"Initialized CentralizedExecutor for run_id={run_id}, "
            f"workflow_id={workflow_plan.workflow_id}"
        )
    
    async def initialize(self) -> None:
        """
        Initialize Kafka connections, database, and agent registry client.
        
        This method must be called before executing the workflow.
        
        Raises:
            Exception: If initialization of any component fails
        """
        logger.info(f"Initializing CentralizedExecutor for run_id={self.run_id}")
        
        try:
            # Initialize Kafka producer
            logger.debug("Initializing Kafka producer")
            self.kafka_producer = KafkaProducerClient(
                bootstrap_servers=self.kafka_bootstrap_servers,
                client_id=self.kafka_client_id
            )
            self.kafka_producer.connect()
            
            # Initialize Kafka consumer for results
            logger.debug("Initializing Kafka consumer")
            self.kafka_consumer = KafkaConsumerClient(
                topics=['results.topic'],
                bootstrap_servers=self.kafka_bootstrap_servers,
                group_id=self.kafka_group_id,
                client_id=self.kafka_client_id
            )
            self.kafka_consumer.connect()
            
            # Initialize database connection
            logger.debug("Initializing database connection")
            self.database = DatabaseConnection(self.database_url)
            self.database.create_tables()
            
            # Initialize repositories
            session = self.database.get_session()
            self.workflow_repo = WorkflowRepository(session)
            self.step_repo = StepRepository(session)
            
            # Initialize Agent Registry client
            logger.debug("Initializing Agent Registry client")
            self.agent_registry = AgentRegistryClient(self.agent_registry_url)
            
            # Initialize Parallel Executor
            logger.debug("Initializing Parallel Executor")
            self.parallel_executor = ParallelExecutor(self)
            
            # Initialize Conditional Executor
            logger.debug("Initializing Conditional Executor")
            self.conditional_executor = ConditionalExecutor(self)
            
            # Initialize Loop Executor
            logger.debug("Initializing Loop Executor")
            self.loop_executor = LoopExecutor(self)
            
            # Initialize Fork-Join Executor
            logger.debug("Initializing Fork-Join Executor")
            self.fork_join_executor = ForkJoinExecutor(self)
            
            # Validate workflow plan structure
            logger.debug("Validating workflow plan structure")
            self._validate_workflow_plan()
            
            logger.info(f"Successfully initialized CentralizedExecutor for run_id={self.run_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize CentralizedExecutor: {e}")
            await self.shutdown()
            raise
    
    def _validate_workflow_plan(self) -> None:
        """
        Validate the workflow plan structure.
        
        The WorkflowPlan Pydantic model already performs validation,
        but this method can add additional runtime checks if needed.
        
        Raises:
            ValueError: If the workflow plan is invalid
        """
        # Basic validation is already done by Pydantic model
        # Additional validation can be added here if needed
        
        logger.debug(
            f"Workflow plan validated: {len(self.workflow_plan.steps)} steps, "
            f"starting from '{self.workflow_plan.start_step}'"
        )
    
    async def shutdown(self) -> None:
        """
        Clean up resources and close connections.
        
        This method should be called when the executor is done,
        whether the workflow completed successfully or failed.
        """
        logger.info(f"Shutting down CentralizedExecutor for run_id={self.run_id}")
        
        # Close Kafka producer
        if self.kafka_producer:
            try:
                self.kafka_producer.close()
                logger.debug("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
        
        # Close Kafka consumer
        if self.kafka_consumer:
            try:
                self.kafka_consumer.close()
                logger.debug("Kafka consumer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")
        
        # Close database connection
        if self.database:
            try:
                self.database.close()
                logger.debug("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
        
        # Close Agent Registry client
        if self.agent_registry:
            try:
                await self.agent_registry.close()
                logger.debug("Agent Registry client closed")
            except Exception as e:
                logger.error(f"Error closing Agent Registry client: {e}")
        
        logger.info(f"CentralizedExecutor shutdown complete for run_id={self.run_id}")
    
    async def load_execution_state(self) -> None:
        """
        Load any existing execution state from the database for replay.
        
        This method queries the database for existing step executions
        and rebuilds the execution state map. This enables the executor
        to resume from the last incomplete step in case of failure.
        
        Raises:
            Exception: If database query fails
        """
        logger.info(f"Loading execution state for run_id={self.run_id}")
        
        try:
            # Query database for existing step executions
            step_executions = self.step_repo.get_steps_by_run_id(self.run_id)
            
            if not step_executions:
                logger.info(f"No existing execution state found for run_id={self.run_id}")
                return
            
            logger.info(f"Found {len(step_executions)} existing step executions")
            
            # Build execution state map from database records
            for step_execution in step_executions:
                step_result = StepResult(
                    step_id=step_execution.step_id,
                    status=step_execution.status,
                    input_data=step_execution.input_data,
                    output_data=step_execution.output_data,
                    error_message=step_execution.error_message
                )
                
                self.execution_state[step_execution.step_id] = step_result
                
                # If step completed successfully, store its output for input mapping
                if step_execution.status == ExecutionStatus.COMPLETED and step_execution.output_data:
                    self.step_outputs[step_execution.step_id] = step_execution.output_data
                    logger.debug(
                        f"Loaded output for step '{step_execution.step_id}' "
                        f"(agent: {step_execution.agent_name})"
                    )
            
            # Identify last completed step
            last_completed_step = self._identify_last_completed_step()
            
            if last_completed_step:
                logger.info(
                    f"Last completed step: '{last_completed_step}'. "
                    f"Workflow will resume from next step."
                )
            else:
                logger.info("No completed steps found. Workflow will start from beginning.")
            
        except Exception as e:
            logger.error(f"Failed to load execution state: {e}")
            raise
    
    def _identify_last_completed_step(self) -> Optional[str]:
        """
        Identify the last completed step in the workflow sequence.
        
        This method traverses the workflow from the start_step and finds
        the last step that has been completed successfully.
        
        Returns:
            The step_id of the last completed step, or None if no steps completed
        """
        current_step_id = self.workflow_plan.start_step
        last_completed = None
        
        while current_step_id is not None:
            # Check if this step has been completed
            if current_step_id in self.execution_state:
                step_result = self.execution_state[current_step_id]
                if step_result.status == ExecutionStatus.COMPLETED:
                    last_completed = current_step_id
                    # Move to next step
                    step = self.workflow_plan.steps[current_step_id]
                    current_step_id = step.next_step
                else:
                    # Step is not completed, stop here
                    break
            else:
                # Step has not been executed yet
                break
        
        return last_completed
    
    async def execute_workflow(self) -> None:
        """
        Execute the workflow from start to finish.
        
        This method implements the main execution loop that:
        1. Starts from start_step or resumes from last incomplete step
        2. Iterates through steps using next_step references
        3. Calls execute_step for each step
        4. Handles workflow completion when next_step is null
        
        Raises:
            Exception: If workflow execution fails
        """
        logger.info(
            f"Starting workflow execution for run_id={self.run_id}, "
            f"workflow_id={self.workflow_plan.workflow_id}"
        )
        
        try:
            # Create or update workflow run record in database
            existing_run = self.workflow_repo.get_run(self.run_id)
            if not existing_run:
                logger.debug("Creating new workflow run record")
                self.workflow_repo.create_run(
                    run_id=self.run_id,
                    workflow_id=self.workflow_plan.workflow_id,
                    workflow_name=self.workflow_plan.name,
                    status=ExecutionStatus.RUNNING
                )
            else:
                logger.debug("Updating existing workflow run record")
                self.workflow_repo.update_run_status(
                    run_id=self.run_id,
                    status=ExecutionStatus.RUNNING
                )
            
            # Determine starting step
            current_step_id = self._determine_starting_step()
            
            if current_step_id is None:
                logger.info("All steps already completed. Workflow is complete.")
                self.workflow_repo.update_run_status(
                    run_id=self.run_id,
                    status=ExecutionStatus.COMPLETED
                )
                return
            
            logger.info(f"Starting execution from step '{current_step_id}'")
            
            # Main execution loop
            while current_step_id is not None:
                step = self.workflow_plan.steps[current_step_id]
                
                logger.info(
                    f"Executing step '{step.id}' (agent: {step.agent_name})"
                )
                
                # Execute the step with recovery logic
                step_result = await self.execute_step_with_recovery(step)
                
                # Store result in execution state
                self.execution_state[step.id] = step_result
                
                # Check if step failed
                if step_result.status == ExecutionStatus.FAILED:
                    logger.error(
                        f"Step '{step.id}' failed: {step_result.error_message}"
                    )
                    # Handle the failure (marks workflow as FAILED)
                    await self.handle_step_failure(step, step_result.error_message)
                    raise Exception(f"Workflow failed at step '{step.id}': {step_result.error_message}")
                
                # Store output for future input mapping
                if step_result.output_data:
                    self.step_outputs[step.id] = step_result.output_data
                
                # Move to next step
                current_step_id = step.next_step
                
                if current_step_id:
                    logger.debug(f"Moving to next step: '{current_step_id}'")
                else:
                    logger.info("Reached end of workflow (next_step is null)")
            
            # Workflow completed successfully
            logger.info(f"Workflow execution completed successfully for run_id={self.run_id}")
            self.workflow_repo.update_run_status(
                run_id=self.run_id,
                status=ExecutionStatus.COMPLETED
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            # Ensure workflow is marked as failed
            try:
                self.workflow_repo.update_run_status(
                    run_id=self.run_id,
                    status=ExecutionStatus.FAILED,
                    error_message=str(e)
                )
            except Exception as db_error:
                logger.error(f"Failed to update workflow status: {db_error}")
            raise
    
    def _determine_starting_step(self) -> Optional[str]:
        """
        Determine which step to start execution from.
        
        If there are completed steps in the execution state, resume from
        the next incomplete step. Otherwise, start from the beginning.
        
        Returns:
            The step_id to start from, or None if all steps are completed
        """
        # Find the last completed step
        last_completed = self._identify_last_completed_step()
        
        if last_completed is None:
            # No completed steps, start from beginning
            return self.workflow_plan.start_step
        
        # Resume from the step after the last completed one
        last_completed_step = self.workflow_plan.steps[last_completed]
        next_step_id = last_completed_step.next_step
        
        if next_step_id is None:
            # All steps completed
            return None
        
        logger.info(
            f"Resuming workflow from step '{next_step_id}' "
            f"(after completed step '{last_completed}')"
        )
        
        return next_step_id
    
    async def execute_step(self, step: WorkflowStep) -> StepResult:
        """
        Execute a single workflow step.
        
        This method dispatches to the appropriate executor based on step type:
        - 'parallel': Dispatches to ParallelExecutor
        - 'agent': Executes as a standard agent step (default)
        
        For agent steps:
        1. Resolves input data using input_mapping and previous outputs
        2. Creates step execution record in database with status RUNNING
        3. Publishes monitoring update with status RUNNING
        4. Publishes AgentTask to orchestrator.tasks.http topic
        5. Waits for AgentResult from results.topic with correlation ID
        6. Updates step execution record with output_data and status COMPLETED/FAILED
        7. Publishes monitoring update with final status
        
        Args:
            step: The WorkflowStep to execute
            
        Returns:
            StepResult containing execution status and output data
            
        Raises:
            Exception: If step execution fails critically
        """
        # Dispatch to appropriate executor based on step type
        if step.type == 'parallel':
            logger.info(f"Dispatching parallel step '{step.id}' to ParallelExecutor")
            return await self._execute_parallel_step(step)
        
        elif step.type == 'conditional':
            logger.info(f"Dispatching conditional step '{step.id}' to ConditionalExecutor")
            return await self._execute_conditional_step(step)
        
        elif step.type == 'loop':
            logger.info(f"Dispatching loop step '{step.id}' to LoopExecutor")
            return await self._execute_loop_step(step)
        
        elif step.type == 'fork_join':
            logger.info(f"Dispatching fork-join step '{step.id}' to ForkJoinExecutor")
            return await self._execute_fork_join_step(step)
        
        # Default: execute as agent step
        return await self._execute_agent_step(step)
    
    async def _execute_parallel_step(self, step: WorkflowStep) -> StepResult:
        """
        Execute a parallel step by dispatching to ParallelExecutor.
        
        Args:
            step: The parallel WorkflowStep to execute
            
        Returns:
            StepResult containing aggregated results from all parallel steps
        """
        logger.info(
            f"Executing parallel step '{step.id}' with {len(step.parallel_steps)} parallel steps"
        )
        
        # Create ParallelBlock from step configuration
        parallel_block = ParallelBlock(
            id=step.id,
            parallel_steps=step.parallel_steps,
            max_parallelism=step.max_parallelism,
            next_step=step.next_step
        )
        
        # Execute parallel block
        results = await self.parallel_executor.execute_parallel_block(parallel_block)
        
        # Aggregate results
        all_succeeded = all(
            r.status == ExecutionStatus.COMPLETED 
            for r in results.values()
        )
        
        # Store individual step outputs
        for step_id, result in results.items():
            if result.output_data:
                self.step_outputs[step_id] = result.output_data
        
        # Create aggregated result for the parallel block
        if all_succeeded:
            # Aggregate all outputs into a single result
            aggregated_output = {
                step_id: result.output_data 
                for step_id, result in results.items()
            }
            
            return StepResult(
                step_id=step.id,
                status=ExecutionStatus.COMPLETED,
                input_data={},
                output_data=aggregated_output
            )
        else:
            # At least one step failed
            failed_steps = [
                step_id for step_id, result in results.items()
                if result.status == ExecutionStatus.FAILED
            ]
            error_message = f"Parallel execution failed: {len(failed_steps)} step(s) failed: {', '.join(failed_steps)}"
            
            return StepResult(
                step_id=step.id,
                status=ExecutionStatus.FAILED,
                input_data={},
                error_message=error_message
            )
    
    async def _execute_conditional_step(self, step: WorkflowStep) -> StepResult:
        """
        Execute a conditional step by dispatching to ConditionalExecutor.
        
        Args:
            step: The conditional WorkflowStep to execute
            
        Returns:
            StepResult from the executed branch
        """
        logger.info(f"Executing conditional step '{step.id}'")
        
        # Execute conditional logic
        return await self.conditional_executor.execute_conditional(step)
    
    async def _execute_loop_step(self, step: WorkflowStep) -> StepResult:
        """
        Execute a loop step by dispatching to LoopExecutor.
        
        Args:
            step: The loop WorkflowStep to execute
            
        Returns:
            StepResult containing aggregated results from all iterations
        """
        logger.info(f"Executing loop step '{step.id}'")
        
        # Execute loop
        return await self.loop_executor.execute_loop(step.id, step.loop_config)
    
    async def _execute_fork_join_step(self, step: WorkflowStep) -> StepResult:
        """
        Execute a fork-join step by dispatching to ForkJoinExecutor.
        
        Args:
            step: The fork-join WorkflowStep to execute
            
        Returns:
            StepResult containing aggregated results from all branches
        """
        logger.info(f"Executing fork-join step '{step.id}'")
        
        # Execute fork-join
        return await self.fork_join_executor.execute_fork_join(step.id, step.fork_join_config)
    
    async def _execute_agent_step(self, step: WorkflowStep) -> StepResult:
        """
        Execute a standard agent step.
        
        Args:
            step: The WorkflowStep to execute
            
        Returns:
            StepResult containing execution status and output data
        """
        # Generate unique IDs for this execution
        step_execution_id = f"{self.run_id}-{step.id}-{uuid.uuid4().hex[:8]}"
        task_id = f"task-{step.id}-{uuid.uuid4().hex[:8]}"
        correlation_id = f"corr-{self.run_id}-{step.id}-{uuid.uuid4().hex[:8]}"
        
        log_event(
            logger, 'info', 'step_start',
            f"Executing step '{step.id}' (agent: {step.agent_name})",
            run_id=self.run_id,
            step_id=step.id,
            step_execution_id=step_execution_id,
            agent_name=step.agent_name,
            task_id=task_id,
            correlation_id=correlation_id
        )
        
        try:
            # Step 1: Resolve input data using input_mapping and previous outputs
            logger.debug(f"Resolving input data for step '{step.id}'")
            resolver = InputMappingResolver(
                workflow_input=self.initial_input,
                step_outputs=self.step_outputs,
                loop_context=self.loop_context
            )
            input_data = resolver.resolve(step.input_mapping)
            logger.debug(
                f"Resolved input data for step '{step.id}'",
                extra={'input_data': input_data}
            )
            
            # Step 2: Create step execution record in database with status RUNNING
            logger.debug(f"Creating step execution record for step '{step.id}'")
            self.step_repo.create_step(
                step_execution_id=step_execution_id,
                run_id=self.run_id,
                step_id=step.id,
                step_name=step.agent_name,  # Using agent_name as step_name
                agent_name=step.agent_name,
                input_data=input_data,
                status=ExecutionStatus.RUNNING
            )
            logger.info(
                f"Created step execution record: {step_execution_id}",
                extra={'step_id': step.id, 'status': ExecutionStatus.RUNNING}
            )
            
            # Step 3: Publish monitoring update with status RUNNING
            logger.debug(f"Publishing RUNNING monitoring update for step '{step.id}'")
            await self._publish_monitoring_update(
                step_id=step.id,
                step_name=step.agent_name,
                status=ExecutionStatus.RUNNING,
                metadata={'step_execution_id': step_execution_id, 'task_id': task_id}
            )
            
            # Step 4: Publish AgentTask to orchestrator.tasks.http topic
            agent_task = AgentTask(
                run_id=self.run_id,
                task_id=task_id,
                agent_name=step.agent_name,
                input_data=input_data,
                correlation_id=correlation_id
            )
            await self.kafka_producer.publish(
                topic='orchestrator.tasks.http',
                message=agent_task.model_dump(),
                key=self.run_id
            )
            log_event(
                logger, 'info', 'agent_call',
                f"Published agent task for step '{step.id}'",
                run_id=self.run_id,
                step_id=step.id,
                task_id=task_id,
                correlation_id=correlation_id,
                agent_name=step.agent_name,
                topic='orchestrator.tasks.http'
            )
            
            # Step 5: Wait for AgentResult from results.topic with correlation ID
            logger.info(
                f"Waiting for agent result for step '{step.id}' "
                f"(correlation_id: {correlation_id})"
            )
            result_message = await self.kafka_consumer.consume_one(
                correlation_id_filter=correlation_id,
                timeout_seconds=300  # 5 minute timeout
            )
            
            if result_message is None:
                # Timeout occurred
                error_message = f"Timeout waiting for agent result (correlation_id: {correlation_id})"
                logger.error(error_message)
                
                # Update step execution record with FAILED status
                self.step_repo.update_step(
                    step_execution_id=step_execution_id,
                    status=ExecutionStatus.FAILED,
                    error_message=error_message
                )
                
                # Publish monitoring update with FAILED status
                await self._publish_monitoring_update(
                    step_id=step.id,
                    step_name=step.agent_name,
                    status=ExecutionStatus.FAILED,
                    metadata={
                        'step_execution_id': step_execution_id,
                        'error': error_message
                    }
                )
                
                return StepResult(
                    step_id=step.id,
                    status=ExecutionStatus.FAILED,
                    input_data=input_data,
                    error_message=error_message
                )
            
            # Parse the result message
            agent_result = AgentResult(**result_message)
            logger.info(
                f"Received agent result for step '{step.id}'",
                extra={
                    'task_id': agent_result.task_id,
                    'status': agent_result.status,
                    'correlation_id': agent_result.correlation_id
                }
            )
            
            # Step 6: Update step execution record with output_data and status
            if agent_result.status == 'SUCCESS':
                self.step_repo.update_step(
                    step_execution_id=step_execution_id,
                    status=ExecutionStatus.COMPLETED,
                    output_data=agent_result.output_data
                )
                
                # Step 7: Publish monitoring update with final status
                await self._publish_monitoring_update(
                    step_id=step.id,
                    step_name=step.agent_name,
                    status=ExecutionStatus.COMPLETED,
                    metadata={
                        'step_execution_id': step_execution_id,
                        'task_id': task_id
                    }
                )
                
                log_event(
                    logger, 'info', 'step_complete',
                    f"Step '{step.id}' completed successfully",
                    run_id=self.run_id,
                    step_id=step.id,
                    step_execution_id=step_execution_id,
                    agent_name=step.agent_name,
                    status=ExecutionStatus.COMPLETED,
                    task_id=task_id
                )
                
                return StepResult(
                    step_id=step.id,
                    status=ExecutionStatus.COMPLETED,
                    input_data=input_data,
                    output_data=agent_result.output_data
                )
            
            else:  # agent_result.status == 'FAILURE'
                error_message = agent_result.error_message or "Agent execution failed"
                
                self.step_repo.update_step(
                    step_execution_id=step_execution_id,
                    status=ExecutionStatus.FAILED,
                    error_message=error_message
                )
                
                # Publish monitoring update with FAILED status
                await self._publish_monitoring_update(
                    step_id=step.id,
                    step_name=step.agent_name,
                    status=ExecutionStatus.FAILED,
                    metadata={
                        'step_execution_id': step_execution_id,
                        'error': error_message
                    }
                )
                
                log_event(
                    logger, 'error', 'step_failed',
                    f"Step '{step.id}' failed: {error_message}",
                    run_id=self.run_id,
                    step_id=step.id,
                    step_execution_id=step_execution_id,
                    agent_name=step.agent_name,
                    status=ExecutionStatus.FAILED,
                    error_message=error_message,
                    task_id=task_id
                )
                
                return StepResult(
                    step_id=step.id,
                    status=ExecutionStatus.FAILED,
                    input_data=input_data,
                    error_message=error_message
                )
        
        except Exception as e:
            error_message = f"Exception during step execution: {str(e)}"
            log_event(
                logger, 'error', 'step_error',
                f"Critical error executing step '{step.id}': {e}",
                run_id=self.run_id,
                step_id=step.id,
                step_execution_id=step_execution_id,
                agent_name=step.agent_name,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            
            # Try to update database and publish monitoring update
            try:
                self.step_repo.update_step(
                    step_execution_id=step_execution_id,
                    status=ExecutionStatus.FAILED,
                    error_message=error_message
                )
                
                await self._publish_monitoring_update(
                    step_id=step.id,
                    step_name=step.agent_name,
                    status=ExecutionStatus.FAILED,
                    metadata={
                        'step_execution_id': step_execution_id,
                        'error': error_message
                    }
                )
            except Exception as cleanup_error:
                logger.error(
                    f"Failed to update step status after error: {cleanup_error}",
                    extra={'original_error': str(e), 'cleanup_error': str(cleanup_error)}
                )
            
            return StepResult(
                step_id=step.id,
                status=ExecutionStatus.FAILED,
                input_data={},
                error_message=error_message
            )
    
    async def _publish_monitoring_update(
        self,
        step_id: str,
        step_name: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Publish a monitoring update to the workflow.monitoring.updates topic.
        
        Args:
            step_id: The step identifier
            step_name: Human-readable step name
            status: The step status (RUNNING, COMPLETED, FAILED)
            metadata: Optional additional metadata
        """
        try:
            monitoring_update = MonitoringUpdate(
                run_id=self.run_id,
                step_id=step_id,
                step_name=step_name,
                status=status,
                metadata=metadata
            )
            
            await self.kafka_producer.publish(
                topic='workflow.monitoring.updates',
                message=monitoring_update.model_dump(),
                key=self.run_id
            )
            
            logger.debug(
                f"Published monitoring update for step '{step_id}'",
                extra={'status': status, 'metadata': metadata}
            )
        except Exception as e:
            logger.error(
                f"Failed to publish monitoring update for step '{step_id}': {e}",
                extra={'error': str(e)}
            )
    
    async def execute_step_with_recovery(self, step: WorkflowStep) -> StepResult:
        """
        Execute a step with error handling and recovery logic.
        
        This method wraps execute_step with recovery capabilities:
        1. Executes the step
        2. If the step fails, queries Agent Registry for recovery configuration
        3. Implements retry logic if configured
        4. Returns final result (success or failure)
        
        Args:
            step: The WorkflowStep to execute
            
        Returns:
            StepResult containing final execution status
        """
        logger.info(
            f"Executing step '{step.id}' with recovery (agent: {step.agent_name})"
        )
        
        # Try to get agent metadata for retry configuration
        agent_metadata = None
        try:
            agent_metadata = await self.agent_registry.get_agent(step.agent_name)
            logger.debug(
                f"Retrieved agent metadata for '{step.agent_name}'",
                extra={'retry_config': agent_metadata.retry_config.model_dump()}
            )
        except Exception as e:
            logger.warning(
                f"Failed to retrieve agent metadata for '{step.agent_name}': {e}. "
                f"Will execute without retry configuration."
            )
        
        # Determine retry configuration
        max_retries = 1  # Default: no retries (1 attempt)
        if agent_metadata and agent_metadata.retry_config:
            max_retries = agent_metadata.retry_config.max_retries
        
        # Execute step with retries
        last_result = None
        for attempt in range(max_retries):
            if attempt > 0:
                logger.info(
                    f"Retrying step '{step.id}' (attempt {attempt + 1}/{max_retries})"
                )
            
            # Execute the step
            result = await self.execute_step(step)
            last_result = result
            
            # Check if step succeeded
            if result.status == ExecutionStatus.COMPLETED:
                if attempt > 0:
                    logger.info(
                        f"Step '{step.id}' succeeded on retry attempt {attempt + 1}"
                    )
                return result
            
            # Step failed
            logger.warning(
                f"Step '{step.id}' failed on attempt {attempt + 1}/{max_retries}: "
                f"{result.error_message}"
            )
            
            # Check if we should retry
            if attempt < max_retries - 1:
                # Calculate delay before retry
                if agent_metadata and agent_metadata.retry_config:
                    delay = self._calculate_retry_delay(
                        attempt,
                        agent_metadata.retry_config.initial_delay_ms,
                        agent_metadata.retry_config.max_delay_ms,
                        agent_metadata.retry_config.backoff_multiplier
                    )
                    logger.info(
                        f"Waiting {delay:.2f}s before retry attempt {attempt + 2}"
                    )
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        logger.error(
            f"Step '{step.id}' failed after {max_retries} attempts. "
            f"Marking as unrecoverable."
        )
        
        return last_result
    
    def _calculate_retry_delay(
        self,
        attempt: int,
        initial_delay_ms: int,
        max_delay_ms: int,
        backoff_multiplier: float
    ) -> float:
        """
        Calculate retry delay with exponential backoff.
        
        Args:
            attempt: Current attempt number (0-indexed)
            initial_delay_ms: Initial delay in milliseconds
            max_delay_ms: Maximum delay in milliseconds
            backoff_multiplier: Multiplier for exponential backoff
            
        Returns:
            Delay in seconds
        """
        delay_ms = initial_delay_ms * (backoff_multiplier ** attempt)
        delay_ms = min(delay_ms, max_delay_ms)
        return delay_ms / 1000.0
    
    async def handle_step_failure(
        self,
        step: WorkflowStep,
        error_message: str
    ) -> None:
        """
        Handle a step failure by marking the workflow as FAILED.
        
        This method is called when a step fails and cannot be recovered.
        It updates the workflow status in the database and logs the failure.
        
        Args:
            step: The WorkflowStep that failed
            error_message: Description of the failure
        """
        logger.error(
            f"Handling unrecoverable failure for step '{step.id}': {error_message}"
        )
        
        # Mark workflow as FAILED
        try:
            self.workflow_repo.update_run_status(
                run_id=self.run_id,
                status=ExecutionStatus.FAILED,
                error_message=f"Step '{step.id}' (agent: {step.agent_name}) failed: {error_message}"
            )
            logger.info(f"Marked workflow run '{self.run_id}' as FAILED")
        except Exception as e:
            logger.error(
                f"Failed to update workflow status to FAILED: {e}",
                extra={'error': str(e)}
            )
        
        # Publish final monitoring update for the workflow
        try:
            await self._publish_monitoring_update(
                step_id='workflow',
                step_name=self.workflow_plan.name,
                status=ExecutionStatus.FAILED,
                metadata={
                    'failed_step': step.id,
                    'error': error_message
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to publish workflow failure monitoring update: {e}",
                extra={'error': str(e)}
            )



# Global executor instance for signal handling
_executor_instance: Optional[CentralizedExecutor] = None
_shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name}, initiating graceful shutdown...")
    _shutdown_event.set()


async def main():
    """
    Main entry point for the Centralized Executor.
    
    This function:
    1. Loads configuration from environment variables
    2. Parses workflow plan from environment or file
    3. Initializes and runs the executor
    4. Handles graceful shutdown on completion or error
    
    Environment Variables:
        RUN_ID: Unique identifier for this workflow run (required)
        WORKFLOW_PLAN: JSON string of workflow plan or path to JSON file (required)
        WORKFLOW_INPUT: JSON string of initial input data (required)
        KAFKA_BROKERS: Comma-separated Kafka broker addresses (required)
        DATABASE_URL: PostgreSQL connection URL (required)
        AGENT_REGISTRY_URL: Agent Registry service URL (required)
        KAFKA_CLIENT_ID: Optional Kafka client ID
        KAFKA_GROUP_ID: Optional Kafka consumer group ID
        LOG_LEVEL: Logging level (default: INFO)
        LOG_FORMAT: Log format ('json' or 'text', default: json)
    """
    global _executor_instance
    
    # Configure structured logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'json').lower()
    setup_logging(log_level=log_level, log_format=log_format)
    
    log_event(
        logger, 'info', 'executor_start',
        "Starting Centralized Executor",
        log_level=log_level,
        log_format=log_format
    )
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load configuration from environment
        run_id = os.getenv('RUN_ID')
        if not run_id:
            raise ValueError("RUN_ID environment variable is required")
        
        workflow_plan_str = os.getenv('WORKFLOW_PLAN')
        if not workflow_plan_str:
            raise ValueError("WORKFLOW_PLAN environment variable is required")
        
        workflow_input_str = os.getenv('WORKFLOW_INPUT')
        if not workflow_input_str:
            raise ValueError("WORKFLOW_INPUT environment variable is required")
        
        kafka_brokers = os.getenv('KAFKA_BROKERS')
        if not kafka_brokers:
            raise ValueError("KAFKA_BROKERS environment variable is required")
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        agent_registry_url = os.getenv('AGENT_REGISTRY_URL')
        if not agent_registry_url:
            raise ValueError("AGENT_REGISTRY_URL environment variable is required")
        
        kafka_client_id = os.getenv('KAFKA_CLIENT_ID')
        kafka_group_id = os.getenv('KAFKA_GROUP_ID')
        
        # Set correlation ID for all logs in this execution context
        set_correlation_id(run_id)
        
        log_event(
            logger, 'info', 'config_loaded',
            f"Configuration loaded for run_id={run_id}",
            run_id=run_id
        )
        
        # Parse workflow plan
        # Check if WORKFLOW_PLAN is a file path or JSON string
        if workflow_plan_str.startswith('{'):
            # It's a JSON string
            workflow_plan_dict = json.loads(workflow_plan_str)
        else:
            # It's a file path
            log_event(
                logger, 'info', 'workflow_plan_load',
                f"Loading workflow plan from file: {workflow_plan_str}",
                run_id=run_id,
                file_path=workflow_plan_str
            )
            with open(workflow_plan_str, 'r') as f:
                workflow_plan_dict = json.load(f)
        
        workflow_plan = WorkflowPlan(**workflow_plan_dict)
        log_event(
            logger, 'info', 'workflow_plan_loaded',
            f"Loaded workflow plan: {workflow_plan.name} (v{workflow_plan.version}), "
            f"{len(workflow_plan.steps)} steps",
            run_id=run_id,
            workflow_id=workflow_plan.workflow_id,
            workflow_name=workflow_plan.name,
            workflow_version=workflow_plan.version,
            step_count=len(workflow_plan.steps)
        )
        
        # Parse initial input
        if workflow_input_str.startswith('{'):
            initial_input = json.loads(workflow_input_str)
        else:
            # It's a file path
            logger.info(f"Loading workflow input from file: {workflow_input_str}")
            with open(workflow_input_str, 'r') as f:
                initial_input = json.load(f)
        
        logger.info(f"Loaded initial input with {len(initial_input)} fields")
        
        # Create executor instance
        executor = CentralizedExecutor(
            run_id=run_id,
            workflow_plan=workflow_plan,
            initial_input=initial_input,
            kafka_bootstrap_servers=kafka_brokers,
            database_url=database_url,
            agent_registry_url=agent_registry_url,
            kafka_client_id=kafka_client_id,
            kafka_group_id=kafka_group_id
        )
        _executor_instance = executor
        
        # Initialize executor
        logger.info("Initializing executor components...")
        await executor.initialize()
        
        # Load any existing execution state for replay
        logger.info("Loading execution state for replay...")
        await executor.load_execution_state()
        
        # Create a task for workflow execution
        execution_task = asyncio.create_task(executor.execute_workflow())
        
        # Wait for either execution to complete or shutdown signal
        done, pending = await asyncio.wait(
            [execution_task, asyncio.create_task(_shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Check if shutdown was requested
        if _shutdown_event.is_set():
            logger.warning("Shutdown signal received during execution")
            # Cancel the execution task
            execution_task.cancel()
            try:
                await execution_task
            except asyncio.CancelledError:
                logger.info("Execution task cancelled")
        else:
            # Execution completed normally
            logger.info("Workflow execution completed")
        
        # Shutdown executor
        logger.info("Shutting down executor...")
        await executor.shutdown()
        
        logger.info("Centralized Executor terminated successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error in Centralized Executor: {e}", exc_info=True)
        
        # Try to shutdown gracefully
        if _executor_instance:
            try:
                await _executor_instance.shutdown()
            except Exception as shutdown_error:
                logger.error(f"Error during shutdown: {shutdown_error}")
        
        sys.exit(1)


if __name__ == "__main__":
    """Entry point when running as a script."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, exiting...")
        sys.exit(0)

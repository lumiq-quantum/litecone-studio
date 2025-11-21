"""Parallel Executor for concurrent step execution."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime

from src.models.workflow import WorkflowStep
from src.executor.execution_models import ExecutionStatus, StepResult

if TYPE_CHECKING:
    from src.executor.centralized_executor import CentralizedExecutor

logger = logging.getLogger(__name__)


@dataclass
class ParallelBlock:
    """
    Represents a parallel execution block.
    
    A parallel block contains multiple steps that should be executed
    concurrently. The block can optionally limit the maximum number
    of concurrent executions.
    """
    id: str
    parallel_steps: List[str]
    max_parallelism: Optional[int] = None
    next_step: Optional[str] = None
    
    def __post_init__(self):
        """Validate parallel block configuration."""
        if not self.parallel_steps:
            raise ValueError("parallel_steps cannot be empty")
        
        if self.max_parallelism is not None and self.max_parallelism < 1:
            raise ValueError("max_parallelism must be at least 1")


class ParallelExecutor:
    """
    Executes multiple workflow steps in parallel using asyncio.
    
    This executor manages concurrent step execution with optional
    concurrency limits, result aggregation, and error handling.
    
    Features:
    - Concurrent execution using asyncio tasks
    - Semaphore-based concurrency control
    - Result aggregation from all parallel steps
    - Partial failure handling
    - Monitoring and logging
    
    Requirements:
    - 1.1: Execute independent steps concurrently
    - 1.2: Publish all agent tasks simultaneously
    - 1.3: Collect results from all steps before proceeding
    - 1.4: Wait for all parallel steps even if one fails
    - 1.5: Aggregate outputs and make available to subsequent steps
    - 1.7: Limit concurrent execution with max_parallelism
    """
    
    def __init__(self, executor: 'CentralizedExecutor'):
        """
        Initialize ParallelExecutor.
        
        Args:
            executor: Reference to parent CentralizedExecutor
        """
        self.executor = executor
        self.semaphore: Optional[asyncio.Semaphore] = None
        
        logger.info("ParallelExecutor initialized")
    
    async def execute_parallel_block(
        self,
        parallel_block: ParallelBlock
    ) -> Dict[str, StepResult]:
        """
        Execute all steps in parallel block concurrently.
        
        This method:
        1. Creates asyncio tasks for each parallel step
        2. Applies concurrency limits if max_parallelism is set
        3. Waits for all tasks to complete
        4. Aggregates results into a dictionary
        5. Handles partial failures gracefully
        
        Args:
            parallel_block: The parallel block configuration
            
        Returns:
            Dictionary mapping step_id to StepResult
            
        Raises:
            Exception: If critical error occurs during execution
        """
        logger.info(
            f"Starting parallel execution of block '{parallel_block.id}' "
            f"with {len(parallel_block.parallel_steps)} steps"
        )
        
        # Create semaphore for concurrency control
        if parallel_block.max_parallelism:
            self.semaphore = asyncio.Semaphore(parallel_block.max_parallelism)
            logger.info(
                f"Concurrency limited to {parallel_block.max_parallelism} "
                f"parallel executions"
            )
        else:
            self.semaphore = None
        
        # Create tasks for all parallel steps
        tasks = []
        for step_id in parallel_block.parallel_steps:
            if step_id not in self.executor.workflow_plan.steps:
                logger.error(f"Step '{step_id}' not found in workflow plan")
                raise ValueError(f"Step '{step_id}' not found in workflow plan")
            
            step = self.executor.workflow_plan.steps[step_id]
            task = asyncio.create_task(
                self._execute_step_with_semaphore(step),
                name=f"parallel-{step_id}"
            )
            tasks.append((step_id, task))
        
        logger.info(f"Created {len(tasks)} parallel tasks")
        
        # Wait for all tasks to complete
        results = {}
        errors = []
        
        for step_id, task in tasks:
            try:
                result = await task
                results[step_id] = result
                
                logger.info(
                    f"Parallel step '{step_id}' completed with status: "
                    f"{result.status}"
                )
            
            except Exception as e:
                # Store exception as failed result
                logger.error(
                    f"Parallel step '{step_id}' failed with exception: {e}",
                    exc_info=True
                )
                
                results[step_id] = StepResult(
                    step_id=step_id,
                    status=ExecutionStatus.FAILED,
                    input_data={},
                    error_message=str(e)
                )
                errors.append((step_id, e))
        
        # Log summary
        success_count = sum(
            1 for r in results.values()
            if r.status == ExecutionStatus.COMPLETED
        )
        
        logger.info(
            f"Parallel block '{parallel_block.id}' completed: "
            f"{success_count}/{len(results)} steps succeeded"
        )
        
        if errors:
            logger.warning(
                f"Parallel block '{parallel_block.id}' had {len(errors)} failures"
            )
        
        return results
    
    async def _execute_step_with_semaphore(
        self,
        step: WorkflowStep
    ) -> StepResult:
        """
        Execute step with optional semaphore for concurrency control.
        
        If max_parallelism is set, this method acquires the semaphore
        before executing the step, ensuring that no more than the
        specified number of steps execute concurrently.
        
        Args:
            step: The workflow step to execute
            
        Returns:
            StepResult from step execution
        """
        if self.semaphore:
            async with self.semaphore:
                logger.debug(
                    f"Acquired semaphore for step '{step.id}', executing..."
                )
                return await self.executor.execute_step(step)
        else:
            return await self.executor.execute_step(step)

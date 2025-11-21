"""Loop Executor for iterating over collections in workflows."""

import asyncio
import logging
import re
from typing import List, Any, Dict, Optional

from src.models.workflow import LoopStep, LoopExecutionMode, LoopErrorPolicy, IterationContext
from src.executor.execution_models import ExecutionStatus, StepResult

logger = logging.getLogger(__name__)


class LoopExecutor:
    """
    Executes loop iterations over collections.
    
    Supports:
    - Sequential execution (one at a time)
    - Parallel execution (all at once or with limit)
    - Error handling policies (continue, stop, collect)
    - Iteration limits
    """
    
    def __init__(self, executor: 'CentralizedExecutor'):
        """
        Initialize the LoopExecutor.
        
        Args:
            executor: Reference to the parent CentralizedExecutor
        """
        self.executor = executor
    
    async def execute_loop(
        self,
        loop_step_id: str,
        loop_config: LoopStep
    ) -> StepResult:
        """
        Execute loop over collection.
        
        Args:
            loop_step_id: ID of the loop step
            loop_config: Loop configuration
            
        Returns:
            StepResult containing aggregated results from all iterations
        """
        logger.info(
            f"Executing loop step '{loop_step_id}' with mode '{loop_config.execution_mode}'"
        )
        
        # Resolve collection reference
        try:
            collection = self._resolve_collection(loop_config.collection)
        except Exception as e:
            error_message = f"Failed to resolve loop collection: {e}"
            logger.error(error_message)
            return StepResult(
                step_id=loop_step_id,
                status=ExecutionStatus.FAILED,
                input_data={},
                error_message=error_message
            )
        
        if not collection:
            logger.warning(f"Empty collection for loop '{loop_step_id}'")
            return StepResult(
                step_id=loop_step_id,
                status=ExecutionStatus.COMPLETED,
                input_data={},
                output_data={"iterations": [], "total_count": 0}
            )
        
        # Apply max_iterations limit
        original_count = len(collection)
        if loop_config.max_iterations:
            collection = collection[:loop_config.max_iterations]
            logger.info(
                f"Limited loop iterations from {original_count} to {len(collection)}"
            )
        
        # Execute based on mode
        if loop_config.execution_mode == LoopExecutionMode.SEQUENTIAL:
            results = await self._execute_sequential(
                loop_step_id, loop_config, collection
            )
        else:
            results = await self._execute_parallel(
                loop_step_id, loop_config, collection
            )
        
        # Check for failures
        failed_results = [r for r in results if r.status == ExecutionStatus.FAILED]
        
        if failed_results:
            error_message = (
                f"Loop completed with {len(failed_results)} failed iteration(s) "
                f"out of {len(results)}"
            )
            return StepResult(
                step_id=loop_step_id,
                status=ExecutionStatus.FAILED,
                input_data={},
                output_data={
                    "iterations": [r.output_data for r in results],
                    "total_count": len(results),
                    "failed_count": len(failed_results)
                },
                error_message=error_message
            )
        
        # All iterations succeeded
        return StepResult(
            step_id=loop_step_id,
            status=ExecutionStatus.COMPLETED,
            input_data={},
            output_data={
                "iterations": [r.output_data for r in results],
                "total_count": len(results)
            }
        )

    def _resolve_collection(self, collection_ref: str) -> List[Any]:
        """
        Resolve collection reference to actual list.
        
        Args:
            collection_ref: Variable reference like ${step-0.output.items}
            
        Returns:
            List of items to iterate over
            
        Raises:
            ValueError: If collection reference is invalid or doesn't resolve to a list
        """
        # Extract variable path from ${...}
        match = re.match(r'\$\{([^}]+)\}', collection_ref)
        if not match:
            raise ValueError(f"Invalid collection reference: {collection_ref}")
        
        path = match.group(1)
        parts = path.split('.', 2)
        
        if len(parts) < 3:
            raise ValueError(
                f"Invalid collection reference '{collection_ref}'. "
                f"Expected format: ${{workflow.input.field}} or ${{step-id.output.field}}"
            )
        
        source_type = parts[0]
        data_type = parts[1]
        field_path = parts[2:]
        
        # Resolve based on source type
        if source_type == "workflow":
            if data_type != "input":
                raise ValueError(
                    f"Workflow collection references must use 'input': {collection_ref}"
                )
            collection = self._get_nested_value(
                self.executor.initial_input, field_path
            )
        else:
            # Assume it's a step ID
            step_id = source_type
            if data_type != "output":
                raise ValueError(
                    f"Step collection references must use 'output': {collection_ref}"
                )
            
            if step_id not in self.executor.step_outputs:
                raise ValueError(
                    f"Step '{step_id}' has not been executed or has no output"
                )
            
            collection = self._get_nested_value(
                self.executor.step_outputs[step_id], field_path
            )
        
        if not isinstance(collection, list):
            raise ValueError(
                f"Collection reference must resolve to a list, got {type(collection)}"
            )
        
        return collection

    def _get_nested_value(self, data: Dict[str, Any], field_path: List[str]) -> Any:
        """
        Get a nested value from a dictionary using a field path.
        
        Args:
            data: The dictionary to traverse
            field_path: List of keys to traverse
            
        Returns:
            The value at the nested path
            
        Raises:
            ValueError: If the path cannot be traversed
        """
        current = data
        
        for key in field_path:
            if not isinstance(current, dict):
                raise ValueError(f"Cannot traverse non-dictionary at key '{key}'")
            
            if key not in current:
                raise ValueError(f"Field '{key}' not found")
            
            current = current[key]
        
        return current

    async def _execute_sequential(
        self,
        loop_step_id: str,
        loop_config: LoopStep,
        collection: List[Any]
    ) -> List[StepResult]:
        """
        Execute iterations sequentially.
        
        Args:
            loop_step_id: ID of the loop step
            loop_config: Loop configuration
            collection: Collection to iterate over
            
        Returns:
            List of StepResult, one per iteration
        """
        results = []
        errors = []
        
        for index, item in enumerate(collection):
            # Create iteration context
            context = IterationContext(
                item=item,
                index=index,
                total=len(collection),
                is_first=(index == 0),
                is_last=(index == len(collection) - 1)
            )
            
            logger.info(
                f"Executing loop iteration {index + 1}/{len(collection)} "
                f"for step '{loop_step_id}'"
            )
            
            try:
                # Execute loop body with context
                result = await self._execute_iteration(
                    loop_step_id, loop_config, context
                )
                results.append(result)
            
            except Exception as e:
                error_result = StepResult(
                    step_id=f"{loop_step_id}-iter-{index}",
                    status=ExecutionStatus.FAILED,
                    input_data={"item": item, "index": index},
                    error_message=str(e)
                )
                
                # Handle error based on policy
                if loop_config.on_error == LoopErrorPolicy.STOP:
                    results.append(error_result)
                    logger.error(
                        f"Loop stopped at iteration {index} due to error: {e}"
                    )
                    raise Exception(
                        f"Loop stopped at iteration {index}: {e}"
                    )
                elif loop_config.on_error == LoopErrorPolicy.CONTINUE:
                    results.append(error_result)
                    errors.append((index, e))
                    logger.warning(
                        f"Loop iteration {index} failed, continuing: {e}"
                    )
                    continue
                elif loop_config.on_error == LoopErrorPolicy.COLLECT:
                    results.append(error_result)
                    errors.append((index, e))
                    logger.warning(
                        f"Loop iteration {index} failed, collecting error: {e}"
                    )
        
        # If collect mode and errors occurred, raise exception with all errors
        if loop_config.on_error == LoopErrorPolicy.COLLECT and errors:
            error_summary = "; ".join([
                f"Iteration {idx}: {err}" for idx, err in errors
            ])
            raise Exception(
                f"Loop completed with {len(errors)} errors: {error_summary}"
            )
        
        return results

    async def _execute_parallel(
        self,
        loop_step_id: str,
        loop_config: LoopStep,
        collection: List[Any]
    ) -> List[StepResult]:
        """
        Execute iterations in parallel.
        
        Args:
            loop_step_id: ID of the loop step
            loop_config: Loop configuration
            collection: Collection to iterate over
            
        Returns:
            List of StepResult, one per iteration
        """
        logger.info(
            f"Executing {len(collection)} loop iterations in parallel "
            f"for step '{loop_step_id}'"
        )
        
        # Create semaphore for concurrency control
        semaphore = None
        if loop_config.max_parallelism:
            semaphore = asyncio.Semaphore(loop_config.max_parallelism)
            logger.info(
                f"Limiting parallel iterations to {loop_config.max_parallelism}"
            )
        
        # Create tasks for all iterations
        tasks = []
        for index, item in enumerate(collection):
            context = IterationContext(
                item=item,
                index=index,
                total=len(collection),
                is_first=(index == 0),
                is_last=(index == len(collection) - 1)
            )
            
            if semaphore:
                task = asyncio.create_task(
                    self._execute_iteration_with_semaphore(
                        loop_step_id, loop_config, context, semaphore
                    )
                )
            else:
                task = asyncio.create_task(
                    self._execute_iteration(loop_step_id, loop_config, context)
                )
            
            tasks.append((index, task))
        
        # Wait for all tasks
        results = [None] * len(collection)
        errors = []
        
        for index, task in tasks:
            try:
                result = await task
                results[index] = result
            except Exception as e:
                error_result = StepResult(
                    step_id=f"{loop_step_id}-iter-{index}",
                    status=ExecutionStatus.FAILED,
                    input_data={"item": collection[index], "index": index},
                    error_message=str(e)
                )
                results[index] = error_result
                errors.append((index, e))
                logger.warning(f"Loop iteration {index} failed: {e}")
        
        # Handle errors based on policy
        if errors and loop_config.on_error == LoopErrorPolicy.STOP:
            first_error = errors[0]
            raise Exception(
                f"Loop failed at iteration {first_error[0]}: {first_error[1]}"
            )
        
        if errors and loop_config.on_error == LoopErrorPolicy.COLLECT:
            error_summary = "; ".join([
                f"Iteration {idx}: {err}" for idx, err in errors
            ])
            raise Exception(
                f"Loop completed with {len(errors)} errors: {error_summary}"
            )
        
        return results

    async def _execute_iteration(
        self,
        loop_step_id: str,
        loop_config: LoopStep,
        context: IterationContext
    ) -> StepResult:
        """
        Execute loop body for single iteration.
        
        Args:
            loop_step_id: ID of the loop step
            loop_config: Loop configuration
            context: Iteration context
            
        Returns:
            StepResult from the last step in loop body
        """
        # Make iteration context available to the executor
        self.executor.loop_context = context
        
        # Execute all steps in loop body
        last_result = None
        for step_id in loop_config.loop_body:
            step = self.executor.workflow_plan.steps[step_id]
            last_result = await self.executor.execute_step(step)
            
            if last_result.status == ExecutionStatus.FAILED:
                # Clear loop context before raising
                self.executor.loop_context = None
                raise Exception(
                    f"Loop body step '{step_id}' failed: "
                    f"{last_result.error_message}"
                )
        
        # Clear loop context
        self.executor.loop_context = None
        
        return last_result
    
    async def _execute_iteration_with_semaphore(
        self,
        loop_step_id: str,
        loop_config: LoopStep,
        context: IterationContext,
        semaphore: asyncio.Semaphore
    ) -> StepResult:
        """
        Execute iteration with semaphore for concurrency control.
        
        Args:
            loop_step_id: ID of the loop step
            loop_config: Loop configuration
            context: Iteration context
            semaphore: Semaphore for concurrency control
            
        Returns:
            StepResult from the iteration
        """
        async with semaphore:
            return await self._execute_iteration(loop_step_id, loop_config, context)

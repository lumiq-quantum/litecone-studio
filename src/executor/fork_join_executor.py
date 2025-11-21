"""Fork-Join Executor for parallel branch execution with join policies."""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

from src.models.workflow import WorkflowStep, ForkJoinStep, JoinPolicy
from src.executor.execution_models import ExecutionStatus, StepResult

logger = logging.getLogger(__name__)


class ForkJoinExecutor:
    """
    Executes fork-join pattern with multiple named branches.
    
    Forks execution into multiple branches, waits for completion
    based on join policy, and aggregates results.
    """
    
    def __init__(self, executor: 'CentralizedExecutor'):
        """
        Initialize ForkJoinExecutor.
        
        Args:
            executor: Reference to the parent CentralizedExecutor
        """
        self.executor = executor
    
    async def execute_fork_join(
        self,
        step_id: str,
        fork_join_config: ForkJoinStep
    ) -> StepResult:
        """
        Execute fork-join pattern.
        
        Args:
            step_id: ID of the fork-join step
            fork_join_config: Fork-join configuration
            
        Returns:
            StepResult with aggregated branch results
            
        Raises:
            Exception: If join policy is not satisfied
        """
        logger.info(
            f"Executing fork-join step '{step_id}' with {len(fork_join_config.branches)} branches, "
            f"join_policy={fork_join_config.join_policy.value}"
        )
        
        # Create tasks for all branches
        branch_tasks = {}
        for branch_name, branch in fork_join_config.branches.items():
            logger.debug(f"Creating task for branch '{branch_name}' with {len(branch.steps)} steps")
            task = asyncio.create_task(
                self._execute_branch(
                    step_id=step_id,
                    branch_name=branch_name,
                    branch=branch,
                    default_timeout=fork_join_config.branch_timeout_seconds
                )
            )
            branch_tasks[branch_name] = task
        
        # Wait for branches based on join policy
        results = await self._wait_for_branches(
            branch_tasks,
            fork_join_config.join_policy,
            fork_join_config.n_required
        )
        
        # Evaluate join policy
        success_count = sum(
            1 for r in results.values()
            if r.status == ExecutionStatus.COMPLETED
        )
        total_count = len(branch_tasks)
        
        logger.info(
            f"Fork-join step '{step_id}' completed: {success_count}/{total_count} branches succeeded"
        )
        
        # Check if join policy is satisfied
        policy_satisfied = self._evaluate_join_policy(
            fork_join_config.join_policy,
            success_count,
            total_count,
            fork_join_config.n_required
        )
        
        if not policy_satisfied:
            error_message = self._build_join_policy_error(
                fork_join_config.join_policy,
                success_count,
                total_count,
                fork_join_config.n_required,
                results
            )
            logger.error(f"Fork-join step '{step_id}' failed: {error_message}")
            
            return StepResult(
                step_id=step_id,
                status=ExecutionStatus.FAILED,
                input_data={},
                error_message=error_message
            )
        
        # Aggregate successful results
        aggregated_output = {
            branch_name: result.output_data
            for branch_name, result in results.items()
        }
        
        return StepResult(
            step_id=step_id,
            status=ExecutionStatus.COMPLETED,
            input_data={},
            output_data=aggregated_output
        )
    
    async def _execute_branch(
        self,
        step_id: str,
        branch_name: str,
        branch,
        default_timeout: Optional[int]
    ) -> StepResult:
        """
        Execute all steps in a branch sequentially.
        
        Args:
            step_id: ID of the parent fork-join step
            branch_name: Name of the branch
            branch: Branch configuration
            default_timeout: Default timeout for the branch
            
        Returns:
            StepResult from the last step in the branch
            
        Raises:
            asyncio.TimeoutError: If branch execution exceeds timeout
        """
        timeout = branch.timeout_seconds or default_timeout
        
        logger.info(
            f"Executing branch '{branch_name}' of fork-join step '{step_id}' "
            f"with {len(branch.steps)} steps"
            + (f", timeout={timeout}s" if timeout else "")
        )
        
        try:
            if timeout:
                return await asyncio.wait_for(
                    self._execute_branch_steps(step_id, branch_name, branch),
                    timeout=timeout
                )
            else:
                return await self._execute_branch_steps(step_id, branch_name, branch)
        
        except asyncio.TimeoutError:
            error_message = f"Branch '{branch_name}' timed out after {timeout}s"
            logger.error(error_message)
            
            return StepResult(
                step_id=f"{step_id}-branch-{branch_name}",
                status=ExecutionStatus.FAILED,
                input_data={},
                error_message=error_message
            )
        
        except Exception as e:
            error_message = f"Branch '{branch_name}' failed: {str(e)}"
            logger.error(error_message)
            
            return StepResult(
                step_id=f"{step_id}-branch-{branch_name}",
                status=ExecutionStatus.FAILED,
                input_data={},
                error_message=error_message
            )
    
    async def _execute_branch_steps(
        self,
        step_id: str,
        branch_name: str,
        branch
    ) -> StepResult:
        """
        Execute steps in branch sequentially.
        
        Args:
            step_id: ID of the parent fork-join step
            branch_name: Name of the branch
            branch: Branch configuration
            
        Returns:
            StepResult from the last step in the branch
            
        Raises:
            Exception: If any step in the branch fails
        """
        last_result = None
        
        for step_index, branch_step_id in enumerate(branch.steps):
            if branch_step_id not in self.executor.workflow_plan.steps:
                raise ValueError(
                    f"Branch '{branch_name}' references non-existent step '{branch_step_id}'"
                )
            
            step = self.executor.workflow_plan.steps[branch_step_id]
            
            logger.debug(
                f"Executing step {step_index + 1}/{len(branch.steps)} "
                f"in branch '{branch_name}': '{branch_step_id}'"
            )
            
            # Execute the step
            last_result = await self.executor.execute_step(step)
            
            # Check if step failed
            if last_result.status == ExecutionStatus.FAILED:
                raise Exception(
                    f"Branch '{branch_name}' failed at step '{branch_step_id}': "
                    f"{last_result.error_message}"
                )
            
            # Store output for future input mapping
            if last_result.output_data:
                self.executor.step_outputs[branch_step_id] = last_result.output_data
        
        # Return result from last step in branch
        if last_result is None:
            # This shouldn't happen since we validate branch has at least one step
            raise ValueError(f"Branch '{branch_name}' has no steps")
        
        return last_result
    
    async def _wait_for_branches(
        self,
        branch_tasks: Dict[str, asyncio.Task],
        join_policy: JoinPolicy,
        n_required: Optional[int]
    ) -> Dict[str, StepResult]:
        """
        Wait for branches based on join policy.
        
        Args:
            branch_tasks: Dictionary mapping branch names to asyncio tasks
            join_policy: Join policy to apply
            n_required: Number of branches required (for N_OF_M policy)
            
        Returns:
            Dictionary mapping branch names to StepResults
        """
        results = {}
        
        # Wait for all tasks to complete
        for branch_name, task in branch_tasks.items():
            try:
                result = await task
                results[branch_name] = result
                logger.debug(
                    f"Branch '{branch_name}' completed with status {result.status.value}"
                )
            except Exception as e:
                # Task raised an exception
                logger.error(f"Branch '{branch_name}' raised exception: {e}")
                results[branch_name] = StepResult(
                    step_id=f"branch-{branch_name}",
                    status=ExecutionStatus.FAILED,
                    input_data={},
                    error_message=str(e)
                )
        
        return results
    
    def _evaluate_join_policy(
        self,
        join_policy: JoinPolicy,
        success_count: int,
        total_count: int,
        n_required: Optional[int]
    ) -> bool:
        """
        Evaluate if join policy is satisfied.
        
        Args:
            join_policy: Join policy to evaluate
            success_count: Number of successful branches
            total_count: Total number of branches
            n_required: Number of branches required (for N_OF_M policy)
            
        Returns:
            True if join policy is satisfied, False otherwise
        """
        if join_policy == JoinPolicy.ALL:
            return success_count == total_count
        
        elif join_policy == JoinPolicy.ANY:
            return success_count > 0
        
        elif join_policy == JoinPolicy.MAJORITY:
            return success_count > total_count / 2
        
        elif join_policy == JoinPolicy.N_OF_M:
            if n_required is None:
                raise ValueError("n_required must be specified for N_OF_M policy")
            return success_count >= n_required
        
        else:
            raise ValueError(f"Unknown join policy: {join_policy}")
    
    def _build_join_policy_error(
        self,
        join_policy: JoinPolicy,
        success_count: int,
        total_count: int,
        n_required: Optional[int],
        results: Dict[str, StepResult]
    ) -> str:
        """
        Build error message for join policy failure.
        
        Args:
            join_policy: Join policy that failed
            success_count: Number of successful branches
            total_count: Total number of branches
            n_required: Number of branches required (for N_OF_M policy)
            results: Dictionary of branch results
            
        Returns:
            Error message string
        """
        failed_branches = [
            name for name, result in results.items()
            if result.status == ExecutionStatus.FAILED
        ]
        
        if join_policy == JoinPolicy.ALL:
            return (
                f"Fork-join failed: {len(failed_branches)} branch(es) failed "
                f"(policy: ALL). Failed branches: {', '.join(failed_branches)}"
            )
        
        elif join_policy == JoinPolicy.ANY:
            return "Fork-join failed: All branches failed (policy: ANY)"
        
        elif join_policy == JoinPolicy.MAJORITY:
            return (
                f"Fork-join failed: Only {success_count}/{total_count} branches succeeded "
                f"(policy: MAJORITY, need > 50%)"
            )
        
        elif join_policy == JoinPolicy.N_OF_M:
            return (
                f"Fork-join failed: Only {success_count}/{total_count} branches succeeded, "
                f"need {n_required} (policy: N_OF_M)"
            )
        
        else:
            return f"Fork-join failed with unknown policy: {join_policy}"

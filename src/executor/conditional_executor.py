"""Conditional executor for workflow branching logic."""

import logging
from typing import TYPE_CHECKING

from src.executor.condition_evaluator import ConditionEvaluator
from src.executor.execution_models import ExecutionStatus, StepResult

if TYPE_CHECKING:
    from src.executor.centralized_executor import CentralizedExecutor
    from src.models.workflow import WorkflowStep

logger = logging.getLogger(__name__)


class ConditionalExecutor:
    """
    Executes conditional branches in workflows.
    
    Evaluates conditions and executes the appropriate branch
    (if_true_step or if_false_step) based on the result.
    """
    
    def __init__(self, executor: 'CentralizedExecutor'):
        """
        Initialize the conditional executor.
        
        Args:
            executor: Reference to the parent CentralizedExecutor
        """
        self.executor = executor
    
    async def execute_conditional(self, step: 'WorkflowStep') -> StepResult:
        """
        Execute a conditional step by evaluating the condition and executing the appropriate branch.
        
        Args:
            step: The conditional WorkflowStep to execute
            
        Returns:
            StepResult from the executed branch or a success result if no branch was taken
        """
        logger.info(f"Executing conditional step '{step.id}'")
        
        # Create condition evaluator with current execution context
        evaluator = ConditionEvaluator(
            workflow_input=self.executor.initial_input,
            step_outputs=self.executor.step_outputs
        )
        
        # Evaluate the condition
        try:
            condition_result = evaluator.evaluate(step.condition.expression)
            logger.info(
                f"Condition evaluated to {condition_result} for step '{step.id}': "
                f"{step.condition.expression}"
            )
        except Exception as e:
            logger.error(f"Failed to evaluate condition for step '{step.id}': {e}")
            return StepResult(
                step_id=step.id,
                status=ExecutionStatus.FAILED,
                input_data={},
                error_message=f"Condition evaluation failed: {str(e)}"
            )
        
        # Determine which branch to execute
        branch_taken = None
        branch_step_id = None
        
        if condition_result:
            branch_taken = "then"
            branch_step_id = step.if_true_step
        else:
            branch_taken = "else"
            branch_step_id = step.if_false_step
        
        logger.info(
            f"Conditional step '{step.id}' taking '{branch_taken}' branch "
            f"(step: {branch_step_id or 'none'})"
        )
        
        # Execute the branch if it exists
        if branch_step_id:
            if branch_step_id not in self.executor.workflow_plan.steps:
                error_msg = f"Branch step '{branch_step_id}' not found in workflow"
                logger.error(error_msg)
                return StepResult(
                    step_id=step.id,
                    status=ExecutionStatus.FAILED,
                    input_data={},
                    error_message=error_msg
                )
            
            branch_step = self.executor.workflow_plan.steps[branch_step_id]
            
            # Execute the branch step
            try:
                branch_result = await self.executor.execute_step(branch_step)
                
                # Store the branch result in step outputs
                if branch_result.output_data:
                    self.executor.step_outputs[branch_step_id] = branch_result.output_data
                
                # Return a result for the conditional step itself
                return StepResult(
                    step_id=step.id,
                    status=branch_result.status,
                    input_data={},
                    output_data={
                        "condition_result": condition_result,
                        "branch_taken": branch_taken,
                        "branch_step_id": branch_step_id,
                        "branch_output": branch_result.output_data
                    },
                    error_message=branch_result.error_message
                )
            
            except Exception as e:
                logger.error(f"Failed to execute branch step '{branch_step_id}': {e}")
                return StepResult(
                    step_id=step.id,
                    status=ExecutionStatus.FAILED,
                    input_data={},
                    error_message=f"Branch execution failed: {str(e)}"
                )
        
        else:
            # No branch to execute, return success
            logger.info(
                f"Conditional step '{step.id}' has no branch for '{branch_taken}', "
                f"continuing to next step"
            )
            return StepResult(
                step_id=step.id,
                status=ExecutionStatus.COMPLETED,
                input_data={},
                output_data={
                    "condition_result": condition_result,
                    "branch_taken": branch_taken,
                    "branch_step_id": None
                }
            )

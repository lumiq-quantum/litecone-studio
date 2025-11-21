"""Pydantic models for workflow plan structure."""

from typing import Dict, Optional, List, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class LoopExecutionMode(str, Enum):
    """Enum for loop execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class LoopErrorPolicy(str, Enum):
    """Enum for loop error handling policies."""
    CONTINUE = "continue"  # Continue with remaining iterations
    STOP = "stop"          # Stop immediately on first error
    COLLECT = "collect"    # Complete all, report errors at end


class JoinPolicy(str, Enum):
    """Enum for fork-join join policies."""
    ALL = "all"          # All branches must succeed
    ANY = "any"          # At least one branch must succeed
    MAJORITY = "majority"  # More than 50% of branches must succeed
    N_OF_M = "n_of_m"    # At least N branches must succeed


class Condition(BaseModel):
    """Model representing a conditional expression."""
    
    expression: str = Field(..., description="The condition expression to evaluate")
    operator: Optional[str] = Field(None, description="Optional simple operator for basic comparisons")
    
    @field_validator('expression')
    @classmethod
    def validate_expression(cls, v: str) -> str:
        """Validate that expression is not empty."""
        if not v or not v.strip():
            raise ValueError("Condition expression cannot be empty")
        return v.strip()


class IterationContext(BaseModel):
    """Context available within loop iterations."""
    item: Any = Field(..., description="Current item from collection")
    index: int = Field(..., description="Current iteration index (0-based)")
    total: int = Field(..., description="Total number of items")
    is_first: bool = Field(..., description="True if this is the first iteration")
    is_last: bool = Field(..., description="True if this is the last iteration")


class Branch(BaseModel):
    """Model representing a single branch in a fork-join step."""
    steps: List[str] = Field(..., description="Step IDs to execute in this branch")
    timeout_seconds: Optional[int] = Field(
        None,
        description="Timeout for this branch in seconds"
    )
    
    @field_validator('steps')
    @classmethod
    def validate_steps(cls, v: List[str]) -> List[str]:
        """Validate that branch has at least one step."""
        if not v or len(v) == 0:
            raise ValueError("Branch must contain at least one step")
        return v
    
    @field_validator('timeout_seconds')
    @classmethod
    def validate_timeout(cls, v: Optional[int]) -> Optional[int]:
        """Validate timeout is positive."""
        if v is not None and v < 1:
            raise ValueError("timeout_seconds must be at least 1")
        return v


class ForkJoinStep(BaseModel):
    """Model representing a fork-join step configuration."""
    branches: Dict[str, Branch] = Field(..., description="Named branches to execute in parallel")
    join_policy: JoinPolicy = Field(
        default=JoinPolicy.ALL,
        description="Policy for determining when to proceed after branches complete"
    )
    n_required: Optional[int] = Field(
        None,
        description="Number of branches required to succeed (for join_policy='n_of_m')"
    )
    branch_timeout_seconds: Optional[int] = Field(
        None,
        description="Default timeout for all branches in seconds"
    )
    
    @field_validator('branches')
    @classmethod
    def validate_branches(cls, v: Dict[str, Branch]) -> Dict[str, Branch]:
        """Validate that there are at least 2 branches."""
        if not v or len(v) < 2:
            raise ValueError("Fork-join must have at least 2 branches")
        return v
    
    @field_validator('n_required')
    @classmethod
    def validate_n_required(cls, v: Optional[int]) -> Optional[int]:
        """Validate n_required is positive."""
        if v is not None and v < 1:
            raise ValueError("n_required must be at least 1")
        return v
    
    @field_validator('branch_timeout_seconds')
    @classmethod
    def validate_branch_timeout(cls, v: Optional[int]) -> Optional[int]:
        """Validate branch_timeout is positive."""
        if v is not None and v < 1:
            raise ValueError("branch_timeout_seconds must be at least 1")
        return v
    
    @model_validator(mode='after')
    def validate_n_of_m_policy(self) -> 'ForkJoinStep':
        """Validate n_required is specified for N_OF_M policy."""
        if self.join_policy == JoinPolicy.N_OF_M and self.n_required is None:
            raise ValueError("n_required must be specified when join_policy is 'n_of_m'")
        if self.join_policy == JoinPolicy.N_OF_M and self.n_required is not None:
            if self.n_required > len(self.branches):
                raise ValueError(
                    f"n_required ({self.n_required}) cannot be greater than "
                    f"number of branches ({len(self.branches)})"
                )
        return self


class LoopStep(BaseModel):
    """Model representing a loop step configuration."""
    collection: str = Field(..., description="Reference to collection: ${step-0.output.items}")
    loop_body: List[str] = Field(..., description="Step IDs to execute for each item")
    execution_mode: LoopExecutionMode = Field(
        default=LoopExecutionMode.SEQUENTIAL,
        description="Execution mode: sequential or parallel"
    )
    max_parallelism: Optional[int] = Field(
        None,
        description="Maximum number of concurrent iterations (for parallel mode)"
    )
    max_iterations: Optional[int] = Field(
        None,
        description="Maximum number of iterations to process"
    )
    on_error: LoopErrorPolicy = Field(
        default=LoopErrorPolicy.STOP,
        description="Error handling policy"
    )
    
    @field_validator('collection')
    @classmethod
    def validate_collection(cls, v: str) -> str:
        """Validate that collection reference is not empty."""
        if not v or not v.strip():
            raise ValueError("Loop collection reference cannot be empty")
        return v.strip()
    
    @field_validator('loop_body')
    @classmethod
    def validate_loop_body(cls, v: List[str]) -> List[str]:
        """Validate that loop body has at least one step."""
        if not v or len(v) == 0:
            raise ValueError("Loop body must contain at least one step")
        return v
    
    @field_validator('max_parallelism')
    @classmethod
    def validate_max_parallelism(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_parallelism is positive."""
        if v is not None and v < 1:
            raise ValueError("max_parallelism must be at least 1")
        return v
    
    @field_validator('max_iterations')
    @classmethod
    def validate_max_iterations(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_iterations is positive."""
        if v is not None and v < 1:
            raise ValueError("max_iterations must be at least 1")
        return v


class WorkflowStep(BaseModel):
    """Model representing a single step in a workflow plan."""
    
    id: str = Field(..., description="Unique identifier for the step")
    type: str = Field(
        default="agent",
        description="Step type: 'agent', 'parallel', 'conditional', 'loop', 'fork_join', etc."
    )
    agent_name: Optional[str] = Field(
        None,
        description="Name of the agent to execute this step (required for type='agent')"
    )
    next_step: Optional[str] = Field(None, description="ID of the next step in sequence, null for final step")
    input_mapping: Optional[Dict[str, str]] = Field(
        default=None,
        description="Mapping of input field names to variable references (e.g., ${workflow.input.field})"
    )
    
    # Parallel execution fields
    parallel_steps: Optional[List[str]] = Field(
        None,
        description="List of step IDs to execute in parallel (for type='parallel')"
    )
    max_parallelism: Optional[int] = Field(
        None,
        description="Maximum number of concurrent parallel executions (for type='parallel')"
    )
    
    # Conditional execution fields
    condition: Optional[Condition] = Field(
        None,
        description="Condition to evaluate for branching (for type='conditional')"
    )
    if_true_step: Optional[str] = Field(
        None,
        description="Step ID to execute if condition is true (for type='conditional')"
    )
    if_false_step: Optional[str] = Field(
        None,
        description="Step ID to execute if condition is false (for type='conditional')"
    )
    
    # Loop execution fields
    loop_config: Optional[LoopStep] = Field(
        None,
        description="Loop configuration (for type='loop')"
    )
    
    # Fork-join execution fields
    fork_join_config: Optional[ForkJoinStep] = Field(
        None,
        description="Fork-join configuration (for type='fork_join')"
    )
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that id is not empty."""
        if not v or not v.strip():
            raise ValueError("Step ID cannot be empty")
        return v.strip()
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate step type."""
        valid_types = ['agent', 'parallel', 'conditional', 'loop', 'fork_join', 'sub_workflow', 'wait_for_event', 'validate']
        if v not in valid_types:
            raise ValueError(f"Invalid step type '{v}'. Must be one of: {', '.join(valid_types)}")
        return v
    
    @model_validator(mode='after')
    def validate_step_configuration(self) -> 'WorkflowStep':
        """Validate step configuration based on type."""
        if self.type == 'agent':
            if not self.agent_name:
                raise ValueError("agent_name is required for type='agent'")
        
        elif self.type == 'parallel':
            if not self.parallel_steps:
                raise ValueError("parallel_steps is required for type='parallel'")
            if len(self.parallel_steps) < 2:
                raise ValueError("parallel_steps must contain at least 2 steps")
            if self.max_parallelism is not None and self.max_parallelism < 1:
                raise ValueError("max_parallelism must be at least 1")
        
        elif self.type == 'conditional':
            if not self.condition:
                raise ValueError("condition is required for type='conditional'")
            if not self.if_true_step and not self.if_false_step:
                raise ValueError("At least one of if_true_step or if_false_step must be specified for type='conditional'")
        
        elif self.type == 'loop':
            if not self.loop_config:
                raise ValueError("loop_config is required for type='loop'")
        
        elif self.type == 'fork_join':
            if not self.fork_join_config:
                raise ValueError("fork_join_config is required for type='fork_join'")
        
        return self
    
    @field_validator('input_mapping')
    @classmethod
    def validate_input_mapping(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Validate that input_mapping values are strings."""
        if v is None:
            return v
        for key, value in v.items():
            if not isinstance(value, str):
                raise ValueError(f"Input mapping value for '{key}' must be a string")
        return v


class WorkflowPlan(BaseModel):
    """Model representing a complete workflow plan."""
    
    workflow_id: str = Field(..., description="Unique identifier for the workflow")
    name: str = Field(..., description="Human-readable name of the workflow")
    version: str = Field(..., description="Version of the workflow plan")
    start_step: str = Field(..., description="ID of the first step to execute")
    steps: Dict[str, WorkflowStep] = Field(
        ...,
        description="Dictionary mapping step IDs to WorkflowStep objects"
    )
    
    @field_validator('workflow_id', 'name', 'version', 'start_step')
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Validate that string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator('steps')
    @classmethod
    def validate_steps_not_empty(cls, v: Dict[str, WorkflowStep]) -> Dict[str, WorkflowStep]:
        """Validate that steps dictionary is not empty."""
        if not v:
            raise ValueError("Workflow must contain at least one step")
        return v
    
    @model_validator(mode='after')
    def validate_workflow_structure(self) -> 'WorkflowPlan':
        """Validate the overall workflow structure."""
        # Validate that start_step exists in steps
        if self.start_step not in self.steps:
            raise ValueError(f"start_step '{self.start_step}' not found in steps dictionary")
        
        # Validate that all step IDs match their dictionary keys
        for step_id, step in self.steps.items():
            if step.id != step_id:
                raise ValueError(
                    f"Step ID mismatch: dictionary key '{step_id}' does not match step.id '{step.id}'"
                )
        
        # Validate that all next_step references point to valid steps
        for step_id, step in self.steps.items():
            if step.next_step is not None and step.next_step not in self.steps:
                raise ValueError(
                    f"Step '{step_id}' references non-existent next_step '{step.next_step}'"
                )
        
        # Validate that there are no circular references
        self._validate_no_cycles()
        
        # Validate that there is at least one terminal step (next_step is None)
        terminal_steps = [step_id for step_id, step in self.steps.items() if step.next_step is None]
        if not terminal_steps:
            raise ValueError("Workflow must have at least one terminal step (with next_step=None)")
        
        return self
    
    def _validate_no_cycles(self) -> None:
        """Validate that the workflow does not contain circular references."""
        visited = set()
        current_step = self.start_step
        
        while current_step is not None:
            if current_step in visited:
                raise ValueError(f"Circular reference detected in workflow at step '{current_step}'")
            
            visited.add(current_step)
            step = self.steps[current_step]
            current_step = step.next_step

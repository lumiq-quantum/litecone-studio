# Design Document: Advanced Workflow Execution Features

## Overview

This design document specifies the technical architecture and implementation approach for 16 advanced workflow execution features. The design builds upon the existing orchestrator architecture while introducing new execution patterns, resilience mechanisms, and workflow management capabilities.

## Design Principles

1. **Backward Compatibility**: Existing workflows must continue to work without modification
2. **Incremental Adoption**: Features can be adopted independently
3. **Performance**: New features should not degrade performance of simple workflows
4. **Observability**: All features must emit structured logs and metrics
5. **Testability**: Each feature must be independently testable
6. **Extensibility**: Design should allow future enhancements

---

## Architecture Overview

### Current Architecture (Baseline)

```
┌─────────────────────────────────────────────────────────────┐
│                  Workflow Management API                     │
└────────────────────────┬────────────────────────────────────┘
                         │ Kafka: workflow.execution.requests
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Execution Consumer                          │
└────────────────────────┬────────────────────────────────────┘
                         │ Spawns
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Centralized Executor (Sequential)               │
│  - Executes steps one by one                                │
│  - Publishes tasks to Kafka                                 │
│  - Waits for results                                        │
└────────────────────────┬────────────────────────────────────┘
                         │ Kafka: orchestrator.tasks.http
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              External Agent Executor (Bridge)                │
└─────────────────────────────────────────────────────────────┘
```

### Enhanced Architecture (Target)

```
┌─────────────────────────────────────────────────────────────┐
│                  Workflow Management API                     │
│  + Scheduling Service                                        │
│  + Version Management                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Execution Consumer                          │
│  + Event Listener (webhooks, Kafka events)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Enhanced Centralized Executor                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Execution Engine (Core)                           │    │
│  │  - Step Executor                                   │    │
│  │  - Parallel Executor                               │    │
│  │  - Loop Executor                                   │    │
│  │  - Conditional Executor                            │    │
│  │  - Fork-Join Executor                              │    │
│  │  - State Machine Executor                          │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Resilience Layer                                  │    │
│  │  - Circuit Breaker Manager                         │    │
│  │  - Retry Strategy Manager                          │    │
│  │  - DLQ Publisher                                   │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Data Layer                                        │    │
│  │  - Cache Manager (Redis)                           │    │
│  │  - Validator                                       │    │
│  │  - Input Resolver                                  │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              External Agent Executor (Bridge)                │
│  + Circuit Breaker Integration                              │
└─────────────────────────────────────────────────────────────┘
```

---


## PHASE 1: CORE EXECUTION PATTERNS

---

### 1. Parallel Execution Design

#### Architecture

**New Components:**
- `ParallelExecutor` - Manages concurrent step execution
- `ParallelStepCoordinator` - Coordinates parallel step lifecycle
- `ResultAggregator` - Collects and aggregates parallel results

#### Class Design

```python
from typing import List, Dict, Any, Optional
import asyncio
from dataclasses import dataclass

@dataclass
class ParallelBlock:
    """Represents a parallel execution block."""
    id: str
    parallel_steps: List[str]
    max_parallelism: Optional[int] = None
    next_step: Optional[str] = None

class ParallelExecutor:
    """
    Executes multiple steps in parallel using asyncio.
    
    Responsibilities:
    - Create asyncio tasks for each parallel step
    - Manage concurrency limits (max_parallelism)
    - Collect results from all parallel steps
    - Handle partial failures
    """
    
    def __init__(self, executor: 'CentralizedExecutor'):
        self.executor = executor
        self.semaphore: Optional[asyncio.Semaphore] = None
    
    async def execute_parallel_block(
        self,
        parallel_block: ParallelBlock
    ) -> Dict[str, StepResult]:
        """
        Execute all steps in parallel block concurrently.
        
        Returns:
            Dictionary mapping step_id to StepResult
        """
        # Create semaphore for concurrency control
        if parallel_block.max_parallelism:
            self.semaphore = asyncio.Semaphore(parallel_block.max_parallelism)
        
        # Create tasks for all parallel steps
        tasks = []
        for step_id in parallel_block.parallel_steps:
            step = self.executor.workflow_plan.steps[step_id]
            task = asyncio.create_task(
                self._execute_step_with_semaphore(step)
            )
            tasks.append((step_id, task))
        
        # Wait for all tasks to complete
        results = {}
        for step_id, task in tasks:
            try:
                result = await task
                results[step_id] = result
            except Exception as e:
                # Store exception as failed result
                results[step_id] = StepResult(
                    step_id=step_id,
                    status=ExecutionStatus.FAILED,
                    input_data={},
                    error_message=str(e)
                )
        
        return results
    
    async def _execute_step_with_semaphore(
        self,
        step: WorkflowStep
    ) -> StepResult:
        """Execute step with semaphore for concurrency control."""
        if self.semaphore:
            async with self.semaphore:
                return await self.executor.execute_step(step)
        else:
            return await self.executor.execute_step(step)
```

#### Workflow Definition Extension

```python
@dataclass
class WorkflowStep:
    """Extended to support parallel execution."""
    id: str
    type: str = "agent"  # New: "agent", "parallel", "conditional", "loop", etc.
    agent_name: Optional[str] = None
    parallel_steps: Optional[List[str]] = None  # For type="parallel"
    max_parallelism: Optional[int] = None
    next_step: Optional[str] = None
    input_mapping: Dict[str, str] = field(default_factory=dict)
```

#### Database Schema Changes

```sql
-- Add step_type column to step_executions
ALTER TABLE step_executions 
ADD COLUMN step_type VARCHAR(50) DEFAULT 'agent';

-- Add parent_step_id for tracking parallel steps
ALTER TABLE step_executions 
ADD COLUMN parent_step_id VARCHAR(255) NULL;

-- Add execution_order for parallel steps
ALTER TABLE step_executions 
ADD COLUMN execution_order INTEGER NULL;

-- Index for querying parallel steps
CREATE INDEX idx_step_parent_step_id ON step_executions(parent_step_id);
```

#### Execution Flow

```
1. Executor encounters parallel block
2. ParallelExecutor creates asyncio tasks for each step
3. If max_parallelism set, use semaphore to limit concurrency
4. Publish all agent tasks to Kafka simultaneously
5. Wait for all results using asyncio.gather()
6. Aggregate results into dictionary
7. Make results available as ${parallel-block-id.outputs}
8. Continue to next_step
```

---

### 2. Conditional Logic Design

#### Architecture

**New Components:**
- `ConditionalExecutor` - Evaluates conditions and executes branches
- `ConditionEvaluator` - Parses and evaluates condition expressions
- `ExpressionParser` - Parses JSONPath and comparison expressions

#### Class Design

```python
from typing import Any, Optional
import re
import json
from jsonpath_ng import parse as jsonpath_parse

@dataclass
class Condition:
    """Represents a conditional expression."""
    expression: str
    operator: Optional[str] = None  # For simple comparisons
    left_operand: Optional[str] = None
    right_operand: Optional[Any] = None

@dataclass
class ConditionalStep:
    """Represents a conditional step."""
    id: str
    type: str = "conditional"
    condition: Condition
    then_step: Optional[str] = None
    else_step: Optional[str] = None
    next_step: Optional[str] = None

class ConditionEvaluator:
    """
    Evaluates conditional expressions.
    
    Supports:
    - Comparison operators: ==, !=, >, <, >=, <=
    - Logical operators: and, or, not
    - Membership: in, not in, contains
    - JSONPath expressions: ${step-1.output.results[0].score}
    """
    
    def __init__(
        self,
        workflow_input: Dict[str, Any],
        step_outputs: Dict[str, Dict[str, Any]]
    ):
        self.workflow_input = workflow_input
        self.step_outputs = step_outputs
    
    def evaluate(self, condition: Condition) -> bool:
        """
        Evaluate condition and return boolean result.
        
        Raises:
            ValueError: If condition is malformed
        """
        try:
            # Parse expression
            expression = condition.expression
            
            # Replace variable references with actual values
            resolved_expression = self._resolve_variables(expression)
            
            # Evaluate using safe eval
            result = self._safe_eval(resolved_expression)
            
            return bool(result)
        
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    def _resolve_variables(self, expression: str) -> str:
        """Replace ${...} references with actual values."""
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_path = match.group(1)
            value = self._get_value_by_path(var_path)
            # Return JSON representation for safe eval
            return json.dumps(value)
        
        return re.sub(pattern, replace_var, expression)
    
    def _get_value_by_path(self, path: str) -> Any:
        """
        Get value using dot notation path.
        
        Examples:
            workflow.input.topic -> self.workflow_input['topic']
            step-1.output.score -> self.step_outputs['step-1']['score']
            step-1.output.results[0].score -> JSONPath evaluation
        """
        parts = path.split('.', 2)
        
        if parts[0] == 'workflow' and parts[1] == 'input':
            # Access workflow input
            remaining_path = parts[2] if len(parts) > 2 else None
            if remaining_path:
                return self._navigate_dict(self.workflow_input, remaining_path)
            return self.workflow_input
        
        elif parts[0].startswith('step-'):
            # Access step output
            step_id = parts[0]
            if step_id not in self.step_outputs:
                raise ValueError(f"Step '{step_id}' output not found")
            
            if len(parts) > 1 and parts[1] == 'output':
                remaining_path = parts[2] if len(parts) > 2 else None
                if remaining_path:
                    return self._navigate_dict(
                        self.step_outputs[step_id],
                        remaining_path
                    )
                return self.step_outputs[step_id]
        
        raise ValueError(f"Invalid path: {path}")
    
    def _navigate_dict(self, data: Dict, path: str) -> Any:
        """Navigate nested dictionary using dot notation and array indices."""
        # Use JSONPath for complex paths with array indices
        if '[' in path:
            jsonpath_expr = jsonpath_parse(f"$.{path}")
            matches = jsonpath_expr.find(data)
            if matches:
                return matches[0].value
            raise ValueError(f"Path not found: {path}")
        
        # Simple dot notation
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise ValueError(f"Key '{key}' not found in path: {path}")
        return current
    
    def _safe_eval(self, expression: str) -> Any:
        """
        Safely evaluate expression.
        
        Only allows comparison and logical operators.
        """
        # Whitelist of allowed operators
        allowed_operators = {
            '==', '!=', '>', '<', '>=', '<=',
            'and', 'or', 'not', 'in', 'contains'
        }
        
        # Replace 'contains' with 'in' for Python eval
        expression = expression.replace(' contains ', ' in ')
        
        # Use ast.literal_eval for safety
        # For now, use eval with restricted globals
        return eval(expression, {"__builtins__": {}}, {})

class ConditionalExecutor:
    """Executes conditional branches."""
    
    def __init__(self, executor: 'CentralizedExecutor'):
        self.executor = executor
        self.evaluator = ConditionEvaluator(
            workflow_input=executor.initial_input,
            step_outputs=executor.step_outputs
        )
    
    async def execute_conditional(
        self,
        conditional_step: ConditionalStep
    ) -> StepResult:
        """
        Evaluate condition and execute appropriate branch.
        
        Returns:
            StepResult from the executed branch
        """
        # Evaluate condition
        condition_result = self.evaluator.evaluate(conditional_step.condition)
        
        # Log which branch was taken
        logger.info(
            f"Condition evaluated to {condition_result} for step '{conditional_step.id}'"
        )
        
        # Execute appropriate branch
        if condition_result:
            if conditional_step.then_step:
                branch_step = self.executor.workflow_plan.steps[conditional_step.then_step]
                return await self.executor.execute_step(branch_step)
        else:
            if conditional_step.else_step:
                branch_step = self.executor.workflow_plan.steps[conditional_step.else_step]
                return await self.executor.execute_step(branch_step)
        
        # No branch executed, return success
        return StepResult(
            step_id=conditional_step.id,
            status=ExecutionStatus.COMPLETED,
            input_data={},
            output_data={"condition_result": condition_result}
        )
```


#### Database Schema Changes

```sql
-- Add conditional execution tracking
ALTER TABLE step_executions 
ADD COLUMN condition_expression TEXT NULL;

ALTER TABLE step_executions 
ADD COLUMN condition_result BOOLEAN NULL;

ALTER TABLE step_executions 
ADD COLUMN branch_taken VARCHAR(50) NULL;  -- 'then', 'else', 'none'
```

---

### 3. Loops/Iterations Design

#### Architecture

**New Components:**
- `LoopExecutor` - Manages loop execution
- `IterationContext` - Tracks current iteration state
- `LoopResultAggregator` - Collects iteration results

#### Class Design

```python
from enum import Enum

class LoopExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"

class LoopErrorPolicy(Enum):
    CONTINUE = "continue"  # Continue with remaining iterations
    STOP = "stop"          # Stop immediately on first error
    COLLECT = "collect"    # Complete all, report errors at end

@dataclass
class LoopStep:
    """Represents a loop step."""
    id: str
    type: str = "loop"
    collection: str  # Reference to collection: ${step-0.output.items}
    loop_body: List[str]  # Step IDs to execute for each item
    execution_mode: LoopExecutionMode = LoopExecutionMode.SEQUENTIAL
    max_parallelism: Optional[int] = None
    max_iterations: Optional[int] = None
    on_error: LoopErrorPolicy = LoopErrorPolicy.STOP
    next_step: Optional[str] = None

@dataclass
class IterationContext:
    """Context available within loop iterations."""
    item: Any  # Current item from collection
    index: int  # Current iteration index (0-based)
    total: int  # Total number of items
    is_first: bool
    is_last: bool

class LoopExecutor:
    """
    Executes loop iterations.
    
    Supports:
    - Sequential execution (one at a time)
    - Parallel execution (all at once or with limit)
    - Error handling policies
    - Iteration limits
    """
    
    def __init__(self, executor: 'CentralizedExecutor'):
        self.executor = executor
    
    async def execute_loop(
        self,
        loop_step: LoopStep
    ) -> List[StepResult]:
        """
        Execute loop over collection.
        
        Returns:
            List of StepResult, one per iteration
        """
        # Resolve collection reference
        collection = self._resolve_collection(loop_step.collection)
        
        if not collection:
            logger.warning(f"Empty collection for loop '{loop_step.id}'")
            return []
        
        # Apply max_iterations limit
        if loop_step.max_iterations:
            collection = collection[:loop_step.max_iterations]
        
        # Execute based on mode
        if loop_step.execution_mode == LoopExecutionMode.SEQUENTIAL:
            return await self._execute_sequential(loop_step, collection)
        else:
            return await self._execute_parallel(loop_step, collection)
    
    def _resolve_collection(self, collection_ref: str) -> List[Any]:
        """Resolve collection reference to actual list."""
        # Use ConditionEvaluator to resolve reference
        evaluator = ConditionEvaluator(
            workflow_input=self.executor.initial_input,
            step_outputs=self.executor.step_outputs
        )
        
        # Extract variable path from ${...}
        match = re.match(r'\$\{([^}]+)\}', collection_ref)
        if match:
            path = match.group(1)
            collection = evaluator._get_value_by_path(path)
            
            if not isinstance(collection, list):
                raise ValueError(
                    f"Collection reference must resolve to a list, "
                    f"got {type(collection)}"
                )
            
            return collection
        
        raise ValueError(f"Invalid collection reference: {collection_ref}")
    
    async def _execute_sequential(
        self,
        loop_step: LoopStep,
        collection: List[Any]
    ) -> List[StepResult]:
        """Execute iterations sequentially."""
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
            
            try:
                # Execute loop body with context
                result = await self._execute_iteration(
                    loop_step,
                    context
                )
                results.append(result)
            
            except Exception as e:
                error_result = StepResult(
                    step_id=f"{loop_step.id}-iter-{index}",
                    status=ExecutionStatus.FAILED,
                    input_data={"item": item, "index": index},
                    error_message=str(e)
                )
                
                # Handle error based on policy
                if loop_step.on_error == LoopErrorPolicy.STOP:
                    results.append(error_result)
                    raise Exception(
                        f"Loop stopped at iteration {index}: {e}"
                    )
                elif loop_step.on_error == LoopErrorPolicy.CONTINUE:
                    results.append(error_result)
                    errors.append((index, e))
                    continue
                elif loop_step.on_error == LoopErrorPolicy.COLLECT:
                    results.append(error_result)
                    errors.append((index, e))
        
        # If collect mode and errors occurred, report them
        if loop_step.on_error == LoopErrorPolicy.COLLECT and errors:
            error_summary = "; ".join([
                f"Iteration {idx}: {err}" for idx, err in errors
            ])
            raise Exception(
                f"Loop completed with {len(errors)} errors: {error_summary}"
            )
        
        return results
    
    async def _execute_parallel(
        self,
        loop_step: LoopStep,
        collection: List[Any]
    ) -> List[StepResult]:
        """Execute iterations in parallel."""
        # Create semaphore for concurrency control
        semaphore = None
        if loop_step.max_parallelism:
            semaphore = asyncio.Semaphore(loop_step.max_parallelism)
        
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
                        loop_step, context, semaphore
                    )
                )
            else:
                task = asyncio.create_task(
                    self._execute_iteration(loop_step, context)
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
                    step_id=f"{loop_step.id}-iter-{index}",
                    status=ExecutionStatus.FAILED,
                    input_data={"item": collection[index], "index": index},
                    error_message=str(e)
                )
                results[index] = error_result
                errors.append((index, e))
        
        # Handle errors based on policy
        if errors and loop_step.on_error == LoopErrorPolicy.STOP:
            first_error = errors[0]
            raise Exception(
                f"Loop failed at iteration {first_error[0]}: {first_error[1]}"
            )
        
        if errors and loop_step.on_error == LoopErrorPolicy.COLLECT:
            error_summary = "; ".join([
                f"Iteration {idx}: {err}" for idx, err in errors
            ])
            raise Exception(
                f"Loop completed with {len(errors)} errors: {error_summary}"
            )
        
        return results
    
    async def _execute_iteration(
        self,
        loop_step: LoopStep,
        context: IterationContext
    ) -> StepResult:
        """Execute loop body for single iteration."""
        # Make iteration context available
        self.executor.loop_context = context
        
        # Execute all steps in loop body
        last_result = None
        for step_id in loop_step.loop_body:
            step = self.executor.workflow_plan.steps[step_id]
            last_result = await self.executor.execute_step(step)
            
            if last_result.status == ExecutionStatus.FAILED:
                raise Exception(
                    f"Loop body step '{step_id}' failed: "
                    f"{last_result.error_message}"
                )
        
        # Clear loop context
        self.executor.loop_context = None
        
        return last_result
    
    async def _execute_iteration_with_semaphore(
        self,
        loop_step: LoopStep,
        context: IterationContext,
        semaphore: asyncio.Semaphore
    ) -> StepResult:
        """Execute iteration with semaphore for concurrency control."""
        async with semaphore:
            return await self._execute_iteration(loop_step, context)
```

#### Input Mapping Extension

```python
class InputMappingResolver:
    """Extended to support loop context."""
    
    def __init__(
        self,
        workflow_input: Dict[str, Any],
        step_outputs: Dict[str, Dict[str, Any]],
        loop_context: Optional[IterationContext] = None
    ):
        self.workflow_input = workflow_input
        self.step_outputs = step_outputs
        self.loop_context = loop_context
    
    def resolve(self, input_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Resolve input mapping with loop context support."""
        resolved = {}
        
        for key, value_expr in input_mapping.items():
            if isinstance(value_expr, str) and value_expr.startswith('${'):
                # Check for loop context references
                if '${loop.item}' in value_expr:
                    if self.loop_context:
                        resolved[key] = self.loop_context.item
                    else:
                        raise ValueError("loop.item referenced outside loop")
                
                elif '${loop.index}' in value_expr:
                    if self.loop_context:
                        resolved[key] = self.loop_context.index
                    else:
                        raise ValueError("loop.index referenced outside loop")
                
                else:
                    # Regular variable resolution
                    resolved[key] = self._resolve_variable(value_expr)
            else:
                resolved[key] = value_expr
        
        return resolved
```


#### Database Schema Changes

```sql
-- Add loop execution tracking
ALTER TABLE step_executions 
ADD COLUMN loop_collection_size INTEGER NULL;

ALTER TABLE step_executions 
ADD COLUMN loop_iteration_index INTEGER NULL;

ALTER TABLE step_executions 
ADD COLUMN loop_execution_mode VARCHAR(50) NULL;

-- Index for querying loop iterations
CREATE INDEX idx_step_loop_iteration ON step_executions(run_id, parent_step_id, loop_iteration_index);
```

---

### 4. Fork-Join Pattern Design

#### Architecture

**New Components:**
- `ForkJoinExecutor` - Manages fork-join execution
- `BranchCoordinator` - Coordinates branch lifecycle
- `JoinPolicyEvaluator` - Evaluates join conditions

#### Class Design

```python
from enum import Enum

class JoinPolicy(Enum):
    ALL = "all"          # All branches must succeed
    ANY = "any"          # At least one branch must succeed
    MAJORITY = "majority"  # More than 50% must succeed
    N_OF_M = "n_of_m"    # At least N branches must succeed

@dataclass
class Branch:
    """Represents a single branch in fork-join."""
    name: str
    steps: List[str]
    timeout_seconds: Optional[int] = None

@dataclass
class ForkJoinStep:
    """Represents a fork-join step."""
    id: str
    type: str = "fork_join"
    branches: Dict[str, Branch]
    join_policy: JoinPolicy = JoinPolicy.ALL
    n_required: Optional[int] = None  # For N_OF_M policy
    branch_timeout_seconds: Optional[int] = None
    next_step: Optional[str] = None

class ForkJoinExecutor:
    """
    Executes fork-join pattern.
    
    Forks execution into multiple branches, waits for completion
    based on join policy, and aggregates results.
    """
    
    def __init__(self, executor: 'CentralizedExecutor'):
        self.executor = executor
    
    async def execute_fork_join(
        self,
        fork_join_step: ForkJoinStep
    ) -> Dict[str, StepResult]:
        """
        Execute fork-join pattern.
        
        Returns:
            Dictionary mapping branch name to final StepResult
        """
        # Create tasks for all branches
        branch_tasks = {}
        for branch_name, branch in fork_join_step.branches.items():
            task = asyncio.create_task(
                self._execute_branch(
                    branch_name,
                    branch,
                    fork_join_step.branch_timeout_seconds
                )
            )
            branch_tasks[branch_name] = task
        
        # Wait for branches based on join policy
        results = await self._wait_for_branches(
            branch_tasks,
            fork_join_step.join_policy,
            fork_join_step.n_required
        )
        
        return results
    
    async def _execute_branch(
        self,
        branch_name: str,
        branch: Branch,
        default_timeout: Optional[int]
    ) -> StepResult:
        """Execute all steps in a branch sequentially."""
        timeout = branch.timeout_seconds or default_timeout
        
        try:
            if timeout:
                return await asyncio.wait_for(
                    self._execute_branch_steps(branch_name, branch),
                    timeout=timeout
                )
            else:
                return await self._execute_branch_steps(branch_name, branch)
        
        except asyncio.TimeoutError:
            raise Exception(
                f"Branch '{branch_name}' timed out after {timeout}s"
            )
    
    async def _execute_branch_steps(
        self,
        branch_name: str,
        branch: Branch
    ) -> StepResult:
        """Execute steps in branch sequentially."""
        last_result = None
        
        for step_id in branch.steps:
            step = self.executor.workflow_plan.steps[step_id]
            last_result = await self.executor.execute_step(step)
            
            if last_result.status == ExecutionStatus.FAILED:
                raise Exception(
                    f"Branch '{branch_name}' failed at step '{step_id}': "
                    f"{last_result.error_message}"
                )
        
        return last_result
    
    async def _wait_for_branches(
        self,
        branch_tasks: Dict[str, asyncio.Task],
        join_policy: JoinPolicy,
        n_required: Optional[int]
    ) -> Dict[str, StepResult]:
        """Wait for branches based on join policy."""
        results = {}
        errors = {}
        
        # Wait for all tasks to complete
        for branch_name, task in branch_tasks.items():
            try:
                result = await task
                results[branch_name] = result
            except Exception as e:
                errors[branch_name] = str(e)
                results[branch_name] = StepResult(
                    step_id=f"branch-{branch_name}",
                    status=ExecutionStatus.FAILED,
                    input_data={},
                    error_message=str(e)
                )
        
        # Evaluate join policy
        success_count = sum(
            1 for r in results.values()
            if r.status == ExecutionStatus.COMPLETED
        )
        total_count = len(branch_tasks)
        
        if join_policy == JoinPolicy.ALL:
            if success_count < total_count:
                raise Exception(
                    f"Fork-join failed: {total_count - success_count} "
                    f"branches failed (policy: ALL)"
                )
        
        elif join_policy == JoinPolicy.ANY:
            if success_count == 0:
                raise Exception(
                    "Fork-join failed: All branches failed (policy: ANY)"
                )
        
        elif join_policy == JoinPolicy.MAJORITY:
            if success_count <= total_count / 2:
                raise Exception(
                    f"Fork-join failed: Only {success_count}/{total_count} "
                    f"branches succeeded (policy: MAJORITY)"
                )
        
        elif join_policy == JoinPolicy.N_OF_M:
            if not n_required:
                raise ValueError("n_required must be specified for N_OF_M policy")
            if success_count < n_required:
                raise Exception(
                    f"Fork-join failed: Only {success_count}/{total_count} "
                    f"branches succeeded, need {n_required} (policy: N_OF_M)"
                )
        
        return results
```

#### Database Schema Changes

```sql
-- Add fork-join tracking
ALTER TABLE step_executions 
ADD COLUMN branch_name VARCHAR(255) NULL;

ALTER TABLE step_executions 
ADD COLUMN join_policy VARCHAR(50) NULL;

-- Index for querying branches
CREATE INDEX idx_step_branch ON step_executions(run_id, parent_step_id, branch_name);
```

---


## PHASE 2: RESILIENCE & ERROR HANDLING

---

### 5. Circuit Breaker Design

#### Architecture

**New Components:**
- `CircuitBreakerManager` - Manages circuit breaker state
- `CircuitBreaker` - Individual circuit breaker per agent
- `CircuitBreakerStateStore` - Shared state storage (Redis)

#### Class Design

```python
from enum import Enum
from datetime import datetime, timedelta
import redis

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    enabled: bool = True
    failure_threshold: int = 5
    failure_rate_threshold: float = 0.5
    timeout_seconds: int = 60
    half_open_max_calls: int = 3
    window_size_seconds: int = 120

class CircuitBreaker:
    """
    Circuit breaker for a single agent.
    
    States:
    - CLOSED: Normal operation, all calls go through
    - OPEN: Agent is failing, reject all calls immediately
    - HALF_OPEN: Testing recovery, allow limited calls
    """
    
    def __init__(
        self,
        agent_name: str,
        config: CircuitBreakerConfig,
        state_store: 'CircuitBreakerStateStore'
    ):
        self.agent_name = agent_name
        self.config = config
        self.state_store = state_store
    
    async def call(self, operation: Callable) -> Any:
        """
        Execute operation through circuit breaker.
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if not self.config.enabled:
            return await operation()
        
        # Check circuit state
        state = await self.state_store.get_state(self.agent_name)
        
        if state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if await self._should_attempt_reset():
                await self.state_store.set_state(
                    self.agent_name,
                    CircuitState.HALF_OPEN
                )
                state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN for agent '{self.agent_name}'"
                )
        
        if state == CircuitState.HALF_OPEN:
            # Check if we can make a test call
            if not await self._can_make_half_open_call():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is HALF_OPEN, max calls reached"
                )
        
        # Execute operation
        try:
            result = await operation()
            await self._record_success()
            return result
        
        except Exception as e:
            await self._record_failure()
            raise
    
    async def _record_success(self):
        """Record successful call."""
        state = await self.state_store.get_state(self.agent_name)
        
        if state == CircuitState.HALF_OPEN:
            # Transition to CLOSED if enough successes
            success_count = await self.state_store.increment_success(
                self.agent_name
            )
            if success_count >= self.config.half_open_max_calls:
                await self.state_store.set_state(
                    self.agent_name,
                    CircuitState.CLOSED
                )
                await self.state_store.reset_counters(self.agent_name)
        
        elif state == CircuitState.CLOSED:
            # Just record the success
            await self.state_store.record_call(
                self.agent_name,
                success=True
            )
    
    async def _record_failure(self):
        """Record failed call."""
        state = await self.state_store.get_state(self.agent_name)
        
        if state == CircuitState.HALF_OPEN:
            # Transition back to OPEN
            await self.state_store.set_state(
                self.agent_name,
                CircuitState.OPEN
            )
            await self.state_store.set_open_timestamp(
                self.agent_name,
                datetime.utcnow()
            )
        
        elif state == CircuitState.CLOSED:
            # Record failure and check thresholds
            await self.state_store.record_call(
                self.agent_name,
                success=False
            )
            
            # Check if we should open the circuit
            if await self._should_open_circuit():
                await self.state_store.set_state(
                    self.agent_name,
                    CircuitState.OPEN
                )
                await self.state_store.set_open_timestamp(
                    self.agent_name,
                    datetime.utcnow()
                )
    
    async def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened."""
        # Get recent call history
        calls = await self.state_store.get_recent_calls(
            self.agent_name,
            window_seconds=self.config.window_size_seconds
        )
        
        if len(calls) < self.config.failure_threshold:
            return False
        
        # Check consecutive failures
        recent_failures = sum(1 for c in calls[-self.config.failure_threshold:] if not c)
        if recent_failures >= self.config.failure_threshold:
            return True
        
        # Check failure rate
        total_calls = len(calls)
        failed_calls = sum(1 for c in calls if not c)
        failure_rate = failed_calls / total_calls
        
        return failure_rate >= self.config.failure_rate_threshold
    
    async def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        open_timestamp = await self.state_store.get_open_timestamp(
            self.agent_name
        )
        
        if not open_timestamp:
            return True
        
        elapsed = (datetime.utcnow() - open_timestamp).total_seconds()
        return elapsed >= self.config.timeout_seconds
    
    async def _can_make_half_open_call(self) -> bool:
        """Check if we can make a call in half-open state."""
        half_open_calls = await self.state_store.get_half_open_calls(
            self.agent_name
        )
        return half_open_calls < self.config.half_open_max_calls

class CircuitBreakerStateStore:
    """
    Shared state storage for circuit breakers using Redis.
    
    Enables circuit breaker state to be shared across multiple
    executor instances.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get_state(self, agent_name: str) -> CircuitState:
        """Get current circuit state."""
        key = f"circuit_breaker:{agent_name}:state"
        state_str = await self.redis.get(key)
        
        if not state_str:
            return CircuitState.CLOSED
        
        return CircuitState(state_str.decode())
    
    async def set_state(self, agent_name: str, state: CircuitState):
        """Set circuit state."""
        key = f"circuit_breaker:{agent_name}:state"
        await self.redis.set(key, state.value)
    
    async def record_call(self, agent_name: str, success: bool):
        """Record a call result in sliding window."""
        key = f"circuit_breaker:{agent_name}:calls"
        timestamp = datetime.utcnow().timestamp()
        value = f"{timestamp}:{1 if success else 0}"
        
        # Add to sorted set with timestamp as score
        await self.redis.zadd(key, {value: timestamp})
        
        # Remove old entries (outside window)
        window_start = timestamp - 120  # 2 minutes
        await self.redis.zremrangebyscore(key, 0, window_start)
    
    async def get_recent_calls(
        self,
        agent_name: str,
        window_seconds: int
    ) -> List[bool]:
        """Get recent call results within window."""
        key = f"circuit_breaker:{agent_name}:calls"
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds
        
        # Get calls within window
        calls = await self.redis.zrangebyscore(
            key,
            window_start,
            now
        )
        
        # Parse results
        return [
            bool(int(call.decode().split(':')[1]))
            for call in calls
        ]
    
    # Additional methods for timestamps, counters, etc.
    # ... (implementation details)

class CircuitBreakerManager:
    """
    Manages circuit breakers for all agents.
    
    Provides a centralized interface for circuit breaker operations.
    """
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
        self.state_store = CircuitBreakerStateStore(self.redis_client)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(
        self,
        agent_name: str,
        config: CircuitBreakerConfig
    ) -> CircuitBreaker:
        """Get or create circuit breaker for agent."""
        if agent_name not in self.circuit_breakers:
            self.circuit_breakers[agent_name] = CircuitBreaker(
                agent_name=agent_name,
                config=config,
                state_store=self.state_store
            )
        
        return self.circuit_breakers[agent_name]
```

#### Integration with Bridge

```python
# In ExternalAgentExecutor
class ExternalAgentExecutor:
    def __init__(self, ..., circuit_breaker_manager: CircuitBreakerManager):
        # ... existing init
        self.circuit_breaker_manager = circuit_breaker_manager
    
    async def invoke_agent(
        self,
        agent_metadata: AgentMetadata,
        task: AgentTask
    ) -> Dict[str, Any]:
        """Invoke agent through circuit breaker."""
        
        # Get circuit breaker for this agent
        circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker(
            agent_name=agent_metadata.name,
            config=agent_metadata.circuit_breaker_config
        )
        
        # Execute through circuit breaker
        try:
            return await circuit_breaker.call(
                lambda: self._invoke_agent_http(agent_metadata, task)
            )
        except CircuitBreakerOpenError as e:
            # Circuit is open, fail immediately
            logger.warning(f"Circuit breaker open for {agent_metadata.name}")
            raise
```


---

### 6. Enhanced Retry Strategies Design

#### Key Changes

**Extend RetryConfig:**
```python
@dataclass
class RetryStrategy:
    type: str  # "exponential_backoff", "fixed_delay", "immediate", "linear_backoff"
    max_retries: int = 3
    initial_delay_ms: int = 1000
    max_delay_ms: int = 30000
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_on_errors: List[str] = field(default_factory=list)
    retry_on_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
```

**Implementation in Bridge:**
- Check error type against `retry_on_errors`
- Check HTTP status against `retry_on_status_codes`
- Apply jitter: `delay * (1 + random.uniform(-0.1, 0.1))`
- Support different backoff strategies

---

### 7. Dead Letter Queue Design

#### Architecture

**New Components:**
- `DLQPublisher` - Publishes failed tasks to DLQ
- `DLQManager` - Manages DLQ operations (list, replay, delete)

**Kafka Topics:**
- `workflow.dlq` - Dead letter queue topic

**Database Table:**
```sql
CREATE TABLE dlq_entries (
    dlq_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id VARCHAR(255) NOT NULL,
    step_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    original_task JSONB NOT NULL,
    failure_reason TEXT NOT NULL,
    retry_history JSONB,
    first_failed_at TIMESTAMP NOT NULL,
    last_failed_at TIMESTAMP NOT NULL,
    failure_count INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'pending_replay',
    replayed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dlq_status ON dlq_entries(status);
CREATE INDEX idx_dlq_agent ON dlq_entries(agent_name);
```

**API Endpoints:**
```
GET    /api/v1/dlq                    - List DLQ entries
GET    /api/v1/dlq/{dlq_id}           - Get DLQ entry details
POST   /api/v1/dlq/{dlq_id}/replay    - Replay task
DELETE /api/v1/dlq/{dlq_id}           - Delete entry
POST   /api/v1/dlq/bulk-replay        - Replay multiple tasks
```

---

## PHASE 3: WORKFLOW COMPOSITION

---

### 8. Sub-Workflows Design

#### Architecture

**Key Concepts:**
- Sub-workflow is a regular workflow called as a step
- Creates parent-child relationship between runs
- Supports nesting up to configurable depth (default: 5)

**Database Schema:**
```sql
ALTER TABLE workflow_runs 
ADD COLUMN parent_run_id VARCHAR(255) NULL;

ALTER TABLE workflow_runs 
ADD COLUMN nesting_level INTEGER DEFAULT 0;

CREATE INDEX idx_run_parent ON workflow_runs(parent_run_id);
```

**Step Definition:**
```python
@dataclass
class SubWorkflowStep:
    id: str
    type: str = "sub_workflow"
    workflow_id: str
    workflow_version: Optional[str] = None
    input_mapping: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: Optional[int] = None
    next_step: Optional[str] = None
```

**Execution Flow:**
1. Executor encounters sub_workflow step
2. Load workflow definition (specific version or latest)
3. Resolve input using input_mapping
4. Create new workflow run with parent_run_id
5. Publish execution request to Kafka
6. Wait for sub-workflow completion (poll database)
7. Extract output and continue parent workflow

---

### 9. Workflow Chaining Design

#### Architecture

**Workflow Definition Extension:**
```python
@dataclass
class WorkflowDefinition:
    # ... existing fields
    on_complete: Optional[ChainConfig] = None

@dataclass
class ChainConfig:
    trigger_workflow: str
    condition: Optional[str] = None
    input_mapping: Dict[str, str] = field(default_factory=dict)
```

**Implementation:**
- Executor checks `on_complete` after workflow completes
- Evaluates condition (if specified)
- Publishes execution request for chained workflow
- Tracks chain relationship in database

**Database Schema:**
```sql
ALTER TABLE workflow_runs 
ADD COLUMN triggered_by_run_id VARCHAR(255) NULL;

ALTER TABLE workflow_runs 
ADD COLUMN chain_sequence INTEGER NULL;

CREATE INDEX idx_run_chain ON workflow_runs(triggered_by_run_id);
```

---

## PHASE 4: ADVANCED CONTROL FLOW

---

### 10. Event-Driven Steps Design

#### Architecture

**New Components:**
- `EventListener` - Listens for events from various sources
- `WebhookManager` - Manages webhook endpoints
- `EventMatcher` - Matches events against filters

**Event Sources:**
1. **Webhook**: Generate unique URL, wait for HTTP POST
2. **Kafka**: Subscribe to topic, wait for matching message
3. **HTTP Poll**: Periodically poll URL until condition met

**Step Definition:**
```python
@dataclass
class EventDrivenStep:
    id: str
    type: str = "wait_for_event"
    event_source: str  # "webhook", "kafka", "http_poll"
    event_filter: Dict[str, Any]
    timeout_seconds: int = 86400
    on_timeout: str = "fail"  # "fail" or "continue"
    next_step: Optional[str] = None
```

**Webhook Implementation:**
```python
# Generate unique webhook URL
webhook_url = f"https://api.example.com/webhooks/{run_id}/{step_id}/{token}"

# Store webhook registration
await webhook_manager.register(
    run_id=run_id,
    step_id=step_id,
    token=token,
    event_filter=event_filter
)

# Pause executor, wait for webhook call
# When webhook receives POST, validate against filter
# Resume executor with event data
```

---

### 11. State Machine Workflows Design

#### Architecture

**Workflow Type Extension:**
```python
@dataclass
class StateMachineWorkflow:
    workflow_id: str
    type: str = "state_machine"
    initial_state: str
    states: Dict[str, State]

@dataclass
class State:
    name: str
    actions: List[str]  # Step IDs to execute
    on_entry: Optional[List[str]] = None
    on_exit: Optional[List[str]] = None
    transitions: List[Transition] = field(default_factory=list)
    terminal: bool = False

@dataclass
class Transition:
    condition: str
    target: str
```

**Execution Flow:**
1. Start from initial_state
2. Execute on_entry actions (if any)
3. Execute state actions
4. Execute on_exit actions (if any)
5. Evaluate transitions in order
6. Move to target state of first matching transition
7. Repeat until terminal state reached

**Database Schema:**
```sql
ALTER TABLE workflow_runs 
ADD COLUMN current_state VARCHAR(255) NULL;

CREATE TABLE state_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id VARCHAR(255) NOT NULL,
    state_name VARCHAR(255) NOT NULL,
    entered_at TIMESTAMP NOT NULL,
    exited_at TIMESTAMP NULL,
    transition_condition TEXT NULL,
    FOREIGN KEY (run_id) REFERENCES workflow_runs(run_id)
);

CREATE INDEX idx_state_history_run ON state_history(run_id);
```

---

### 12. Workflow Pause/Resume Design

#### Architecture

**API Endpoints:**
```
POST /api/v1/runs/{run_id}/pause
POST /api/v1/runs/{run_id}/resume
```

**Database Schema:**
```sql
ALTER TABLE workflow_runs 
ADD COLUMN paused_at TIMESTAMP NULL;

ALTER TABLE workflow_runs 
ADD COLUMN paused_by VARCHAR(255) NULL;

ALTER TABLE workflow_runs 
ADD COLUMN pause_reason TEXT NULL;
```

**Implementation:**
1. Pause request sets flag in database
2. Executor checks pause flag before each step
3. If paused, executor completes current step then stops
4. Executor persists state and terminates
5. Resume request clears pause flag
6. New executor spawned, loads state, continues execution

---

## PHASE 5: DATA & PERFORMANCE

---

### 13. Data Validation Steps Design

#### Architecture

**Step Definition:**
```python
@dataclass
class ValidationStep:
    id: str
    type: str = "validate"
    data_source: str  # Reference to data
    validation_schema: Dict[str, Any]
    assertions: List[str] = field(default_factory=list)
    validation_mode: str = "strict"  # "strict" or "warn"
    on_validation_error: str = "fail"
    next_step: Optional[str] = None
```

**Validator Implementation:**
```python
import jsonschema

class DataValidator:
    def validate(
        self,
        data: Any,
        schema: Dict[str, Any],
        assertions: List[str]
    ) -> ValidationResult:
        # JSON Schema validation
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            return ValidationResult(valid=False, errors=[str(e)])
        
        # Assertion validation
        for assertion in assertions:
            if not self._evaluate_assertion(assertion, data):
                return ValidationResult(
                    valid=False,
                    errors=[f"Assertion failed: {assertion}"]
                )
        
        return ValidationResult(valid=True, errors=[])
```

---

### 14. Conditional Caching Design

#### Architecture

**Cache Storage:** Redis

**Step Configuration:**
```python
@dataclass
class CachingConfig:
    enabled: bool = True
    cache_key_template: str
    cache_ttl_seconds: int = 3600
    cache_condition: Optional[str] = None
    cache_scope: str = "global"  # "global", "workflow", "user"
    cache_storage: str = "redis"
    cache_on_success_only: bool = True
```

**Implementation:**
```python
class CacheManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl_seconds: int
    ):
        """Set cached value with TTL."""
        await self.redis.setex(
            key,
            ttl_seconds,
            json.dumps(value)
        )
    
    def generate_cache_key(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate cache key from template."""
        # Replace variables in template
        # Example: "agent:${agent_name}:input:${hash(input_data)}"
        return template.format(**context)
```

**Execution Flow:**
1. Before invoking agent, check if caching enabled
2. Evaluate cache_condition (if specified)
3. Generate cache key from template
4. Check cache for existing value
5. If hit, return cached value
6. If miss, invoke agent
7. If success and condition met, store in cache

---

## PHASE 6: WORKFLOW MANAGEMENT

---

### 15. Workflow Scheduling Design

#### Architecture

**New Service:** `SchedulerService`

**Database Schema:**
```sql
CREATE TABLE workflow_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL,
    cron_expression VARCHAR(255) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    input_template JSONB,
    enabled BOOLEAN DEFAULT true,
    start_date TIMESTAMP NULL,
    end_date TIMESTAMP NULL,
    max_concurrent_runs INTEGER DEFAULT 1,
    on_failure VARCHAR(50) DEFAULT 'retry',
    retry_config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_run_at TIMESTAMP NULL,
    next_run_at TIMESTAMP NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(id)
);

CREATE INDEX idx_schedule_next_run ON workflow_schedules(next_run_at) WHERE enabled = true;
```

**Scheduler Implementation:**
```python
from croniter import croniter
from datetime import datetime
import pytz

class SchedulerService:
    """
    Manages scheduled workflow executions.
    
    Runs as a background service that:
    1. Polls for schedules due to run
    2. Triggers workflow execution
    3. Updates next_run_at
    """
    
    async def run(self):
        """Main scheduler loop."""
        while True:
            # Get schedules due to run
            schedules = await self.get_due_schedules()
            
            for schedule in schedules:
                await self.execute_schedule(schedule)
            
            # Sleep until next check
            await asyncio.sleep(60)  # Check every minute
    
    async def execute_schedule(self, schedule: WorkflowSchedule):
        """Execute a scheduled workflow."""
        # Check max concurrent runs
        active_runs = await self.count_active_runs(schedule.workflow_id)
        if active_runs >= schedule.max_concurrent_runs:
            logger.warning(f"Max concurrent runs reached for schedule {schedule.schedule_id}")
            return
        
        # Evaluate input template
        input_data = self.evaluate_input_template(schedule.input_template)
        
        # Trigger workflow execution
        try:
            await self.execution_service.execute_workflow(
                workflow_id=schedule.workflow_id,
                input_data=input_data,
                triggered_by=f"schedule:{schedule.schedule_id}"
            )
            
            # Update last_run_at and next_run_at
            await self.update_schedule_timestamps(schedule)
        
        except Exception as e:
            await self.handle_schedule_failure(schedule, e)
    
    def calculate_next_run(
        self,
        cron_expression: str,
        timezone: str,
        from_time: datetime
    ) -> datetime:
        """Calculate next run time from cron expression."""
        tz = pytz.timezone(timezone)
        local_time = from_time.astimezone(tz)
        
        cron = croniter(cron_expression, local_time)
        next_run = cron.get_next(datetime)
        
        return next_run.astimezone(pytz.UTC)
```

---

### 16. Enhanced Workflow Versioning Design

#### Architecture

**Database Schema (Already Exists, Enhance):**
```sql
-- Add version metadata
ALTER TABLE workflow_definitions 
ADD COLUMN change_summary TEXT NULL;

ALTER TABLE workflow_definitions 
ADD COLUMN previous_version INTEGER NULL;

ALTER TABLE workflow_definitions 
ADD COLUMN is_latest BOOLEAN DEFAULT false;

-- Version status
ALTER TABLE workflow_definitions 
ADD COLUMN version_status VARCHAR(50) DEFAULT 'active';
-- Values: 'draft', 'active', 'deprecated', 'archived'

CREATE INDEX idx_workflow_version_status ON workflow_definitions(workflow_id, version_status);
```

**API Endpoints:**
```
GET    /api/v1/workflows/{workflow_id}/versions
GET    /api/v1/workflows/{workflow_id}/versions/{version}
POST   /api/v1/workflows/{workflow_id}/versions/{version}/rollback
GET    /api/v1/workflows/{workflow_id}/versions/compare?from=v1&to=v2
PUT    /api/v1/workflows/{workflow_id}/versions/{version}/status
```

**Version Comparison:**
```python
import difflib

class VersionComparator:
    def compare(
        self,
        version1: WorkflowDefinition,
        version2: WorkflowDefinition
    ) -> Dict[str, Any]:
        """Compare two workflow versions."""
        # Convert to JSON for comparison
        v1_json = json.dumps(version1.workflow_data, indent=2, sort_keys=True)
        v2_json = json.dumps(version2.workflow_data, indent=2, sort_keys=True)
        
        # Generate diff
        diff = list(difflib.unified_diff(
            v1_json.splitlines(),
            v2_json.splitlines(),
            lineterm='',
            fromfile=f'v{version1.version}',
            tofile=f'v{version2.version}'
        ))
        
        return {
            "from_version": version1.version,
            "to_version": version2.version,
            "diff": diff,
            "changes_summary": self._summarize_changes(version1, version2)
        }
```

---


## INTEGRATION & DEPLOYMENT

---

### Centralized Executor Refactoring

**New Architecture:**

```python
class CentralizedExecutor:
    """
    Enhanced executor with support for all execution patterns.
    """
    
    def __init__(self, ...):
        # ... existing init
        
        # New executors
        self.parallel_executor = ParallelExecutor(self)
        self.conditional_executor = ConditionalExecutor(self)
        self.loop_executor = LoopExecutor(self)
        self.fork_join_executor = ForkJoinExecutor(self)
        self.state_machine_executor = StateMachineExecutor(self)
        
        # Resilience components
        self.circuit_breaker_manager = CircuitBreakerManager(redis_url)
        self.dlq_publisher = DLQPublisher(kafka_producer)
        
        # Data components
        self.cache_manager = CacheManager(redis_client)
        self.validator = DataValidator()
        
        # Loop context (for iterations)
        self.loop_context: Optional[IterationContext] = None
    
    async def execute_step(self, step: WorkflowStep) -> StepResult:
        """
        Execute step based on type.
        
        Dispatches to appropriate executor based on step.type.
        """
        # Check for pause
        if await self._is_paused():
            await self._wait_for_resume()
        
        # Dispatch based on step type
        if step.type == "agent":
            return await self._execute_agent_step(step)
        
        elif step.type == "parallel":
            parallel_block = ParallelBlock(**step.__dict__)
            results = await self.parallel_executor.execute_parallel_block(
                parallel_block
            )
            # Aggregate results
            return self._aggregate_parallel_results(step.id, results)
        
        elif step.type == "conditional":
            conditional_step = ConditionalStep(**step.__dict__)
            return await self.conditional_executor.execute_conditional(
                conditional_step
            )
        
        elif step.type == "loop":
            loop_step = LoopStep(**step.__dict__)
            results = await self.loop_executor.execute_loop(loop_step)
            return self._aggregate_loop_results(step.id, results)
        
        elif step.type == "fork_join":
            fork_join_step = ForkJoinStep(**step.__dict__)
            results = await self.fork_join_executor.execute_fork_join(
                fork_join_step
            )
            return self._aggregate_fork_join_results(step.id, results)
        
        elif step.type == "sub_workflow":
            sub_workflow_step = SubWorkflowStep(**step.__dict__)
            return await self._execute_sub_workflow(sub_workflow_step)
        
        elif step.type == "wait_for_event":
            event_step = EventDrivenStep(**step.__dict__)
            return await self._execute_event_driven_step(event_step)
        
        elif step.type == "validate":
            validation_step = ValidationStep(**step.__dict__)
            return await self._execute_validation_step(validation_step)
        
        else:
            raise ValueError(f"Unknown step type: {step.type}")
    
    async def _execute_agent_step(self, step: WorkflowStep) -> StepResult:
        """Execute regular agent step with caching support."""
        # Check cache if enabled
        if step.caching and step.caching.enabled:
            cached_result = await self._check_cache(step)
            if cached_result:
                return cached_result
        
        # Execute step (existing logic)
        result = await self._execute_step_original(step)
        
        # Store in cache if conditions met
        if step.caching and step.caching.enabled:
            await self._store_in_cache(step, result)
        
        return result
```

---

### Database Migration Strategy

**Migration Order:**

1. **Phase 1 Migrations:**
   - Add `step_type` column
   - Add `parent_step_id` column
   - Add `execution_order` column
   - Add conditional tracking columns
   - Add loop tracking columns
   - Add branch tracking columns

2. **Phase 2 Migrations:**
   - Create `dlq_entries` table
   - Add circuit breaker state (handled by Redis)

3. **Phase 3 Migrations:**
   - Add `parent_run_id` column
   - Add `nesting_level` column
   - Add `triggered_by_run_id` column
   - Add `chain_sequence` column

4. **Phase 4 Migrations:**
   - Add `current_state` column
   - Create `state_history` table
   - Add pause/resume columns

5. **Phase 6 Migrations:**
   - Create `workflow_schedules` table
   - Add version metadata columns

**Backward Compatibility:**
- All new columns have defaults or are nullable
- Existing workflows continue to work (type defaults to "agent")
- New features are opt-in

---

### Configuration Management

**New Environment Variables:**

```bash
# Redis (for circuit breaker and caching)
REDIS_URL=redis://localhost:6379/0

# Circuit Breaker
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_DEFAULT_THRESHOLD=5
CIRCUIT_BREAKER_DEFAULT_TIMEOUT=60

# Caching
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=3600

# Scheduling
SCHEDULER_ENABLED=true
SCHEDULER_CHECK_INTERVAL=60

# Limits
MAX_PARALLEL_STEPS=50
MAX_LOOP_ITERATIONS=10000
MAX_WORKFLOW_NESTING=5
MAX_FORK_JOIN_BRANCHES=20
```

---

### Monitoring & Observability

**New Metrics:**

```python
# Execution pattern metrics
parallel_execution_duration = Histogram(
    'parallel_execution_duration_seconds',
    'Duration of parallel execution blocks',
    ['workflow_id', 'step_id']
)

loop_iteration_count = Counter(
    'loop_iteration_count_total',
    'Total loop iterations executed',
    ['workflow_id', 'step_id', 'execution_mode']
)

conditional_branch_taken = Counter(
    'conditional_branch_taken_total',
    'Conditional branches taken',
    ['workflow_id', 'step_id', 'branch']
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['agent_name']
)

circuit_breaker_failures = Counter(
    'circuit_breaker_failures_total',
    'Circuit breaker failures',
    ['agent_name']
)

# Cache metrics
cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate',
    ['step_id']
)

# DLQ metrics
dlq_entries_total = Counter(
    'dlq_entries_total',
    'Total DLQ entries',
    ['agent_name']
)
```

**New Log Events:**

```python
# Parallel execution
log_event(logger, 'info', 'parallel_start',
    f"Starting parallel execution of {len(steps)} steps")

# Loop execution
log_event(logger, 'info', 'loop_start',
    f"Starting loop with {len(collection)} iterations")

# Circuit breaker
log_event(logger, 'warning', 'circuit_breaker_open',
    f"Circuit breaker opened for agent '{agent_name}'")

# Cache
log_event(logger, 'debug', 'cache_hit',
    f"Cache hit for step '{step_id}'")
```

---

### Testing Strategy

**Unit Tests:**
- Test each executor independently
- Mock dependencies (Kafka, Redis, Database)
- Test edge cases (empty collections, invalid conditions, etc.)

**Integration Tests:**
- Test executor with real Kafka and Redis
- Test database persistence
- Test circuit breaker state sharing

**End-to-End Tests:**
- Test complete workflows with all patterns
- Test failure scenarios
- Test recovery mechanisms

**Performance Tests:**
- Benchmark parallel execution vs sequential
- Test loop performance with large collections
- Test cache hit rate impact

---

### Deployment Strategy

**Phase 1 Deployment (Foundation):**
1. Deploy database migrations
2. Deploy enhanced executor with Phase 1 features
3. Deploy updated bridge with circuit breaker support
4. Test with pilot workflows

**Phase 2 Deployment (Resilience):**
1. Deploy Redis for circuit breaker state
2. Enable circuit breaker for selected agents
3. Deploy DLQ infrastructure
4. Monitor and tune thresholds

**Phase 3-6 Deployment (Advanced Features):**
1. Deploy incrementally, one phase at a time
2. Enable features per workflow (opt-in)
3. Monitor performance and stability
4. Gather feedback and iterate

**Rollback Plan:**
- Database migrations are backward compatible
- Feature flags allow disabling new features
- Old executor version can still run existing workflows

---

### Performance Considerations

**Parallel Execution:**
- Use asyncio for concurrency (no thread overhead)
- Limit max parallelism to prevent resource exhaustion
- Monitor Kafka consumer lag

**Loops:**
- Batch database writes for iterations
- Use connection pooling
- Consider pagination for very large collections

**Circuit Breaker:**
- Redis operations are fast (<1ms)
- State is cached locally for 1 second
- Minimal overhead when circuit is closed

**Caching:**
- Redis operations are fast (<1ms)
- Cache key generation is optimized
- TTL prevents unbounded growth

---

### Security Considerations

**Circuit Breaker:**
- Redis connection uses authentication
- Circuit breaker state is not sensitive data

**Caching:**
- Cache keys include tenant/user ID for isolation
- Sensitive data can be excluded from caching
- Cache TTL prevents stale data

**DLQ:**
- DLQ entries may contain sensitive data
- Encrypt at rest
- Access control via API

**Sub-Workflows:**
- Validate nesting depth to prevent DoS
- Check permissions before executing sub-workflow

---

## Summary

This design provides a comprehensive architecture for implementing 16 advanced workflow execution features. Key design decisions:

1. **Modular Executors**: Each pattern has its own executor class
2. **Backward Compatible**: Existing workflows continue to work
3. **Opt-In Features**: New features are enabled per workflow
4. **Shared State**: Circuit breaker and cache use Redis
5. **Async-First**: All executors use asyncio for concurrency
6. **Observable**: Comprehensive metrics and logging
7. **Testable**: Each component can be tested independently

**Next Steps:**
1. Review and approve design
2. Create implementation tasks
3. Begin Phase 1 implementation
4. Iterate based on feedback


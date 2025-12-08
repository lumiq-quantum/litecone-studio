"""Pattern generation utilities for complex workflow structures."""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PatternGenerator:
    """Generates complex workflow patterns like loops, conditionals, parallel, and fork-join."""
    
    @staticmethod
    def generate_loop_structure(
        loop_step_id: str,
        collection_reference: str,
        loop_body_steps: List[str],
        execution_mode: str = "sequential",
        max_iterations: int = 100,
        on_error: str = "continue",
        next_step: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a loop step structure.
        
        Args:
            loop_step_id: ID for the loop step
            collection_reference: Reference to the collection to iterate over (e.g., "${step-1.output.items}")
            loop_body_steps: List of step IDs that form the loop body
            execution_mode: "sequential" or "parallel"
            max_iterations: Maximum number of iterations
            on_error: Error handling strategy ("continue", "stop", "fail")
            next_step: Next step after loop completes
            
        Returns:
            Loop step definition
        """
        logger.debug(f"Generating loop structure: {loop_step_id}")
        
        return {
            "id": loop_step_id,
            "type": "loop",
            "loop_config": {
                "collection": collection_reference,
                "loop_body": loop_body_steps,
                "execution_mode": execution_mode,
                "max_iterations": max_iterations,
                "on_error": on_error
            },
            "next_step": next_step
        }
    
    @staticmethod
    def generate_conditional_structure(
        conditional_step_id: str,
        condition_expression: str,
        if_true_step: str,
        if_false_step: str,
        next_step: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a conditional step structure.
        
        Args:
            conditional_step_id: ID for the conditional step
            condition_expression: Boolean expression to evaluate
            if_true_step: Step to execute if condition is true
            if_false_step: Step to execute if condition is false
            next_step: Next step after conditional branches complete
            
        Returns:
            Conditional step definition
        """
        logger.debug(f"Generating conditional structure: {conditional_step_id}")
        
        return {
            "id": conditional_step_id,
            "type": "conditional",
            "condition": {
                "expression": condition_expression
            },
            "if_true_step": if_true_step,
            "if_false_step": if_false_step,
            "next_step": next_step
        }
    
    @staticmethod
    def generate_parallel_structure(
        parallel_step_id: str,
        parallel_steps: List[str],
        max_parallelism: Optional[int] = None,
        next_step: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a parallel execution block structure.
        
        Args:
            parallel_step_id: ID for the parallel block
            parallel_steps: List of step IDs to execute in parallel
            max_parallelism: Maximum number of concurrent executions
            next_step: Next step after all parallel steps complete
            
        Returns:
            Parallel step definition
        """
        logger.debug(f"Generating parallel structure: {parallel_step_id}")
        
        step_def = {
            "id": parallel_step_id,
            "type": "parallel",
            "parallel_steps": parallel_steps,
            "next_step": next_step
        }
        
        if max_parallelism is not None:
            step_def["max_parallelism"] = max_parallelism
        
        return step_def
    
    @staticmethod
    def generate_fork_join_structure(
        fork_join_step_id: str,
        branches: Dict[str, Dict[str, Any]],
        join_policy: str = "all",
        branch_timeout_seconds: int = 60,
        next_step: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a fork-join structure.
        
        Args:
            fork_join_step_id: ID for the fork-join step
            branches: Dictionary of branch_name -> branch_config
                     Each branch_config should have:
                     - steps: List of step IDs in the branch
                     - timeout_seconds: Optional timeout for the branch
            join_policy: Join policy ("all", "any", "n_of_m")
            branch_timeout_seconds: Default timeout for branches
            next_step: Next step after fork-join completes
            
        Returns:
            Fork-join step definition
        """
        logger.debug(f"Generating fork-join structure: {fork_join_step_id}")
        
        # Ensure each branch has required fields
        formatted_branches = {}
        for branch_name, branch_config in branches.items():
            formatted_branches[branch_name] = {
                "steps": branch_config.get("steps", []),
                "timeout_seconds": branch_config.get("timeout_seconds", 30)
            }
        
        return {
            "id": fork_join_step_id,
            "type": "fork_join",
            "fork_join_config": {
                "branches": formatted_branches,
                "join_policy": join_policy,
                "branch_timeout_seconds": branch_timeout_seconds
            },
            "next_step": next_step
        }
    
    @staticmethod
    def validate_nested_references(
        workflow_json: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate that nested patterns have correct step references.
        
        Args:
            workflow_json: Workflow to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        steps = workflow_json.get("steps", {})
        
        # Collect all step IDs
        all_step_ids = set(steps.keys())
        
        for step_id, step in steps.items():
            step_type = step.get("type", "agent")
            
            # Validate loop body references
            if step_type == "loop":
                loop_config = step.get("loop_config", {})
                loop_body = loop_config.get("loop_body", [])
                
                for body_step_id in loop_body:
                    if body_step_id not in all_step_ids:
                        errors.append(
                            f"Loop step '{step_id}' references non-existent body step '{body_step_id}'"
                        )
            
            # Validate conditional branch references
            elif step_type == "conditional":
                if_true = step.get("if_true_step")
                if_false = step.get("if_false_step")
                
                if if_true and if_true not in all_step_ids:
                    errors.append(
                        f"Conditional step '{step_id}' references non-existent true branch '{if_true}'"
                    )
                
                if if_false and if_false not in all_step_ids:
                    errors.append(
                        f"Conditional step '{step_id}' references non-existent false branch '{if_false}'"
                    )
            
            # Validate parallel step references
            elif step_type == "parallel":
                parallel_steps = step.get("parallel_steps", [])
                
                for parallel_step_id in parallel_steps:
                    if parallel_step_id not in all_step_ids:
                        errors.append(
                            f"Parallel step '{step_id}' references non-existent parallel step '{parallel_step_id}'"
                        )
            
            # Validate fork-join branch references
            elif step_type == "fork_join":
                fork_join_config = step.get("fork_join_config", {})
                branches = fork_join_config.get("branches", {})
                
                for branch_name, branch_config in branches.items():
                    branch_steps = branch_config.get("steps", [])
                    
                    for branch_step_id in branch_steps:
                        if branch_step_id not in all_step_ids:
                            errors.append(
                                f"Fork-join step '{step_id}' branch '{branch_name}' references non-existent step '{branch_step_id}'"
                            )
            
            # Validate next_step reference
            next_step = step.get("next_step")
            if next_step and next_step not in all_step_ids:
                errors.append(
                    f"Step '{step_id}' references non-existent next_step '{next_step}'"
                )
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def detect_pattern_type(description: str) -> List[str]:
        """
        Detect which workflow patterns are mentioned in a description.
        
        Args:
            description: Natural language description
            
        Returns:
            List of detected pattern types
        """
        description_lower = description.lower()
        patterns = []
        
        # Loop patterns
        loop_keywords = [
            "loop", "iterate", "for each", "foreach", "repeat",
            "process each", "process all", "batch", "multiple items"
        ]
        if any(keyword in description_lower for keyword in loop_keywords):
            patterns.append("loop")
        
        # Conditional patterns
        conditional_keywords = [
            "if", "when", "condition", "depending on", "based on",
            "check if", "validate", "decide", "choose", "branch"
        ]
        if any(keyword in description_lower for keyword in conditional_keywords):
            patterns.append("conditional")
        
        # Parallel patterns
        parallel_keywords = [
            "parallel", "concurrent", "simultaneously", "at the same time",
            "in parallel", "concurrently"
        ]
        if any(keyword in description_lower for keyword in parallel_keywords):
            patterns.append("parallel")
        
        # Fork-join patterns
        fork_join_keywords = [
            "fork", "split", "branch out", "multiple paths",
            "join", "merge", "combine results", "aggregate"
        ]
        # Need both fork and join concepts
        has_fork = any(kw in description_lower for kw in ["fork", "split", "branch out", "multiple paths"])
        has_join = any(kw in description_lower for kw in ["join", "merge", "combine", "aggregate"])
        if has_fork and has_join:
            patterns.append("fork_join")
        
        logger.debug(f"Detected patterns in description: {patterns}")
        return patterns


class PatternPromptBuilder:
    """Builds enhanced prompts for pattern generation."""
    
    @staticmethod
    def build_pattern_examples() -> str:
        """
        Build example patterns for the LLM prompt.
        
        Returns:
            Formatted string with pattern examples
        """
        return """
WORKFLOW PATTERN EXAMPLES:

1. LOOP Pattern:
   Use when processing multiple items from a collection.
   {
     "step-id": {
       "type": "loop",
       "loop_config": {
         "collection": "${previous-step.output.items}",
         "loop_body": ["process-item-step"],
         "execution_mode": "sequential",
         "max_iterations": 100,
         "on_error": "continue"
       },
       "next_step": "after-loop-step"
     }
   }

2. CONDITIONAL Pattern:
   Use when execution path depends on a condition.
   {
     "step-id": {
       "type": "conditional",
       "condition": {
         "expression": "${previous-step.output.value} > 10"
       },
       "if_true_step": "high-value-step",
       "if_false_step": "low-value-step",
       "next_step": "merge-step"
     }
   }

3. PARALLEL Pattern:
   Use when multiple steps can run concurrently.
   {
     "step-id": {
       "type": "parallel",
       "parallel_steps": ["step-a", "step-b", "step-c"],
       "max_parallelism": 3,
       "next_step": "combine-results-step"
     }
   }

4. FORK-JOIN Pattern:
   Use when splitting into multiple branches that later merge.
   {
     "step-id": {
       "type": "fork_join",
       "fork_join_config": {
         "branches": {
           "branch_a": {
             "steps": ["branch-a-step-1", "branch-a-step-2"],
             "timeout_seconds": 30
           },
           "branch_b": {
             "steps": ["branch-b-step"],
             "timeout_seconds": 30
           }
         },
         "join_policy": "all",
         "branch_timeout_seconds": 60
       },
       "next_step": "after-join-step"
     }
   }

NESTED PATTERNS:
You can nest patterns within each other. For example:
- A loop body can contain conditional steps
- Parallel steps can contain loops
- Fork-join branches can contain any pattern

IMPORTANT: Ensure all referenced step IDs exist in the steps object.
"""
    
    @staticmethod
    def build_enhanced_prompt(
        description: str,
        available_agents: List[Any],
        detected_patterns: List[str]
    ) -> str:
        """
        Build an enhanced prompt that includes pattern guidance.
        
        Args:
            description: User's workflow description
            available_agents: List of available agents
            detected_patterns: List of detected pattern types
            
        Returns:
            Enhanced prompt string
        """
        from .agent_query import AgentMetadata
        
        # Format agents
        agents_text = PatternPromptBuilder._format_agents(available_agents)
        
        # Build pattern-specific guidance
        pattern_guidance = ""
        if detected_patterns:
            pattern_guidance = f"\nDETECTED PATTERNS: {', '.join(detected_patterns)}\n"
            pattern_guidance += "Please use the appropriate pattern structures shown in the examples below.\n"
        
        prompt = f"""You are an AI assistant that generates workflow JSON definitions based on user requirements.

Available Agents:
{agents_text}

{pattern_guidance}
{PatternPromptBuilder.build_pattern_examples()}

User Request:
{description}

Generate a valid workflow JSON that:
1. Uses only the agents listed above
2. Uses appropriate workflow patterns (loop, conditional, parallel, fork-join) based on the requirements
3. Ensures all step references are valid
4. Follows this EXACT schema structure:
   - name: string (workflow name)
   - description: string (workflow description)
   - version: string (version number, default "1.0")
   - start_step: string (name of first step)
   - steps: object (map of step IDs to step definitions)

CRITICAL: Each step MUST include these fields:
- id: string (REQUIRED - unique step identifier, must match the key in steps object)
- type: string (REQUIRED - one of: "agent", "loop", "conditional", "parallel")
- next_step: string or null (REQUIRED - ID of next step, or null if final step)

For type="agent" steps (REQUIRED fields):
- agent_name: string (REQUIRED - use "agent_name" NOT "agent_id")
- input_mapping: object (REQUIRED - map of input fields to values)

For type="loop" steps (REQUIRED fields):
- loop_config: object with:
  - collection: string (reference to array)
  - loop_body: array of step IDs
  - execution_mode: "sequential" or "parallel" (optional, default "sequential")
  - on_error: "stop", "continue", or "collect" (optional, default "stop")

For type="conditional" steps (REQUIRED fields):
- condition: object with expression field
- if_true_step: string (step ID if condition is true)
- if_false_step: string (step ID if condition is false)

For type="parallel" steps (REQUIRED fields):
- parallel_steps: array of step IDs to execute in parallel

IMPORTANT: Use "agent_name" field, NOT "agent_id". Each step must have an "id" field that matches its key in the steps object.

Respond with a JSON object containing:
- workflow: the complete workflow JSON following the exact schema above
- explanation: brief explanation of the workflow design and patterns used

Format your response as valid JSON."""
        
        return prompt
    
    @staticmethod
    def _format_agents(agents: List[Any]) -> str:
        """Format agents for prompt."""
        if not agents:
            return "No agents available"
        
        lines = []
        for agent in agents:
            desc = agent.description or "No description"
            caps = ", ".join(agent.capabilities) if hasattr(agent, 'capabilities') and agent.capabilities else "None specified"
            lines.append(f"- {agent.name}: {desc} (Capabilities: {caps})")
        
        return "\n".join(lines)

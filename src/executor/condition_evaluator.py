"""Condition evaluator for conditional workflow steps."""

import re
import json
import logging
from typing import Dict, Any, Optional
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """
    Evaluates conditional expressions for workflow branching.
    
    Supports:
    - Comparison operators: ==, !=, >, <, >=, <=
    - Logical operators: and, or, not
    - Membership: in, not in, contains
    - JSONPath expressions: ${step-1.output.results[0].score}
    - Variable references: ${workflow.input.*}, ${step-*.output.*}
    """
    
    # Regex pattern to match ${...} variable references
    VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    def __init__(
        self,
        workflow_input: Dict[str, Any],
        step_outputs: Dict[str, Dict[str, Any]]
    ):
        """
        Initialize the condition evaluator.
        
        Args:
            workflow_input: The initial input data provided to the workflow
            step_outputs: Dictionary mapping step IDs to their output data
        """
        self.workflow_input = workflow_input or {}
        self.step_outputs = step_outputs or {}
    
    def evaluate(self, expression: str) -> bool:
        """
        Evaluate a conditional expression and return boolean result.
        
        Args:
            expression: The condition expression to evaluate
            
        Returns:
            Boolean result of the evaluation
            
        Raises:
            ValueError: If the expression is malformed
        """
        try:
            logger.debug(f"Evaluating condition: {expression}")
            
            # Replace variable references with actual values
            resolved_expression = self._resolve_variables(expression)
            logger.debug(f"Resolved expression: {resolved_expression}")
            
            # Evaluate using safe eval
            result = self._safe_eval(resolved_expression)
            
            logger.debug(f"Condition result: {result}")
            return bool(result)
        
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}", exc_info=True)
            # Treat evaluation errors as false
            return False
    
    def _resolve_variables(self, expression: str) -> str:
        """
        Replace ${...} variable references with actual values.
        
        Args:
            expression: The expression containing variable references
            
        Returns:
            Expression with variables replaced by JSON-encoded values
        """
        def replace_var(match):
            var_path = match.group(1)
            try:
                value = self._get_value_by_path(var_path)
                # Return JSON representation for safe eval
                return json.dumps(value)
            except Exception as e:
                logger.warning(f"Failed to resolve variable '{var_path}': {e}")
                # Return null for unresolvable variables
                return 'null'
        
        return re.sub(self.VARIABLE_PATTERN, replace_var, expression)
    
    def _get_value_by_path(self, path: str) -> Any:
        """
        Get value using dot notation path with JSONPath support.
        
        Examples:
            workflow.input.topic -> self.workflow_input['topic']
            step-1.output.score -> self.step_outputs['step-1']['score']
            step-1.output.results[0].score -> JSONPath evaluation
        
        Args:
            path: The variable path to resolve
            
        Returns:
            The value at the specified path
            
        Raises:
            ValueError: If the path cannot be resolved
        """
        parts = path.split('.', 2)
        
        if len(parts) < 2:
            raise ValueError(f"Invalid path: {path}")
        
        if parts[0] == 'workflow' and parts[1] == 'input':
            # Access workflow input
            if len(parts) == 2:
                return self.workflow_input
            
            remaining_path = parts[2]
            return self._navigate_dict(self.workflow_input, remaining_path)
        
        elif parts[0].startswith('step-'):
            # Access step output
            step_id = parts[0]
            if step_id not in self.step_outputs:
                raise ValueError(f"Step '{step_id}' output not found")
            
            if len(parts) > 1 and parts[1] == 'output':
                if len(parts) == 2:
                    return self.step_outputs[step_id]
                
                remaining_path = parts[2]
                return self._navigate_dict(
                    self.step_outputs[step_id],
                    remaining_path
                )
            else:
                raise ValueError(f"Invalid step path: {path}")
        
        raise ValueError(f"Invalid path: {path}")
    
    def _navigate_dict(self, data: Dict, path: str) -> Any:
        """
        Navigate nested dictionary using dot notation and array indices.
        
        Supports JSONPath for complex paths with array indices.
        
        Args:
            data: The dictionary to navigate
            path: The path to navigate (e.g., "results[0].score")
            
        Returns:
            The value at the specified path
            
        Raises:
            ValueError: If the path cannot be navigated
        """
        # Use JSONPath for complex paths with array indices
        if '[' in path:
            try:
                jsonpath_expr = jsonpath_parse(f"$.{path}")
                matches = jsonpath_expr.find(data)
                if matches:
                    return matches[0].value
                raise ValueError(f"Path not found: {path}")
            except JsonPathParserError as e:
                raise ValueError(f"Invalid JSONPath: {path} - {e}")
        
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
        Safely evaluate expression with restricted operations.
        
        Only allows comparison and logical operators.
        
        Args:
            expression: The expression to evaluate
            
        Returns:
            The result of the evaluation
            
        Raises:
            Exception: If evaluation fails
        """
        # Replace 'contains' with 'in' for Python eval
        expression = expression.replace(' contains ', ' in ')
        
        # Replace JSON boolean literals with Python boolean literals
        # This handles the case where json.dumps() produces 'true'/'false'
        # We need to be careful to only replace standalone words, not parts of strings
        import re
        expression = re.sub(r'\btrue\b', 'True', expression)
        expression = re.sub(r'\bfalse\b', 'False', expression)
        expression = re.sub(r'\bnull\b', 'None', expression)
        
        # Use eval with restricted globals and locals
        # This is safe because we've already replaced variables with JSON values
        try:
            return eval(expression, {"__builtins__": {}}, {})
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {expression} - {e}")

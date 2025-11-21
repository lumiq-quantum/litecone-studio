"""Input mapping resolver for workflow variable substitution."""

import re
from typing import Dict, Any, Optional


class InputMappingResolver:
    """Resolves variable references in input mappings to actual values."""
    
    # Regex pattern to match ${workflow.input.field} or ${step-id.output.field}
    VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    def __init__(
        self,
        workflow_input: Dict[str, Any],
        step_outputs: Optional[Dict[str, Dict[str, Any]]] = None,
        loop_context: Optional[Any] = None
    ):
        """
        Initialize the input mapping resolver.
        
        Args:
            workflow_input: The initial input data provided to the workflow
            step_outputs: Dictionary mapping step IDs to their output data
            loop_context: Optional IterationContext for loop variable resolution
        """
        self.workflow_input = workflow_input or {}
        self.step_outputs = step_outputs or {}
        self.loop_context = loop_context
    
    def resolve(self, input_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Resolve all variable references in the input mapping.
        
        Args:
            input_mapping: Dictionary mapping field names to variable references
            
        Returns:
            Dictionary with resolved values
            
        Raises:
            ValueError: If a variable reference cannot be resolved
        """
        resolved = {}
        
        for field_name, value_expression in input_mapping.items():
            resolved[field_name] = self._resolve_expression(value_expression, field_name)
        
        return resolved
    
    def _resolve_expression(self, expression: str, field_name: str) -> Any:
        """
        Resolve a single expression that may contain variable references.
        
        Args:
            expression: The expression to resolve (e.g., "${workflow.input.topic}")
            field_name: The name of the field being resolved (for error messages)
            
        Returns:
            The resolved value
            
        Raises:
            ValueError: If the expression cannot be resolved
        """
        # Find all variable references in the expression
        matches = list(self.VARIABLE_PATTERN.finditer(expression))
        
        if not matches:
            # No variables to substitute, return as-is
            return expression
        
        # If the entire expression is a single variable reference, return the actual value
        if len(matches) == 1 and matches[0].group(0) == expression:
            variable_path = matches[0].group(1)
            return self._resolve_variable(variable_path, field_name)
        
        # Multiple variables or mixed content - perform string substitution
        result = expression
        for match in reversed(matches):  # Process in reverse to maintain positions
            variable_path = match.group(1)
            value = self._resolve_variable(variable_path, field_name)
            
            # Convert value to string for substitution
            if not isinstance(value, str):
                raise ValueError(
                    f"Cannot substitute non-string value for '{variable_path}' in field '{field_name}'. "
                    f"Use a single variable reference to pass complex types."
                )
            
            result = result[:match.start()] + value + result[match.end():]
        
        return result
    
    def _resolve_variable(self, variable_path: str, field_name: str) -> Any:
        """
        Resolve a single variable path to its value.
        
        Args:
            variable_path: The variable path (e.g., "workflow.input.topic" or "step-1.output.result")
            field_name: The name of the field being resolved (for error messages)
            
        Returns:
            The resolved value
            
        Raises:
            ValueError: If the variable cannot be resolved
        """
        parts = variable_path.split('.')
        
        # Handle loop context variables
        if parts[0] == "loop":
            if not self.loop_context:
                raise ValueError(
                    f"Cannot resolve '${{{variable_path}}}' in field '{field_name}': "
                    f"Not in a loop context"
                )
            
            if len(parts) < 2:
                raise ValueError(
                    f"Invalid loop variable reference '${{{variable_path}}}' in field '{field_name}'. "
                    f"Expected format: ${{loop.item}} or ${{loop.index}}"
                )
            
            loop_field = parts[1]
            if loop_field == "item":
                return self.loop_context.item
            elif loop_field == "index":
                return self.loop_context.index
            elif loop_field == "total":
                return self.loop_context.total
            elif loop_field == "is_first":
                return self.loop_context.is_first
            elif loop_field == "is_last":
                return self.loop_context.is_last
            else:
                raise ValueError(
                    f"Invalid loop field '${{{variable_path}}}' in field '{field_name}'. "
                    f"Valid fields: item, index, total, is_first, is_last"
                )
        
        if len(parts) < 3:
            raise ValueError(
                f"Invalid variable reference '${{{variable_path}}}' in field '{field_name}'. "
                f"Expected format: ${{workflow.input.field}} or ${{step-id.output.field}}"
            )
        
        source_type = parts[0]
        data_type = parts[1]
        field_path = parts[2:]
        
        # Resolve based on source type
        if source_type == "workflow":
            if data_type != "input":
                raise ValueError(
                    f"Invalid variable reference '${{{variable_path}}}' in field '{field_name}'. "
                    f"Workflow variables must use 'input' (e.g., ${{workflow.input.field}})"
                )
            return self._get_nested_value(self.workflow_input, field_path, variable_path, field_name)
        
        else:
            # Assume it's a step ID (e.g., "step-1.output.result")
            step_id = source_type
            
            if data_type != "output":
                raise ValueError(
                    f"Invalid variable reference '${{{variable_path}}}' in field '{field_name}'. "
                    f"Step variables must use 'output' (e.g., ${{step-id.output.field}})"
                )
            
            if step_id not in self.step_outputs:
                raise ValueError(
                    f"Cannot resolve '${{{variable_path}}}' in field '{field_name}': "
                    f"Step '{step_id}' has not been executed or has no output"
                )
            
            return self._get_nested_value(self.step_outputs[step_id], field_path, variable_path, field_name)
    
    def _get_nested_value(
        self,
        data: Dict[str, Any],
        field_path: list[str],
        variable_path: str,
        field_name: str
    ) -> Any:
        """
        Get a nested value from a dictionary using a field path.
        
        Args:
            data: The dictionary to traverse
            field_path: List of keys to traverse (e.g., ["result", "data"])
            variable_path: The original variable path (for error messages)
            field_name: The name of the field being resolved (for error messages)
            
        Returns:
            The value at the nested path
            
        Raises:
            ValueError: If the path cannot be traversed
        """
        current = data
        
        for i, key in enumerate(field_path):
            if not isinstance(current, dict):
                traversed_path = '.'.join(field_path[:i])
                raise ValueError(
                    f"Cannot resolve '${{{variable_path}}}' in field '{field_name}': "
                    f"'{traversed_path}' is not a dictionary"
                )
            
            if key not in current:
                traversed_path = '.'.join(field_path[:i+1])
                raise ValueError(
                    f"Cannot resolve '${{{variable_path}}}' in field '{field_name}': "
                    f"Field '{traversed_path}' not found"
                )
            
            current = current[key]
        
        return current

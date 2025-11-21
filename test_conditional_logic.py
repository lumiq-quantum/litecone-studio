"""
Simple test script for conditional logic implementation.

This script tests the ConditionEvaluator with various expressions.
"""

import sys
import json
from src.executor.condition_evaluator import ConditionEvaluator


def test_condition_evaluator():
    """Test the ConditionEvaluator with various expressions."""
    
    print("Testing ConditionEvaluator...")
    print("=" * 60)
    
    # Test data
    workflow_input = {
        "threshold": 0.8,
        "status": "approved",
        "count": 15,
        "tags": ["important", "urgent"]
    }
    
    step_outputs = {
        "step-1": {
            "score": 0.9,
            "valid": True,
            "message": "Processing complete",
            "results": [
                {"name": "item1", "value": 100},
                {"name": "item2", "value": 200}
            ]
        },
        "step-2": {
            "status": "success",
            "count": 10
        }
    }
    
    # Create evaluator
    evaluator = ConditionEvaluator(workflow_input, step_outputs)
    
    # Test cases
    test_cases = [
        # Simple comparisons
        ("${step-1.output.score} > 0.8", True, "Simple comparison (>)"),
        ("${step-1.output.score} == 0.9", True, "Equality comparison"),
        ("${step-2.output.count} < 20", True, "Less than comparison"),
        
        # Logical operators
        ("${step-1.output.valid} and ${step-2.output.status} == 'success'", True, "Logical AND"),
        ("${step-1.output.score} > 1.0 or ${step-1.output.valid}", True, "Logical OR"),
        
        # Membership tests
        ("'complete' in ${step-1.output.message}", True, "String contains"),
        ("'important' in ${workflow.input.tags}", True, "Array membership"),
        
        # JSONPath expressions
        ("${step-1.output.results[0].value} == 100", True, "JSONPath array access"),
        ("${step-1.output.results[1].name} == 'item2'", True, "JSONPath nested access"),
        
        # Workflow input references
        ("${workflow.input.threshold} == 0.8", True, "Workflow input access"),
        ("${workflow.input.status} == 'approved'", True, "Workflow input string"),
        
        # False conditions
        ("${step-1.output.score} < 0.5", False, "False comparison"),
        ("${step-2.output.status} == 'failed'", False, "False equality"),
    ]
    
    passed = 0
    failed = 0
    
    for expression, expected, description in test_cases:
        try:
            result = evaluator.evaluate(expression)
            status = "✓ PASS" if result == expected else "✗ FAIL"
            if result == expected:
                passed += 1
            else:
                failed += 1
            
            print(f"{status} | {description}")
            print(f"       Expression: {expression}")
            print(f"       Expected: {expected}, Got: {result}")
            print()
        
        except Exception as e:
            failed += 1
            print(f"✗ ERROR | {description}")
            print(f"        Expression: {expression}")
            print(f"        Error: {e}")
            print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = test_condition_evaluator()
    sys.exit(0 if success else 1)

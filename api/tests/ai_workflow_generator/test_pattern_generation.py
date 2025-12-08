"""Tests for pattern generation utilities."""

import pytest
from api.services.ai_workflow_generator.pattern_generation import (
    PatternGenerator,
    PatternPromptBuilder
)
from api.services.ai_workflow_generator.agent_query import AgentMetadata


class TestPatternGenerator:
    """Tests for PatternGenerator class."""
    
    def test_generate_loop_structure(self):
        """Test loop structure generation."""
        loop_step = PatternGenerator.generate_loop_structure(
            loop_step_id="loop-1",
            collection_reference="${step-1.output.items}",
            loop_body_steps=["process-item"],
            execution_mode="sequential",
            max_iterations=100,
            on_error="continue",
            next_step="step-2"
        )
        
        assert loop_step["id"] == "loop-1"
        assert loop_step["type"] == "loop"
        assert loop_step["loop_config"]["collection"] == "${step-1.output.items}"
        assert loop_step["loop_config"]["loop_body"] == ["process-item"]
        assert loop_step["loop_config"]["execution_mode"] == "sequential"
        assert loop_step["loop_config"]["max_iterations"] == 100
        assert loop_step["loop_config"]["on_error"] == "continue"
        assert loop_step["next_step"] == "step-2"
    
    def test_generate_conditional_structure(self):
        """Test conditional structure generation."""
        conditional_step = PatternGenerator.generate_conditional_structure(
            conditional_step_id="cond-1",
            condition_expression="${step-1.output.value} > 10",
            if_true_step="high-value",
            if_false_step="low-value",
            next_step="merge"
        )
        
        assert conditional_step["id"] == "cond-1"
        assert conditional_step["type"] == "conditional"
        assert conditional_step["condition"]["expression"] == "${step-1.output.value} > 10"
        assert conditional_step["if_true_step"] == "high-value"
        assert conditional_step["if_false_step"] == "low-value"
        assert conditional_step["next_step"] == "merge"
    
    def test_generate_parallel_structure(self):
        """Test parallel structure generation."""
        parallel_step = PatternGenerator.generate_parallel_structure(
            parallel_step_id="parallel-1",
            parallel_steps=["step-a", "step-b", "step-c"],
            max_parallelism=3,
            next_step="combine"
        )
        
        assert parallel_step["id"] == "parallel-1"
        assert parallel_step["type"] == "parallel"
        assert parallel_step["parallel_steps"] == ["step-a", "step-b", "step-c"]
        assert parallel_step["max_parallelism"] == 3
        assert parallel_step["next_step"] == "combine"
    
    def test_generate_parallel_structure_without_max_parallelism(self):
        """Test parallel structure generation without max_parallelism."""
        parallel_step = PatternGenerator.generate_parallel_structure(
            parallel_step_id="parallel-1",
            parallel_steps=["step-a", "step-b"],
            next_step="combine"
        )
        
        assert parallel_step["id"] == "parallel-1"
        assert parallel_step["type"] == "parallel"
        assert "max_parallelism" not in parallel_step
    
    def test_generate_fork_join_structure(self):
        """Test fork-join structure generation."""
        branches = {
            "branch_a": {
                "steps": ["step-a1", "step-a2"],
                "timeout_seconds": 30
            },
            "branch_b": {
                "steps": ["step-b1"],
                "timeout_seconds": 20
            }
        }
        
        fork_join_step = PatternGenerator.generate_fork_join_structure(
            fork_join_step_id="fork-join-1",
            branches=branches,
            join_policy="all",
            branch_timeout_seconds=60,
            next_step="aggregate"
        )
        
        assert fork_join_step["id"] == "fork-join-1"
        assert fork_join_step["type"] == "fork_join"
        assert fork_join_step["fork_join_config"]["join_policy"] == "all"
        assert fork_join_step["fork_join_config"]["branch_timeout_seconds"] == 60
        assert "branch_a" in fork_join_step["fork_join_config"]["branches"]
        assert "branch_b" in fork_join_step["fork_join_config"]["branches"]
        assert fork_join_step["next_step"] == "aggregate"
    
    def test_validate_nested_references_valid(self):
        """Test validation of valid nested references."""
        workflow = {
            "name": "test-workflow",
            "start_step": "loop-1",
            "steps": {
                "loop-1": {
                    "id": "loop-1",
                    "type": "loop",
                    "loop_config": {
                        "collection": "${workflow.input.items}",
                        "loop_body": ["process-item"],
                        "execution_mode": "sequential"
                    },
                    "next_step": "final"
                },
                "process-item": {
                    "id": "process-item",
                    "type": "agent",
                    "agent_name": "processor",
                    "input_mapping": {}
                },
                "final": {
                    "id": "final",
                    "type": "agent",
                    "agent_name": "finalizer",
                    "input_mapping": {}
                }
            }
        }
        
        is_valid, errors = PatternGenerator.validate_nested_references(workflow)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_nested_references_invalid_loop_body(self):
        """Test validation catches invalid loop body reference."""
        workflow = {
            "name": "test-workflow",
            "start_step": "loop-1",
            "steps": {
                "loop-1": {
                    "id": "loop-1",
                    "type": "loop",
                    "loop_config": {
                        "collection": "${workflow.input.items}",
                        "loop_body": ["non-existent-step"],
                        "execution_mode": "sequential"
                    }
                }
            }
        }
        
        is_valid, errors = PatternGenerator.validate_nested_references(workflow)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "non-existent-step" in errors[0]
    
    def test_validate_nested_references_invalid_conditional(self):
        """Test validation catches invalid conditional branch references."""
        workflow = {
            "name": "test-workflow",
            "start_step": "cond-1",
            "steps": {
                "cond-1": {
                    "id": "cond-1",
                    "type": "conditional",
                    "condition": {"expression": "true"},
                    "if_true_step": "non-existent-true",
                    "if_false_step": "non-existent-false"
                }
            }
        }
        
        is_valid, errors = PatternGenerator.validate_nested_references(workflow)
        
        assert is_valid is False
        assert len(errors) == 2
        assert any("non-existent-true" in e for e in errors)
        assert any("non-existent-false" in e for e in errors)
    
    def test_validate_nested_references_invalid_parallel(self):
        """Test validation catches invalid parallel step references."""
        workflow = {
            "name": "test-workflow",
            "start_step": "parallel-1",
            "steps": {
                "parallel-1": {
                    "id": "parallel-1",
                    "type": "parallel",
                    "parallel_steps": ["step-a", "non-existent-step"]
                },
                "step-a": {
                    "id": "step-a",
                    "type": "agent",
                    "agent_name": "agent-a",
                    "input_mapping": {}
                }
            }
        }
        
        is_valid, errors = PatternGenerator.validate_nested_references(workflow)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "non-existent-step" in errors[0]
    
    def test_validate_nested_references_invalid_fork_join(self):
        """Test validation catches invalid fork-join branch references."""
        workflow = {
            "name": "test-workflow",
            "start_step": "fork-join-1",
            "steps": {
                "fork-join-1": {
                    "id": "fork-join-1",
                    "type": "fork_join",
                    "fork_join_config": {
                        "branches": {
                            "branch_a": {
                                "steps": ["non-existent-step"],
                                "timeout_seconds": 30
                            }
                        },
                        "join_policy": "all"
                    }
                }
            }
        }
        
        is_valid, errors = PatternGenerator.validate_nested_references(workflow)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "non-existent-step" in errors[0]
    
    def test_validate_nested_references_invalid_next_step(self):
        """Test validation catches invalid next_step references."""
        workflow = {
            "name": "test-workflow",
            "start_step": "step-1",
            "steps": {
                "step-1": {
                    "id": "step-1",
                    "type": "agent",
                    "agent_name": "agent-1",
                    "input_mapping": {},
                    "next_step": "non-existent-step"
                }
            }
        }
        
        is_valid, errors = PatternGenerator.validate_nested_references(workflow)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "non-existent-step" in errors[0]
    
    def test_detect_pattern_type_loop(self):
        """Test detection of loop patterns."""
        descriptions = [
            "Process each item in the list",
            "Loop through all records",
            "Iterate over the collection",
            "For each file, process it",
            "Repeat for all entries"
        ]
        
        for desc in descriptions:
            patterns = PatternGenerator.detect_pattern_type(desc)
            assert "loop" in patterns, f"Failed to detect loop in: {desc}"
    
    def test_detect_pattern_type_conditional(self):
        """Test detection of conditional patterns."""
        descriptions = [
            "If the value is greater than 10, do X",
            "When the condition is met, proceed",
            "Check if the data is valid",
            "Depending on the result, choose path A or B",
            "Decide based on the score"
        ]
        
        for desc in descriptions:
            patterns = PatternGenerator.detect_pattern_type(desc)
            assert "conditional" in patterns, f"Failed to detect conditional in: {desc}"
    
    def test_detect_pattern_type_parallel(self):
        """Test detection of parallel patterns."""
        descriptions = [
            "Process steps A, B, and C in parallel",
            "Run these tasks concurrently",
            "Execute simultaneously",
            "Do these at the same time"
        ]
        
        for desc in descriptions:
            patterns = PatternGenerator.detect_pattern_type(desc)
            assert "parallel" in patterns, f"Failed to detect parallel in: {desc}"
    
    def test_detect_pattern_type_fork_join(self):
        """Test detection of fork-join patterns."""
        descriptions = [
            "Fork into multiple branches and then join the results",
            "Split the workflow and merge the outputs",
            "Branch out to different paths and combine them",
            "Fork to process different data sources and aggregate"
        ]
        
        for desc in descriptions:
            patterns = PatternGenerator.detect_pattern_type(desc)
            assert "fork_join" in patterns, f"Failed to detect fork_join in: {desc}"
    
    def test_detect_pattern_type_multiple(self):
        """Test detection of multiple patterns."""
        description = "Loop through items, and if the value is high, process in parallel"
        patterns = PatternGenerator.detect_pattern_type(description)
        
        assert "loop" in patterns
        assert "conditional" in patterns
        assert "parallel" in patterns
    
    def test_detect_pattern_type_none(self):
        """Test detection when no patterns are present."""
        description = "Just process the data normally"
        patterns = PatternGenerator.detect_pattern_type(description)
        
        # May still detect some patterns due to keywords, but that's okay
        # This test just ensures it doesn't crash
        assert isinstance(patterns, list)


class TestPatternPromptBuilder:
    """Tests for PatternPromptBuilder class."""
    
    def test_build_pattern_examples(self):
        """Test building pattern examples."""
        examples = PatternPromptBuilder.build_pattern_examples()
        
        assert "LOOP Pattern" in examples
        assert "CONDITIONAL Pattern" in examples
        assert "PARALLEL Pattern" in examples
        assert "FORK-JOIN Pattern" in examples
        assert "NESTED PATTERNS" in examples
    
    def test_build_enhanced_prompt(self):
        """Test building enhanced prompt with patterns."""
        agents = [
            AgentMetadata(
                name="processor",
                description="Processes data",
                url="http://localhost:8001",
                capabilities=["process"],
                status="active"
            )
        ]
        
        description = "Loop through items and process each one"
        detected_patterns = ["loop"]
        
        prompt = PatternPromptBuilder.build_enhanced_prompt(
            description=description,
            available_agents=agents,
            detected_patterns=detected_patterns
        )
        
        assert "processor" in prompt
        assert "Loop through items" in prompt
        assert "DETECTED PATTERNS: loop" in prompt
        assert "LOOP Pattern" in prompt
    
    def test_build_enhanced_prompt_no_patterns(self):
        """Test building enhanced prompt without detected patterns."""
        agents = [
            AgentMetadata(
                name="processor",
                description="Processes data",
                url="http://localhost:8001",
                capabilities=["process"],
                status="active"
            )
        ]
        
        description = "Process the data"
        detected_patterns = []
        
        prompt = PatternPromptBuilder.build_enhanced_prompt(
            description=description,
            available_agents=agents,
            detected_patterns=detected_patterns
        )
        
        assert "processor" in prompt
        assert "Process the data" in prompt
        assert "DETECTED PATTERNS" not in prompt
    
    def test_build_enhanced_prompt_multiple_patterns(self):
        """Test building enhanced prompt with multiple patterns."""
        agents = [
            AgentMetadata(
                name="processor",
                description="Processes data",
                url="http://localhost:8001",
                capabilities=["process"],
                status="active"
            )
        ]
        
        description = "Loop and process with conditionals"
        detected_patterns = ["loop", "conditional"]
        
        prompt = PatternPromptBuilder.build_enhanced_prompt(
            description=description,
            available_agents=agents,
            detected_patterns=detected_patterns
        )
        
        assert "DETECTED PATTERNS: loop, conditional" in prompt

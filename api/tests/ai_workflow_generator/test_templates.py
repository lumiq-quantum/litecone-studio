"""Tests for workflow generation templates.

This test file validates:
- Example workflow descriptions are well-formed
- Prompt templates can be formatted correctly
- Agent formatting templates produce valid output
- Error message templates include helpful suggestions
- Explanation templates provide clear information
"""

import pytest
from api.services.ai_workflow_generator.templates import (
    EXAMPLE_WORKFLOW_DESCRIPTIONS,
    WORKFLOW_PATTERN_EXAMPLES,
    PromptTemplates,
    AgentFormattingTemplates,
    ErrorMessageTemplates,
    ExplanationTemplates,
    get_example_description,
    get_pattern_example,
    format_error_message,
    build_prompt
)


class TestExampleWorkflowDescriptions:
    """Test example workflow descriptions."""
    
    def test_all_examples_exist(self):
        """Test that all expected example types exist."""
        expected_types = [
            "simple_sequential",
            "with_conditional",
            "with_loop",
            "with_parallel",
            "with_fork_join",
            "complex_nested",
            "data_pipeline",
            "document_processing"
        ]
        
        for example_type in expected_types:
            assert example_type in EXAMPLE_WORKFLOW_DESCRIPTIONS
            assert len(EXAMPLE_WORKFLOW_DESCRIPTIONS[example_type].strip()) > 0
    
    def test_examples_are_descriptive(self):
        """Test that examples contain meaningful descriptions."""
        for name, description in EXAMPLE_WORKFLOW_DESCRIPTIONS.items():
            # Should have multiple lines
            lines = [line.strip() for line in description.strip().split('\n') if line.strip()]
            assert len(lines) >= 2, f"Example '{name}' should have at least 2 lines"
            
            # Should contain action words
            desc_lower = description.lower()
            action_words = ['create', 'process', 'send', 'analyze', 'validate', 'generate']
            assert any(word in desc_lower for word in action_words), \
                f"Example '{name}' should contain action words"
    
    def test_get_example_description(self):
        """Test getting example descriptions."""
        # Valid example
        desc = get_example_description("simple_sequential")
        assert len(desc) > 0
        assert "workflow" in desc.lower()
        
        # Invalid example returns default
        desc = get_example_description("nonexistent")
        assert len(desc) > 0


class TestWorkflowPatternExamples:
    """Test workflow pattern examples."""
    
    def test_all_pattern_examples_exist(self):
        """Test that pattern examples exist."""
        expected_patterns = [
            "simple_sequential",
            "with_conditional",
            "with_loop",
            "with_parallel"
        ]
        
        for pattern in expected_patterns:
            assert pattern in WORKFLOW_PATTERN_EXAMPLES
    
    def test_pattern_examples_are_valid_workflows(self):
        """Test that pattern examples have valid workflow structure."""
        for name, workflow in WORKFLOW_PATTERN_EXAMPLES.items():
            # Must have required fields
            assert "name" in workflow, f"Pattern '{name}' missing 'name'"
            assert "description" in workflow, f"Pattern '{name}' missing 'description'"
            assert "start_step" in workflow, f"Pattern '{name}' missing 'start_step'"
            assert "steps" in workflow, f"Pattern '{name}' missing 'steps'"
            
            # Steps must be a dict
            assert isinstance(workflow["steps"], dict), f"Pattern '{name}' steps must be dict"
            
            # Start step must exist in steps
            assert workflow["start_step"] in workflow["steps"], \
                f"Pattern '{name}' start_step not in steps"
            
            # Each step must have a type
            for step_id, step in workflow["steps"].items():
                assert "type" in step, f"Pattern '{name}' step '{step_id}' missing type"
    
    def test_get_pattern_example(self):
        """Test getting pattern examples."""
        # Valid pattern
        pattern = get_pattern_example("simple_sequential")
        assert "steps" in pattern
        assert "start_step" in pattern
        
        # Invalid pattern returns default
        pattern = get_pattern_example("nonexistent")
        assert "steps" in pattern


class TestPromptTemplates:
    """Test prompt templates."""
    
    def test_base_workflow_generation_template(self):
        """Test base workflow generation template."""
        prompt = PromptTemplates.BASE_WORKFLOW_GENERATION.format(
            description="Test workflow",
            agents="agent-1, agent-2"
        )
        
        assert "Test workflow" in prompt
        assert "agent-1" in prompt
        assert "workflow" in prompt.lower()
        assert "JSON" in prompt
    
    def test_conditional_pattern_template(self):
        """Test conditional pattern template."""
        template = PromptTemplates.CONDITIONAL_PATTERN
        
        assert "conditional" in template
        assert "condition" in template
        assert "true_next" in template
        assert "false_next" in template
    
    def test_loop_pattern_template(self):
        """Test loop pattern template."""
        template = PromptTemplates.LOOP_PATTERN
        
        assert "loop" in template
        assert "collection" in template
        assert "loop_body" in template
    
    def test_parallel_pattern_template(self):
        """Test parallel pattern template."""
        template = PromptTemplates.PARALLEL_PATTERN
        
        assert "parallel" in template
        assert "branches" in template
    
    def test_fork_join_pattern_template(self):
        """Test fork-join pattern template."""
        template = PromptTemplates.FORK_JOIN_PATTERN
        
        assert "fork_join" in template
        assert "join_policy" in template
        assert "all" in template
        assert "any" in template
    
    def test_workflow_refinement_template(self):
        """Test workflow refinement template."""
        prompt = PromptTemplates.WORKFLOW_REFINEMENT.format(
            current_workflow='{"name": "test"}',
            modification_request="Add a new step",
            conversation_history="Previous messages",
            agents="agent-1"
        )
        
        assert "Add a new step" in prompt
        assert "test" in prompt
        assert "agent-1" in prompt
    
    def test_agent_suggestion_template(self):
        """Test agent suggestion template."""
        prompt = PromptTemplates.AGENT_SUGGESTION.format(
            requirement="Process data",
            agents="agent-1, agent-2"
        )
        
        assert "Process data" in prompt
        assert "agent-1" in prompt
        assert "suggestion" in prompt.lower()
    
    def test_build_prompt_function(self):
        """Test build_prompt helper function."""
        prompt = build_prompt(
            "BASE_WORKFLOW_GENERATION",
            description="Test",
            agents="agent-1"
        )
        
        assert "Test" in prompt
        assert "agent-1" in prompt
    
    def test_build_prompt_invalid_template(self):
        """Test build_prompt with invalid template."""
        with pytest.raises(ValueError, match="Unknown template"):
            build_prompt("NONEXISTENT_TEMPLATE")


class TestAgentFormattingTemplates:
    """Test agent formatting templates."""
    
    def test_format_agent_list_empty(self):
        """Test formatting empty agent list."""
        result = AgentFormattingTemplates.format_agent_list([])
        assert "No agents" in result
    
    def test_format_agent_list_single(self):
        """Test formatting single agent."""
        agents = [{
            "name": "test-agent",
            "description": "Test description",
            "capabilities": ["cap1", "cap2"],
            "status": "active"
        }]
        
        result = AgentFormattingTemplates.format_agent_list(agents)
        
        assert "test-agent" in result
        assert "Test description" in result
        assert "cap1" in result
        assert "cap2" in result
        assert "active" in result
    
    def test_format_agent_list_multiple(self):
        """Test formatting multiple agents."""
        agents = [
            {"name": "agent-1", "description": "First", "capabilities": [], "status": "active"},
            {"name": "agent-2", "description": "Second", "capabilities": ["cap"], "status": "active"}
        ]
        
        result = AgentFormattingTemplates.format_agent_list(agents)
        
        assert "agent-1" in result
        assert "agent-2" in result
        assert "First" in result
        assert "Second" in result
    
    def test_format_agent_detail(self):
        """Test formatting agent detail."""
        agent = {
            "name": "test-agent",
            "description": "Test description",
            "url": "http://example.com",
            "capabilities": ["cap1", "cap2"],
            "status": "active"
        }
        
        result = AgentFormattingTemplates.format_agent_detail(agent)
        
        assert "test-agent" in result
        assert "Test description" in result
        assert "http://example.com" in result
        assert "cap1" in result
        assert "cap2" in result
        assert "active" in result
    
    def test_format_agent_suggestion(self):
        """Test formatting agent suggestion."""
        agent = {
            "name": "test-agent",
            "description": "Test description"
        }
        
        result = AgentFormattingTemplates.format_agent_suggestion(
            agent,
            reason="Best match for the task",
            confidence="high"
        )
        
        assert "test-agent" in result
        assert "Best match" in result
        assert "high" in result


class TestErrorMessageTemplates:
    """Test error message templates."""
    
    def test_invalid_description_error(self):
        """Test invalid description error message."""
        msg = ErrorMessageTemplates.INVALID_DESCRIPTION
        
        assert "description" in msg.lower()
        assert "Suggestions" in msg
        assert "specific" in msg.lower()
    
    def test_no_agents_available_error(self):
        """Test no agents available error message."""
        msg = ErrorMessageTemplates.NO_AGENTS_AVAILABLE
        
        assert "agent" in msg.lower()
        assert "registry" in msg.lower()
        assert "Suggestions" in msg
    
    def test_agent_not_found_error(self):
        """Test agent not found error message."""
        msg = format_error_message(
            "AGENT_NOT_FOUND",
            agent_name="test-agent",
            available_agents="agent-1, agent-2"
        )
        
        assert "test-agent" in msg
        assert "agent-1" in msg
        assert "Suggestions" in msg
    
    def test_validation_failed_error(self):
        """Test validation failed error message."""
        msg = format_error_message(
            "VALIDATION_FAILED",
            error_count=2,
            errors="Error 1\nError 2"
        )
        
        assert "2" in msg
        assert "Error 1" in msg
        assert "Error 2" in msg
        assert "Suggestions" in msg
    
    def test_unsupported_format_error(self):
        """Test unsupported format error message."""
        msg = format_error_message(
            "UNSUPPORTED_FORMAT",
            format="xyz",
            supported_formats="pdf, docx, txt"
        )
        
        assert "xyz" in msg
        assert "pdf" in msg
        assert "Suggestions" in msg
    
    def test_document_too_large_error(self):
        """Test document too large error message."""
        msg = format_error_message(
            "DOCUMENT_TOO_LARGE",
            file_size_mb=15,
            max_size_mb=10
        )
        
        assert "15" in msg
        assert "10" in msg
        assert "Suggestions" in msg
    
    def test_rate_limit_exceeded_error(self):
        """Test rate limit exceeded error message."""
        msg = format_error_message(
            "RATE_LIMIT_EXCEEDED",
            max_requests=50,
            window_seconds=60,
            wait_time=30
        )
        
        assert "50" in msg
        assert "60" in msg
        assert "30" in msg
        assert "Suggestions" in msg
    
    def test_circular_reference_error(self):
        """Test circular reference error message."""
        msg = format_error_message(
            "CIRCULAR_REFERENCE",
            cycle_path="step1 -> step2 -> step1"
        )
        
        assert "step1" in msg
        assert "step2" in msg
        assert "cycle" in msg.lower()
        assert "Suggestions" in msg
    
    def test_format_error_message_missing_variable(self):
        """Test error message with missing template variable."""
        msg = format_error_message(
            "AGENT_NOT_FOUND",
            agent_name="test"
            # Missing available_agents
        )
        
        # Should still return a message
        assert "test" in msg
        assert len(msg) > 0


class TestExplanationTemplates:
    """Test explanation templates."""
    
    def test_workflow_generated_explanation(self):
        """Test workflow generated explanation."""
        explanation = ExplanationTemplates.workflow_generated(
            workflow_name="test-workflow",
            num_steps=5,
            agents_used=["agent-1", "agent-2"]
        )
        
        assert "test-workflow" in explanation
        assert "5" in explanation
        assert "agent-1" in explanation
        assert "agent-2" in explanation
        assert "validated" in explanation.lower()
    
    def test_workflow_modified_explanation(self):
        """Test workflow modified explanation."""
        explanation = ExplanationTemplates.workflow_modified(
            changes=["Added new step", "Updated agent"],
            preserved_count=3
        )
        
        assert "Added new step" in explanation
        assert "Updated agent" in explanation
        assert "3" in explanation
        assert "Preserved" in explanation
    
    def test_agent_selected_explanation(self):
        """Test agent selected explanation."""
        explanation = ExplanationTemplates.agent_selected(
            agent_name="test-agent",
            reason="Best match for the task",
            alternatives=["alt-agent-1", "alt-agent-2"]
        )
        
        assert "test-agent" in explanation
        assert "Best match" in explanation
        assert "alt-agent-1" in explanation
        assert "Alternative" in explanation
    
    def test_agent_selected_no_alternatives(self):
        """Test agent selected explanation without alternatives."""
        explanation = ExplanationTemplates.agent_selected(
            agent_name="test-agent",
            reason="Only available agent"
        )
        
        assert "test-agent" in explanation
        assert "Only available" in explanation
        assert "Alternative" not in explanation
    
    def test_pattern_detected_explanation(self):
        """Test pattern detected explanation."""
        explanation = ExplanationTemplates.pattern_detected(
            pattern_type="loop",
            description="Iterates over a collection of items"
        )
        
        assert "loop" in explanation
        assert "Iterates" in explanation
        assert "pattern" in explanation.lower()
    
    def test_validation_auto_corrected_explanation(self):
        """Test validation auto-corrected explanation."""
        explanation = ExplanationTemplates.validation_auto_corrected(
            corrections=["Fixed missing next field", "Added default input mapping"]
        )
        
        assert "Fixed missing next field" in explanation
        assert "Added default input mapping" in explanation
        assert "corrected" in explanation.lower()
    
    def test_clarification_response(self):
        """Test clarification response."""
        response = ExplanationTemplates.clarification_response(
            question="How does the loop work?",
            answer="The loop iterates over each item in the collection"
        )
        
        assert "How does the loop work?" in response
        assert "iterates" in response
        assert "Question" in response
        assert "Answer" in response


class TestTemplateIntegration:
    """Test integration between different template types."""
    
    def test_example_to_prompt_flow(self):
        """Test using example description in a prompt."""
        description = get_example_description("simple_sequential")
        agents = AgentFormattingTemplates.format_agent_list([
            {"name": "agent-1", "description": "Test", "capabilities": [], "status": "active"}
        ])
        
        prompt = build_prompt(
            "BASE_WORKFLOW_GENERATION",
            description=description,
            agents=agents
        )
        
        assert len(prompt) > 0
        assert "agent-1" in prompt
        assert "workflow" in prompt.lower()
    
    def test_error_to_explanation_flow(self):
        """Test error message followed by explanation."""
        error = format_error_message(
            "VALIDATION_FAILED",
            error_count=1,
            errors="Missing start_step"
        )
        
        explanation = ExplanationTemplates.validation_auto_corrected(
            corrections=["Added start_step field"]
        )
        
        assert "Missing start_step" in error
        assert "Added start_step" in explanation
    
    def test_all_templates_have_suggestions(self):
        """Test that all error templates include suggestions."""
        error_attrs = [
            attr for attr in dir(ErrorMessageTemplates)
            if not attr.startswith('_') and attr.isupper()
        ]
        
        for attr_name in error_attrs:
            template = getattr(ErrorMessageTemplates, attr_name)
            if isinstance(template, str):
                # Should contain "Suggestions" or "Suggestion"
                assert "Suggestion" in template, \
                    f"Error template '{attr_name}' should include suggestions"

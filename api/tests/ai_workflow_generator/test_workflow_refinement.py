"""Tests for workflow refinement service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.services.ai_workflow_generator.workflow_refinement import (
    WorkflowRefinementService,
    WorkflowModificationParser,
    WorkflowDiffer,
    ModificationRequest
)
from api.services.ai_workflow_generator.gemini_service import LLMResponse
from api.services.ai_workflow_generator.agent_query import AgentMetadata
from api.services.ai_workflow_generator.chat_session import Message
from datetime import datetime
from uuid import uuid4


@pytest.fixture
def mock_gemini_service():
    """Create a mock Gemini service."""
    return AsyncMock()


@pytest.fixture
def sample_agents():
    """Create sample agent metadata."""
    return [
        AgentMetadata(
            name="data-processor",
            description="Processes data files",
            url="http://localhost:8001",
            capabilities=["process", "data"],
            status="active"
        ),
        AgentMetadata(
            name="validator",
            description="Validates input data",
            url="http://localhost:8002",
            capabilities=["validate", "data"],
            status="active"
        ),
        AgentMetadata(
            name="transformer",
            description="Transforms data format",
            url="http://localhost:8003",
            capabilities=["transform", "data"],
            status="active"
        )
    ]


@pytest.fixture
def sample_workflow():
    """Create a sample workflow JSON."""
    return {
        "name": "data-processing-workflow",
        "description": "Process and validate data",
        "start_step": "step1",
        "steps": {
            "step1": {
                "id": "step1",
                "type": "agent",
                "agent_name": "data-processor",
                "input_mapping": {
                    "data": "${workflow.input.data}"
                },
                "next_step": "step2"
            },
            "step2": {
                "id": "step2",
                "type": "agent",
                "agent_name": "validator",
                "input_mapping": {
                    "data": "${step1.output}"
                },
                "next_step": None
            }
        }
    }


@pytest.fixture
def conversation_history():
    """Create sample conversation history."""
    return [
        Message(
            id=uuid4(),
            role="user",
            content="Create a workflow to process data",
            timestamp=datetime.utcnow()
        ),
        Message(
            id=uuid4(),
            role="assistant",
            content="I've created a workflow with data processing and validation steps",
            timestamp=datetime.utcnow()
        )
    ]


class TestWorkflowModificationParser:
    """Tests for WorkflowModificationParser."""
    
    def test_parse_add_request(self):
        """Test parsing an add modification request."""
        request = "Add a new step to transform the data"
        parsed = WorkflowModificationParser.parse_request(request)
        
        assert parsed.request_type == "add"
        assert parsed.raw_request == request
    
    def test_parse_remove_request(self):
        """Test parsing a remove modification request."""
        request = "Remove the validation step"
        parsed = WorkflowModificationParser.parse_request(request)
        
        assert parsed.request_type == "remove"
    
    def test_parse_modify_request(self):
        """Test parsing a modify modification request."""
        request = "Change the data-processor to use different input"
        parsed = WorkflowModificationParser.parse_request(request)
        
        assert parsed.request_type == "modify"
    
    def test_parse_clarify_request(self):
        """Test parsing a clarification request."""
        request = "What does the validator step do?"
        parsed = WorkflowModificationParser.parse_request(request)
        
        assert parsed.request_type == "clarify"
    
    def test_parse_clarify_request_with_explain(self):
        """Test parsing a clarification request with 'explain'."""
        request = "Explain how the workflow processes data"
        parsed = WorkflowModificationParser.parse_request(request)
        
        assert parsed.request_type == "clarify"
    
    def test_extract_target_elements_quoted(self):
        """Test extracting target elements from quoted strings."""
        request = 'Modify the "data-processor" step'
        parsed = WorkflowModificationParser.parse_request(request)
        
        assert "data-processor" in parsed.target_elements
    
    def test_extract_target_elements_step_reference(self):
        """Test extracting step references."""
        request = "Change step1 to use different agent"
        parsed = WorkflowModificationParser.parse_request(request)
        
        assert "1" in parsed.target_elements or "step1" in str(parsed.target_elements)
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        request = "Add a parallel processing step with conditional logic"
        parsed = WorkflowModificationParser.parse_request(request)
        
        assert "parallel" in parsed.modification_details["keywords"]
        assert "conditional" in parsed.modification_details["keywords"]


class TestWorkflowDiffer:
    """Tests for WorkflowDiffer."""
    
    def test_compute_diff_added_steps(self):
        """Test computing diff when steps are added."""
        old_workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {"id": "step1", "type": "agent", "agent_name": "agent1"}
            }
        }
        
        new_workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {"id": "step1", "type": "agent", "agent_name": "agent1"},
                "step2": {"id": "step2", "type": "agent", "agent_name": "agent2"}
            }
        }
        
        diff = WorkflowDiffer.compute_diff(old_workflow, new_workflow)
        
        assert "step2" in diff["added_steps"]
        assert len(diff["removed_steps"]) == 0
        assert "step1" in diff["unchanged_steps"]
    
    def test_compute_diff_removed_steps(self):
        """Test computing diff when steps are removed."""
        old_workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {"id": "step1", "type": "agent", "agent_name": "agent1"},
                "step2": {"id": "step2", "type": "agent", "agent_name": "agent2"}
            }
        }
        
        new_workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {"id": "step1", "type": "agent", "agent_name": "agent1"}
            }
        }
        
        diff = WorkflowDiffer.compute_diff(old_workflow, new_workflow)
        
        assert "step2" in diff["removed_steps"]
        assert len(diff["added_steps"]) == 0
    
    def test_compute_diff_modified_steps(self):
        """Test computing diff when steps are modified."""
        old_workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {"id": "step1", "type": "agent", "agent_name": "agent1"}
            }
        }
        
        new_workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {"id": "step1", "type": "agent", "agent_name": "agent2"}
            }
        }
        
        diff = WorkflowDiffer.compute_diff(old_workflow, new_workflow)
        
        assert len(diff["modified_steps"]) == 1
        assert diff["modified_steps"][0]["step_id"] == "step1"
    
    def test_compute_diff_metadata_changes(self):
        """Test computing diff for metadata changes."""
        old_workflow = {
            "name": "old-name",
            "description": "old description",
            "start_step": "step1",
            "steps": {}
        }
        
        new_workflow = {
            "name": "new-name",
            "description": "old description",
            "start_step": "step1",
            "steps": {}
        }
        
        diff = WorkflowDiffer.compute_diff(old_workflow, new_workflow)
        
        assert "name" in diff["metadata_changes"]
        assert diff["metadata_changes"]["name"]["old"] == "old-name"
        assert diff["metadata_changes"]["name"]["new"] == "new-name"
    
    def test_generate_change_summary(self):
        """Test generating human-readable change summary."""
        diff = {
            "added_steps": ["step3"],
            "removed_steps": ["step2"],
            "modified_steps": [{"step_id": "step1"}],
            "unchanged_steps": ["step4", "step5"],
            "metadata_changes": {}
        }
        
        summary = WorkflowDiffer.generate_change_summary(diff)
        
        assert "Added 1 step(s): step3" in summary
        assert "Removed 1 step(s): step2" in summary
        assert "Modified 1 step(s): step1" in summary
        assert "Preserved 2 unchanged step(s)" in summary
    
    def test_generate_change_summary_no_changes(self):
        """Test generating summary when no changes."""
        diff = {
            "added_steps": [],
            "removed_steps": [],
            "modified_steps": [],
            "unchanged_steps": [],
            "metadata_changes": {}
        }
        
        summary = WorkflowDiffer.generate_change_summary(diff)
        
        assert summary == "No changes detected"


class TestWorkflowRefinementService:
    """Tests for WorkflowRefinementService."""
    
    @pytest.mark.asyncio
    async def test_refine_workflow_add_step(
        self,
        mock_gemini_service,
        sample_workflow,
        sample_agents,
        conversation_history
    ):
        """Test refining workflow by adding a step."""
        # Setup
        service = WorkflowRefinementService(mock_gemini_service)
        
        # Create modified workflow with new step
        modified_workflow = {
            **sample_workflow,
            "steps": {
                **sample_workflow["steps"],
                "step3": {
                    "id": "step3",
                    "type": "agent",
                    "agent_name": "transformer",
                    "input_mapping": {"data": "${step2.output}"},
                    "next_step": None
                }
            }
        }
        
        # Update step2 to point to step3
        modified_workflow["steps"]["step2"]["next_step"] = "step3"
        
        # Mock Gemini response
        mock_gemini_service.chat.return_value = LLMResponse(
            content="Added a transformation step after validation",
            workflow_json=modified_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 100}
        )
        
        # Execute
        result_workflow, explanation, suggestions = await service.refine_workflow(
            current_workflow=sample_workflow,
            modification_request="Add a step to transform the data after validation",
            conversation_history=conversation_history,
            available_agents=sample_agents
        )
        
        # Assert
        assert result_workflow is not None
        assert "step3" in result_workflow["steps"]
        assert "Added" in explanation or "transformation" in explanation.lower()
        assert result_workflow["steps"]["step1"] == sample_workflow["steps"]["step1"]  # Preserved
    
    @pytest.mark.asyncio
    async def test_refine_workflow_clarification(
        self,
        mock_gemini_service,
        sample_workflow,
        sample_agents,
        conversation_history
    ):
        """Test handling clarification requests."""
        # Setup
        service = WorkflowRefinementService(mock_gemini_service)
        
        # Mock Gemini response for clarification
        mock_gemini_service.chat.return_value = LLMResponse(
            content="The validator step checks the data for correctness and completeness.",
            workflow_json=None,
            finish_reason="STOP",
            usage={"total_tokens": 50}
        )
        
        # Execute
        result_workflow, explanation, suggestions = await service.refine_workflow(
            current_workflow=sample_workflow,
            modification_request="What does the validator step do?",
            conversation_history=conversation_history,
            available_agents=sample_agents
        )
        
        # Assert
        assert result_workflow is None  # No workflow modification for clarification
        assert "validator" in explanation.lower()
        assert len(suggestions) == 0
    
    @pytest.mark.asyncio
    async def test_refine_workflow_remove_step(
        self,
        mock_gemini_service,
        sample_workflow,
        sample_agents,
        conversation_history
    ):
        """Test refining workflow by removing a step."""
        # Setup
        service = WorkflowRefinementService(mock_gemini_service)
        
        # Create modified workflow with step removed
        modified_workflow = {
            **sample_workflow,
            "steps": {
                "step1": {
                    **sample_workflow["steps"]["step1"],
                    "next_step": None
                }
            }
        }
        
        # Mock Gemini response
        mock_gemini_service.chat.return_value = LLMResponse(
            content="Removed the validation step as requested",
            workflow_json=modified_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 80}
        )
        
        # Execute
        result_workflow, explanation, suggestions = await service.refine_workflow(
            current_workflow=sample_workflow,
            modification_request="Remove the validation step",
            conversation_history=conversation_history,
            available_agents=sample_agents
        )
        
        # Assert
        assert result_workflow is not None
        assert "step2" not in result_workflow["steps"]
        assert "step1" in result_workflow["steps"]  # Preserved
        assert "Removed" in explanation
    
    @pytest.mark.asyncio
    async def test_refine_workflow_modify_step(
        self,
        mock_gemini_service,
        sample_workflow,
        sample_agents,
        conversation_history
    ):
        """Test refining workflow by modifying a step."""
        # Setup
        service = WorkflowRefinementService(mock_gemini_service)
        
        # Create modified workflow with changed agent
        modified_workflow = {
            **sample_workflow,
            "steps": {
                "step1": {
                    **sample_workflow["steps"]["step1"],
                    "agent_name": "transformer"
                },
                "step2": sample_workflow["steps"]["step2"]
            }
        }
        
        # Mock Gemini response
        mock_gemini_service.chat.return_value = LLMResponse(
            content="Changed step1 to use the transformer agent",
            workflow_json=modified_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 90}
        )
        
        # Execute
        result_workflow, explanation, suggestions = await service.refine_workflow(
            current_workflow=sample_workflow,
            modification_request="Change step1 to use the transformer agent",
            conversation_history=conversation_history,
            available_agents=sample_agents
        )
        
        # Assert
        assert result_workflow is not None
        assert result_workflow["steps"]["step1"]["agent_name"] == "transformer"
        assert result_workflow["steps"]["step2"] == sample_workflow["steps"]["step2"]  # Preserved
        assert "Modified" in explanation or "Changed" in explanation
    
    @pytest.mark.asyncio
    async def test_refine_workflow_preservation(
        self,
        mock_gemini_service,
        sample_workflow,
        sample_agents,
        conversation_history
    ):
        """Test that unchanged steps are preserved."""
        # Setup
        service = WorkflowRefinementService(mock_gemini_service)
        
        # Create modified workflow with only step2 changed
        modified_workflow = {
            **sample_workflow,
            "steps": {
                "step1": sample_workflow["steps"]["step1"],  # Unchanged
                "step2": {
                    **sample_workflow["steps"]["step2"],
                    "input_mapping": {"data": "${step1.output}", "mode": "strict"}
                }
            }
        }
        
        # Mock Gemini response
        mock_gemini_service.chat.return_value = LLMResponse(
            content="Updated validation step to use strict mode",
            workflow_json=modified_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 85}
        )
        
        # Execute
        result_workflow, explanation, suggestions = await service.refine_workflow(
            current_workflow=sample_workflow,
            modification_request="Make the validator use strict mode",
            conversation_history=conversation_history,
            available_agents=sample_agents
        )
        
        # Assert
        assert result_workflow is not None
        # Step1 should be completely unchanged
        assert result_workflow["steps"]["step1"] == sample_workflow["steps"]["step1"]
        # Step2 should be modified
        assert result_workflow["steps"]["step2"] != sample_workflow["steps"]["step2"]
        assert "preserved" in explanation.lower() or "unchanged" in explanation.lower()
    
    @pytest.mark.asyncio
    async def test_refine_workflow_error_handling(
        self,
        mock_gemini_service,
        sample_workflow,
        sample_agents,
        conversation_history
    ):
        """Test error handling in workflow refinement."""
        # Setup
        service = WorkflowRefinementService(mock_gemini_service)
        
        # Mock Gemini to raise exception
        mock_gemini_service.chat.side_effect = Exception("API error")
        
        # Execute
        result_workflow, explanation, suggestions = await service.refine_workflow(
            current_workflow=sample_workflow,
            modification_request="Add a step",
            conversation_history=conversation_history,
            available_agents=sample_agents
        )
        
        # Assert
        assert result_workflow is None
        assert "Error" in explanation
    
    @pytest.mark.asyncio
    async def test_refine_workflow_generates_suggestions(
        self,
        mock_gemini_service,
        sample_workflow,
        sample_agents,
        conversation_history
    ):
        """Test that refinement generates helpful suggestions."""
        # Setup
        service = WorkflowRefinementService(mock_gemini_service)
        
        # Create modified workflow with multiple new steps
        modified_workflow = {
            **sample_workflow,
            "steps": {
                **sample_workflow["steps"],
                "step3": {"id": "step3", "type": "agent", "agent_name": "agent3"},
                "step4": {"id": "step4", "type": "agent", "agent_name": "agent4"}
            }
        }
        
        # Mock Gemini response
        mock_gemini_service.chat.return_value = LLMResponse(
            content="Added two new processing steps",
            workflow_json=modified_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 100}
        )
        
        # Execute
        result_workflow, explanation, suggestions = await service.refine_workflow(
            current_workflow=sample_workflow,
            modification_request="Add two more processing steps",
            conversation_history=conversation_history,
            available_agents=sample_agents
        )
        
        # Assert
        assert result_workflow is not None
        assert len(suggestions) > 0
        # Should suggest reviewing input mappings for new steps
        assert any("input" in s.lower() or "test" in s.lower() for s in suggestions)

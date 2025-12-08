"""Tests for workflow generation service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.ai_workflow_generator.workflow_generation import (
    WorkflowGenerationService,
    WorkflowGenerationResult
)
from api.services.ai_workflow_generator.gemini_service import LLMResponse
from api.services.ai_workflow_generator.agent_query import AgentMetadata
from api.services.ai_workflow_generator.workflow_validation import ValidationResult


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=AsyncSession)


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


@pytest.mark.asyncio
async def test_generate_from_text_success(mock_db, mock_gemini_service, sample_agents, sample_workflow):
    """Test successful workflow generation from text description."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="Generated a workflow to process and validate data",
            workflow_json=sample_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 100}
        )
        
        # Mock validation service
        with patch.object(service.validation_service, 'validate_workflow') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                auto_corrections=[]
            )
            
            # Execute
            result = await service.generate_from_text("Process and validate data files")
            
            # Assert
            assert result.success is True
            assert result.workflow_json is not None
            assert result.workflow_json["name"] == "data-processing-workflow"
            assert len(result.validation_errors) == 0
            assert "data-processor" in result.agents_used
            assert "validator" in result.agents_used


@pytest.mark.asyncio
async def test_generate_from_text_no_agents(mock_db, mock_gemini_service):
    """Test workflow generation when no agents are available."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Mock agent query service to return empty list
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=[]):
        # Execute
        result = await service.generate_from_text("Process data")
        
        # Assert
        assert result.success is False
        assert result.workflow_json is None
        assert "No active agents available" in result.explanation
        assert len(result.validation_errors) > 0


@pytest.mark.asyncio
async def test_generate_from_text_gemini_fails(mock_db, mock_gemini_service, sample_agents):
    """Test workflow generation when Gemini fails to return valid JSON."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response with no workflow JSON
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="I couldn't generate a workflow",
            workflow_json=None,
            finish_reason="STOP",
            usage={"total_tokens": 50}
        )
        
        # Execute
        result = await service.generate_from_text("Do something complex")
        
        # Assert
        assert result.success is False
        assert result.workflow_json is None
        assert "Failed to generate workflow JSON" in result.validation_errors


@pytest.mark.asyncio
async def test_generate_from_text_with_validation_errors(mock_db, mock_gemini_service, sample_agents, sample_workflow):
    """Test workflow generation with validation errors."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="Generated workflow",
            workflow_json=sample_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 100}
        )
        
        # Mock validation service with errors
        with patch.object(service.validation_service, 'validate_workflow') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=False,
                errors=["Circular reference detected"],
                warnings=[],
                auto_corrections=[]
            )
            
            # Execute
            result = await service.generate_from_text("Process data")
            
            # Assert
            assert result.success is False
            assert result.workflow_json is not None
            assert "Circular reference detected" in result.validation_errors


@pytest.mark.asyncio
async def test_generate_from_text_with_auto_corrections(mock_db, mock_gemini_service, sample_agents, sample_workflow):
    """Test workflow generation with auto-corrections applied."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="Generated workflow",
            workflow_json=sample_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 100}
        )
        
        # Mock validation service with auto-corrections
        with patch.object(service.validation_service, 'validate_workflow') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                auto_corrections=["Added missing input_mapping to step1"]
            )
            
            # Execute
            result = await service.generate_from_text("Process data")
            
            # Assert
            assert result.success is True
            assert len(result.suggestions) > 0
            assert any("input_mapping" in s for s in result.suggestions)


@pytest.mark.asyncio
async def test_generate_from_document(mock_db, mock_gemini_service, sample_agents, sample_workflow):
    """Test workflow generation from document content."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="Generated workflow from document",
            workflow_json=sample_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 100}
        )
        
        # Mock validation service
        with patch.object(service.validation_service, 'validate_workflow') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                auto_corrections=[]
            )
            
            # Execute
            document_content = "This document describes a workflow to process and validate data files."
            result = await service.generate_from_document(document_content, "pdf")
            
            # Assert
            assert result.success is True
            assert result.workflow_json is not None
            # Should use same logic as generate_from_text


@pytest.mark.asyncio
async def test_generate_input_mappings(mock_db, mock_gemini_service):
    """Test that input mappings are generated for steps without them."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Workflow with missing input_mapping
    workflow = {
        "name": "test-workflow",
        "start_step": "step1",
        "steps": {
            "step1": {
                "id": "step1",
                "type": "agent",
                "agent_name": "test-agent"
                # No input_mapping
            }
        }
    }
    
    # Execute
    result = service._generate_input_mappings(workflow)
    
    # Assert
    assert "input_mapping" in result["steps"]["step1"]
    assert result["steps"]["step1"]["input_mapping"] is not None


@pytest.mark.asyncio
async def test_assign_agents_to_steps(mock_db, mock_gemini_service, sample_workflow, sample_agents):
    """Test extraction of agents used in workflow."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Execute
    agents_used = service._assign_agents_to_steps(sample_workflow, sample_agents)
    
    # Assert
    assert "data-processor" in agents_used
    assert "validator" in agents_used
    assert len(agents_used) == 2


@pytest.mark.asyncio
async def test_identify_workflow_steps(mock_db, mock_gemini_service, sample_agents):
    """Test identification of workflow steps from description."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Execute
    description = "Process the data using data-processor and then validate it"
    steps = service._identify_workflow_steps(description, sample_agents)
    
    # Assert
    assert "process" in steps
    assert "validate" in steps


@pytest.mark.asyncio
async def test_validate_workflow(mock_db, mock_gemini_service, sample_workflow):
    """Test workflow validation method."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Mock validation service
    with patch.object(service.validation_service, 'validate_workflow') as mock_validate:
        mock_validate.return_value = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Some warning"],
            auto_corrections=[]
        )
        
        # Execute
        result = await service.validate_workflow(sample_workflow)
        
        # Assert
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 1


@pytest.mark.asyncio
async def test_generate_from_text_exception_handling(mock_db, mock_gemini_service, sample_agents):
    """Test that exceptions are handled gracefully."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Mock agent query service to raise exception
    with patch.object(service.agent_query_service, 'get_all_agents', side_effect=Exception("Database error")):
        # Execute
        result = await service.generate_from_text("Process data")
        
        # Assert
        assert result.success is False
        # Error message now comes from error handling system
        assert ("unexpected error" in result.explanation.lower() or "error" in result.explanation.lower())
        assert len(result.validation_errors) > 0


@pytest.mark.asyncio
async def test_refine_workflow_success(mock_db, mock_gemini_service, sample_agents, sample_workflow):
    """Test successful workflow refinement."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Create modified workflow
    modified_workflow = {
        **sample_workflow,
        "steps": {
            **sample_workflow["steps"],
            "step3": {
                "id": "step3",
                "type": "agent",
                "agent_name": "data-processor",
                "input_mapping": {"data": "${step2.output}"},
                "next_step": None
            }
        }
    }
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock refinement service
        with patch.object(service.refinement_service, 'refine_workflow') as mock_refine:
            mock_refine.return_value = (
                modified_workflow,
                "Added a new processing step",
                ["Review the new step configuration"]
            )
            
            # Mock validation service
            with patch.object(service.validation_service, 'validate_workflow') as mock_validate:
                mock_validate.return_value = ValidationResult(
                    is_valid=True,
                    errors=[],
                    warnings=[],
                    auto_corrections=[]
                )
                
                # Execute
                from api.services.ai_workflow_generator.chat_session import Message
                from datetime import datetime
                from uuid import uuid4
                
                conversation_history = [
                    Message(
                        id=uuid4(),
                        role="user",
                        content="Create a workflow",
                        timestamp=datetime.utcnow()
                    )
                ]
                
                result = await service.refine_workflow(
                    current_workflow=sample_workflow,
                    modification_request="Add another processing step",
                    conversation_history=conversation_history
                )
                
                # Assert
                assert result.success is True
                assert result.workflow_json is not None
                assert "step3" in result.workflow_json["steps"]
                assert "Added" in result.explanation


@pytest.mark.asyncio
async def test_refine_workflow_clarification(mock_db, mock_gemini_service, sample_agents, sample_workflow):
    """Test workflow refinement with clarification request."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock refinement service to return clarification (no workflow)
        with patch.object(service.refinement_service, 'refine_workflow') as mock_refine:
            mock_refine.return_value = (
                None,  # No workflow for clarification
                "The validator step checks data for correctness",
                []
            )
            
            # Execute
            from api.services.ai_workflow_generator.chat_session import Message
            from datetime import datetime
            from uuid import uuid4
            
            conversation_history = [
                Message(
                    id=uuid4(),
                    role="user",
                    content="What does the validator do?",
                    timestamp=datetime.utcnow()
                )
            ]
            
            result = await service.refine_workflow(
                current_workflow=sample_workflow,
                modification_request="What does the validator do?",
                conversation_history=conversation_history
            )
            
            # Assert
            assert result.success is True
            assert result.workflow_json is None  # No workflow modification
            assert "validator" in result.explanation.lower()


@pytest.mark.asyncio
async def test_refine_workflow_with_validation_errors(mock_db, mock_gemini_service, sample_agents, sample_workflow):
    """Test workflow refinement with validation errors."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Create modified workflow
    modified_workflow = {
        **sample_workflow,
        "steps": {
            **sample_workflow["steps"],
            "step3": {
                "id": "step3",
                "type": "agent",
                "agent_name": "nonexistent-agent",
                "input_mapping": {},
                "next_step": None
            }
        }
    }
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock refinement service
        with patch.object(service.refinement_service, 'refine_workflow') as mock_refine:
            mock_refine.return_value = (
                modified_workflow,
                "Added a new step",
                []
            )
            
            # Mock validation service with errors
            with patch.object(service.validation_service, 'validate_workflow') as mock_validate:
                mock_validate.return_value = ValidationResult(
                    is_valid=False,
                    errors=["Agent 'nonexistent-agent' not found"],
                    warnings=[],
                    auto_corrections=[]
                )
                
                # Execute
                from api.services.ai_workflow_generator.chat_session import Message
                from datetime import datetime
                from uuid import uuid4
                
                conversation_history = [
                    Message(
                        id=uuid4(),
                        role="user",
                        content="Add a step",
                        timestamp=datetime.utcnow()
                    )
                ]
                
                result = await service.refine_workflow(
                    current_workflow=sample_workflow,
                    modification_request="Add a step",
                    conversation_history=conversation_history
                )
                
                # Assert
                assert result.success is False
                assert len(result.validation_errors) > 0
                assert "nonexistent-agent" in result.validation_errors[0]

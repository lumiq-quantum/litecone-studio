"""Unit tests for Workflow Validation Service."""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.ai_workflow_generator.workflow_validation import (
    WorkflowValidationService,
    ValidationResult
)
from api.services.ai_workflow_generator.agent_query import AgentMetadata


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def validation_service(mock_db_session):
    """Create a WorkflowValidationService instance."""
    return WorkflowValidationService(mock_db_session)


@pytest.fixture
def validation_service_no_db():
    """Create a WorkflowValidationService instance without database."""
    return WorkflowValidationService(None)


@pytest.fixture
def valid_workflow():
    """Create a valid workflow for testing."""
    return {
        "name": "test-workflow",
        "description": "A test workflow",
        "start_step": "step1",
        "steps": {
            "step1": {
                "id": "step1",
                "type": "agent",
                "agent_name": "test-agent",
                "input_mapping": {"input": "value"},
                "next_step": "step2"
            },
            "step2": {
                "id": "step2",
                "type": "agent",
                "agent_name": "test-agent-2",
                "input_mapping": {"data": "${step1.output}"},
                "next_step": None
            }
        }
    }


@pytest.fixture
def workflow_with_cycle():
    """Create a workflow with a circular reference."""
    return {
        "name": "cycle-workflow",
        "start_step": "step1",
        "steps": {
            "step1": {
                "id": "step1",
                "type": "agent",
                "agent_name": "agent1",
                "input_mapping": {},
                "next_step": "step2"
            },
            "step2": {
                "id": "step2",
                "type": "agent",
                "agent_name": "agent2",
                "input_mapping": {},
                "next_step": "step3"
            },
            "step3": {
                "id": "step3",
                "type": "agent",
                "agent_name": "agent3",
                "input_mapping": {},
                "next_step": "step1"  # Creates cycle
            }
        }
    }


@pytest.fixture
def workflow_with_unreachable():
    """Create a workflow with unreachable steps."""
    return {
        "name": "unreachable-workflow",
        "start_step": "step1",
        "steps": {
            "step1": {
                "id": "step1",
                "type": "agent",
                "agent_name": "agent1",
                "input_mapping": {},
                "next_step": None
            },
            "step2": {
                "id": "step2",
                "type": "agent",
                "agent_name": "agent2",
                "input_mapping": {},
                "next_step": None
            }
        }
    }


class TestValidationResult:
    """Tests for ValidationResult class."""
    
    def test_validation_result_initialization(self):
        """Test ValidationResult can be initialized."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["warning1"],
            auto_corrections=[]
        )
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == ["warning1"]
        assert result.auto_corrections == []
    
    def test_validation_result_to_dict(self):
        """Test ValidationResult can be converted to dictionary."""
        result = ValidationResult(
            is_valid=False,
            errors=["error1"],
            warnings=["warning1"],
            auto_corrections=["correction1"]
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["is_valid"] is False
        assert result_dict["errors"] == ["error1"]
        assert result_dict["warnings"] == ["warning1"]
        assert result_dict["auto_corrections"] == ["correction1"]


class TestWorkflowValidationService:
    """Tests for WorkflowValidationService class."""
    
    def test_validate_schema_valid_workflow(self, validation_service_no_db, valid_workflow):
        """Test schema validation with a valid workflow."""
        errors = validation_service_no_db.validate_schema(valid_workflow)
        assert errors == []
    
    def test_validate_schema_missing_name(self, validation_service_no_db):
        """Test schema validation with missing name."""
        workflow = {
            "start_step": "step1",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "agent1",
                    "input_mapping": {}
                }
            }
        }
        
        errors = validation_service_no_db.validate_schema(workflow)
        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)
    
    def test_validate_schema_missing_start_step(self, validation_service_no_db):
        """Test schema validation with missing start_step."""
        workflow = {
            "name": "test",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "agent1",
                    "input_mapping": {}
                }
            }
        }
        
        errors = validation_service_no_db.validate_schema(workflow)
        assert len(errors) > 0
        assert any("start_step" in error.lower() for error in errors)
    
    def test_validate_schema_empty_steps(self, validation_service_no_db):
        """Test schema validation with empty steps."""
        workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {}
        }
        
        errors = validation_service_no_db.validate_schema(workflow)
        assert len(errors) > 0
    
    def test_validate_schema_agent_step_missing_agent_name(self, validation_service_no_db):
        """Test schema validation for agent step without agent_name."""
        workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "input_mapping": {}
                }
            }
        }
        
        errors = validation_service_no_db.validate_schema(workflow)
        assert len(errors) > 0
        assert any("agent_name" in error.lower() for error in errors)
    
    def test_detect_cycles_no_cycle(self, validation_service_no_db, valid_workflow):
        """Test cycle detection with no cycles."""
        errors = validation_service_no_db.detect_cycles(valid_workflow)
        assert errors == []
    
    def test_detect_cycles_with_cycle(self, validation_service_no_db, workflow_with_cycle):
        """Test cycle detection with a circular reference."""
        errors = validation_service_no_db.detect_cycles(workflow_with_cycle)
        assert len(errors) > 0
        assert any("circular" in error.lower() for error in errors)
    
    def test_detect_cycles_self_reference(self, validation_service_no_db):
        """Test cycle detection with self-referencing step."""
        workflow = {
            "name": "self-ref",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "agent1",
                    "input_mapping": {},
                    "next_step": "step1"  # Self-reference
                }
            }
        }
        
        errors = validation_service_no_db.detect_cycles(workflow)
        assert len(errors) > 0
        assert any("circular" in error.lower() for error in errors)
    
    def test_detect_cycles_empty_workflow(self, validation_service_no_db):
        """Test cycle detection with empty workflow."""
        workflow = {"name": "empty", "start_step": "step1", "steps": {}}
        errors = validation_service_no_db.detect_cycles(workflow)
        assert errors == []
    
    def test_check_reachability_all_reachable(self, validation_service_no_db, valid_workflow):
        """Test reachability check with all steps reachable."""
        errors = validation_service_no_db.check_reachability(valid_workflow)
        assert errors == []
    
    def test_check_reachability_with_unreachable(self, validation_service_no_db, workflow_with_unreachable):
        """Test reachability check with unreachable steps."""
        errors = validation_service_no_db.check_reachability(workflow_with_unreachable)
        assert len(errors) > 0
        assert any("unreachable" in error.lower() for error in errors)
        assert any("step2" in error for error in errors)
    
    def test_check_reachability_parallel_steps(self, validation_service_no_db):
        """Test reachability with parallel execution."""
        workflow = {
            "name": "parallel-workflow",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "parallel",
                    "parallel_steps": ["step2", "step3"],
                    "next_step": None
                },
                "step2": {
                    "id": "step2",
                    "type": "agent",
                    "agent_name": "agent2",
                    "input_mapping": {},
                    "next_step": None
                },
                "step3": {
                    "id": "step3",
                    "type": "agent",
                    "agent_name": "agent3",
                    "input_mapping": {},
                    "next_step": None
                }
            }
        }
        
        errors = validation_service_no_db.check_reachability(workflow)
        assert errors == []
    
    def test_check_reachability_conditional_steps(self, validation_service_no_db):
        """Test reachability with conditional branches."""
        workflow = {
            "name": "conditional-workflow",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "conditional",
                    "condition": {"expression": "true"},
                    "if_true_step": "step2",
                    "if_false_step": "step3",
                    "next_step": None
                },
                "step2": {
                    "id": "step2",
                    "type": "agent",
                    "agent_name": "agent2",
                    "input_mapping": {},
                    "next_step": None
                },
                "step3": {
                    "id": "step3",
                    "type": "agent",
                    "agent_name": "agent3",
                    "input_mapping": {},
                    "next_step": None
                }
            }
        }
        
        errors = validation_service_no_db.check_reachability(workflow)
        assert errors == []
    
    def test_check_reachability_loop_steps(self, validation_service_no_db):
        """Test reachability with loop body."""
        workflow = {
            "name": "loop-workflow",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "loop",
                    "loop_config": {
                        "collection": "${workflow.input.items}",
                        "loop_body": ["step2"]
                    },
                    "next_step": None
                },
                "step2": {
                    "id": "step2",
                    "type": "agent",
                    "agent_name": "agent2",
                    "input_mapping": {},
                    "next_step": None
                }
            }
        }
        
        errors = validation_service_no_db.check_reachability(workflow)
        assert errors == []
    
    @pytest.mark.asyncio
    async def test_validate_agent_references_all_valid(self, validation_service, valid_workflow):
        """Test agent reference validation with all valid agents."""
        # Mock agent query service
        mock_agent1 = AgentMetadata(
            name="test-agent",
            description="Test agent",
            url="http://localhost:8001",
            capabilities=[],
            status="active"
        )
        mock_agent2 = AgentMetadata(
            name="test-agent-2",
            description="Test agent 2",
            url="http://localhost:8002",
            capabilities=[],
            status="active"
        )
        
        with patch.object(validation_service.agent_query_service, 'get_agent_details', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = lambda name: mock_agent1 if name == "test-agent" else mock_agent2
            
            errors = await validation_service.validate_agent_references(valid_workflow)
            assert errors == []
    
    @pytest.mark.asyncio
    async def test_validate_agent_references_agent_not_found(self, validation_service, valid_workflow):
        """Test agent reference validation with non-existent agent."""
        with patch.object(validation_service.agent_query_service, 'get_agent_details', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            errors = await validation_service.validate_agent_references(valid_workflow)
            assert len(errors) > 0
            assert any("not found" in error.lower() for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_agent_references_agent_inactive(self, validation_service, valid_workflow):
        """Test agent reference validation with inactive agent."""
        mock_agent = AgentMetadata(
            name="test-agent",
            description="Test agent",
            url="http://localhost:8001",
            capabilities=[],
            status="inactive"
        )
        
        with patch.object(validation_service.agent_query_service, 'get_agent_details', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_agent
            
            errors = await validation_service.validate_agent_references(valid_workflow)
            assert len(errors) > 0
            assert any("not active" in error.lower() for error in errors)
    
    def test_auto_correct_missing_name(self, validation_service_no_db):
        """Test auto-correction of missing workflow name."""
        workflow = {
            "start_step": "step1",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "agent1",
                    "input_mapping": {}
                }
            }
        }
        
        corrected = validation_service_no_db.auto_correct(workflow, [])
        assert "name" in corrected
        assert corrected["name"] == "untitled-workflow"
    
    def test_auto_correct_missing_start_step(self, validation_service_no_db):
        """Test auto-correction of missing start_step."""
        workflow = {
            "name": "test",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "agent1",
                    "input_mapping": {}
                }
            }
        }
        
        corrected = validation_service_no_db.auto_correct(workflow, [])
        assert "start_step" in corrected
        assert corrected["start_step"] == "step1"
    
    def test_auto_correct_missing_step_id(self, validation_service_no_db):
        """Test auto-correction of missing step ID."""
        workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "type": "agent",
                    "agent_name": "agent1",
                    "input_mapping": {}
                }
            }
        }
        
        corrected = validation_service_no_db.auto_correct(workflow, [])
        assert corrected["steps"]["step1"]["id"] == "step1"
    
    def test_auto_correct_missing_agent_name(self, validation_service_no_db):
        """Test auto-correction of missing agent_name."""
        workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "input_mapping": {}
                }
            }
        }
        
        corrected = validation_service_no_db.auto_correct(workflow, [])
        assert "agent_name" in corrected["steps"]["step1"]
        assert corrected["steps"]["step1"]["agent_name"] == "default-agent"
    
    def test_auto_correct_missing_input_mapping(self, validation_service_no_db):
        """Test auto-correction of missing input_mapping."""
        workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "agent1"
                }
            }
        }
        
        corrected = validation_service_no_db.auto_correct(workflow, [])
        assert "input_mapping" in corrected["steps"]["step1"]
        assert corrected["steps"]["step1"]["input_mapping"] == {}
    
    def test_auto_correct_invalid_next_step(self, validation_service_no_db):
        """Test auto-correction of invalid next_step reference."""
        workflow = {
            "name": "test",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "agent1",
                    "input_mapping": {},
                    "next_step": "non-existent"
                }
            }
        }
        
        corrected = validation_service_no_db.auto_correct(workflow, [])
        assert corrected["steps"]["step1"]["next_step"] is None
    
    @pytest.mark.asyncio
    async def test_validate_workflow_valid(self, validation_service_no_db, valid_workflow):
        """Test full workflow validation with valid workflow."""
        result = await validation_service_no_db.validate_workflow(valid_workflow)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_workflow_with_errors(self, validation_service_no_db, workflow_with_cycle):
        """Test full workflow validation with errors."""
        result = await validation_service_no_db.validate_workflow(workflow_with_cycle)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_validate_workflow_with_auto_correction(self, validation_service_no_db):
        """Test workflow validation with auto-correction."""
        workflow = {
            "start_step": "step1",
            "steps": {
                "step1": {
                    "type": "agent",
                    "agent_name": "agent1"
                }
            }
        }
        
        result = await validation_service_no_db.validate_workflow(workflow)
        
        # Should have auto-corrections
        assert len(result.auto_corrections) > 0

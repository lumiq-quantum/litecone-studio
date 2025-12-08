"""Integration tests for complex workflow pattern generation."""

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
            name="data-fetcher",
            description="Fetches data from sources",
            url="http://localhost:8001",
            capabilities=["fetch", "data"],
            status="active"
        ),
        AgentMetadata(
            name="item-processor",
            description="Processes individual items",
            url="http://localhost:8002",
            capabilities=["process", "item"],
            status="active"
        ),
        AgentMetadata(
            name="validator",
            description="Validates data",
            url="http://localhost:8003",
            capabilities=["validate"],
            status="active"
        ),
        AgentMetadata(
            name="aggregator",
            description="Aggregates results",
            url="http://localhost:8004",
            capabilities=["aggregate", "combine"],
            status="active"
        )
    ]


@pytest.mark.asyncio
async def test_generate_workflow_with_loop_pattern(mock_db, mock_gemini_service, sample_agents):
    """Test workflow generation with loop pattern."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Create a workflow with loop pattern
    loop_workflow = {
        "name": "batch-processing-workflow",
        "description": "Process items in a batch",
        "version": "1.0",
        "start_step": "fetch-data",
        "steps": {
            "fetch-data": {
                "id": "fetch-data",
                "type": "agent",
                "agent_name": "data-fetcher",
                "input_mapping": {
                    "source": "${workflow.input.source}"
                },
                "next_step": "process-loop"
            },
            "process-loop": {
                "id": "process-loop",
                "type": "loop",
                "loop_config": {
                    "collection": "${fetch-data.output.items}",
                    "loop_body": ["process-item"],
                    "execution_mode": "sequential",
                    "max_iterations": 100,
                    "on_error": "continue"
                },
                "next_step": "aggregate"
            },
            "process-item": {
                "id": "process-item",
                "type": "agent",
                "agent_name": "item-processor",
                "input_mapping": {
                    "item": "${loop.item}",
                    "index": "${loop.index}"
                },
                "next_step": None
            },
            "aggregate": {
                "id": "aggregate",
                "type": "agent",
                "agent_name": "aggregator",
                "input_mapping": {
                    "results": "${process-loop.output.iterations}"
                },
                "next_step": None
            }
        }
    }
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="Generated a workflow with loop pattern to process items in batch",
            workflow_json=loop_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 150}
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
            result = await service.generate_from_text(
                "Fetch data and process each item in the collection"
            )
            
            # Assert
            assert result.success is True
            assert result.workflow_json is not None
            assert "process-loop" in result.workflow_json["steps"]
            assert result.workflow_json["steps"]["process-loop"]["type"] == "loop"
            assert "loop_config" in result.workflow_json["steps"]["process-loop"]


@pytest.mark.asyncio
async def test_generate_workflow_with_conditional_pattern(mock_db, mock_gemini_service, sample_agents):
    """Test workflow generation with conditional pattern."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Create a workflow with conditional pattern
    conditional_workflow = {
        "name": "conditional-processing-workflow",
        "description": "Process data based on validation result",
        "version": "1.0",
        "start_step": "validate",
        "steps": {
            "validate": {
                "id": "validate",
                "type": "agent",
                "agent_name": "validator",
                "input_mapping": {
                    "data": "${workflow.input.data}"
                },
                "next_step": "check-valid"
            },
            "check-valid": {
                "id": "check-valid",
                "type": "conditional",
                "condition": {
                    "expression": "${validate.output.is_valid} == true"
                },
                "if_true_step": "process-valid",
                "if_false_step": "process-invalid",
                "next_step": "aggregate"
            },
            "process-valid": {
                "id": "process-valid",
                "type": "agent",
                "agent_name": "item-processor",
                "input_mapping": {
                    "data": "${validate.output.data}"
                },
                "next_step": None
            },
            "process-invalid": {
                "id": "process-invalid",
                "type": "agent",
                "agent_name": "item-processor",
                "input_mapping": {
                    "data": "${validate.output.data}",
                    "mode": "error_handling"
                },
                "next_step": None
            },
            "aggregate": {
                "id": "aggregate",
                "type": "agent",
                "agent_name": "aggregator",
                "input_mapping": {
                    "result": "${check-valid.output}"
                },
                "next_step": None
            }
        }
    }
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="Generated a workflow with conditional branching based on validation",
            workflow_json=conditional_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 150}
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
            result = await service.generate_from_text(
                "Validate the data and if valid process it, otherwise handle the error"
            )
            
            # Assert
            assert result.success is True
            assert result.workflow_json is not None
            assert "check-valid" in result.workflow_json["steps"]
            assert result.workflow_json["steps"]["check-valid"]["type"] == "conditional"


@pytest.mark.asyncio
async def test_generate_workflow_with_parallel_pattern(mock_db, mock_gemini_service, sample_agents):
    """Test workflow generation with parallel pattern."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Create a workflow with parallel pattern
    parallel_workflow = {
        "name": "parallel-processing-workflow",
        "description": "Process multiple data sources in parallel",
        "version": "1.0",
        "start_step": "parallel-fetch",
        "steps": {
            "parallel-fetch": {
                "id": "parallel-fetch",
                "type": "parallel",
                "parallel_steps": ["fetch-source-a", "fetch-source-b", "fetch-source-c"],
                "max_parallelism": 3,
                "next_step": "aggregate"
            },
            "fetch-source-a": {
                "id": "fetch-source-a",
                "type": "agent",
                "agent_name": "data-fetcher",
                "input_mapping": {
                    "source": "source_a"
                },
                "next_step": None
            },
            "fetch-source-b": {
                "id": "fetch-source-b",
                "type": "agent",
                "agent_name": "data-fetcher",
                "input_mapping": {
                    "source": "source_b"
                },
                "next_step": None
            },
            "fetch-source-c": {
                "id": "fetch-source-c",
                "type": "agent",
                "agent_name": "data-fetcher",
                "input_mapping": {
                    "source": "source_c"
                },
                "next_step": None
            },
            "aggregate": {
                "id": "aggregate",
                "type": "agent",
                "agent_name": "aggregator",
                "input_mapping": {
                    "source_a_data": "${fetch-source-a.output}",
                    "source_b_data": "${fetch-source-b.output}",
                    "source_c_data": "${fetch-source-c.output}"
                },
                "next_step": None
            }
        }
    }
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="Generated a workflow with parallel execution for multiple data sources",
            workflow_json=parallel_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 150}
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
            result = await service.generate_from_text(
                "Fetch data from three sources simultaneously and combine the results"
            )
            
            # Assert
            assert result.success is True
            assert result.workflow_json is not None
            assert "parallel-fetch" in result.workflow_json["steps"]
            assert result.workflow_json["steps"]["parallel-fetch"]["type"] == "parallel"


@pytest.mark.asyncio
async def test_generate_workflow_with_fork_join_pattern(mock_db, mock_gemini_service, sample_agents):
    """Test workflow generation with fork-join pattern."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Create a workflow with fork-join pattern
    fork_join_workflow = {
        "name": "fork-join-workflow",
        "description": "Fork into branches and join results",
        "version": "1.0",
        "start_step": "fork-join-process",
        "steps": {
            "fork-join-process": {
                "id": "fork-join-process",
                "type": "fork_join",
                "fork_join_config": {
                    "branches": {
                        "branch_a": {
                            "steps": ["process-a"],
                            "timeout_seconds": 30
                        },
                        "branch_b": {
                            "steps": ["process-b"],
                            "timeout_seconds": 30
                        }
                    },
                    "join_policy": "all",
                    "branch_timeout_seconds": 60
                },
                "next_step": "aggregate"
            },
            "process-a": {
                "id": "process-a",
                "type": "agent",
                "agent_name": "item-processor",
                "input_mapping": {
                    "data": "${workflow.input.data_a}"
                },
                "next_step": None
            },
            "process-b": {
                "id": "process-b",
                "type": "agent",
                "agent_name": "item-processor",
                "input_mapping": {
                    "data": "${workflow.input.data_b}"
                },
                "next_step": None
            },
            "aggregate": {
                "id": "aggregate",
                "type": "agent",
                "agent_name": "aggregator",
                "input_mapping": {
                    "branch_a_result": "${fork-join-process.output.branch_a}",
                    "branch_b_result": "${fork-join-process.output.branch_b}"
                },
                "next_step": None
            }
        }
    }
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="Generated a workflow with fork-join pattern",
            workflow_json=fork_join_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 150}
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
            result = await service.generate_from_text(
                "Fork into two branches to process different data and then merge the results"
            )
            
            # Assert
            assert result.success is True
            assert result.workflow_json is not None
            assert "fork-join-process" in result.workflow_json["steps"]
            assert result.workflow_json["steps"]["fork-join-process"]["type"] == "fork_join"


@pytest.mark.asyncio
async def test_generate_workflow_with_nested_patterns(mock_db, mock_gemini_service, sample_agents):
    """Test workflow generation with nested patterns (loop with conditional inside)."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Create a workflow with nested patterns
    nested_workflow = {
        "name": "nested-pattern-workflow",
        "description": "Loop with conditional logic inside",
        "version": "1.0",
        "start_step": "fetch-data",
        "steps": {
            "fetch-data": {
                "id": "fetch-data",
                "type": "agent",
                "agent_name": "data-fetcher",
                "input_mapping": {
                    "source": "${workflow.input.source}"
                },
                "next_step": "process-loop"
            },
            "process-loop": {
                "id": "process-loop",
                "type": "loop",
                "loop_config": {
                    "collection": "${fetch-data.output.items}",
                    "loop_body": ["validate-item", "check-valid"],
                    "execution_mode": "sequential",
                    "max_iterations": 100,
                    "on_error": "continue"
                },
                "next_step": "aggregate"
            },
            "validate-item": {
                "id": "validate-item",
                "type": "agent",
                "agent_name": "validator",
                "input_mapping": {
                    "item": "${loop.item}"
                },
                "next_step": "check-valid"
            },
            "check-valid": {
                "id": "check-valid",
                "type": "conditional",
                "condition": {
                    "expression": "${validate-item.output.is_valid} == true"
                },
                "if_true_step": "process-valid-item",
                "if_false_step": "skip-item",
                "next_step": None
            },
            "process-valid-item": {
                "id": "process-valid-item",
                "type": "agent",
                "agent_name": "item-processor",
                "input_mapping": {
                    "item": "${loop.item}"
                },
                "next_step": None
            },
            "skip-item": {
                "id": "skip-item",
                "type": "agent",
                "agent_name": "item-processor",
                "input_mapping": {
                    "item": "${loop.item}",
                    "mode": "skip"
                },
                "next_step": None
            },
            "aggregate": {
                "id": "aggregate",
                "type": "agent",
                "agent_name": "aggregator",
                "input_mapping": {
                    "results": "${process-loop.output.iterations}"
                },
                "next_step": None
            }
        }
    }
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="Generated a workflow with nested loop and conditional patterns",
            workflow_json=nested_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 200}
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
            result = await service.generate_from_text(
                "Loop through items, validate each one, and if valid process it, otherwise skip"
            )
            
            # Assert
            assert result.success is True
            assert result.workflow_json is not None
            assert "process-loop" in result.workflow_json["steps"]
            assert result.workflow_json["steps"]["process-loop"]["type"] == "loop"
            assert "check-valid" in result.workflow_json["steps"]
            assert result.workflow_json["steps"]["check-valid"]["type"] == "conditional"


@pytest.mark.asyncio
async def test_nested_reference_validation_catches_errors(mock_db, mock_gemini_service, sample_agents):
    """Test that nested reference validation catches invalid references."""
    # Setup
    service = WorkflowGenerationService(mock_db, mock_gemini_service)
    
    # Create a workflow with invalid nested references
    invalid_workflow = {
        "name": "invalid-nested-workflow",
        "description": "Workflow with invalid references",
        "version": "1.0",
        "start_step": "process-loop",
        "steps": {
            "process-loop": {
                "id": "process-loop",
                "type": "loop",
                "loop_config": {
                    "collection": "${workflow.input.items}",
                    "loop_body": ["non-existent-step"],  # Invalid reference
                    "execution_mode": "sequential"
                },
                "next_step": None
            }
        }
    }
    
    # Mock agent query service
    with patch.object(service.agent_query_service, 'get_all_agents', return_value=sample_agents):
        # Mock Gemini response
        mock_gemini_service.generate_workflow.return_value = LLMResponse(
            content="Generated workflow",
            workflow_json=invalid_workflow,
            finish_reason="STOP",
            usage={"total_tokens": 100}
        )
        
        # Execute
        result = await service.generate_from_text("Process items in a loop")
        
        # Assert
        assert result.success is False
        assert len(result.validation_errors) > 0
        assert any("non-existent-step" in error for error in result.validation_errors)

"""Tests for schema loader functionality."""

import pytest
import json
from pathlib import Path
from api.services.ai_workflow_generator.schema_loader import SchemaLoader, SchemaVersion


@pytest.fixture
def schema_loader():
    """Create a schema loader instance."""
    return SchemaLoader()


@pytest.fixture
def valid_workflow():
    """Create a valid workflow for testing."""
    return {
        "name": "test-workflow",
        "description": "Test workflow",
        "start_step": "step1",
        "steps": {
            "step1": {
                "id": "step1",
                "type": "agent",
                "agent_name": "TestAgent",
                "input_mapping": {
                    "input": "${workflow.input.data}"
                },
                "next_step": None
            }
        }
    }


@pytest.fixture
def invalid_workflow_missing_name():
    """Create an invalid workflow missing required name field."""
    return {
        "start_step": "step1",
        "steps": {
            "step1": {
                "id": "step1",
                "type": "agent",
                "agent_name": "TestAgent",
                "input_mapping": {},
                "next_step": None
            }
        }
    }


@pytest.fixture
def invalid_workflow_wrong_type():
    """Create an invalid workflow with wrong step type."""
    return {
        "name": "test-workflow",
        "start_step": "step1",
        "steps": {
            "step1": {
                "id": "step1",
                "type": "invalid_type",
                "agent_name": "TestAgent",
                "input_mapping": {},
                "next_step": None
            }
        }
    }


class TestSchemaLoader:
    """Test schema loader functionality."""
    
    def test_schema_loader_initialization(self, schema_loader):
        """Test that schema loader initializes correctly."""
        assert schema_loader is not None
        assert schema_loader.schemas is not None
        assert len(schema_loader.schemas) > 0
        assert schema_loader.latest_version is not None
    
    def test_get_latest_schema(self, schema_loader):
        """Test getting the latest schema version."""
        latest = schema_loader.get_schema()
        assert latest is not None
        assert isinstance(latest, SchemaVersion)
        assert latest.version_string is not None
    
    def test_get_specific_schema_version(self, schema_loader):
        """Test getting a specific schema version."""
        versions = schema_loader.get_available_versions()
        assert len(versions) > 0
        
        # Get first available version
        version = versions[0]
        schema = schema_loader.get_schema(version)
        assert schema is not None
        assert schema.version_string == version
    
    def test_get_nonexistent_schema_version(self, schema_loader):
        """Test that requesting nonexistent version raises error."""
        with pytest.raises(ValueError, match="not found"):
            schema_loader.get_schema("99.99.99")
    
    def test_get_available_versions(self, schema_loader):
        """Test getting list of available versions."""
        versions = schema_loader.get_available_versions()
        assert isinstance(versions, list)
        assert len(versions) > 0
        assert all(isinstance(v, str) for v in versions)
    
    def test_get_latest_version_string(self, schema_loader):
        """Test getting latest version string."""
        version = schema_loader.get_latest_version()
        assert isinstance(version, str)
        assert version in schema_loader.get_available_versions()
    
    def test_validate_valid_workflow(self, schema_loader, valid_workflow):
        """Test validating a valid workflow."""
        errors = schema_loader.validate(valid_workflow)
        assert errors == []
    
    def test_validate_invalid_workflow_missing_field(
        self,
        schema_loader,
        invalid_workflow_missing_name
    ):
        """Test validating workflow with missing required field."""
        errors = schema_loader.validate(invalid_workflow_missing_name)
        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)
    
    def test_validate_invalid_workflow_wrong_type(
        self,
        schema_loader,
        invalid_workflow_wrong_type
    ):
        """Test validating workflow with invalid step type."""
        errors = schema_loader.validate(invalid_workflow_wrong_type)
        assert len(errors) > 0
        assert any("type" in error.lower() or "invalid_type" in error.lower() for error in errors)
    
    def test_validate_with_specific_version(self, schema_loader, valid_workflow):
        """Test validating with a specific schema version."""
        version = schema_loader.get_latest_version()
        errors = schema_loader.validate(valid_workflow, version_string=version)
        assert errors == []
    
    def test_detect_version(self, schema_loader, valid_workflow):
        """Test schema version detection."""
        detected_schema = schema_loader.detect_version(valid_workflow)
        assert detected_schema is not None
        assert isinstance(detected_schema, SchemaVersion)
    
    def test_detect_version_with_explicit_version(self, schema_loader, valid_workflow):
        """Test version detection when workflow specifies schema_version."""
        version = schema_loader.get_latest_version()
        workflow_with_version = {
            **valid_workflow,
            "schema_version": version
        }
        
        detected_schema = schema_loader.detect_version(workflow_with_version)
        assert detected_schema.version_string == version
    
    def test_schema_version_object(self, schema_loader):
        """Test SchemaVersion object properties."""
        schema = schema_loader.get_schema()
        
        assert schema.version_string is not None
        assert schema.version is not None
        assert schema.schema_data is not None
        assert schema.file_path is not None
        assert schema.validator is not None
    
    def test_schema_validation_error_messages(
        self,
        schema_loader,
        invalid_workflow_missing_name
    ):
        """Test that validation errors have clear messages."""
        errors = schema_loader.validate(invalid_workflow_missing_name)
        
        assert len(errors) > 0
        # Errors should be strings
        assert all(isinstance(e, str) for e in errors)
        # Errors should be descriptive
        assert all(len(e) > 10 for e in errors)


class TestSchemaEvolution:
    """Test schema evolution support."""
    
    def test_multiple_schema_versions_loaded(self, schema_loader):
        """Test that multiple schema versions can be loaded."""
        versions = schema_loader.get_available_versions()
        # We should have at least one version
        assert len(versions) >= 1
    
    def test_schema_version_comparison(self, schema_loader):
        """Test that schema versions are properly ordered."""
        versions = schema_loader.get_available_versions()
        
        if len(versions) > 1:
            # Versions should be in ascending order
            for i in range(len(versions) - 1):
                v1 = schema_loader.get_schema(versions[i])
                v2 = schema_loader.get_schema(versions[i + 1])
                assert v1.version < v2.version
    
    def test_reload_schemas(self, schema_loader):
        """Test reloading schemas from disk."""
        original_count = len(schema_loader.schemas)
        
        schema_loader.reload_schemas()
        
        # Should have same number of schemas after reload
        assert len(schema_loader.schemas) == original_count
        assert schema_loader.latest_version is not None


class TestComplexWorkflows:
    """Test validation of complex workflow patterns."""
    
    def test_validate_parallel_workflow(self, schema_loader):
        """Test validating workflow with parallel steps."""
        workflow = {
            "name": "parallel-workflow",
            "start_step": "parallel1",
            "steps": {
                "parallel1": {
                    "id": "parallel1",
                    "type": "parallel",
                    "parallel_steps": ["step1", "step2"],
                    "next_step": None
                },
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "Agent1",
                    "input_mapping": {},
                    "next_step": None
                },
                "step2": {
                    "id": "step2",
                    "type": "agent",
                    "agent_name": "Agent2",
                    "input_mapping": {},
                    "next_step": None
                }
            }
        }
        
        errors = schema_loader.validate(workflow)
        assert errors == []
    
    def test_validate_conditional_workflow(self, schema_loader):
        """Test validating workflow with conditional steps."""
        workflow = {
            "name": "conditional-workflow",
            "start_step": "cond1",
            "steps": {
                "cond1": {
                    "id": "cond1",
                    "type": "conditional",
                    "condition": {
                        "expression": "${step1.output.value} > 10"
                    },
                    "if_true_step": "step1",
                    "if_false_step": "step2",
                    "next_step": None
                },
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "Agent1",
                    "input_mapping": {},
                    "next_step": None
                },
                "step2": {
                    "id": "step2",
                    "type": "agent",
                    "agent_name": "Agent2",
                    "input_mapping": {},
                    "next_step": None
                }
            }
        }
        
        errors = schema_loader.validate(workflow)
        assert errors == []
    
    def test_validate_loop_workflow(self, schema_loader):
        """Test validating workflow with loop steps."""
        workflow = {
            "name": "loop-workflow",
            "start_step": "loop1",
            "steps": {
                "loop1": {
                    "id": "loop1",
                    "type": "loop",
                    "loop_config": {
                        "collection": "${workflow.input.items}",
                        "loop_body": ["step1"]
                    },
                    "next_step": None
                },
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "Agent1",
                    "input_mapping": {},
                    "next_step": None
                }
            }
        }
        
        errors = schema_loader.validate(workflow)
        assert errors == []
    
    def test_validate_invalid_parallel_too_few_steps(self, schema_loader):
        """Test that parallel steps with < 2 steps is invalid."""
        workflow = {
            "name": "invalid-parallel",
            "start_step": "parallel1",
            "steps": {
                "parallel1": {
                    "id": "parallel1",
                    "type": "parallel",
                    "parallel_steps": ["step1"],  # Only 1 step, need at least 2
                    "next_step": None
                },
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "Agent1",
                    "input_mapping": {},
                    "next_step": None
                }
            }
        }
        
        errors = schema_loader.validate(workflow)
        assert len(errors) > 0
    
    def test_validate_invalid_conditional_missing_condition(self, schema_loader):
        """Test that conditional without condition is invalid."""
        workflow = {
            "name": "invalid-conditional",
            "start_step": "cond1",
            "steps": {
                "cond1": {
                    "id": "cond1",
                    "type": "conditional",
                    # Missing condition
                    "if_true_step": "step1",
                    "next_step": None
                },
                "step1": {
                    "id": "step1",
                    "type": "agent",
                    "agent_name": "Agent1",
                    "input_mapping": {},
                    "next_step": None
                }
            }
        }
        
        errors = schema_loader.validate(workflow)
        assert len(errors) > 0

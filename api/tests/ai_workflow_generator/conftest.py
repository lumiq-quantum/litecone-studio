"""Pytest configuration and fixtures for AI workflow generator tests."""

import pytest
from hypothesis import settings

# Configure Hypothesis for property-based testing
# Run a minimum of 100 iterations as specified in the design document
settings.register_profile("ai_workflow", max_examples=100, deadline=None)
settings.load_profile("ai_workflow")


@pytest.fixture
def sample_workflow_json():
    """Sample workflow JSON for testing."""
    return {
        "name": "test-workflow",
        "description": "Test workflow",
        "start_step": "step1",
        "steps": {
            "step1": {
                "agent": "test-agent",
                "input_mapping": {},
                "next_step": "step2"
            },
            "step2": {
                "agent": "test-agent-2",
                "input_mapping": {},
                "next_step": None
            }
        }
    }


@pytest.fixture
def sample_agent_metadata():
    """Sample agent metadata for testing."""
    return [
        {
            "name": "test-agent",
            "description": "A test agent for processing data",
            "url": "http://localhost:8001",
            "status": "active"
        },
        {
            "name": "test-agent-2",
            "description": "Another test agent for validation",
            "url": "http://localhost:8002",
            "status": "active"
        }
    ]

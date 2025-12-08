"""Integration tests for AI Workflow Generator with main API."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_ai_routes_registered(client):
    """Test that AI workflow routes are registered in the main app."""
    # Test that the OpenAPI schema includes AI workflow endpoints
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    paths = openapi_spec.get("paths", {})
    
    # Check that AI workflow endpoints are present
    assert "/api/v1/ai-workflows/generate" in paths
    assert "/api/v1/ai-workflows/upload" in paths
    assert "/api/v1/ai-workflows/chat/sessions" in paths
    assert "/api/v1/ai-workflows/agents/suggest" in paths


def test_ai_health_check_endpoint(client):
    """Test that AI service health check endpoint exists."""
    response = client.get("/health/ai")
    assert response.status_code in [200, 503]  # Either healthy or unhealthy is valid
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "services" in data
    
    # Check that Gemini API status is included
    services = data.get("services", {})
    assert "gemini_api" in services


def test_readiness_check_includes_ai_service(client):
    """Test that readiness check includes AI service status."""
    response = client.get("/health/ready")
    assert response.status_code in [200, 503]
    
    data = response.json()
    assert "checks" in data
    
    checks = data.get("checks", {})
    assert "ai_workflow_generator" in checks


def test_root_endpoint_includes_ai_workflows(client):
    """Test that root endpoint includes AI workflows in endpoints list."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "endpoints" in data
    
    endpoints = data.get("endpoints", {})
    assert "ai_workflows" in endpoints
    assert endpoints["ai_workflows"] == "/api/v1/ai-workflows"


def test_api_documentation_includes_ai_tag(client):
    """Test that API documentation includes AI Workflows tag."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    tags = openapi_spec.get("tags", [])
    
    # Find AI Workflows tag
    ai_tag = None
    for tag in tags:
        if tag.get("name") == "AI Workflows":
            ai_tag = tag
            break
    
    assert ai_tag is not None
    assert "description" in ai_tag
    assert "AI-powered workflow generation" in ai_tag["description"]


def test_chat_session_model_imported(client):
    """Test that ChatSessionModel is properly imported in models module."""
    from api.models import ChatSessionModel
    
    # Verify the model has the expected attributes
    assert hasattr(ChatSessionModel, '__tablename__')
    assert ChatSessionModel.__tablename__ == 'ai_chat_sessions'
    
    # Verify key columns exist
    assert hasattr(ChatSessionModel, 'id')
    assert hasattr(ChatSessionModel, 'user_id')
    assert hasattr(ChatSessionModel, 'status')
    assert hasattr(ChatSessionModel, 'current_workflow')
    assert hasattr(ChatSessionModel, 'messages')

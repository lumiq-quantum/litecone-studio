"""Integration tests for AI workflow generator API routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


class TestGenerateWorkflowEndpoint:
    """Tests for POST /api/v1/ai-workflows/generate endpoint."""
    
    @patch('api.routes.ai_workflows.WorkflowGenerationService')
    @patch('api.routes.ai_workflows.get_db')
    def test_generate_workflow_success(self, mock_get_db, mock_service_class, client):
        """Test successful workflow generation from text description."""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock the result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.workflow_json = {"name": "test-workflow", "steps": {}}
        mock_result.explanation = "Generated workflow successfully"
        mock_result.validation_errors = []
        mock_result.suggestions = []
        mock_result.agents_used = ["test-agent"]
        
        mock_service.generate_from_text = AsyncMock(return_value=mock_result)
        
        # Make request
        response = client.post(
            "/api/v1/ai-workflows/generate",
            json={
                "description": "Create a workflow that processes data"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "workflow_json" in data
        assert data["explanation"] == "Generated workflow successfully"


class TestUploadDocumentEndpoint:
    """Tests for POST /api/v1/ai-workflows/upload endpoint."""
    
    @patch('api.routes.ai_workflows.WorkflowGenerationService')
    @patch('api.routes.ai_workflows.DocumentProcessingService')
    @patch('api.routes.ai_workflows.get_db')
    def test_upload_document_success(self, mock_get_db, mock_doc_service_class, mock_workflow_service_class, client):
        """Test successful workflow generation from document upload."""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_doc_service = MagicMock()
        mock_doc_service_class.return_value = mock_doc_service
        mock_doc_service.validate_file.return_value = {"valid": True}
        mock_doc_service.extract_text = AsyncMock(return_value="Document content")
        
        mock_workflow_service = MagicMock()
        mock_workflow_service_class.return_value = mock_workflow_service
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.workflow_json = {"name": "test-workflow", "steps": {}}
        mock_result.explanation = "Generated workflow from document"
        mock_result.validation_errors = []
        mock_result.suggestions = []
        mock_result.agents_used = ["test-agent"]
        
        mock_workflow_service.generate_from_document = AsyncMock(return_value=mock_result)
        
        # Make request
        response = client.post(
            "/api/v1/ai-workflows/upload",
            files={"file": ("test.txt", b"Test content", "text/plain")}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestChatSessionEndpoints:
    """Tests for chat session endpoints."""
    
    @patch('api.routes.ai_workflows.ChatSessionManager')
    @patch('api.routes.ai_workflows.get_db')
    def test_create_chat_session(self, mock_get_db, mock_manager_class, client):
        """Test creating a new chat session."""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.user_id = None
        mock_session.status = "active"
        mock_session.created_at = datetime.utcnow()
        mock_session.updated_at = datetime.utcnow()
        mock_session.expires_at = datetime.utcnow() + timedelta(minutes=30)
        mock_session.messages = []
        mock_session.current_workflow = None
        mock_session.workflow_history = []
        
        mock_manager.create_session = AsyncMock(return_value=mock_session)
        
        # Make request
        response = client.post(
            "/api/v1/ai-workflows/chat/sessions",
            json={}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert "id" in data
    
    @patch('api.routes.ai_workflows.ChatSessionManager')
    @patch('api.routes.ai_workflows.get_db')
    def test_get_chat_session(self, mock_get_db, mock_manager_class, client):
        """Test retrieving a chat session."""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.user_id = None
        mock_session.status = "active"
        mock_session.created_at = datetime.utcnow()
        mock_session.updated_at = datetime.utcnow()
        mock_session.expires_at = datetime.utcnow() + timedelta(minutes=30)
        mock_session.messages = []
        mock_session.current_workflow = None
        mock_session.workflow_history = []
        
        mock_manager.get_session = AsyncMock(return_value=mock_session)
        
        # Make request
        response = client.get(f"/api/v1/ai-workflows/chat/sessions/{session_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
    
    @patch('api.routes.ai_workflows.ChatSessionManager')
    @patch('api.routes.ai_workflows.get_db')
    def test_delete_chat_session(self, mock_get_db, mock_manager_class, client):
        """Test deleting a chat session."""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        
        mock_manager.get_session = AsyncMock(return_value=mock_session)
        mock_manager.delete_session = AsyncMock()
        
        # Make request
        response = client.delete(f"/api/v1/ai-workflows/chat/sessions/{session_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"]


class TestWorkflowExportEndpoint:
    """Tests for workflow export endpoint."""
    
    @patch('api.routes.ai_workflows.ChatSessionManager')
    @patch('api.routes.ai_workflows.get_db')
    def test_export_workflow(self, mock_get_db, mock_manager_class, client):
        """Test exporting workflow JSON from session."""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.current_workflow = {
            "name": "test-workflow",
            "steps": {}
        }
        
        mock_manager.get_session = AsyncMock(return_value=mock_session)
        
        # Make request
        response = client.get(f"/api/v1/ai-workflows/chat/sessions/{session_id}/export")
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers.get("content-disposition", "")
        data = response.json()
        assert data["name"] == "test-workflow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

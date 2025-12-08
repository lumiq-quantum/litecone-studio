"""Tests for workflow save functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import httpx

from api.services.ai_workflow_generator.workflow_api_client import WorkflowAPIClient
from api.services.ai_workflow_generator.workflow_generation import WorkflowGenerationService
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def sample_workflow():
    """Create a sample workflow JSON."""
    return {
        "name": "test-workflow",
        "start_step": "step1",
        "steps": {
            "step1": {
                "id": "step1",
                "type": "agent",
                "agent_name": "test-agent",
                "input_mapping": {
                    "data": "${workflow.input.data}"
                },
                "next_step": None
            }
        }
    }


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client."""
    return AsyncMock()


class TestWorkflowAPIClient:
    """Tests for WorkflowAPIClient."""
    
    def test_generate_unique_name_no_conflict(self):
        """Test unique name generation without conflict."""
        client = WorkflowAPIClient()
        
        # First attempt should return base name
        name = client._generate_unique_name("my-workflow", 0)
        assert name == "my-workflow"
    
    def test_generate_unique_name_with_conflict(self):
        """Test unique name generation with conflict."""
        client = WorkflowAPIClient()
        
        # Subsequent attempts should add suffix
        name = client._generate_unique_name("my-workflow", 1)
        assert name == "my-workflow-1"
        
        name = client._generate_unique_name("my-workflow", 2)
        assert name == "my-workflow-2"
    
    @pytest.mark.asyncio
    async def test_create_workflow_success(self, sample_workflow):
        """Test successful workflow creation."""
        client = WorkflowAPIClient()
        workflow_id = uuid4()
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": str(workflow_id),
            "name": "test-workflow",
            "version": 1,
            "status": "active"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            # Execute
            result = await client.create_workflow(
                workflow_json=sample_workflow,
                name="test-workflow",
                description="Test workflow"
            )
            
            # Assert
            assert result["workflow_id"] == str(workflow_id)
            assert result["name"] == "test-workflow"
            assert result["version"] == 1
            assert "link" in result
            assert result["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_create_workflow_name_conflict_retry(self, sample_workflow):
        """Test workflow creation with name conflict and retry."""
        client = WorkflowAPIClient()
        workflow_id = uuid4()
        
        # Mock first response with conflict, second with success
        conflict_response = MagicMock()
        conflict_response.status_code = 400
        conflict_response.json.return_value = {
            "detail": "Workflow name already exists"
        }
        
        success_response = MagicMock()
        success_response.status_code = 201
        success_response.json.return_value = {
            "id": str(workflow_id),
            "name": "test-workflow-1",
            "version": 1,
            "status": "active"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.side_effect = [conflict_response, success_response]
            mock_client_class.return_value = mock_client
            
            # Execute
            result = await client.create_workflow(
                workflow_json=sample_workflow,
                name="test-workflow",
                description="Test workflow"
            )
            
            # Assert
            assert result["workflow_id"] == str(workflow_id)
            assert result["name"] == "test-workflow-1"  # Name was modified
            assert mock_client.post.call_count == 2  # Retried once
    
    @pytest.mark.asyncio
    async def test_create_workflow_validation_error(self, sample_workflow):
        """Test workflow creation with validation error (no retry)."""
        client = WorkflowAPIClient()
        
        # Mock validation error response
        error_response = MagicMock()
        error_response.status_code = 400
        error_response.json.return_value = {
            "detail": "Invalid workflow structure: missing start_step"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = error_response
            mock_client_class.return_value = mock_client
            
            # Execute and expect exception
            with pytest.raises(ValueError) as exc_info:
                await client.create_workflow(
                    workflow_json=sample_workflow,
                    name="test-workflow",
                    description="Test workflow"
                )
            
            # Assert
            assert "validation failed" in str(exc_info.value).lower()
            assert mock_client.post.call_count == 1  # No retry
    
    @pytest.mark.asyncio
    async def test_create_workflow_max_retries_exceeded(self, sample_workflow):
        """Test workflow creation when max retries are exceeded."""
        client = WorkflowAPIClient()
        
        # Mock conflict response for all attempts
        conflict_response = MagicMock()
        conflict_response.status_code = 400
        conflict_response.json.return_value = {
            "detail": "Workflow name already exists"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = conflict_response
            mock_client_class.return_value = mock_client
            
            # Execute and expect exception
            with pytest.raises(ValueError) as exc_info:
                await client.create_workflow(
                    workflow_json=sample_workflow,
                    name="test-workflow",
                    description="Test workflow",
                    max_retries=3
                )
            
            # Assert
            assert "Failed to create workflow after 3 attempts" in str(exc_info.value)
            assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_create_workflow_timeout(self, sample_workflow):
        """Test workflow creation with timeout error."""
        client = WorkflowAPIClient()
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value = mock_client
            
            # Execute and expect exception
            with pytest.raises(ValueError) as exc_info:
                await client.create_workflow(
                    workflow_json=sample_workflow,
                    name="test-workflow",
                    description="Test workflow"
                )
            
            # Assert
            assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_workflow_connection_error(self, sample_workflow):
        """Test workflow creation with connection error."""
        client = WorkflowAPIClient()
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.side_effect = httpx.RequestError("Connection refused")
            mock_client_class.return_value = mock_client
            
            # Execute and expect exception
            with pytest.raises(ValueError) as exc_info:
                await client.create_workflow(
                    workflow_json=sample_workflow,
                    name="test-workflow",
                    description="Test workflow"
                )
            
            # Assert
            assert "Failed to connect" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_workflow_success(self):
        """Test successful workflow retrieval."""
        client = WorkflowAPIClient()
        workflow_id = uuid4()
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": str(workflow_id),
            "name": "test-workflow",
            "version": 1
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            # Execute
            result = await client.get_workflow(workflow_id)
            
            # Assert
            assert result is not None
            assert result["id"] == str(workflow_id)
            assert result["name"] == "test-workflow"
    
    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self):
        """Test workflow retrieval when workflow not found."""
        client = WorkflowAPIClient()
        workflow_id = uuid4()
        
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            # Execute
            result = await client.get_workflow(workflow_id)
            
            # Assert
            assert result is None


class TestWorkflowGenerationServiceSave:
    """Tests for WorkflowGenerationService.save_workflow method."""
    
    @pytest.mark.asyncio
    async def test_save_workflow_success(self, sample_workflow):
        """Test successful workflow save."""
        mock_db = MagicMock(spec=AsyncSession)
        service = WorkflowGenerationService(mock_db)
        workflow_id = uuid4()
        
        # Mock the API client
        with patch("api.services.ai_workflow_generator.workflow_api_client.WorkflowAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.create_workflow.return_value = {
                "workflow_id": str(workflow_id),
                "name": "test-workflow",
                "version": 1,
                "link": f"http://localhost:8000/api/v1/workflows/{workflow_id}",
                "status": "active"
            }
            mock_client_class.return_value = mock_client
            
            # Execute
            result = await service.save_workflow(
                workflow_json=sample_workflow,
                name="test-workflow",
                description="Test workflow"
            )
            
            # Assert
            assert result["workflow_id"] == str(workflow_id)
            assert result["name"] == "test-workflow"
            assert result["version"] == 1
            assert "link" in result
            mock_client.create_workflow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_workflow_failure(self, sample_workflow):
        """Test workflow save failure."""
        mock_db = MagicMock(spec=AsyncSession)
        service = WorkflowGenerationService(mock_db)
        
        # Mock the API client to raise error
        with patch("api.services.ai_workflow_generator.workflow_api_client.WorkflowAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.create_workflow.side_effect = ValueError("API error")
            mock_client_class.return_value = mock_client
            
            # Execute and expect exception
            with pytest.raises(ValueError) as exc_info:
                await service.save_workflow(
                    workflow_json=sample_workflow,
                    name="test-workflow",
                    description="Test workflow"
                )
            
            # Assert
            assert "API error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_save_workflow_with_name_conflict_resolution(self, sample_workflow):
        """Test workflow save with automatic name conflict resolution."""
        mock_db = MagicMock(spec=AsyncSession)
        service = WorkflowGenerationService(mock_db)
        workflow_id = uuid4()
        
        # Mock the API client
        with patch("api.services.ai_workflow_generator.workflow_api_client.WorkflowAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            # Return result with modified name (conflict was resolved)
            mock_client.create_workflow.return_value = {
                "workflow_id": str(workflow_id),
                "name": "test-workflow-1",  # Name was modified
                "version": 1,
                "link": f"http://localhost:8000/api/v1/workflows/{workflow_id}",
                "status": "active"
            }
            mock_client_class.return_value = mock_client
            
            # Execute
            result = await service.save_workflow(
                workflow_json=sample_workflow,
                name="test-workflow",
                description="Test workflow"
            )
            
            # Assert
            assert result["workflow_id"] == str(workflow_id)
            assert result["name"] == "test-workflow-1"  # Name was modified
            assert result["version"] == 1


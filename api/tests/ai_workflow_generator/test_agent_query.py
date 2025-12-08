"""Unit tests for Agent Query Service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.ai_workflow_generator.agent_query import (
    AgentQueryService,
    AgentMetadata
)
from api.models.agent import Agent


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def sample_agents():
    """Create sample agent models for testing."""
    return [
        Agent(
            name="data-processor",
            url="http://localhost:8001",
            description="Processes and transforms data files including JSON, CSV, and XML formats",
            status="active"
        ),
        Agent(
            name="email-sender",
            url="http://localhost:8002",
            description="Sends email notifications to users with customizable templates",
            status="active"
        ),
        Agent(
            name="image-analyzer",
            url="http://localhost:8003",
            description="Analyzes images and extracts metadata, performs object detection",
            status="active"
        ),
        Agent(
            name="inactive-agent",
            url="http://localhost:8004",
            description="An inactive agent for testing",
            status="inactive"
        )
    ]


@pytest.fixture
def agent_query_service(mock_db_session):
    """Create an AgentQueryService instance."""
    return AgentQueryService(mock_db_session)


class TestAgentMetadata:
    """Tests for AgentMetadata class."""
    
    def test_agent_metadata_initialization(self):
        """Test AgentMetadata can be initialized with all fields."""
        metadata = AgentMetadata(
            name="test-agent",
            description="A test agent",
            url="http://localhost:8000",
            capabilities=["process", "data"],
            status="active"
        )
        
        assert metadata.name == "test-agent"
        assert metadata.description == "A test agent"
        assert metadata.url == "http://localhost:8000"
        assert metadata.capabilities == ["process", "data"]
        assert metadata.status == "active"
    
    def test_agent_metadata_to_dict(self):
        """Test AgentMetadata can be converted to dictionary."""
        metadata = AgentMetadata(
            name="test-agent",
            description="A test agent",
            url="http://localhost:8000",
            capabilities=["process", "data"],
            status="active"
        )
        
        result = metadata.to_dict()
        
        assert result["name"] == "test-agent"
        assert result["description"] == "A test agent"
        assert result["url"] == "http://localhost:8000"
        assert result["capabilities"] == ["process", "data"]
        assert result["status"] == "active"
    
    def test_extract_capabilities_from_description(self):
        """Test capability extraction from agent description."""
        description = "Processes data files and handles authentication for users"
        capabilities = AgentMetadata._extract_capabilities(description)
        
        assert "process" in capabilities
        assert "handle" in capabilities
        assert "data" in capabilities
        assert "authentication" in capabilities
    
    def test_extract_capabilities_empty_description(self):
        """Test capability extraction with empty description."""
        capabilities = AgentMetadata._extract_capabilities("")
        assert capabilities == []
    
    def test_extract_capabilities_no_matches(self):
        """Test capability extraction with no matching patterns."""
        description = "This is a simple description without keywords"
        capabilities = AgentMetadata._extract_capabilities(description)
        # Should still extract some basic keywords
        assert isinstance(capabilities, list)
    
    def test_from_agent_model(self, sample_agents):
        """Test creating AgentMetadata from Agent model."""
        agent = sample_agents[0]
        metadata = AgentMetadata.from_agent(agent)
        
        assert metadata.name == agent.name
        assert metadata.description == agent.description
        assert metadata.url == agent.url
        assert metadata.status == agent.status
        assert isinstance(metadata.capabilities, list)


class TestAgentQueryService:
    """Tests for AgentQueryService class."""
    
    @pytest.mark.asyncio
    async def test_get_all_agents(self, agent_query_service, sample_agents, mock_db_session):
        """Test retrieving all agents from registry."""
        # Mock repository list method
        with patch.object(agent_query_service.repository, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = sample_agents[:3]  # Only active agents
            
            result = await agent_query_service.get_all_agents(status="active")
            
            assert len(result) == 3
            assert all(isinstance(agent, AgentMetadata) for agent in result)
            assert result[0].name == "data-processor"
            assert result[1].name == "email-sender"
            assert result[2].name == "image-analyzer"
            mock_list.assert_called_once_with(status="active", limit=1000)
    
    @pytest.mark.asyncio
    async def test_get_all_agents_with_caching(self, agent_query_service, sample_agents):
        """Test that get_all_agents uses caching."""
        with patch.object(agent_query_service.repository, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = sample_agents[:3]
            
            # First call - should hit database
            result1 = await agent_query_service.get_all_agents(status="active")
            assert len(result1) == 3
            assert mock_list.call_count == 1
            
            # Second call - should use cache
            result2 = await agent_query_service.get_all_agents(status="active")
            assert len(result2) == 3
            assert mock_list.call_count == 1  # Still 1, not called again
            
            # Results should be the same
            assert result1 == result2
    
    @pytest.mark.asyncio
    async def test_get_all_agents_cache_expiration(self, agent_query_service, sample_agents):
        """Test that cache expires after TTL."""
        with patch.object(agent_query_service.repository, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = sample_agents[:3]
            
            # First call
            await agent_query_service.get_all_agents(status="active")
            assert mock_list.call_count == 1
            
            # Simulate cache expiration by manipulating timestamp
            cache_key = "agents_active"
            agent_query_service._cache_timestamps[cache_key] = datetime.utcnow() - timedelta(seconds=400)
            
            # Second call - should hit database again
            await agent_query_service.get_all_agents(status="active")
            assert mock_list.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_agent_details(self, agent_query_service, sample_agents):
        """Test retrieving specific agent details."""
        with patch.object(agent_query_service.repository, 'get_by_name', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_agents[0]
            
            result = await agent_query_service.get_agent_details("data-processor")
            
            assert result is not None
            assert isinstance(result, AgentMetadata)
            assert result.name == "data-processor"
            assert result.url == "http://localhost:8001"
            mock_get.assert_called_once_with("data-processor")
    
    @pytest.mark.asyncio
    async def test_get_agent_details_not_found(self, agent_query_service):
        """Test retrieving non-existent agent."""
        with patch.object(agent_query_service.repository, 'get_by_name', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await agent_query_service.get_agent_details("non-existent")
            
            assert result is None
            mock_get.assert_called_once_with("non-existent")
    
    @pytest.mark.asyncio
    async def test_get_agent_details_with_caching(self, agent_query_service, sample_agents):
        """Test that get_agent_details uses caching."""
        with patch.object(agent_query_service.repository, 'get_by_name', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_agents[0]
            
            # First call
            result1 = await agent_query_service.get_agent_details("data-processor")
            assert mock_get.call_count == 1
            
            # Second call - should use cache
            result2 = await agent_query_service.get_agent_details("data-processor")
            assert mock_get.call_count == 1  # Not called again
            
            assert result1.name == result2.name
    
    @pytest.mark.asyncio
    async def test_find_agents_by_capability_exact_match(self, agent_query_service, sample_agents):
        """Test finding agents by capability with exact matches."""
        with patch.object(agent_query_service, 'get_all_agents', new_callable=AsyncMock) as mock_get_all:
            agent_metadata = [AgentMetadata.from_agent(agent) for agent in sample_agents[:3]]
            mock_get_all.return_value = agent_metadata
            
            result = await agent_query_service.find_agents_by_capability("process data")
            
            # data-processor should be first due to high relevance
            assert len(result) > 0
            assert result[0].name == "data-processor"
    
    @pytest.mark.asyncio
    async def test_find_agents_by_capability_partial_match(self, agent_query_service, sample_agents):
        """Test finding agents by capability with partial matches."""
        with patch.object(agent_query_service, 'get_all_agents', new_callable=AsyncMock) as mock_get_all:
            agent_metadata = [AgentMetadata.from_agent(agent) for agent in sample_agents[:3]]
            mock_get_all.return_value = agent_metadata
            
            result = await agent_query_service.find_agents_by_capability("email")
            
            # email-sender should be in results
            assert any(agent.name == "email-sender" for agent in result)
    
    @pytest.mark.asyncio
    async def test_find_agents_by_capability_no_match(self, agent_query_service, sample_agents):
        """Test finding agents with no matching capability."""
        with patch.object(agent_query_service, 'get_all_agents', new_callable=AsyncMock) as mock_get_all:
            agent_metadata = [AgentMetadata.from_agent(agent) for agent in sample_agents[:3]]
            mock_get_all.return_value = agent_metadata
            
            result = await agent_query_service.find_agents_by_capability("quantum computing")
            
            # Should return empty list for no matches
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_find_agents_by_capability_empty_description(self, agent_query_service, sample_agents):
        """Test finding agents with empty capability description."""
        with patch.object(agent_query_service, 'get_all_agents', new_callable=AsyncMock) as mock_get_all:
            agent_metadata = [AgentMetadata.from_agent(agent) for agent in sample_agents[:3]]
            mock_get_all.return_value = agent_metadata
            
            result = await agent_query_service.find_agents_by_capability("")
            
            # Should return all agents when no filter provided
            assert len(result) == 3
    
    def test_format_agents_for_llm_with_agents(self, agent_query_service):
        """Test formatting agents for LLM prompt."""
        agents = [
            AgentMetadata(
                name="test-agent-1",
                description="First test agent",
                url="http://localhost:8001",
                capabilities=["process", "data"],
                status="active"
            ),
            AgentMetadata(
                name="test-agent-2",
                description="Second test agent",
                url="http://localhost:8002",
                capabilities=["send", "email"],
                status="active"
            )
        ]
        
        result = agent_query_service.format_agents_for_llm(agents)
        
        assert "Available Agents:" in result
        assert "test-agent-1" in result
        assert "test-agent-2" in result
        assert "http://localhost:8001" in result
        assert "http://localhost:8002" in result
        assert "First test agent" in result
        assert "Second test agent" in result
        assert "process, data" in result
        assert "send, email" in result
    
    def test_format_agents_for_llm_empty_list(self, agent_query_service):
        """Test formatting empty agent list for LLM."""
        result = agent_query_service.format_agents_for_llm([])
        assert result == "No agents available."
    
    def test_format_agents_for_llm_without_description(self, agent_query_service):
        """Test formatting agents without descriptions."""
        agents = [
            AgentMetadata(
                name="test-agent",
                description=None,
                url="http://localhost:8001",
                capabilities=["process"],
                status="active"
            )
        ]
        
        result = agent_query_service.format_agents_for_llm(agents)
        
        assert "test-agent" in result
        assert "http://localhost:8001" in result
        # Description line should not be present
        assert "Description:" not in result
    
    def test_cache_operations(self, agent_query_service):
        """Test cache set, get, and validation operations."""
        # Test setting cache
        agent_query_service._set_cache("test_key", "test_value")
        assert agent_query_service._is_cache_valid("test_key")
        assert agent_query_service._get_from_cache("test_key") == "test_value"
        
        # Test cache expiration
        agent_query_service._cache_timestamps["test_key"] = datetime.utcnow() - timedelta(seconds=400)
        assert not agent_query_service._is_cache_valid("test_key")
        assert agent_query_service._get_from_cache("test_key") is None
        
        # Test clear cache
        agent_query_service._set_cache("key1", "value1")
        agent_query_service._set_cache("key2", "value2")
        agent_query_service._clear_cache()
        assert len(agent_query_service._cache) == 0
        assert len(agent_query_service._cache_timestamps) == 0

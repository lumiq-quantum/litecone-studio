"""Integration tests for Agent Suggestion feature."""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.ai_workflow_generator.workflow_generation import WorkflowGenerationService
from api.services.ai_workflow_generator.agent_query import AgentMetadata
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
            name="pdf-processor",
            url="http://localhost:8003",
            description="Processes PDF documents and extracts text content",
            status="active"
        )
    ]


class TestAgentSuggestionIntegration:
    """Integration tests for agent suggestion functionality."""
    
    @pytest.mark.asyncio
    async def test_suggest_agents_clear_match_integration(self, mock_db_session, sample_agents):
        """Test full agent suggestion flow with clear match."""
        # Create workflow generation service
        service = WorkflowGenerationService(mock_db_session)
        
        # Mock the agent query to return sample agents
        with patch.object(service.agent_query_service.repository, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = sample_agents
            
            # Request suggestions for email capability
            result = await service.suggest_agents_for_capability(
                capability_description="send email notifications"
            )
            
            # Verify result structure
            assert result is not None
            assert len(result.suggestions) > 0
            
            # Should select email-sender as best match
            assert result.suggestions[0].agent.name == "email-sender"
            
            # Should not be ambiguous
            assert not result.is_ambiguous
            assert not result.requires_user_choice
            assert not result.no_match
            
            # Should include agent description (Requirement 4.4)
            assert result.suggestions[0].agent.description is not None
            assert "email" in result.explanation.lower()
    
    @pytest.mark.asyncio
    async def test_suggest_agents_ambiguous_match_integration(self, mock_db_session, sample_agents):
        """Test full agent suggestion flow with ambiguous matches."""
        # Create workflow generation service
        service = WorkflowGenerationService(mock_db_session)
        
        # Mock the agent query to return sample agents
        with patch.object(service.agent_query_service.repository, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = sample_agents
            
            # Request suggestions for processing capability (both data-processor and pdf-processor match)
            result = await service.suggest_agents_for_capability(
                capability_description="process documents"
            )
            
            # Verify result structure
            assert result is not None
            assert len(result.suggestions) >= 2
            
            # Should be marked as ambiguous (Requirement 4.5)
            assert result.is_ambiguous
            assert result.requires_user_choice
            assert not result.no_match
            
            # Should include multiple agent descriptions (Requirement 4.4)
            for suggestion in result.suggestions[:2]:
                assert suggestion.agent.description is not None
            
            # Explanation should indicate choice is needed
            assert "choose" in result.explanation.lower() or "multiple" in result.explanation.lower()
    
    @pytest.mark.asyncio
    async def test_suggest_agents_no_match_integration(self, mock_db_session, sample_agents):
        """Test full agent suggestion flow with no matches."""
        # Create workflow generation service
        service = WorkflowGenerationService(mock_db_session)
        
        # Mock the agent query to return sample agents
        with patch.object(service.agent_query_service.repository, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = sample_agents
            
            # Request suggestions for capability that doesn't match any agent
            result = await service.suggest_agents_for_capability(
                capability_description="quantum computing blockchain"
            )
            
            # Verify result structure
            assert result is not None
            
            # Should have no suggestions
            assert len(result.suggestions) == 0
            
            # Should be marked as no match (Requirement 4.3)
            assert result.no_match
            assert not result.is_ambiguous
            assert not result.requires_user_choice
            
            # Should provide alternatives (Requirement 4.3)
            assert len(result.alternatives) > 0
            assert any("custom agent" in alt.lower() for alt in result.alternatives)
            assert any("available agents" in alt.lower() for alt in result.alternatives)
    
    @pytest.mark.asyncio
    async def test_suggest_agents_includes_all_metadata(self, mock_db_session, sample_agents):
        """Test that suggestions include all required metadata."""
        # Create workflow generation service
        service = WorkflowGenerationService(mock_db_session)
        
        # Mock the agent query to return sample agents
        with patch.object(service.agent_query_service.repository, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = sample_agents
            
            # Request suggestions
            result = await service.suggest_agents_for_capability(
                capability_description="process data"
            )
            
            # Verify all suggestions have complete metadata
            for suggestion in result.suggestions:
                assert suggestion.agent.name is not None
                assert suggestion.agent.url is not None
                assert suggestion.agent.status == "active"
                assert suggestion.relevance_score >= 0
                assert suggestion.reason is not None
                
                # Should include capabilities (Requirement 4.4)
                assert isinstance(suggestion.agent.capabilities, list)
    
    @pytest.mark.asyncio
    async def test_suggest_agents_with_no_active_agents(self, mock_db_session):
        """Test agent suggestion when no active agents are available."""
        # Create workflow generation service
        service = WorkflowGenerationService(mock_db_session)
        
        # Mock the agent query to return empty list
        with patch.object(service.agent_query_service.repository, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = []
            
            # Request suggestions
            result = await service.suggest_agents_for_capability(
                capability_description="process data"
            )
            
            # Should indicate no match
            assert result.no_match
            assert len(result.suggestions) == 0
            
            # Should provide alternatives
            assert len(result.alternatives) > 0
    
    @pytest.mark.asyncio
    async def test_suggest_agents_caching_behavior(self, mock_db_session, sample_agents):
        """Test that agent suggestions use cached agent data."""
        # Create workflow generation service
        service = WorkflowGenerationService(mock_db_session)
        
        # Mock the agent query to return sample agents
        with patch.object(service.agent_query_service.repository, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = sample_agents
            
            # First request
            result1 = await service.suggest_agents_for_capability(
                capability_description="send email"
            )
            
            # Second request - should use cache
            result2 = await service.suggest_agents_for_capability(
                capability_description="send email"
            )
            
            # Should only query database once due to caching
            assert mock_list.call_count == 1
            
            # Results should be consistent
            assert result1.suggestions[0].agent.name == result2.suggestions[0].agent.name

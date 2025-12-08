"""Unit tests for Agent Suggestion Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from api.services.ai_workflow_generator.agent_suggestion import (
    AgentSuggestionService,
    AgentSuggestion,
    AgentSuggestionResult
)
from api.services.ai_workflow_generator.agent_query import AgentMetadata


@pytest.fixture
def agent_suggestion_service():
    """Create an AgentSuggestionService instance."""
    return AgentSuggestionService()


@pytest.fixture
def sample_agents():
    """Create sample agent metadata for testing."""
    return [
        AgentMetadata(
            name="data-processor",
            description="Processes and transforms data files including JSON, CSV, and XML formats",
            url="http://localhost:8001",
            capabilities=["process", "transform", "data", "json", "csv", "xml"],
            status="active"
        ),
        AgentMetadata(
            name="email-sender",
            description="Sends email notifications to users with customizable templates",
            url="http://localhost:8002",
            capabilities=["send", "email", "notification", "user"],
            status="active"
        ),
        AgentMetadata(
            name="image-analyzer",
            description="Analyzes images and extracts metadata, performs object detection",
            url="http://localhost:8003",
            capabilities=["analyze", "image", "extract", "perform"],
            status="active"
        ),
        AgentMetadata(
            name="pdf-processor",
            description="Processes PDF documents and extracts text content",
            url="http://localhost:8004",
            capabilities=["process", "pdf", "document", "extract", "text"],
            status="active"
        ),
        AgentMetadata(
            name="generic-handler",
            description="Generic agent that can handle various tasks",
            url="http://localhost:8005",
            capabilities=["handle", "generic"],
            status="active"
        )
    ]


class TestAgentSuggestion:
    """Tests for AgentSuggestion dataclass."""
    
    def test_agent_suggestion_initialization(self, sample_agents):
        """Test AgentSuggestion can be initialized."""
        suggestion = AgentSuggestion(
            agent=sample_agents[0],
            relevance_score=85.0,
            reason="Agent matches required capabilities"
        )
        
        assert suggestion.agent.name == "data-processor"
        assert suggestion.relevance_score == 85.0
        assert suggestion.reason == "Agent matches required capabilities"
    
    def test_agent_suggestion_to_dict(self, sample_agents):
        """Test AgentSuggestion can be converted to dictionary."""
        suggestion = AgentSuggestion(
            agent=sample_agents[0],
            relevance_score=85.0,
            reason="Agent matches required capabilities"
        )
        
        result = suggestion.to_dict()
        
        assert "agent" in result
        assert result["relevance_score"] == 85.0
        assert result["reason"] == "Agent matches required capabilities"
        assert result["agent"]["name"] == "data-processor"


class TestAgentSuggestionResult:
    """Tests for AgentSuggestionResult dataclass."""
    
    def test_agent_suggestion_result_initialization(self, sample_agents):
        """Test AgentSuggestionResult can be initialized."""
        suggestions = [
            AgentSuggestion(sample_agents[0], 85.0, "Good match")
        ]
        
        result = AgentSuggestionResult(
            suggestions=suggestions,
            is_ambiguous=False,
            requires_user_choice=False,
            no_match=False,
            alternatives=[],
            explanation="Selected best agent"
        )
        
        assert len(result.suggestions) == 1
        assert not result.is_ambiguous
        assert not result.requires_user_choice
        assert not result.no_match
        assert result.explanation == "Selected best agent"
    
    def test_agent_suggestion_result_to_dict(self, sample_agents):
        """Test AgentSuggestionResult can be converted to dictionary."""
        suggestions = [
            AgentSuggestion(sample_agents[0], 85.0, "Good match")
        ]
        
        result = AgentSuggestionResult(
            suggestions=suggestions,
            is_ambiguous=False,
            requires_user_choice=False,
            no_match=False,
            alternatives=[],
            explanation="Selected best agent"
        )
        
        dict_result = result.to_dict()
        
        assert "suggestions" in dict_result
        assert "is_ambiguous" in dict_result
        assert "requires_user_choice" in dict_result
        assert "no_match" in dict_result
        assert "alternatives" in dict_result
        assert "explanation" in dict_result


class TestAgentSuggestionService:
    """Tests for AgentSuggestionService class."""
    
    def test_calculate_relevance_score_high_match(self, agent_suggestion_service, sample_agents):
        """Test relevance score calculation with high match."""
        agent = sample_agents[0]  # data-processor
        capability_description = "process data files"
        keywords = {"process", "data", "files"}
        
        score, reason = agent_suggestion_service.calculate_relevance_score(
            agent, capability_description, keywords
        )
        
        # Should have high score due to capability and name matches
        assert score > 30.0
        assert "capabilities" in reason or "name" in reason
    
    def test_calculate_relevance_score_low_match(self, agent_suggestion_service, sample_agents):
        """Test relevance score calculation with low match."""
        agent = sample_agents[1]  # email-sender
        capability_description = "process data files"
        keywords = {"process", "data", "files"}
        
        score, reason = agent_suggestion_service.calculate_relevance_score(
            agent, capability_description, keywords
        )
        
        # Should have low or zero score
        assert score < 50.0
    
    def test_calculate_relevance_score_no_match(self, agent_suggestion_service, sample_agents):
        """Test relevance score calculation with no match."""
        agent = sample_agents[1]  # email-sender
        capability_description = "quantum computing"
        keywords = {"quantum", "computing"}
        
        score, reason = agent_suggestion_service.calculate_relevance_score(
            agent, capability_description, keywords
        )
        
        # Should have very low or zero score
        assert score < 30.0
    
    def test_score_agents_sorts_by_relevance(self, agent_suggestion_service, sample_agents):
        """Test that score_agents sorts agents by relevance."""
        capability_description = "process data files"
        
        suggestions = agent_suggestion_service.score_agents(
            agents=sample_agents,
            capability_description=capability_description
        )
        
        # Should return suggestions sorted by score
        assert len(suggestions) > 0
        
        # Verify sorting (scores should be descending)
        for i in range(len(suggestions) - 1):
            assert suggestions[i].relevance_score >= suggestions[i + 1].relevance_score
    
    def test_score_agents_filters_low_scores(self, agent_suggestion_service, sample_agents):
        """Test that score_agents filters out low-scoring agents."""
        capability_description = "quantum computing blockchain AI"
        
        suggestions = agent_suggestion_service.score_agents(
            agents=sample_agents,
            capability_description=capability_description
        )
        
        # Should filter out agents with scores below threshold
        for suggestion in suggestions:
            assert suggestion.relevance_score >= agent_suggestion_service.MIN_RELEVANCE_SCORE
    
    def test_score_agents_limits_results(self, agent_suggestion_service):
        """Test that score_agents limits number of results."""
        # Create many agents
        many_agents = [
            AgentMetadata(
                name=f"agent-{i}",
                description=f"Agent {i} that processes data",
                url=f"http://localhost:800{i}",
                capabilities=["process", "data"],
                status="active"
            )
            for i in range(20)
        ]
        
        capability_description = "process data"
        
        suggestions = agent_suggestion_service.score_agents(
            agents=many_agents,
            capability_description=capability_description
        )
        
        # Should limit to MAX_SUGGESTIONS
        assert len(suggestions) <= agent_suggestion_service.MAX_SUGGESTIONS
    
    def test_is_ambiguous_selection_true(self, agent_suggestion_service, sample_agents):
        """Test ambiguity detection with similar scores."""
        suggestions = [
            AgentSuggestion(sample_agents[0], 90.0, "Good match"),
            AgentSuggestion(sample_agents[1], 85.0, "Also good match")
        ]
        
        is_ambiguous = agent_suggestion_service.is_ambiguous_selection(suggestions)
        
        # Scores are within threshold, should be ambiguous
        assert is_ambiguous
    
    def test_is_ambiguous_selection_false(self, agent_suggestion_service, sample_agents):
        """Test ambiguity detection with different scores."""
        suggestions = [
            AgentSuggestion(sample_agents[0], 90.0, "Good match"),
            AgentSuggestion(sample_agents[1], 50.0, "Weak match")
        ]
        
        is_ambiguous = agent_suggestion_service.is_ambiguous_selection(suggestions)
        
        # Scores are not within threshold, should not be ambiguous
        assert not is_ambiguous
    
    def test_is_ambiguous_selection_single_agent(self, agent_suggestion_service, sample_agents):
        """Test ambiguity detection with single agent."""
        suggestions = [
            AgentSuggestion(sample_agents[0], 90.0, "Good match")
        ]
        
        is_ambiguous = agent_suggestion_service.is_ambiguous_selection(suggestions)
        
        # Only one agent, cannot be ambiguous
        assert not is_ambiguous
    
    def test_is_ambiguous_selection_empty(self, agent_suggestion_service):
        """Test ambiguity detection with no agents."""
        suggestions = []
        
        is_ambiguous = agent_suggestion_service.is_ambiguous_selection(suggestions)
        
        # No agents, cannot be ambiguous
        assert not is_ambiguous
    
    def test_generate_no_match_alternatives(self, agent_suggestion_service, sample_agents):
        """Test generating alternatives when no match found."""
        capability_description = "quantum computing"
        
        alternatives = agent_suggestion_service.generate_no_match_alternatives(
            capability_description=capability_description,
            available_agents=sample_agents
        )
        
        # Should return list of alternatives
        assert len(alternatives) > 0
        assert any("custom agent" in alt.lower() for alt in alternatives)
        assert any("available agents" in alt.lower() for alt in alternatives)
    
    def test_generate_no_match_alternatives_with_generic(self, agent_suggestion_service, sample_agents):
        """Test alternatives include generic agents if available."""
        capability_description = "some task"
        
        alternatives = agent_suggestion_service.generate_no_match_alternatives(
            capability_description=capability_description,
            available_agents=sample_agents
        )
        
        # Should suggest generic agent
        assert any("generic" in alt.lower() for alt in alternatives)
    
    def test_suggest_agents_clear_match(self, agent_suggestion_service, sample_agents):
        """Test agent suggestion with clear single match."""
        capability_description = "send email notifications"
        
        result = agent_suggestion_service.suggest_agents(
            capability_description=capability_description,
            available_agents=sample_agents
        )
        
        # Should have suggestions
        assert len(result.suggestions) > 0
        
        # Should not be ambiguous
        assert not result.is_ambiguous
        assert not result.requires_user_choice
        assert not result.no_match
        
        # Best match should be email-sender
        assert result.suggestions[0].agent.name == "email-sender"
        
        # Should include agent description in explanation (Requirement 4.4)
        assert result.suggestions[0].agent.description in result.explanation or \
               "email" in result.explanation.lower()
    
    def test_suggest_agents_ambiguous_match(self, agent_suggestion_service, sample_agents):
        """Test agent suggestion with ambiguous matches."""
        # Both data-processor and pdf-processor can process documents
        capability_description = "process documents"
        
        result = agent_suggestion_service.suggest_agents(
            capability_description=capability_description,
            available_agents=sample_agents
        )
        
        # Should have multiple suggestions
        assert len(result.suggestions) >= 2
        
        # Should be marked as ambiguous (Requirement 4.5)
        assert result.is_ambiguous
        assert result.requires_user_choice
        assert not result.no_match
        
        # Explanation should present choices
        assert "choose" in result.explanation.lower() or "multiple" in result.explanation.lower()
        
        # Should include agent descriptions (Requirement 4.4)
        for suggestion in result.suggestions[:2]:
            if suggestion.agent.description:
                assert suggestion.agent.description in result.explanation
    
    def test_suggest_agents_no_match(self, agent_suggestion_service, sample_agents):
        """Test agent suggestion with no matches."""
        capability_description = "quantum computing blockchain"
        
        result = agent_suggestion_service.suggest_agents(
            capability_description=capability_description,
            available_agents=sample_agents
        )
        
        # Should have no suggestions
        assert len(result.suggestions) == 0
        
        # Should be marked as no match (Requirement 4.3)
        assert result.no_match
        assert not result.is_ambiguous
        assert not result.requires_user_choice
        
        # Should provide alternatives (Requirement 4.3)
        assert len(result.alternatives) > 0
        assert any("custom agent" in alt.lower() for alt in result.alternatives)
    
    def test_suggest_agents_includes_capabilities(self, agent_suggestion_service, sample_agents):
        """Test that suggestions include agent capabilities."""
        capability_description = "process data"
        
        result = agent_suggestion_service.suggest_agents(
            capability_description=capability_description,
            available_agents=sample_agents
        )
        
        # Should have suggestions
        assert len(result.suggestions) > 0
        
        # Suggestions should include capabilities
        for suggestion in result.suggestions:
            assert len(suggestion.agent.capabilities) > 0
    
    def test_format_agent_choice_prompt(self, agent_suggestion_service, sample_agents):
        """Test formatting agent choice prompt for users."""
        suggestions = [
            AgentSuggestion(sample_agents[0], 90.0, "Good match"),
            AgentSuggestion(sample_agents[1], 85.0, "Also good")
        ]
        
        result = AgentSuggestionResult(
            suggestions=suggestions,
            is_ambiguous=True,
            requires_user_choice=True,
            no_match=False,
            alternatives=[],
            explanation="Multiple agents available"
        )
        
        prompt = agent_suggestion_service.format_agent_choice_prompt(result)
        
        # Should include agent names
        assert "data-processor" in prompt
        assert "email-sender" in prompt
        
        # Should include choice instructions
        assert "choose" in prompt.lower()
        assert "1." in prompt
        assert "2." in prompt
    
    def test_format_agent_choice_prompt_not_ambiguous(self, agent_suggestion_service, sample_agents):
        """Test formatting prompt when not ambiguous."""
        suggestions = [
            AgentSuggestion(sample_agents[0], 90.0, "Good match")
        ]
        
        result = AgentSuggestionResult(
            suggestions=suggestions,
            is_ambiguous=False,
            requires_user_choice=False,
            no_match=False,
            alternatives=[],
            explanation="Clear match"
        )
        
        prompt = agent_suggestion_service.format_agent_choice_prompt(result)
        
        # Should return empty string when not ambiguous
        assert prompt == ""
    
    def test_format_agent_choice_prompt_truncates_long_descriptions(self, agent_suggestion_service):
        """Test that long descriptions are truncated in prompt."""
        long_description = "A" * 150  # Very long description
        
        agent = AgentMetadata(
            name="test-agent",
            description=long_description,
            url="http://localhost:8000",
            capabilities=["test"],
            status="active"
        )
        
        suggestions = [
            AgentSuggestion(agent, 90.0, "Match")
        ]
        
        result = AgentSuggestionResult(
            suggestions=suggestions,
            is_ambiguous=True,
            requires_user_choice=True,
            no_match=False,
            alternatives=[],
            explanation="Choose"
        )
        
        prompt = agent_suggestion_service.format_agent_choice_prompt(result)
        
        # Should truncate long description
        assert "..." in prompt
        assert len(prompt) < len(long_description) + 200  # Reasonable length

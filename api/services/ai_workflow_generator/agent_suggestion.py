"""Agent suggestion service for handling ambiguous agent selection scenarios."""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .agent_query import AgentMetadata

logger = logging.getLogger(__name__)


@dataclass
class AgentSuggestion:
    """
    Represents a suggested agent with explanation.
    
    Attributes:
        agent: The agent metadata
        relevance_score: Score indicating how well the agent matches (0-100)
        reason: Explanation of why this agent was suggested
    """
    agent: AgentMetadata
    relevance_score: float
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "agent": self.agent.to_dict(),
            "relevance_score": self.relevance_score,
            "reason": self.reason
        }


@dataclass
class AgentSuggestionResult:
    """
    Result of agent suggestion operation.
    
    Attributes:
        suggestions: List of agent suggestions
        is_ambiguous: Whether the selection is ambiguous (multiple good matches)
        requires_user_choice: Whether user input is needed to choose
        no_match: Whether no suitable agents were found
        alternatives: Alternative approaches if no match found
        explanation: Overall explanation of the suggestion result
    """
    suggestions: List[AgentSuggestion]
    is_ambiguous: bool
    requires_user_choice: bool
    no_match: bool
    alternatives: List[str]
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "suggestions": [s.to_dict() for s in self.suggestions],
            "is_ambiguous": self.is_ambiguous,
            "requires_user_choice": self.requires_user_choice,
            "no_match": self.no_match,
            "alternatives": self.alternatives,
            "explanation": self.explanation
        }


class AgentSuggestionService:
    """
    Service for generating agent suggestions in ambiguous scenarios.
    
    This service implements requirements 4.3, 4.4, and 4.5:
    - 4.3: Handle no-match scenarios with alternatives
    - 4.4: Include agent descriptions in suggestions
    - 4.5: Present multi-agent choices for ambiguous cases
    """
    
    # Thresholds for determining ambiguity
    AMBIGUITY_THRESHOLD = 0.8  # If top 2+ agents score within this ratio, it's ambiguous
    MIN_RELEVANCE_SCORE = 30.0  # Minimum score to be considered a match
    MAX_SUGGESTIONS = 5  # Maximum number of suggestions to return
    
    def __init__(self):
        """Initialize the agent suggestion service."""
        logger.info("Initialized AgentSuggestionService")
    
    def calculate_relevance_score(
        self,
        agent: AgentMetadata,
        capability_description: str,
        keywords: set
    ) -> Tuple[float, str]:
        """
        Calculate how relevant an agent is for a given capability.
        
        Args:
            agent: Agent to score
            capability_description: Description of required capability
            keywords: Set of keywords extracted from capability description
            
        Returns:
            Tuple of (score, reason) where score is 0-100 and reason explains the score
        """
        score = 0.0
        reasons = []
        
        # Score based on capability matches
        capability_matches = 0
        for capability in agent.capabilities:
            if capability.lower() in keywords:
                capability_matches += 1
                score += 15.0  # High weight for capability match
        
        if capability_matches > 0:
            reasons.append(f"matches {capability_matches} required capabilities")
        
        # Score based on description matches
        if agent.description:
            desc_lower = agent.description.lower()
            description_matches = 0
            
            for keyword in keywords:
                if keyword in desc_lower:
                    description_matches += 1
                    score += 5.0  # Medium weight for description match
            
            if description_matches > 0:
                reasons.append(f"description mentions {description_matches} relevant keywords")
        
        # Score based on name matches
        name_lower = agent.name.lower()
        name_matches = 0
        for keyword in keywords:
            if keyword in name_lower:
                name_matches += 1
                score += 10.0  # Good weight for name match
        
        if name_matches > 0:
            reasons.append(f"name contains {name_matches} relevant terms")
        
        # Cap score at 100
        score = min(score, 100.0)
        
        # Build reason string
        if reasons:
            reason = "Agent " + ", ".join(reasons)
        else:
            reason = "Agent has no direct matches but may be relevant"
        
        return score, reason
    
    def score_agents(
        self,
        agents: List[AgentMetadata],
        capability_description: str
    ) -> List[AgentSuggestion]:
        """
        Score and rank agents by relevance to a capability.
        
        Args:
            agents: List of agents to score
            capability_description: Description of required capability
            
        Returns:
            List of AgentSuggestion objects, sorted by relevance (highest first)
        """
        import re
        
        # Extract keywords from capability description
        desc_lower = capability_description.lower()
        keywords = set(re.findall(r'\b\w+\b', desc_lower))
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
            'are', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'should', 'could', 'may',
            'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        keywords = keywords - stop_words
        
        # Score each agent
        suggestions = []
        for agent in agents:
            score, reason = self.calculate_relevance_score(agent, capability_description, keywords)
            
            if score >= self.MIN_RELEVANCE_SCORE:
                suggestions.append(AgentSuggestion(
                    agent=agent,
                    relevance_score=score,
                    reason=reason
                ))
        
        # Sort by score (descending)
        suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit to max suggestions
        return suggestions[:self.MAX_SUGGESTIONS]
    
    def is_ambiguous_selection(
        self,
        suggestions: List[AgentSuggestion]
    ) -> bool:
        """
        Determine if agent selection is ambiguous.
        
        Selection is ambiguous when multiple agents have similar high scores,
        making it unclear which one the user intended.
        
        Args:
            suggestions: List of scored agent suggestions
            
        Returns:
            True if selection is ambiguous, False otherwise
        """
        if len(suggestions) < 2:
            return False
        
        # Check if top 2 agents have similar scores
        top_score = suggestions[0].relevance_score
        second_score = suggestions[1].relevance_score
        
        # If second score is within threshold of top score, it's ambiguous
        if top_score == 0:
            return False
        
        score_ratio = second_score / top_score
        return score_ratio >= self.AMBIGUITY_THRESHOLD
    
    def generate_no_match_alternatives(
        self,
        capability_description: str,
        available_agents: List[AgentMetadata]
    ) -> List[str]:
        """
        Generate alternative approaches when no suitable agent is found.
        
        Implements requirement 4.3: suggest alternatives or manual agent creation.
        
        Args:
            capability_description: Description of required capability
            available_agents: List of all available agents
            
        Returns:
            List of alternative suggestions
        """
        alternatives = []
        
        # Suggest manual agent creation
        alternatives.append(
            f"Create a custom agent that can handle: {capability_description}"
        )
        
        # Suggest reviewing available agents
        if available_agents:
            alternatives.append(
                f"Review the {len(available_agents)} available agents to see if any can be adapted"
            )
            
            # Suggest top 3 agents even if they don't match well
            alternatives.append(
                "Consider these agents that might be adaptable: " +
                ", ".join(agent.name for agent in available_agents[:3])
            )
        
        # Suggest breaking down the requirement
        alternatives.append(
            "Break down the requirement into smaller steps that existing agents can handle"
        )
        
        # Suggest using a generic agent if available
        generic_agents = [a for a in available_agents if 'generic' in a.name.lower() or 'general' in a.name.lower()]
        if generic_agents:
            alternatives.append(
                f"Use a generic agent like '{generic_agents[0].name}' and configure it for this task"
            )
        
        return alternatives
    
    def suggest_agents(
        self,
        capability_description: str,
        available_agents: List[AgentMetadata]
    ) -> AgentSuggestionResult:
        """
        Generate agent suggestions for a given capability requirement.
        
        This is the main entry point for agent suggestion logic. It handles:
        - Scoring and ranking agents by relevance
        - Detecting ambiguous selections
        - Handling no-match scenarios
        - Including agent descriptions in suggestions (requirement 4.4)
        - Presenting multi-agent choices (requirement 4.5)
        
        Args:
            capability_description: Description of required capability
            available_agents: List of available agents to choose from
            
        Returns:
            AgentSuggestionResult with suggestions and guidance
        """
        logger.info(f"Generating agent suggestions for: {capability_description[:100]}...")
        
        # Score and rank agents
        suggestions = self.score_agents(available_agents, capability_description)
        
        # Check for no matches
        if not suggestions:
            logger.warning("No suitable agents found for capability")
            alternatives = self.generate_no_match_alternatives(
                capability_description,
                available_agents
            )
            
            explanation = (
                f"No agents were found that match the required capability: '{capability_description}'. "
                f"Consider the following alternatives:"
            )
            
            return AgentSuggestionResult(
                suggestions=[],
                is_ambiguous=False,
                requires_user_choice=False,
                no_match=True,
                alternatives=alternatives,
                explanation=explanation
            )
        
        # Check for ambiguous selection
        is_ambiguous = self.is_ambiguous_selection(suggestions)
        
        if is_ambiguous:
            logger.info(f"Ambiguous agent selection detected with {len(suggestions)} similar matches")
            
            # Build explanation with agent descriptions
            explanation_parts = [
                f"Multiple agents can handle '{capability_description}'. Please choose one:"
            ]
            
            for i, suggestion in enumerate(suggestions[:3], 1):  # Show top 3
                agent = suggestion.agent
                explanation_parts.append(
                    f"\n{i}. {agent.name} (score: {suggestion.relevance_score:.0f})"
                )
                if agent.description:
                    explanation_parts.append(f"   Description: {agent.description}")
                if agent.capabilities:
                    explanation_parts.append(f"   Capabilities: {', '.join(agent.capabilities[:5])}")
                explanation_parts.append(f"   Reason: {suggestion.reason}")
            
            explanation = "".join(explanation_parts)
            
            return AgentSuggestionResult(
                suggestions=suggestions,
                is_ambiguous=True,
                requires_user_choice=True,
                no_match=False,
                alternatives=[],
                explanation=explanation
            )
        
        # Single clear match
        best_suggestion = suggestions[0]
        agent = best_suggestion.agent
        
        logger.info(f"Selected agent '{agent.name}' with score {best_suggestion.relevance_score:.0f}")
        
        # Build explanation including agent description (requirement 4.4)
        explanation_parts = [
            f"Selected agent '{agent.name}' for '{capability_description}'."
        ]
        
        if agent.description:
            explanation_parts.append(f"\nDescription: {agent.description}")
        
        if agent.capabilities:
            explanation_parts.append(f"\nCapabilities: {', '.join(agent.capabilities[:5])}")
        
        explanation_parts.append(f"\nReason: {best_suggestion.reason}")
        
        # Mention alternatives if there are other good matches
        if len(suggestions) > 1:
            other_agents = [s.agent.name for s in suggestions[1:3]]
            explanation_parts.append(
                f"\n\nOther suitable agents: {', '.join(other_agents)}"
            )
        
        explanation = "".join(explanation_parts)
        
        return AgentSuggestionResult(
            suggestions=suggestions,
            is_ambiguous=False,
            requires_user_choice=False,
            no_match=False,
            alternatives=[],
            explanation=explanation
        )
    
    def format_agent_choice_prompt(
        self,
        suggestion_result: AgentSuggestionResult
    ) -> str:
        """
        Format a user-friendly prompt for choosing between agents.
        
        Args:
            suggestion_result: Result containing multiple agent suggestions
            
        Returns:
            Formatted prompt string for user
        """
        if not suggestion_result.is_ambiguous or not suggestion_result.suggestions:
            return ""
        
        lines = ["Please choose an agent:"]
        
        for i, suggestion in enumerate(suggestion_result.suggestions, 1):
            agent = suggestion.agent
            lines.append(f"\n{i}. {agent.name}")
            
            if agent.description:
                # Truncate long descriptions
                desc = agent.description
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                lines.append(f"   {desc}")
            
            lines.append(f"   Match score: {suggestion.relevance_score:.0f}/100")
        
        lines.append("\nEnter the number of your choice (1-{})".format(len(suggestion_result.suggestions)))
        
        return "\n".join(lines)

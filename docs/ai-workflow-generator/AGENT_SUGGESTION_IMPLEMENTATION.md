# Agent Suggestion Feature Implementation

## Overview

This document describes the implementation of the agent suggestion feature for the AI Workflow Generator, which addresses Requirements 4.3, 4.4, and 4.5 from the specification.

## Requirements Implemented

### Requirement 4.3: No-Match Scenario Handling
**WHEN no suitable agent exists THEN the Workflow Generator SHALL inform the user and suggest alternative approaches or manual agent creation**

Implementation:
- `generate_no_match_alternatives()` method generates contextual alternatives when no agents match
- Suggests creating custom agents, reviewing available agents, breaking down requirements, and using generic agents
- Returns structured alternatives list in `AgentSuggestionResult`

### Requirement 4.4: Agent Description Inclusion
**WHEN the Workflow Generator suggests an agent THEN the Workflow Generator SHALL include the agent's description and capabilities in the explanation**

Implementation:
- All `AgentSuggestion` objects include full agent metadata (name, description, URL, capabilities)
- Explanations automatically include agent descriptions and capabilities
- API response schema (`AgentSuggestionItem`) exposes all agent metadata to clients

### Requirement 4.5: Multi-Agent Choice Presentation
**WHEN agent selection is ambiguous THEN the Workflow Generator SHALL ask the user to choose between multiple suitable agents**

Implementation:
- `is_ambiguous_selection()` detects when multiple agents have similar relevance scores
- `AgentSuggestionResult` includes `is_ambiguous` and `requires_user_choice` flags
- `format_agent_choice_prompt()` generates user-friendly choice prompts
- Explanations clearly present multiple options with descriptions and scores

## Components Created

### 1. AgentSuggestionService (`agent_suggestion.py`)

Core service that implements agent suggestion logic:

**Key Methods:**
- `suggest_agents()` - Main entry point for generating suggestions
- `score_agents()` - Scores and ranks agents by relevance
- `calculate_relevance_score()` - Calculates how well an agent matches a capability
- `is_ambiguous_selection()` - Detects ambiguous scenarios
- `generate_no_match_alternatives()` - Generates alternatives when no match found
- `format_agent_choice_prompt()` - Formats user-friendly choice prompts

**Key Classes:**
- `AgentSuggestion` - Represents a single agent suggestion with score and reason
- `AgentSuggestionResult` - Complete result including suggestions, flags, and alternatives

### 2. API Endpoint (`ai_workflows.py`)

New endpoint: `POST /api/v1/ai-workflows/agents/suggest`

**Request Schema:**
```json
{
  "capability_description": "send email notifications"
}
```

**Response Schema:**
```json
{
  "suggestions": [
    {
      "agent_name": "email-sender",
      "agent_url": "http://localhost:8002",
      "agent_description": "Sends email notifications...",
      "capabilities": ["send", "email", "notification"],
      "relevance_score": 85.0,
      "reason": "Agent matches 3 required capabilities"
    }
  ],
  "is_ambiguous": false,
  "requires_user_choice": false,
  "no_match": false,
  "alternatives": [],
  "explanation": "Selected agent 'email-sender' for 'send email notifications'..."
}
```

### 3. Integration with WorkflowGenerationService

Added method: `suggest_agents_for_capability(capability_description)`

This method:
- Queries available agents from the registry
- Uses `AgentSuggestionService` to generate suggestions
- Returns structured `AgentSuggestionResult`

## Scoring Algorithm

The relevance scoring algorithm considers:

1. **Capability Matches** (15 points each)
   - Direct matches between agent capabilities and required keywords
   
2. **Name Matches** (10 points each)
   - Keywords found in agent name
   
3. **Description Matches** (5 points each)
   - Keywords found in agent description

**Thresholds:**
- Minimum relevance score: 30.0 (agents below this are filtered out)
- Ambiguity threshold: 0.8 (if second-best score is ≥80% of best score, it's ambiguous)
- Maximum suggestions: 5 (limits response size)

## Ambiguity Detection

Selection is considered ambiguous when:
- Multiple agents (2+) are available
- Second-best agent's score is within 80% of the best agent's score
- Example: Agent A scores 90, Agent B scores 85 → ambiguous (85/90 = 0.94 ≥ 0.8)

## Testing

### Unit Tests (`test_agent_suggestion.py`)
- 23 tests covering all service methods
- Tests for scoring, ambiguity detection, alternative generation
- Tests for clear matches, ambiguous matches, and no matches

### Integration Tests (`test_agent_suggestion_integration.py`)
- 6 tests covering end-to-end flows
- Tests integration with WorkflowGenerationService
- Tests caching behavior
- Tests all three scenarios: clear match, ambiguous match, no match

**All 49 tests pass successfully.**

## Usage Examples

### Example 1: Clear Match
```python
result = await service.suggest_agents_for_capability("send email notifications")
# Returns: email-sender agent with high confidence
# is_ambiguous: False
# requires_user_choice: False
```

### Example 2: Ambiguous Match
```python
result = await service.suggest_agents_for_capability("process documents")
# Returns: multiple agents (data-processor, pdf-processor)
# is_ambiguous: True
# requires_user_choice: True
# explanation: "Multiple agents can handle 'process documents'. Please choose one..."
```

### Example 3: No Match
```python
result = await service.suggest_agents_for_capability("quantum computing")
# Returns: empty suggestions list
# no_match: True
# alternatives: ["Create a custom agent...", "Review available agents...", ...]
```

## API Usage

```bash
# Request agent suggestions
curl -X POST http://localhost:8080/api/v1/ai-workflows/agents/suggest \
  -H "Content-Type: application/json" \
  -d '{"capability_description": "send email notifications"}'
```

## Future Enhancements

Potential improvements for future iterations:

1. **Machine Learning**: Use ML models to improve relevance scoring
2. **User Feedback**: Learn from user choices to improve suggestions
3. **Semantic Matching**: Use embeddings for better capability matching
4. **Agent Popularity**: Factor in agent usage statistics
5. **Performance Metrics**: Track agent success rates to inform suggestions

## Conclusion

The agent suggestion feature successfully implements all three requirements (4.3, 4.4, 4.5) with:
- Comprehensive handling of ambiguous scenarios
- Rich agent metadata in all suggestions
- Clear alternatives when no matches are found
- Well-tested, production-ready code
- Clean API for client integration

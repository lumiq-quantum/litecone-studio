"""Templates and example prompts for AI workflow generation.

This module provides reusable templates for:
- Example workflow descriptions for testing
- Prompt templates for different workflow patterns
- Agent description formatting templates
- Error message templates
- Explanation templates for workflow changes

Requirements: 1.1, 3.3, 4.4
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


# ============================================================================
# Example Workflow Descriptions for Testing
# ============================================================================

EXAMPLE_WORKFLOW_DESCRIPTIONS = {
    "simple_sequential": """
        Create a workflow that processes customer orders:
        1. Validate the order data
        2. Check inventory availability
        3. Process payment
        4. Send confirmation email
    """,
    
    "with_conditional": """
        Create a workflow for content moderation:
        1. Analyze the content for inappropriate material
        2. If the content is flagged, send it for manual review
        3. If the content is clean, publish it automatically
        4. Send notification to the content creator
    """,
    
    "with_loop": """
        Create a workflow that processes a batch of images:
        1. For each image in the batch:
           - Resize the image to standard dimensions
           - Apply watermark
           - Upload to storage
        2. Generate a summary report of all processed images
    """,
    
    "with_parallel": """
        Create a workflow for comprehensive data analysis:
        1. Fetch the dataset
        2. Run these analyses in parallel:
           - Statistical analysis
           - Sentiment analysis
           - Trend detection
        3. Combine all results into a final report
    """,
    
    "with_fork_join": """
        Create a workflow for multi-channel notification:
        1. Prepare the notification message
        2. Send to all channels simultaneously:
           - Email notification
           - SMS notification
           - Push notification
        3. Wait for all channels to complete
        4. Log the delivery status
    """,
    
    "complex_nested": """
        Create a workflow for e-commerce order fulfillment:
        1. Validate order and check inventory
        2. If items are available:
           - For each item in the order:
             * Reserve inventory
             * Calculate shipping cost
           - Process payment
           - If payment succeeds:
             * Generate shipping label
             * Send confirmation email
           - If payment fails:
             * Release inventory
             * Send payment failure notification
        3. If items are not available:
           - Send out-of-stock notification
           - Add to backorder queue
    """,
    
    "data_pipeline": """
        Create a data processing pipeline:
        1. Extract data from multiple sources in parallel
        2. Transform and clean the data
        3. Validate data quality
        4. If validation passes, load into data warehouse
        5. If validation fails, send alert and retry with corrections
    """,
    
    "document_processing": """
        Create a workflow for document processing:
        1. Upload document
        2. Extract text from document
        3. Analyze document for key information
        4. Classify document type
        5. Store document with metadata
        6. Index for search
    """
}


# ============================================================================
# Prompt Templates for Different Workflow Patterns
# ============================================================================

class PromptTemplates:
    """Templates for constructing LLM prompts."""
    
    BASE_WORKFLOW_GENERATION = """You are an expert workflow designer. Generate a valid workflow JSON based on the user's requirements.

User Requirements:
{description}

Available Agents:
{agents}

Generate a workflow JSON that:
1. Uses only the available agents listed above
2. Follows this JSON structure:
{{
  "name": "descriptive-workflow-name",
  "description": "Clear description of what the workflow does",
  "start_step": "step_1",
  "steps": {{
    "step_1": {{
      "type": "agent",
      "agent_name": "agent-name",
      "input_mapping": {{
        "param": "${{workflow.input.field}}"
      }},
      "next": "step_2"
    }}
  }}
}}

3. Includes proper input mappings using ${{workflow.input.field}} or ${{steps.step_id.output.field}} syntax
4. Has a clear flow from start_step to completion
5. Uses appropriate step types: agent, conditional, loop, parallel, fork_join

Respond with a JSON object containing:
{{
  "workflow": <the workflow JSON>,
  "explanation": "Brief explanation of the workflow design"
}}"""

    CONDITIONAL_PATTERN = """
For conditional logic, use this pattern:
{{
  "step_id": {{
    "type": "conditional",
    "condition": "${{steps.previous_step.output.status}} == 'success'",
    "true_next": "success_step",
    "false_next": "failure_step"
  }}
}}

The condition should be a boolean expression using:
- Comparison operators: ==, !=, <, >, <=, >=
- Logical operators: and, or, not
- References to workflow data: ${{workflow.input.field}} or ${{steps.step_id.output.field}}"""

    LOOP_PATTERN = """
For iterating over collections, use this pattern:
{{
  "step_id": {{
    "type": "loop",
    "collection": "${{workflow.input.items}}",
    "loop_body": "processing_step",
    "next": "after_loop_step"
  }},
  "processing_step": {{
    "type": "agent",
    "agent_name": "processor-agent",
    "input_mapping": {{
      "item": "${{loop.current_item}}"
    }},
    "next": "step_id"  // Returns to loop
  }}
}}

The loop will iterate over the collection and execute the loop_body for each item."""

    PARALLEL_PATTERN = """
For parallel execution, use this pattern:
{{
  "step_id": {{
    "type": "parallel",
    "branches": ["branch_1", "branch_2", "branch_3"],
    "next": "after_parallel_step"
  }},
  "branch_1": {{
    "type": "agent",
    "agent_name": "agent-1",
    "input_mapping": {{}},
    "next": "step_id"  // Returns to parallel coordinator
  }}
}}

All branches will execute simultaneously and the workflow continues when all complete."""

    FORK_JOIN_PATTERN = """
For fork-join patterns with join policies, use this pattern:
{{
  "step_id": {{
    "type": "fork_join",
    "branches": ["branch_1", "branch_2"],
    "join_policy": "all",  // Options: all, any, n_of_m
    "next": "after_join_step"
  }}
}}

Join policies:
- "all": Wait for all branches to complete
- "any": Continue when any branch completes
- "n_of_m": Continue when N branches complete (specify with "required_completions": N)"""

    WORKFLOW_REFINEMENT = """You are helping refine an existing workflow based on user feedback.

Current Workflow:
{current_workflow}

User Request:
{modification_request}

Previous Conversation:
{conversation_history}

Available Agents:
{agents}

Analyze the user's request and:
1. If it's a clarification question, provide a clear explanation without modifying the workflow
2. If it's a modification request, update ONLY the affected parts of the workflow
3. Preserve all unchanged portions exactly as they are
4. Ensure the modified workflow remains valid

Respond with a JSON object:
{{
  "workflow": <updated workflow JSON or null if just answering a question>,
  "explanation": "Clear explanation of what changed and why",
  "changes": ["List of specific changes made"]
}}"""

    AGENT_SUGGESTION = """Based on the requirement: "{requirement}"

Available agents:
{agents}

Suggest the most appropriate agent(s) for this task. Consider:
1. Agent capabilities and descriptions
2. How well the agent matches the requirement
3. Any alternative agents that could work

Provide your suggestion in this format:
{{
  "primary_suggestion": {{
    "agent_name": "agent-name",
    "reason": "Why this agent is the best fit",
    "confidence": "high/medium/low"
  }},
  "alternatives": [
    {{
      "agent_name": "alternative-agent",
      "reason": "Why this could also work"
    }}
  ],
  "no_match_guidance": "If no agents match, suggest what kind of agent would be needed"
}}"""


# ============================================================================
# Agent Description Formatting Templates
# ============================================================================

class AgentFormattingTemplates:
    """Templates for formatting agent information."""
    
    @staticmethod
    def format_agent_list(agents: List[Dict[str, Any]]) -> str:
        """Format a list of agents for LLM prompts.
        
        Args:
            agents: List of agent metadata dictionaries
            
        Returns:
            Formatted string describing all agents
        """
        if not agents:
            return "No agents currently available."
        
        lines = []
        for agent in agents:
            name = agent.get('name', 'Unknown')
            description = agent.get('description', 'No description available')
            capabilities = agent.get('capabilities', [])
            status = agent.get('status', 'unknown')
            
            caps_str = ", ".join(capabilities) if capabilities else "None specified"
            
            lines.append(f"• {name} ({status})")
            lines.append(f"  Description: {description}")
            lines.append(f"  Capabilities: {caps_str}")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_agent_detail(agent: Dict[str, Any]) -> str:
        """Format detailed information about a single agent.
        
        Args:
            agent: Agent metadata dictionary
            
        Returns:
            Formatted string with agent details
        """
        name = agent.get('name', 'Unknown')
        description = agent.get('description', 'No description available')
        url = agent.get('url', 'No URL provided')
        capabilities = agent.get('capabilities', [])
        status = agent.get('status', 'unknown')
        
        caps_str = "\n  - ".join(capabilities) if capabilities else "None specified"
        
        return f"""Agent: {name}
Status: {status}
Description: {description}
Endpoint: {url}
Capabilities:
  - {caps_str}"""
    
    @staticmethod
    def format_agent_suggestion(agent: Dict[str, Any], reason: str, confidence: str = "high") -> str:
        """Format an agent suggestion with reasoning.
        
        Args:
            agent: Agent metadata dictionary
            reason: Explanation of why this agent is suggested
            confidence: Confidence level (high/medium/low)
            
        Returns:
            Formatted suggestion string
        """
        name = agent.get('name', 'Unknown')
        description = agent.get('description', 'No description available')
        
        return f"""Suggested Agent: {name} (Confidence: {confidence})
Description: {description}
Reason: {reason}"""


# ============================================================================
# Error Message Templates
# ============================================================================

class ErrorMessageTemplates:
    """Templates for error messages with helpful suggestions."""
    
    # User Input Errors
    INVALID_DESCRIPTION = """Unable to generate workflow from the provided description.

Issue: The description is too vague or doesn't contain enough information about the required workflow steps.

Suggestions:
• Provide more specific details about what the workflow should do
• List the steps or actions that should be performed
• Mention any conditional logic, loops, or parallel processing requirements
• Specify what data the workflow will process

Example: Instead of "process data", try "validate customer data, check for duplicates, and store in database"."""

    NO_AGENTS_AVAILABLE = """Cannot generate workflow: No agents are currently available in the system.

Issue: The agent registry is empty or all agents are inactive.

Suggestions:
• Register agents in the agent registry before generating workflows
• Ensure at least one agent has 'active' status
• Check that the agent registry service is running and accessible
• Contact your system administrator if you believe agents should be available"""

    AGENT_NOT_FOUND = """Cannot use agent '{agent_name}' in workflow.

Issue: The specified agent does not exist in the agent registry or is not active.

Suggestions:
• Check the agent name spelling
• Verify the agent is registered in the agent registry
• Ensure the agent status is 'active'
• Use the agent suggestion feature to find available agents
• Available agents: {available_agents}"""

    VALIDATION_FAILED = """Workflow validation failed with {error_count} error(s).

Issues found:
{errors}

Suggestions:
• Review the errors above and make corrections
• Ensure all agent references are valid
• Check that all steps are reachable from the start_step
• Verify there are no circular references in the workflow
• Use the workflow validation endpoint to check specific issues"""

    # Document Processing Errors
    UNSUPPORTED_FORMAT = """Cannot process document: Unsupported file format '{format}'.

Supported formats: {supported_formats}

Suggestions:
• Convert your document to one of the supported formats
• For PDF: Ensure the file is a valid PDF document
• For DOCX: Use Microsoft Word format (.docx), not older .doc format
• For text files: Use .txt or .md extensions"""

    DOCUMENT_TOO_LARGE = """Cannot process document: File size exceeds the maximum limit.

File size: {file_size_mb} MB
Maximum allowed: {max_size_mb} MB

Suggestions:
• Reduce the document size by removing unnecessary content
• Split large documents into smaller sections
• Compress images if the document contains many images
• Extract only the relevant text and submit as a text description"""

    EXTRACTION_FAILED = """Failed to extract text from document.

Issue: {error_details}

Suggestions:
• Ensure the document is not corrupted
• Check that the document is not password-protected
• Try converting the document to a different format
• If the document contains only images, use OCR to extract text first"""

    # LLM Service Errors
    LLM_SERVICE_ERROR = """AI service temporarily unavailable.

Issue: {error_details}

Suggestions:
• The AI service may be experiencing high load
• Wait a few moments and try again
• If the issue persists, contact support
• Your request has been logged and will be retried automatically"""

    RATE_LIMIT_EXCEEDED = """Request rate limit exceeded.

Issue: Too many requests in a short time period.

Current limits:
• Maximum {max_requests} requests per session
• Rate limit window: {window_seconds} seconds

Suggestions:
• Wait {wait_time} seconds before making another request
• Reduce the frequency of requests
• Consider batching multiple changes into a single request"""

    # Validation Errors
    CIRCULAR_REFERENCE = """Workflow contains circular references.

Issue: Steps form a cycle, which would cause infinite execution.

Detected cycle: {cycle_path}

Suggestions:
• Review the 'next' fields in your workflow steps
• Ensure there is a clear path from start to completion
• Use conditional logic to break potential cycles
• Consider using loop structures for intentional iteration"""

    UNREACHABLE_STEPS = """Workflow contains unreachable steps.

Issue: Some steps cannot be reached from the start_step.

Unreachable steps: {unreachable_steps}

Suggestions:
• Check that all steps are properly connected
• Verify the 'next' fields point to valid step IDs
• Remove unused steps or connect them to the workflow
• Ensure conditional branches cover all cases"""

    # Session Errors
    SESSION_EXPIRED = """Chat session has expired.

Issue: The session has been inactive for more than {timeout_minutes} minutes.

Suggestions:
• Start a new chat session to continue
• Your previous workflow has been saved and can be retrieved
• Consider saving important workflows before long breaks"""

    SESSION_NOT_FOUND = """Chat session not found.

Issue: The specified session ID does not exist or has been deleted.

Suggestions:
• Check that you're using the correct session ID
• The session may have expired due to inactivity
• Start a new session to create a workflow"""


# ============================================================================
# Explanation Templates for Workflow Changes
# ============================================================================

class ExplanationTemplates:
    """Templates for explaining workflow changes and decisions."""
    
    @staticmethod
    def workflow_generated(workflow_name: str, num_steps: int, agents_used: List[str]) -> str:
        """Explain a newly generated workflow.
        
        Args:
            workflow_name: Name of the workflow
            num_steps: Number of steps in the workflow
            agents_used: List of agent names used
            
        Returns:
            Explanation string
        """
        agents_str = ", ".join(agents_used) if agents_used else "no agents"
        return f"""Generated workflow '{workflow_name}' with {num_steps} step(s).

The workflow uses the following agents: {agents_str}

The workflow has been validated and is ready to use. You can:
• Review the workflow JSON to see the complete structure
• Make modifications by describing what you'd like to change
• Save the workflow to start using it
• Ask questions about how the workflow works"""
    
    @staticmethod
    def workflow_modified(changes: List[str], preserved_count: int) -> str:
        """Explain modifications made to a workflow.
        
        Args:
            changes: List of changes made
            preserved_count: Number of steps preserved unchanged
            
        Returns:
            Explanation string
        """
        changes_str = "\n• ".join(changes)
        return f"""Modified the workflow based on your request.

Changes made:
• {changes_str}

Preserved {preserved_count} unchanged step(s) from the original workflow.

The modified workflow has been validated and is ready to use."""
    
    @staticmethod
    def agent_selected(agent_name: str, reason: str, alternatives: Optional[List[str]] = None) -> str:
        """Explain why an agent was selected.
        
        Args:
            agent_name: Name of selected agent
            reason: Reason for selection
            alternatives: Optional list of alternative agents
            
        Returns:
            Explanation string
        """
        explanation = f"""Selected agent '{agent_name}' for this step.

Reason: {reason}"""
        
        if alternatives:
            alts_str = ", ".join(alternatives)
            explanation += f"\n\nAlternative agents that could also work: {alts_str}"
        
        return explanation
    
    @staticmethod
    def pattern_detected(pattern_type: str, description: str) -> str:
        """Explain a detected workflow pattern.
        
        Args:
            pattern_type: Type of pattern (loop, conditional, parallel, etc.)
            description: Description of how the pattern is used
            
        Returns:
            Explanation string
        """
        return f"""Detected {pattern_type} pattern in your requirements.

{description}

This pattern has been implemented in the workflow structure."""
    
    @staticmethod
    def validation_auto_corrected(corrections: List[str]) -> str:
        """Explain automatic corrections made during validation.
        
        Args:
            corrections: List of corrections applied
            
        Returns:
            Explanation string
        """
        corrections_str = "\n• ".join(corrections)
        return f"""Automatically corrected validation issues:

• {corrections_str}

The workflow is now valid and ready to use."""
    
    @staticmethod
    def clarification_response(question: str, answer: str) -> str:
        """Format a response to a clarification question.
        
        Args:
            question: The user's question
            answer: The answer/explanation
            
        Returns:
            Formatted response
        """
        return f"""Question: {question}

Answer: {answer}

Let me know if you need any other clarifications or if you'd like to make changes to the workflow."""


# ============================================================================
# Workflow Pattern Examples
# ============================================================================

WORKFLOW_PATTERN_EXAMPLES = {
    "simple_sequential": {
        "name": "simple-data-processing",
        "description": "Process data through validation and storage",
        "start_step": "validate",
        "steps": {
            "validate": {
                "type": "agent",
                "agent_name": "data-validator",
                "input_mapping": {
                    "data": "${workflow.input.raw_data}"
                },
                "next": "store"
            },
            "store": {
                "type": "agent",
                "agent_name": "data-storage",
                "input_mapping": {
                    "validated_data": "${steps.validate.output.data}"
                },
                "next": None
            }
        }
    },
    
    "with_conditional": {
        "name": "conditional-processing",
        "description": "Process data with conditional branching",
        "start_step": "check_data",
        "steps": {
            "check_data": {
                "type": "agent",
                "agent_name": "data-checker",
                "input_mapping": {
                    "data": "${workflow.input.data}"
                },
                "next": "decide"
            },
            "decide": {
                "type": "conditional",
                "condition": "${steps.check_data.output.is_valid} == true",
                "true_next": "process",
                "false_next": "reject"
            },
            "process": {
                "type": "agent",
                "agent_name": "data-processor",
                "input_mapping": {
                    "data": "${steps.check_data.output.data}"
                },
                "next": None
            },
            "reject": {
                "type": "agent",
                "agent_name": "error-handler",
                "input_mapping": {
                    "error": "${steps.check_data.output.error}"
                },
                "next": None
            }
        }
    },
    
    "with_loop": {
        "name": "batch-processing",
        "description": "Process multiple items in a loop",
        "start_step": "loop_items",
        "steps": {
            "loop_items": {
                "type": "loop",
                "collection": "${workflow.input.items}",
                "loop_body": "process_item",
                "next": "summarize"
            },
            "process_item": {
                "type": "agent",
                "agent_name": "item-processor",
                "input_mapping": {
                    "item": "${loop.current_item}"
                },
                "next": "loop_items"
            },
            "summarize": {
                "type": "agent",
                "agent_name": "summarizer",
                "input_mapping": {
                    "results": "${steps.loop_items.output.results}"
                },
                "next": None
            }
        }
    },
    
    "with_parallel": {
        "name": "parallel-analysis",
        "description": "Run multiple analyses in parallel",
        "start_step": "fetch_data",
        "steps": {
            "fetch_data": {
                "type": "agent",
                "agent_name": "data-fetcher",
                "input_mapping": {
                    "source": "${workflow.input.source}"
                },
                "next": "parallel_analysis"
            },
            "parallel_analysis": {
                "type": "parallel",
                "branches": ["analyze_stats", "analyze_sentiment", "analyze_trends"],
                "next": "combine_results"
            },
            "analyze_stats": {
                "type": "agent",
                "agent_name": "stats-analyzer",
                "input_mapping": {
                    "data": "${steps.fetch_data.output.data}"
                },
                "next": "parallel_analysis"
            },
            "analyze_sentiment": {
                "type": "agent",
                "agent_name": "sentiment-analyzer",
                "input_mapping": {
                    "data": "${steps.fetch_data.output.data}"
                },
                "next": "parallel_analysis"
            },
            "analyze_trends": {
                "type": "agent",
                "agent_name": "trend-analyzer",
                "input_mapping": {
                    "data": "${steps.fetch_data.output.data}"
                },
                "next": "parallel_analysis"
            },
            "combine_results": {
                "type": "agent",
                "agent_name": "result-combiner",
                "input_mapping": {
                    "stats": "${steps.analyze_stats.output}",
                    "sentiment": "${steps.analyze_sentiment.output}",
                    "trends": "${steps.analyze_trends.output}"
                },
                "next": None
            }
        }
    }
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_example_description(pattern_type: str) -> str:
    """Get an example workflow description for a specific pattern.
    
    Args:
        pattern_type: Type of pattern (simple_sequential, with_conditional, etc.)
        
    Returns:
        Example description string
    """
    return EXAMPLE_WORKFLOW_DESCRIPTIONS.get(
        pattern_type,
        EXAMPLE_WORKFLOW_DESCRIPTIONS["simple_sequential"]
    )


def get_pattern_example(pattern_type: str) -> Dict[str, Any]:
    """Get an example workflow JSON for a specific pattern.
    
    Args:
        pattern_type: Type of pattern
        
    Returns:
        Example workflow dictionary
    """
    return WORKFLOW_PATTERN_EXAMPLES.get(
        pattern_type,
        WORKFLOW_PATTERN_EXAMPLES["simple_sequential"]
    )


def format_error_message(error_type: str, **kwargs) -> str:
    """Format an error message using templates.
    
    Args:
        error_type: Type of error (e.g., 'INVALID_DESCRIPTION', 'NO_AGENTS_AVAILABLE')
        **kwargs: Template variables
        
    Returns:
        Formatted error message
    """
    template = getattr(ErrorMessageTemplates, error_type, None)
    if template is None:
        return f"An error occurred: {error_type}"
    
    try:
        return template.format(**kwargs)
    except KeyError as e:
        # Try to do partial formatting for the variables we have
        import string
        
        # Get all template variables
        template_vars = [fname for _, fname, _, _ in string.Formatter().parse(template) if fname]
        
        # Format only the variables we have
        partial_template = template
        for var in template_vars:
            if var in kwargs:
                # Replace this specific variable
                partial_template = partial_template.replace(f"{{{var}}}", str(kwargs[var]))
        
        return f"{partial_template}\n\n(Missing template variable: {e})"


def build_prompt(template_name: str, **kwargs) -> str:
    """Build a prompt using templates.
    
    Args:
        template_name: Name of the template
        **kwargs: Template variables
        
    Returns:
        Formatted prompt string
    """
    template = getattr(PromptTemplates, template_name, None)
    if template is None:
        raise ValueError(f"Unknown template: {template_name}")
    
    return template.format(**kwargs)

"""Gemini LLM service for AI workflow generation."""

import json
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.api_core import exceptions as google_exceptions

from .base_llm_service import BaseLLMService, LLMResponse
from .config import ai_workflow_config
from .agent_query import AgentMetadata
from .chat_session import Message
from .pattern_generation import PatternGenerator, PatternPromptBuilder
from .errors import LLMServiceError, ResourceError
from .logging_utils import LLMLogger, PerformanceLogger, log_operation

logger = logging.getLogger(__name__)


# Alias for backward compatibility
GeminiResponse = LLMResponse


class GeminiService(BaseLLMService):
    """Service for interacting with Google Gemini LLM."""
    
    # Retriable error types
    RETRIABLE_ERRORS = (
        google_exceptions.ResourceExhausted,  # Rate limit
        google_exceptions.ServiceUnavailable,  # Service unavailable
        google_exceptions.DeadlineExceeded,    # Timeout
        google_exceptions.InternalServerError, # Internal error
    )
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini service.
        
        Args:
            api_key: Optional API key override (uses config if not provided)
        """
        self.api_key = api_key or ai_workflow_config.gemini_api_key
        self.model_name = ai_workflow_config.gemini_model
        self.max_tokens = ai_workflow_config.gemini_max_tokens
        self.temperature = ai_workflow_config.gemini_temperature
        
        # Retry configuration
        self.max_retries = ai_workflow_config.max_retries
        self.initial_delay_ms = ai_workflow_config.initial_retry_delay_ms
        self.max_delay_ms = ai_workflow_config.max_retry_delay_ms
        self.backoff_multiplier = ai_workflow_config.retry_backoff_multiplier
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Initialized Gemini service with model: {self.model_name}")
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: Current retry attempt (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay_ms = min(
            self.initial_delay_ms * (self.backoff_multiplier ** attempt),
            self.max_delay_ms
        )
        return delay_ms / 1000.0
    
    async def _call_with_retry(self, func, *args, **kwargs) -> Any:
        """
        Call a function with exponential backoff retry logic.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                # Call the function
                result = func(*args, **kwargs)
                
                # If it's a coroutine, await it
                if asyncio.iscoroutine(result):
                    result = await result
                
                # Log successful retry if not first attempt
                if attempt > 0:
                    duration_ms = (time.time() - start_time) * 1000
                    logger.info(
                        f"Retry successful on attempt {attempt + 1} after {duration_ms:.2f}ms",
                        extra={
                            "event_type": "retry_success",
                            "attempt": attempt + 1,
                            "total_duration_ms": round(duration_ms, 2)
                        }
                    )
                
                return result
                
            except self.RETRIABLE_ERRORS as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        f"Retriable error on attempt {attempt + 1}/{self.max_retries + 1}: {e}. "
                        f"Retrying in {delay:.2f}s...",
                        extra={
                            "event_type": "retry_attempt",
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries + 1,
                            "delay_seconds": delay,
                            "error_type": type(e).__name__
                        }
                    )
                    await asyncio.sleep(delay)
                else:
                    duration_ms = (time.time() - start_time) * 1000
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed. Last error: {e}",
                        extra={
                            "event_type": "retry_exhausted",
                            "total_attempts": self.max_retries + 1,
                            "total_duration_ms": round(duration_ms, 2),
                            "error_type": type(e).__name__
                        }
                    )
                    
                    # Wrap in LLMServiceError
                    llm_error = LLMServiceError(
                        message=f"LLM service call failed after {self.max_retries + 1} attempts",
                        details={
                            "attempts": self.max_retries + 1,
                            "last_error": str(e),
                            "error_type": type(e).__name__
                        },
                        suggestions=[
                            "The AI service may be experiencing high load",
                            "Try again in a few moments",
                            "If the issue persists, contact support"
                        ],
                        recoverable=True,
                        original_error=e
                    )
                    llm_error.log()
                    raise
            
            except Exception as e:
                # Non-retriable error, raise immediately
                logger.error(
                    f"Non-retriable error: {e}",
                    extra={
                        "event_type": "non_retriable_error",
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                
                # Wrap in LLMServiceError
                llm_error = LLMServiceError(
                    message=f"LLM service call failed: {str(e)}",
                    details={"error_type": type(e).__name__},
                    suggestions=["Check the error details and try again"],
                    recoverable=False,
                    original_error=e
                )
                llm_error.log()
                raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens (approximate)
        """
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}. Using approximation.")
            # Fallback: rough approximation (1 token ≈ 4 characters)
            return len(text) // 4
    
    def _check_context_window(self, text: str) -> bool:
        """
        Check if text fits within context window.
        
        Args:
            text: Text to check
            
        Returns:
            True if text fits, False otherwise
        """
        token_count = self.count_tokens(text)
        return token_count <= self.max_tokens
    
    def _truncate_to_fit(self, text: str, max_tokens: Optional[int] = None) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens (uses config if not provided)
            
        Returns:
            Truncated text
        """
        max_tokens = max_tokens or self.max_tokens
        current_tokens = self.count_tokens(text)
        
        if current_tokens <= max_tokens:
            return text
        
        # Binary search to find the right length
        left, right = 0, len(text)
        result = text
        
        while left < right:
            mid = (left + right + 1) // 2
            truncated = text[:mid]
            
            if self.count_tokens(truncated) <= max_tokens:
                result = truncated
                left = mid
            else:
                right = mid - 1
        
        logger.warning(
            f"Truncated text from {current_tokens} to ~{self.count_tokens(result)} tokens"
        )
        return result
    
    def _build_workflow_generation_prompt(
        self,
        description: str,
        available_agents: List[AgentMetadata]
    ) -> str:
        """
        Build prompt for workflow generation with pattern support.
        
        Args:
            description: User's workflow description
            available_agents: List of available agents
            
        Returns:
            Formatted prompt
        """
        # Detect patterns in the description
        detected_patterns = PatternGenerator.detect_pattern_type(description)
        
        # Build enhanced prompt with pattern examples
        prompt = PatternPromptBuilder.build_enhanced_prompt(
            description=description,
            available_agents=available_agents,
            detected_patterns=detected_patterns
        )
        
        return prompt
    
    def _format_agents_for_prompt(self, agents: List[AgentMetadata]) -> str:
        """
        Format agents for LLM prompt.
        
        Args:
            agents: List of agents
            
        Returns:
            Formatted string
        """
        if not agents:
            return "No agents available"
        
        lines = []
        for agent in agents:
            desc = agent.description or "No description"
            caps = ", ".join(agent.capabilities) if agent.capabilities else "None specified"
            lines.append(f"- {agent.name}: {desc} (Capabilities: {caps})")
        
        return "\n".join(lines)
    
    def _parse_workflow_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse workflow JSON from LLM response.
        
        Args:
            response_text: Raw response text
            
        Returns:
            Parsed response with workflow and explanation
        """
        try:
            # Try to parse as JSON directly
            parsed = json.loads(response_text)
            
            # Check if it has the expected structure
            if "workflow" in parsed:
                return parsed
            
            # If the entire response is a workflow, wrap it
            if "steps" in parsed and "start_step" in parsed:
                return {
                    "workflow": parsed,
                    "explanation": "Generated workflow based on your requirements."
                }
            
            return parsed
            
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            
            if json_match:
                try:
                    parsed = json.loads(json_match.group(1))
                    if "workflow" in parsed:
                        return parsed
                    if "steps" in parsed and "start_step" in parsed:
                        return {
                            "workflow": parsed,
                            "explanation": "Generated workflow based on your requirements."
                        }
                except json.JSONDecodeError:
                    pass
            
            # Fallback: return error structure
            logger.error(f"Failed to parse workflow from response: {response_text[:200]}")
            return {
                "workflow": None,
                "explanation": "Failed to parse workflow JSON from response.",
                "error": "Invalid JSON format"
            }
    
    async def generate_workflow(
        self,
        prompt: str,
        available_agents: List[AgentMetadata],
        conversation_history: Optional[List[Message]] = None
    ) -> LLMResponse:
        """
        Generate a workflow using Gemini.
        
        Args:
            prompt: User prompt describing the workflow
            available_agents: List of available agents
            conversation_history: Optional conversation history
            
        Returns:
            LLMResponse with generated workflow
        """
        start_time = time.time()
        
        with log_operation("generate_workflow_llm", {"prompt_length": len(prompt), "num_agents": len(available_agents)}) as op_logger:
            try:
                # Build the prompt
                full_prompt = self._build_workflow_generation_prompt(prompt, available_agents)
                
                # Check and truncate if needed
                if not self._check_context_window(full_prompt):
                    logger.warning("Prompt exceeds context window, truncating...")
                    op_logger.log("warning", "Prompt truncated to fit context window")
                    full_prompt = self._truncate_to_fit(full_prompt)
                
                # Configure generation
                generation_config = GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
                
                # Call Gemini with retry logic
                llm_start = time.time()
                response = await self._call_with_retry(
                    self.model.generate_content,
                    full_prompt,
                    generation_config=generation_config
                )
                llm_duration_ms = (time.time() - llm_start) * 1000
                
                # Extract response text
                response_text = response.text
                
                # Parse the response
                parsed = self._parse_workflow_response(response_text)
                
                # Extract usage information
                usage = {}
                if hasattr(response, 'usage_metadata'):
                    usage = {
                        'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                        'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                        'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0),
                    }
                
                # Log LLM call
                LLMLogger.log_llm_call(
                    model=self.model_name,
                    prompt=full_prompt,
                    response=response_text,
                    usage=usage,
                    duration_ms=llm_duration_ms
                )
                
                # Log performance metric
                PerformanceLogger.log_metric(
                    metric_name="llm_call_duration",
                    value=llm_duration_ms,
                    unit="ms",
                    context={"operation": "generate_workflow", "model": self.model_name}
                )
                
                return LLMResponse(
                    content=parsed.get("explanation", response_text),
                    workflow_json=parsed.get("workflow"),
                    finish_reason=getattr(response, 'finish_reason', 'STOP'),
                    usage=usage
                )
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(f"Error generating workflow: {e}", exc_info=True)
                
                # Log failed LLM call
                LLMLogger.log_llm_call(
                    model=self.model_name,
                    prompt=prompt,
                    duration_ms=duration_ms,
                    error=str(e)
                )
                
                return LLMResponse(
                    content=f"Error generating workflow: {str(e)}",
                    workflow_json=None,
                    finish_reason="ERROR",
                    usage={}
                )
    
    async def chat(
        self,
        message: str,
        conversation_history: List[Message],
        current_workflow: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Chat with Gemini for workflow refinement.
        
        Args:
            message: User message
            conversation_history: Previous conversation
            current_workflow: Current workflow state
            
        Returns:
            LLMResponse with chat response
        """
        try:
            # Build conversation context
            context_parts = ["You are an AI assistant helping refine a workflow definition."]
            
            if current_workflow:
                context_parts.append(f"\nCurrent Workflow:\n{json.dumps(current_workflow, indent=2)}")
            
            # Add conversation history
            if conversation_history:
                context_parts.append("\nConversation History:")
                for msg in conversation_history[-5:]:  # Last 5 messages
                    context_parts.append(f"{msg.role}: {msg.content}")
            
            context_parts.append(f"\nUser: {message}")
            context_parts.append("\nProvide a helpful response. If modifying the workflow, include the updated workflow JSON in your response.")
            
            full_prompt = "\n".join(context_parts)
            
            # Check and truncate if needed
            if not self._check_context_window(full_prompt):
                logger.warning("Chat prompt exceeds context window, truncating history...")
                # Reduce history and try again
                context_parts = ["You are an AI assistant helping refine a workflow definition."]
                if current_workflow:
                    context_parts.append(f"\nCurrent Workflow:\n{json.dumps(current_workflow, indent=2)}")
                context_parts.append(f"\nUser: {message}")
                full_prompt = "\n".join(context_parts)
                full_prompt = self._truncate_to_fit(full_prompt)
            
            # Configure generation
            generation_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            
            # Call Gemini with retry logic
            response = await self._call_with_retry(
                self.model.generate_content,
                full_prompt,
                generation_config=generation_config
            )
            
            response_text = response.text
            
            # Try to extract workflow JSON if present
            workflow_json = None
            try:
                parsed = self._parse_workflow_response(response_text)
                workflow_json = parsed.get("workflow")
            except:
                pass
            
            # Extract usage information
            usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = {
                    'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                    'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                    'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0),
                }
            
            return LLMResponse(
                content=response_text,
                workflow_json=workflow_json,
                finish_reason=getattr(response, 'finish_reason', 'STOP'),
                usage=usage
            )
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return LLMResponse(
                content=f"Error processing chat message: {str(e)}",
                workflow_json=None,
                finish_reason="ERROR",
                usage={}
            )
    
    async def explain_workflow(
        self,
        workflow_json: Dict[str, Any]
    ) -> str:
        """
        Generate an explanation of a workflow.
        
        Args:
            workflow_json: Workflow to explain
            
        Returns:
            Human-readable explanation
        """
        try:
            prompt = f"""Explain the following workflow in simple, human-readable terms:

{json.dumps(workflow_json, indent=2)}

Provide a clear explanation of:
1. What the workflow does
2. The sequence of steps
3. Any conditional logic or parallel execution
4. The agents involved and their roles"""

            # Check and truncate if needed
            if not self._check_context_window(prompt):
                logger.warning("Explanation prompt exceeds context window, truncating workflow...")
                # Truncate the workflow JSON
                workflow_str = json.dumps(workflow_json, indent=2)
                max_workflow_tokens = self.max_tokens - 200  # Reserve tokens for the prompt template
                truncated_workflow = self._truncate_to_fit(workflow_str, max_workflow_tokens)
                prompt = f"""Explain the following workflow in simple, human-readable terms:

{truncated_workflow}

Provide a clear explanation of what you can see in this workflow."""
            
            # Configure generation
            generation_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            
            # Call Gemini with retry logic
            response = await self._call_with_retry(
                self.model.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error explaining workflow: {e}")
            return f"Error generating explanation: {str(e)}"

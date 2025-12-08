"""Base LLM service interface for provider abstraction."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from an LLM service."""
    
    content: str
    workflow_json: Optional[Dict[str, Any]] = None
    finish_reason: str = ""
    usage: Optional[Dict[str, int]] = None
    
    def __post_init__(self):
        """Initialize usage dict if None."""
        if self.usage is None:
            self.usage = {}


class BaseLLMService(ABC):
    """Abstract base class for LLM service providers."""
    
    @abstractmethod
    async def generate_workflow(
        self,
        prompt: str,
        available_agents: List[Any],
        conversation_history: Optional[List[Any]] = None
    ) -> LLMResponse:
        """
        Generate a workflow using the LLM.
        
        Args:
            prompt: User prompt describing the workflow
            available_agents: List of available agents
            conversation_history: Optional conversation history
            
        Returns:
            LLMResponse with generated workflow
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        message: str,
        conversation_history: List[Any],
        current_workflow: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Chat with the LLM for workflow refinement.
        
        Args:
            message: User message
            conversation_history: Previous conversation
            current_workflow: Current workflow state
            
        Returns:
            LLMResponse with chat response
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass

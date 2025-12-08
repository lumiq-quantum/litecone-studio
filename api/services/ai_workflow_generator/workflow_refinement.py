"""Workflow refinement service for iterative workflow modifications."""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from copy import deepcopy

from .gemini_service import GeminiService
from .agent_query import AgentMetadata
from .chat_session import Message

logger = logging.getLogger(__name__)


class ModificationRequest:
    """Parsed modification request."""
    
    def __init__(
        self,
        request_type: str,
        target_elements: List[str],
        modification_details: Dict[str, Any],
        raw_request: str
    ):
        """
        Initialize modification request.
        
        Args:
            request_type: Type of modification (add, remove, modify, clarify)
            target_elements: Elements to modify (step names, workflow properties)
            modification_details: Details of the modification
            raw_request: Original user request
        """
        self.request_type = request_type
        self.target_elements = target_elements
        self.modification_details = modification_details
        self.raw_request = raw_request


class WorkflowModificationParser:
    """Parser for workflow modification requests."""
    
    # Keywords for different modification types
    ADD_KEYWORDS = ['add', 'insert', 'include', 'create', 'new']
    REMOVE_KEYWORDS = ['remove', 'delete', 'drop', 'eliminate']
    MODIFY_KEYWORDS = ['change', 'modify', 'update', 'edit', 'alter', 'adjust']
    CLARIFY_KEYWORDS = ['explain', 'clarify', 'what', 'why', 'how', 'describe', 'tell me']
    
    @classmethod
    def parse_request(cls, request: str) -> ModificationRequest:
        """
        Parse a user modification request.
        
        Args:
            request: User's modification request
            
        Returns:
            Parsed modification request
        """
        request_lower = request.lower()
        
        # Determine request type
        request_type = cls._determine_request_type(request_lower)
        
        # Extract target elements (step names, workflow properties)
        target_elements = cls._extract_target_elements(request)
        
        # Extract modification details
        modification_details = {
            'description': request,
            'keywords': cls._extract_keywords(request_lower)
        }
        
        logger.debug(
            f"Parsed request: type={request_type}, "
            f"targets={target_elements}, details={modification_details}"
        )
        
        return ModificationRequest(
            request_type=request_type,
            target_elements=target_elements,
            modification_details=modification_details,
            raw_request=request
        )
    
    @classmethod
    def _determine_request_type(cls, request_lower: str) -> str:
        """Determine the type of modification request."""
        # Check for clarification first (highest priority)
        if any(keyword in request_lower for keyword in cls.CLARIFY_KEYWORDS):
            # Check if it's a question
            if '?' in request_lower or request_lower.startswith(tuple(cls.CLARIFY_KEYWORDS)):
                return 'clarify'
        
        # Check for add
        if any(keyword in request_lower for keyword in cls.ADD_KEYWORDS):
            return 'add'
        
        # Check for remove
        if any(keyword in request_lower for keyword in cls.REMOVE_KEYWORDS):
            return 'remove'
        
        # Check for modify
        if any(keyword in request_lower for keyword in cls.MODIFY_KEYWORDS):
            return 'modify'
        
        # Default to modify if unclear
        return 'modify'
    
    @classmethod
    def _extract_target_elements(cls, request: str) -> List[str]:
        """Extract target elements from request."""
        import re
        
        # Look for quoted strings (likely step names or agent names)
        quoted = re.findall(r'"([^"]+)"', request)
        if quoted:
            return quoted
        
        # Look for step references (step1, step_1, step 1)
        step_refs = re.findall(r'step[_\s]*(\w+)', request, re.IGNORECASE)
        if step_refs:
            return step_refs
        
        # Look for agent references
        agent_refs = re.findall(r'agent[_\s]+(\w+)', request, re.IGNORECASE)
        if agent_refs:
            return agent_refs
        
        return []
    
    @classmethod
    def _extract_keywords(cls, request_lower: str) -> List[str]:
        """Extract relevant keywords from request."""
        keywords = []
        
        # Common workflow concepts
        concepts = [
            'parallel', 'sequential', 'loop', 'conditional', 'if', 'then',
            'fork', 'join', 'input', 'output', 'mapping', 'agent', 'step'
        ]
        
        for concept in concepts:
            if concept in request_lower:
                keywords.append(concept)
        
        return keywords


class WorkflowDiffer:
    """Utility to compute differences between workflows."""
    
    @classmethod
    def compute_diff(
        cls,
        old_workflow: Dict[str, Any],
        new_workflow: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute differences between two workflows.
        
        Args:
            old_workflow: Original workflow
            new_workflow: Modified workflow
            
        Returns:
            Dictionary describing the changes
        """
        changes = {
            'added_steps': [],
            'removed_steps': [],
            'modified_steps': [],
            'unchanged_steps': [],
            'metadata_changes': {}
        }
        
        old_steps = old_workflow.get('steps', {})
        new_steps = new_workflow.get('steps', {})
        
        old_step_ids = set(old_steps.keys())
        new_step_ids = set(new_steps.keys())
        
        # Find added steps
        changes['added_steps'] = list(new_step_ids - old_step_ids)
        
        # Find removed steps
        changes['removed_steps'] = list(old_step_ids - new_step_ids)
        
        # Find modified and unchanged steps
        common_steps = old_step_ids & new_step_ids
        for step_id in common_steps:
            if old_steps[step_id] != new_steps[step_id]:
                changes['modified_steps'].append({
                    'step_id': step_id,
                    'old': old_steps[step_id],
                    'new': new_steps[step_id]
                })
            else:
                changes['unchanged_steps'].append(step_id)
        
        # Check metadata changes
        for key in ['name', 'description', 'start_step']:
            old_val = old_workflow.get(key)
            new_val = new_workflow.get(key)
            if old_val != new_val:
                changes['metadata_changes'][key] = {
                    'old': old_val,
                    'new': new_val
                }
        
        return changes
    
    @classmethod
    def generate_change_summary(cls, diff: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of changes.
        
        Args:
            diff: Diff computed by compute_diff
            
        Returns:
            Human-readable summary
        """
        summary_parts = []
        
        if diff['added_steps']:
            summary_parts.append(
                f"Added {len(diff['added_steps'])} step(s): {', '.join(diff['added_steps'])}"
            )
        
        if diff['removed_steps']:
            summary_parts.append(
                f"Removed {len(diff['removed_steps'])} step(s): {', '.join(diff['removed_steps'])}"
            )
        
        if diff['modified_steps']:
            modified_ids = [m['step_id'] for m in diff['modified_steps']]
            summary_parts.append(
                f"Modified {len(diff['modified_steps'])} step(s): {', '.join(modified_ids)}"
            )
        
        if diff['unchanged_steps']:
            summary_parts.append(
                f"Preserved {len(diff['unchanged_steps'])} unchanged step(s)"
            )
        
        if diff['metadata_changes']:
            for key, change in diff['metadata_changes'].items():
                summary_parts.append(
                    f"Changed {key} from '{change['old']}' to '{change['new']}'"
                )
        
        if not summary_parts:
            return "No changes detected"
        
        return "; ".join(summary_parts)


class WorkflowRefinementService:
    """Service for refining workflows through iterative modifications."""
    
    def __init__(self, gemini_service: GeminiService):
        """
        Initialize the refinement service.
        
        Args:
            gemini_service: Gemini service for LLM interactions
        """
        self.gemini_service = gemini_service
        self.parser = WorkflowModificationParser()
        self.differ = WorkflowDiffer()
    
    async def refine_workflow(
        self,
        current_workflow: Dict[str, Any],
        modification_request: str,
        conversation_history: List[Message],
        available_agents: List[AgentMetadata]
    ) -> Tuple[Optional[Dict[str, Any]], str, List[str]]:
        """
        Refine a workflow based on user modification request.
        
        This method implements surgical updates that preserve unchanged portions
        of the workflow while applying requested modifications.
        
        Args:
            current_workflow: Current workflow JSON
            modification_request: User's modification request
            conversation_history: Previous conversation messages
            available_agents: List of available agents
            
        Returns:
            Tuple of (modified_workflow, explanation, suggestions)
        """
        try:
            # Parse the modification request
            parsed_request = self.parser.parse_request(modification_request)
            
            # Handle clarification requests differently
            if parsed_request.request_type == 'clarify':
                explanation = await self._handle_clarification(
                    current_workflow,
                    modification_request,
                    conversation_history
                )
                return None, explanation, []
            
            # For modifications, use LLM to generate updated workflow
            modified_workflow, explanation = await self._apply_modification(
                current_workflow,
                modification_request,
                conversation_history,
                available_agents,
                parsed_request
            )
            
            if modified_workflow is None:
                return None, explanation, ["Unable to apply modification"]
            
            # Compute diff to verify preservation
            diff = self.differ.compute_diff(current_workflow, modified_workflow)
            
            # Generate change summary
            change_summary = self.differ.generate_change_summary(diff)
            
            # Enhance explanation with change summary
            enhanced_explanation = self._enhance_explanation(
                explanation,
                change_summary,
                diff
            )
            
            # Generate suggestions
            suggestions = self._generate_suggestions(diff, parsed_request)
            
            logger.info(f"Workflow refinement completed: {change_summary}")
            
            return modified_workflow, enhanced_explanation, suggestions
            
        except Exception as e:
            logger.error(f"Error refining workflow: {e}", exc_info=True)
            return None, f"Error refining workflow: {str(e)}", []
    
    async def _handle_clarification(
        self,
        current_workflow: Dict[str, Any],
        clarification_request: str,
        conversation_history: List[Message]
    ) -> str:
        """
        Handle clarification requests about the workflow.
        
        Args:
            current_workflow: Current workflow
            clarification_request: User's clarification request
            conversation_history: Conversation history
            
        Returns:
            Explanation text
        """
        logger.info(f"Handling clarification request: {clarification_request}")
        
        # Build prompt for clarification
        prompt = self._build_clarification_prompt(
            current_workflow,
            clarification_request
        )
        
        # Use Gemini to generate explanation
        response = await self.gemini_service.chat(
            message=prompt,
            conversation_history=conversation_history,
            current_workflow=current_workflow
        )
        
        return response.content
    
    def _build_clarification_prompt(
        self,
        workflow: Dict[str, Any],
        request: str
    ) -> str:
        """Build prompt for clarification requests."""
        return f"""The user is asking about the current workflow:

User Question: {request}

Current Workflow:
{json.dumps(workflow, indent=2)}

Please provide a clear, helpful explanation that answers their question. Focus on:
- Workflow structure and design decisions
- Agent capabilities and why they were chosen
- How data flows through the workflow
- Any conditional logic, loops, or parallel execution patterns

Keep the explanation concise and user-friendly."""
    
    async def _apply_modification(
        self,
        current_workflow: Dict[str, Any],
        modification_request: str,
        conversation_history: List[Message],
        available_agents: List[AgentMetadata],
        parsed_request: ModificationRequest
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Apply modification to workflow using LLM.
        
        Args:
            current_workflow: Current workflow
            modification_request: User's modification request
            conversation_history: Conversation history
            available_agents: Available agents
            parsed_request: Parsed request
            
        Returns:
            Tuple of (modified_workflow, explanation)
        """
        logger.info(f"Applying modification: {parsed_request.request_type}")
        
        # Build prompt for modification
        prompt = self._build_modification_prompt(
            current_workflow,
            modification_request,
            available_agents,
            parsed_request
        )
        
        # Use Gemini to generate modified workflow
        response = await self.gemini_service.chat(
            message=prompt,
            conversation_history=conversation_history,
            current_workflow=current_workflow
        )
        
        # Extract modified workflow from response
        modified_workflow = response.workflow_json
        
        if modified_workflow is None:
            # Try to parse from content
            modified_workflow = self._extract_workflow_from_text(response.content)
        
        explanation = response.content
        
        return modified_workflow, explanation
    
    def _build_modification_prompt(
        self,
        workflow: Dict[str, Any],
        request: str,
        available_agents: List[AgentMetadata],
        parsed_request: ModificationRequest
    ) -> str:
        """Build prompt for workflow modification."""
        agent_list = self._format_agents(available_agents)
        
        return f"""You are modifying an existing workflow based on a user request.

IMPORTANT: Preserve all parts of the workflow that are not mentioned in the modification request.
Only change what the user explicitly asks to change.

Current Workflow:
{json.dumps(workflow, indent=2)}

Available Agents:
{agent_list}

User Modification Request: {request}

Request Type: {parsed_request.request_type}
Target Elements: {', '.join(parsed_request.target_elements) if parsed_request.target_elements else 'Not specified'}

Please:
1. Apply ONLY the requested changes
2. Preserve all unchanged steps and their configurations
3. Maintain the overall workflow structure unless explicitly asked to change it
4. Ensure all step references remain valid
5. Return the complete modified workflow as JSON

Respond with:
1. A brief explanation of what you changed and why
2. The complete modified workflow JSON

Format your response as:
{{
  "explanation": "Brief explanation of changes",
  "workflow": {{ ... complete workflow JSON ... }}
}}"""
    
    def _format_agents(self, agents: List[AgentMetadata]) -> str:
        """Format agents for prompt."""
        if not agents:
            return "No agents available"
        
        lines = []
        for agent in agents:
            desc = agent.description or "No description"
            lines.append(f"- {agent.name}: {desc}")
        
        return "\n".join(lines)
    
    def _extract_workflow_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract workflow JSON from text response."""
        import re
        
        try:
            # Try to parse entire text as JSON
            parsed = json.loads(text)
            if 'workflow' in parsed:
                return parsed['workflow']
            if 'steps' in parsed:
                return parsed
            return None
        except json.JSONDecodeError:
            pass
        
        # Try to extract from code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                if 'workflow' in parsed:
                    return parsed['workflow']
                if 'steps' in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _enhance_explanation(
        self,
        original_explanation: str,
        change_summary: str,
        diff: Dict[str, Any]
    ) -> str:
        """
        Enhance explanation with change summary.
        
        Args:
            original_explanation: Original LLM explanation
            change_summary: Summary of changes
            diff: Computed diff
            
        Returns:
            Enhanced explanation
        """
        # Add change summary if not already present
        if change_summary.lower() not in original_explanation.lower():
            enhanced = f"{original_explanation}\n\nChanges Applied: {change_summary}"
        else:
            enhanced = original_explanation
        
        # Add preservation note if there are unchanged steps
        if diff['unchanged_steps']:
            count = len(diff['unchanged_steps'])
            enhanced += f"\n\nNote: {count} step(s) were preserved unchanged as requested."
        
        return enhanced
    
    def _generate_suggestions(
        self,
        diff: Dict[str, Any],
        parsed_request: ModificationRequest
    ) -> List[str]:
        """Generate suggestions based on the modification."""
        suggestions = []
        
        # Suggest validation if steps were added
        if diff['added_steps']:
            suggestions.append("Review the new steps to ensure they have correct input mappings")
        
        # Suggest testing if significant changes
        if len(diff['modified_steps']) > 2 or len(diff['added_steps']) > 1:
            suggestions.append("Consider testing the workflow with sample data")
        
        # Suggest clarification if request was ambiguous
        if not parsed_request.target_elements:
            suggestions.append("If the changes don't match your intent, try being more specific about which steps to modify")
        
        return suggestions

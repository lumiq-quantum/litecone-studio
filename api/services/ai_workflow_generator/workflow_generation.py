"""Workflow generation service for AI-powered workflow creation."""

import logging
import time
import json
from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .gemini_service import GeminiService
from .agent_query import AgentQueryService, AgentMetadata
from .workflow_validation import WorkflowValidationService
from .chat_session import Message
from .pattern_generation import PatternGenerator
from .workflow_refinement import WorkflowRefinementService
from .agent_suggestion import AgentSuggestionService, AgentSuggestionResult
from .errors import (
    UserInputError, ValidationError as WorkflowValidationError,
    IntegrationError, InternalError, handle_error
)
from .logging_utils import log_operation, PerformanceLogger

logger = logging.getLogger(__name__)


class WorkflowGenerationResult:
    """Result of workflow generation operation."""
    
    def __init__(
        self,
        success: bool,
        workflow_json: Optional[Dict[str, Any]] = None,
        explanation: str = "",
        validation_errors: Optional[List[str]] = None,
        suggestions: Optional[List[str]] = None,
        agents_used: Optional[List[str]] = None
    ):
        self.success = success
        self.workflow_json = workflow_json
        self.explanation = explanation
        self.validation_errors = validation_errors or []
        self.suggestions = suggestions or []
        self.agents_used = agents_used or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "workflow_json": self.workflow_json,
            "explanation": self.explanation,
            "validation_errors": self.validation_errors,
            "suggestions": self.suggestions,
            "agents_used": self.agents_used
        }


class WorkflowGenerationService:
    """Service for generating workflows from natural language descriptions."""
    
    def __init__(
        self,
        db: AsyncSession,
        gemini_service: Optional[GeminiService] = None
    ):
        """
        Initialize the workflow generation service.
        
        Args:
            db: Database session for agent queries
            gemini_service: Optional Gemini service instance (creates new if not provided)
        """
        self.db = db
        self.gemini_service = gemini_service or GeminiService()
        self.agent_query_service = AgentQueryService(db)
        self.validation_service = WorkflowValidationService(db)
        self.refinement_service = WorkflowRefinementService(self.gemini_service)
        self.suggestion_service = AgentSuggestionService()
        logger.info("Initialized WorkflowGenerationService")
    
    async def _query_available_agents(self) -> List[AgentMetadata]:
        """
        Query the agent registry for available agents.
        
        Returns:
            List of active agents
        """
        logger.info("Querying agent registry for available agents")
        agents = await self.agent_query_service.get_all_agents(status="active")
        logger.info(f"Found {len(agents)} active agents")
        return agents
    
    def _identify_workflow_steps(
        self,
        description: str,
        available_agents: List[AgentMetadata]
    ) -> List[str]:
        """
        Identify potential workflow steps from description.
        
        This is a helper method that extracts key action verbs and concepts
        from the description to help guide workflow generation.
        
        Args:
            description: Natural language description
            available_agents: List of available agents
            
        Returns:
            List of identified step concepts
        """
        # Extract action verbs and key concepts
        import re
        
        # Common workflow action verbs
        action_verbs = [
            'process', 'validate', 'transform', 'send', 'receive',
            'create', 'update', 'delete', 'fetch', 'store', 'retrieve',
            'analyze', 'generate', 'parse', 'format', 'filter', 'sort'
        ]
        
        desc_lower = description.lower()
        identified_steps = []
        
        # Look for action verbs in description
        for verb in action_verbs:
            if re.search(rf'\b{verb}\w*\b', desc_lower):
                identified_steps.append(verb)
        
        # Look for agent capabilities mentioned
        for agent in available_agents:
            if agent.name.lower() in desc_lower:
                identified_steps.append(f"use_{agent.name}")
        
        logger.debug(f"Identified potential steps: {identified_steps}")
        return identified_steps
    
    def _assign_agents_to_steps(
        self,
        workflow_json: Dict[str, Any],
        available_agents: List[AgentMetadata]
    ) -> List[str]:
        """
        Extract list of agents used in the workflow.
        
        Args:
            workflow_json: Generated workflow
            available_agents: List of available agents
            
        Returns:
            List of agent names used in the workflow
        """
        agents_used = set()
        
        steps = workflow_json.get('steps', {})
        for step_id, step in steps.items():
            step_type = step.get('type', 'agent')
            if step_type == 'agent':
                agent_name = step.get('agent_name')
                if agent_name:
                    agents_used.add(agent_name)
        
        return list(agents_used)
    
    def _generate_input_mappings(
        self,
        workflow_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ensure all agent steps have proper input mappings.
        
        This is a post-processing step to add default input mappings
        if they're missing.
        
        Args:
            workflow_json: Workflow to process
            
        Returns:
            Workflow with complete input mappings
        """
        steps = workflow_json.get('steps', {})
        
        for step_id, step in steps.items():
            step_type = step.get('type', 'agent')
            
            if step_type == 'agent':
                # Ensure input_mapping exists
                if 'input_mapping' not in step:
                    step['input_mapping'] = {}
                
                # If input_mapping is empty, add a default mapping
                if not step['input_mapping']:
                    # Map workflow input to agent input
                    step['input_mapping'] = {
                        'data': '${workflow.input}'
                    }
        
        return workflow_json
    
    async def _llm_self_correct(
        self,
        workflow: Dict[str, Any],
        errors: List[str],
        available_agents: List[AgentMetadata]
    ) -> Dict[str, Any]:
        """
        Ask the LLM to fix validation errors in the workflow.
        
        This implements self-correction where the LLM reviews its own output
        and fixes specific validation errors.
        
        Args:
            workflow: The workflow with validation errors
            errors: List of validation error messages
            available_agents: List of available agents
            
        Returns:
            Corrected workflow JSON
        """
        logger.info("Requesting LLM to self-correct validation errors")
        
        # Build a prompt asking the LLM to fix the errors
        error_list = "\n".join([f"- {error}" for error in errors])
        
        correction_prompt = f"""The workflow you generated has validation errors. Please fix them.

Current Workflow JSON:
```json
{json.dumps(workflow, indent=2)}
```

Validation Errors:
{error_list}

Please generate a CORRECTED workflow JSON that fixes all these validation errors.
Make sure to:
1. Keep the same workflow logic and structure
2. Fix ONLY the validation errors listed above
3. Ensure all required fields are present
4. Use correct field names and types
5. Follow the exact schema requirements

Respond with a JSON object containing:
{{
  "workflow": <the corrected workflow JSON>,
  "explanation": "Brief explanation of what was fixed"
}}"""

        # Call the LLM to fix the errors
        llm_response = await self.gemini_service.generate_workflow(
            prompt=correction_prompt,
            available_agents=available_agents,
            conversation_history=None
        )
        
        if llm_response.workflow_json:
            logger.info("LLM successfully generated corrected workflow")
            return llm_response.workflow_json
        else:
            logger.warning("LLM did not return a corrected workflow")
            return workflow  # Return original if correction failed
    
    async def _validate_and_correct(
        self,
        workflow_json: Dict[str, Any]
    ) -> tuple[Dict[str, Any], List[str], List[str]]:
        """
        Validate workflow and apply auto-corrections.
        
        Args:
            workflow_json: Workflow to validate
            
        Returns:
            Tuple of (corrected_workflow, errors, auto_corrections)
        """
        logger.info("Validating generated workflow")
        
        # First validate nested pattern references
        is_valid_nested, nested_errors = PatternGenerator.validate_nested_references(workflow_json)
        
        if not is_valid_nested:
            logger.warning(f"Nested pattern validation found {len(nested_errors)} errors")
            return workflow_json, nested_errors, []
        
        # Then run standard validation
        validation_result = await self.validation_service.validate_workflow(workflow_json)
        
        # Use the corrected workflow from validation result
        corrected_workflow = validation_result.corrected_workflow or workflow_json
        
        if validation_result.is_valid:
            logger.info("Workflow validation passed")
            # Return auto_corrections even when valid (they may have been applied)
            return corrected_workflow, [], validation_result.auto_corrections
        
        logger.warning(f"Workflow validation found {len(validation_result.errors)} errors")
        
        # If there are auto-corrections, use the corrected workflow
        if validation_result.auto_corrections:
            logger.info(f"Applied {len(validation_result.auto_corrections)} auto-corrections")
        
        return corrected_workflow, validation_result.errors, validation_result.auto_corrections
    
    async def generate_from_text(
        self,
        description: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> WorkflowGenerationResult:
        """
        Generate a workflow from a natural language description.
        
        This method orchestrates the complete workflow generation process:
        1. Query agent registry for available agents
        2. Identify workflow steps from description
        3. Use Gemini to generate workflow JSON
        4. Validate and auto-correct the workflow
        5. Return the result with explanation
        
        Args:
            description: Natural language description of the workflow
            user_preferences: Optional user preferences for generation
            
        Returns:
            WorkflowGenerationResult with the generated workflow
        """
        start_time = time.time()
        agent_query_duration = 0
        llm_duration = 0
        validation_duration = 0
        
        with log_operation("generate_workflow_from_text", {"description_length": len(description)}) as op_logger:
            try:
                logger.info(f"Generating workflow from text description: {description[:100]}...")
                
                # Step 1: Query available agents
                agent_start = time.time()
                available_agents = await self._query_available_agents()
                agent_query_duration = (time.time() - agent_start) * 1000
                
                if not available_agents:
                    logger.warning("No active agents found in registry")
                    error = IntegrationError(
                        message="No active agents available in the system",
                        service_name="agent_registry",
                        suggestions=[
                            "Register agents in the agent registry",
                            "Ensure at least one agent is in 'active' status"
                        ]
                    )
                    error.log()
                    
                    return WorkflowGenerationResult(
                        success=False,
                        workflow_json=None,
                        explanation="No active agents available in the system. Please register agents before generating workflows.",
                        validation_errors=["No active agents available"],
                        suggestions=["Register agents in the agent registry"]
                    )
                
                # Step 2: Identify potential workflow steps (for logging/debugging)
                identified_steps = self._identify_workflow_steps(description, available_agents)
                logger.debug(f"Identified steps: {identified_steps}")
                
                # Step 3: Generate workflow using Gemini
                logger.info("Calling Gemini to generate workflow")
                llm_start = time.time()
                llm_response = await self.gemini_service.generate_workflow(
                    prompt=description,
                    available_agents=available_agents,
                    conversation_history=None
                )
                llm_duration = (time.time() - llm_start) * 1000
                
                if not llm_response.workflow_json:
                    logger.error("Gemini did not return a valid workflow JSON")
                    error = UserInputError(
                        message="Failed to generate workflow from description",
                        details={"llm_response": llm_response.content[:200]},
                        suggestions=[
                            "Try rephrasing your description with more specific details",
                            "Include information about what steps should be performed",
                            "Mention specific agents or capabilities you want to use"
                        ]
                    )
                    error.log()
                    
                    return WorkflowGenerationResult(
                        success=False,
                        workflow_json=None,
                        explanation=llm_response.content,
                        validation_errors=["Failed to generate workflow JSON"],
                        suggestions=["Try rephrasing your description with more specific details"]
                    )
                
                workflow_json = llm_response.workflow_json
                explanation = llm_response.content
                
                # Step 4: Generate/ensure input mappings
                workflow_json = self._generate_input_mappings(workflow_json)
                
                # Step 5: Identify agents used
                agents_used = self._assign_agents_to_steps(workflow_json, available_agents)
                logger.info(f"Workflow uses {len(agents_used)} agents: {agents_used}")
                
                # Step 6: Validate and auto-correct
                validation_start = time.time()
                corrected_workflow, errors, auto_corrections = await self._validate_and_correct(workflow_json)
                validation_duration = (time.time() - validation_start) * 1000
                
                # Step 7: If validation errors remain, ask LLM to fix them (self-correction)
                if errors and len(errors) > 0:
                    logger.info(f"Attempting LLM self-correction for {len(errors)} validation errors")
                    try:
                        self_corrected_workflow = await self._llm_self_correct(
                            workflow=corrected_workflow,
                            errors=errors,
                            available_agents=available_agents
                        )
                        
                        # Validate the self-corrected workflow
                        corrected_workflow, errors_after, auto_corrections_after = await self._validate_and_correct(self_corrected_workflow)
                        
                        if len(errors_after) < len(errors):
                            logger.info(f"LLM self-correction reduced errors from {len(errors)} to {len(errors_after)}")
                            errors = errors_after
                            auto_corrections.extend(auto_corrections_after)
                            auto_corrections.append(f"LLM self-correction fixed {len(errors) - len(errors_after)} validation errors")
                        else:
                            logger.warning("LLM self-correction did not improve validation errors")
                    except Exception as e:
                        logger.error(f"LLM self-correction failed: {e}")
                        # Continue with the original corrected workflow
                
                # Build suggestions based on validation
                suggestions = []
                if auto_corrections:
                    suggestions.extend(auto_corrections)
                if errors:
                    suggestions.append("Review and fix validation errors before using this workflow")
                    
                    # Log validation errors
                    validation_error = WorkflowValidationError(
                        message="Workflow validation found errors",
                        validation_errors=errors,
                        suggestions=suggestions
                    )
                    validation_error.log()
                
                success = len(errors) == 0
                
                # Log comprehensive metrics
                total_duration = (time.time() - start_time) * 1000
                workflow_size = len(json.dumps(corrected_workflow))
                num_steps = len(corrected_workflow.get('steps', {}))
                
                PerformanceLogger.log_workflow_generation_metrics(
                    total_duration_ms=total_duration,
                    llm_duration_ms=llm_duration,
                    validation_duration_ms=validation_duration,
                    agent_query_duration_ms=agent_query_duration,
                    workflow_size_bytes=workflow_size,
                    num_steps=num_steps,
                    num_agents=len(agents_used)
                )
                
                return WorkflowGenerationResult(
                    success=success,
                    workflow_json=corrected_workflow,
                    explanation=explanation,
                    validation_errors=errors,
                    suggestions=suggestions,
                    agents_used=agents_used
                )
                
            except Exception as e:
                logger.error(f"Error generating workflow from text: {e}", exc_info=True)
                
                # Handle error and create response
                error_response = handle_error(e, context={"operation": "generate_from_text"})
                
                return WorkflowGenerationResult(
                    success=False,
                    workflow_json=None,
                    explanation=error_response.message,
                    validation_errors=[error_response.message],
                    suggestions=error_response.suggestions
                )
    
    async def generate_from_document(
        self,
        document_content: str,
        document_type: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> WorkflowGenerationResult:
        """
        Generate a workflow from extracted document content.
        
        This method treats document content the same as text descriptions,
        as per Requirement 2.2: "Document and text processing consistency"
        
        Args:
            document_content: Extracted text from document
            document_type: Type of document (pdf, docx, txt, md)
            user_preferences: Optional user preferences for generation
            
        Returns:
            WorkflowGenerationResult with the generated workflow
        """
        logger.info(f"Generating workflow from {document_type} document content")
        
        # Process document content the same as text description
        # This ensures consistency as per Property 5 in the design
        return await self.generate_from_text(
            description=document_content,
            user_preferences=user_preferences
        )
    
    async def refine_workflow(
        self,
        current_workflow: Dict[str, Any],
        modification_request: str,
        conversation_history: List[Any]
    ) -> WorkflowGenerationResult:
        """
        Refine an existing workflow based on user modification request.
        
        This method implements surgical workflow updates that preserve unchanged
        portions while applying requested modifications. It also handles
        clarification requests and generates explanations of changes.
        
        Args:
            current_workflow: Current workflow JSON
            modification_request: User's modification request
            conversation_history: Previous conversation messages
            
        Returns:
            WorkflowGenerationResult with the refined workflow
        """
        try:
            logger.info(f"Refining workflow with request: {modification_request[:100]}...")
            
            # Query available agents for context
            available_agents = await self._query_available_agents()
            
            # Use refinement service to apply modifications
            modified_workflow, explanation, suggestions = await self.refinement_service.refine_workflow(
                current_workflow=current_workflow,
                modification_request=modification_request,
                conversation_history=conversation_history,
                available_agents=available_agents
            )
            
            # If this was a clarification request, return without workflow
            if modified_workflow is None:
                return WorkflowGenerationResult(
                    success=True,
                    workflow_json=None,
                    explanation=explanation,
                    validation_errors=[],
                    suggestions=suggestions,
                    agents_used=[]
                )
            
            # Validate the modified workflow
            corrected_workflow, errors, auto_corrections = await self._validate_and_correct(modified_workflow)
            
            # Identify agents used
            agents_used = self._assign_agents_to_steps(corrected_workflow, available_agents)
            
            # Combine suggestions
            all_suggestions = suggestions + auto_corrections
            
            success = len(errors) == 0
            
            return WorkflowGenerationResult(
                success=success,
                workflow_json=corrected_workflow,
                explanation=explanation,
                validation_errors=errors,
                suggestions=all_suggestions,
                agents_used=agents_used
            )
            
        except Exception as e:
            logger.error(f"Error refining workflow: {e}", exc_info=True)
            return WorkflowGenerationResult(
                success=False,
                workflow_json=None,
                explanation=f"Error refining workflow: {str(e)}",
                validation_errors=[str(e)],
                suggestions=["Check the error message and try again"]
            )
    
    async def validate_workflow(
        self,
        workflow_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a workflow JSON structure.
        
        Args:
            workflow_json: Workflow JSON to validate
            
        Returns:
            Validation result with errors and suggestions
        """
        validation_result = await self.validation_service.validate_workflow(workflow_json)
        return validation_result.to_dict()
    
    async def suggest_agents_for_capability(
        self,
        capability_description: str
    ) -> AgentSuggestionResult:
        """
        Suggest agents for a given capability requirement.
        
        This method implements requirements 4.3, 4.4, and 4.5:
        - 4.3: Handle no-match scenarios with alternatives
        - 4.4: Include agent descriptions in suggestions
        - 4.5: Present multi-agent choices for ambiguous cases
        
        Args:
            capability_description: Description of required capability
            
        Returns:
            AgentSuggestionResult with suggestions and guidance
        """
        logger.info(f"Suggesting agents for capability: {capability_description[:100]}...")
        
        # Get all available agents
        available_agents = await self._query_available_agents()
        
        # Use suggestion service to generate suggestions
        suggestion_result = self.suggestion_service.suggest_agents(
            capability_description=capability_description,
            available_agents=available_agents
        )
        
        return suggestion_result
    
    async def save_workflow(
        self,
        workflow_json: Dict[str, Any],
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save a workflow to the system via workflow API.
        
        This method creates a workflow definition via the workflow API,
        implementing unique name generation, conflict resolution, and
        error handling as specified in requirements 6.1-6.5.
        
        Args:
            workflow_json: Workflow JSON to save
            name: Name for the workflow
            description: Optional description
            
        Returns:
            Dictionary containing:
                - workflow_id: UUID of the created workflow
                - name: Final workflow name used
                - version: Workflow version number
                - link: URL to view the workflow
                - status: Workflow status
                
        Raises:
            ValueError: If workflow creation fails
            
        Requirements:
        - 6.1: Creates workflow via workflow API
        - 6.2: Generates unique workflow names
        - 6.3: Resolves name conflicts
        - 6.4: Returns workflow ID and link
        - 6.5: Handles errors and allows retry
        """
        from .workflow_api_client import WorkflowAPIClient
        
        logger.info(f"Saving workflow with name: {name}")
        
        # Create API client
        api_client = WorkflowAPIClient()
        
        try:
            # Create workflow via API
            result = await api_client.create_workflow(
                workflow_json=workflow_json,
                name=name,
                description=description
            )
            
            logger.info(f"Successfully saved workflow '{result['name']}' with ID: {result['workflow_id']}")
            
            return result
            
        except ValueError as e:
            logger.error(f"Failed to save workflow: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving workflow: {e}", exc_info=True)
            raise ValueError(f"Failed to save workflow: {str(e)}")

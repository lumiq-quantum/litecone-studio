"""API routes for AI workflow generator."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
from uuid import UUID
import logging

from api.schemas.ai_workflow import (
    WorkflowGenerationRequest,
    WorkflowGenerationResponse,
    ChatSessionCreateRequest,
    ChatSessionResponse,
    ChatMessageRequest,
    WorkflowSaveRequest,
    WorkflowSaveResponse,
    AgentSuggestionRequest,
    AgentSuggestionResponse,
    AgentSuggestionItem,
    ErrorResponse
)
from api.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from api.services.ai_workflow_generator.workflow_generation import WorkflowGenerationService
from api.services.ai_workflow_generator.chat_session import ChatSessionManager, Message
from api.services.ai_workflow_generator.document_processing import DocumentProcessingService, DocumentProcessingError
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai-workflows",
    tags=["AI Workflows"],
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)


@router.post(
    "/generate",
    response_model=WorkflowGenerationResponse,
    summary="Generate workflow from text description",
    description="Generate a workflow JSON from a natural language description"
)
async def generate_workflow(
    request: WorkflowGenerationRequest,
    db: AsyncSession = Depends(get_db)
) -> WorkflowGenerationResponse:
    """
    Generate a workflow from natural language description.
    
    This endpoint implements Requirement 1.1: Parse natural language descriptions
    and generate valid workflow JSON with appropriate agent assignments.
    
    Args:
        request: Workflow generation request with description and preferences
        db: Database session
        
    Returns:
        WorkflowGenerationResponse with generated workflow and explanation
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        logger.info(f"Generating workflow from description: {request.description[:100]}...")
        
        # Create workflow generation service
        service = WorkflowGenerationService(db)
        
        # Generate workflow from text
        result = await service.generate_from_text(
            description=request.description,
            user_preferences=request.user_preferences
        )
        
        # Convert result to response schema
        return WorkflowGenerationResponse(
            success=result.success,
            workflow_json=result.workflow_json,
            explanation=result.explanation,
            validation_errors=result.validation_errors,
            suggestions=result.suggestions,
            agents_used=result.agents_used
        )
        
    except Exception as e:
        logger.error(f"Error generating workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate workflow: {str(e)}"
        )


@router.post(
    "/upload",
    response_model=WorkflowGenerationResponse,
    summary="Generate workflow from document",
    description="Upload a document and generate a workflow from its content"
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> WorkflowGenerationResponse:
    """
    Generate a workflow from an uploaded document.
    
    This endpoint implements Requirement 2.1: Extract text from documents
    (PDF, DOCX, TXT, MD) and generate workflows from the content.
    
    Args:
        file: Uploaded document file
        db: Database session
        
    Returns:
        WorkflowGenerationResponse with generated workflow and explanation
        
    Raises:
        HTTPException: If upload or generation fails
    """
    try:
        logger.info(f"Processing uploaded document: {file.filename}")
        
        # Extract file type from filename
        file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        logger.info(f"File size: {file_size} bytes, type: {file_type}")
        
        # Create document processing service
        doc_service = DocumentProcessingService()
        
        # Validate file
        validation_result = doc_service.validate_file(file_size, file_type)
        if not validation_result["valid"]:
            logger.warning(f"File validation failed: {validation_result['error']}")
            raise HTTPException(
                status_code=400,
                detail=validation_result["error"]
            )
        
        # Extract text from document
        try:
            extracted_text = await doc_service.extract_text(file_content, file_type)
            logger.info(f"Extracted {len(extracted_text)} characters from document")
        except DocumentProcessingError as e:
            logger.error(f"Document processing error: {e.message}")
            raise HTTPException(
                status_code=400,
                detail=e.message
            )
        
        # Create workflow generation service
        workflow_service = WorkflowGenerationService(db)
        
        # Generate workflow from document content
        result = await workflow_service.generate_from_document(
            document_content=extracted_text,
            document_type=file_type,
            user_preferences=None
        )
        
        # Convert result to response schema
        return WorkflowGenerationResponse(
            success=result.success,
            workflow_json=result.workflow_json,
            explanation=result.explanation,
            validation_errors=result.validation_errors,
            suggestions=result.suggestions,
            agents_used=result.agents_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post(
    "/chat/sessions",
    response_model=ChatSessionResponse,
    summary="Create a chat session",
    description="Create a new chat session for interactive workflow refinement"
)
async def create_chat_session(
    request: ChatSessionCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> ChatSessionResponse:
    """
    Create a new chat session for interactive workflow refinement.
    
    This endpoint implements Requirement 3.1: Create stateful sessions that
    maintain conversation history and current workflow state.
    
    Args:
        request: Chat session creation request
        db: Database session
        
    Returns:
        ChatSessionResponse with session details
        
    Raises:
        HTTPException: If session creation fails
    """
    try:
        logger.info("Creating new chat session")
        
        # Create chat session manager
        session_manager = ChatSessionManager(db)
        
        # Create session
        session = await session_manager.create_session(
            initial_description=request.initial_description,
            user_id=request.user_id
        )
        
        logger.info(f"Created chat session: {session.id}")
        
        # If initial description provided, generate workflow immediately
        if request.initial_description:
            logger.info("Generating initial workflow from description")
            workflow_service = WorkflowGenerationService(db)
            
            result = await workflow_service.generate_from_text(
                description=request.initial_description,
                user_preferences=None
            )
            
            # Create assistant response message
            from uuid import uuid4
            assistant_message = Message(
                id=uuid4(),
                role="assistant",
                content=result.explanation,
                timestamp=datetime.utcnow(),
                metadata={
                    "success": result.success,
                    "validation_errors": result.validation_errors,
                    "suggestions": result.suggestions,
                    "agents_used": result.agents_used
                }
            )
            
            session = await session_manager.add_message(session.id, assistant_message)
            
            # Update workflow if one was generated
            if result.workflow_json is not None:
                session = await session_manager.update_workflow(session.id, result.workflow_json)
        
        # Convert to response schema
        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
            expires_at=session.expires_at,
            messages=[
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in session.messages
            ],
            current_workflow=session.current_workflow,
            workflow_history=session.workflow_history
        )
        
    except Exception as e:
        logger.error(f"Error creating chat session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create chat session: {str(e)}"
        )


@router.post(
    "/chat/sessions/{session_id}/messages",
    response_model=ChatSessionResponse,
    summary="Send a chat message",
    description="Send a message to refine the workflow in a chat session"
)
async def send_chat_message(
    session_id: UUID,
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db)
) -> ChatSessionResponse:
    """
    Send a message to refine the workflow in a chat session.
    
    This endpoint implements Requirement 3.2: Update workflow JSON based on
    user requests while preserving unaffected portions.
    
    Args:
        session_id: Chat session ID
        request: Chat message request
        db: Database session
        
    Returns:
        ChatSessionResponse with updated session state
        
    Raises:
        HTTPException: If session not found or message processing fails
    """
    try:
        logger.info(f"Processing message for session {session_id}")
        
        # Create managers and services
        session_manager = ChatSessionManager(db)
        workflow_service = WorkflowGenerationService(db)
        
        # Get existing session
        session = await session_manager.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session {session_id} not found"
            )
        
        # Check if session is expired
        if session.status == "expired":
            raise HTTPException(
                status_code=400,
                detail="Chat session has expired"
            )
        
        # Add user message to session
        user_message = Message(
            id=UUID(int=0),  # Will be replaced when added
            role="user",
            content=request.message,
            timestamp=datetime.utcnow()
        )
        
        from uuid import uuid4
        user_message.id = uuid4()
        session = await session_manager.add_message(session_id, user_message)
        
        # If this is the first message and no workflow exists, generate initial workflow
        if session.current_workflow is None:
            logger.info("Generating initial workflow from first message")
            result = await workflow_service.generate_from_text(
                description=request.message,
                user_preferences=None
            )
        else:
            # Refine existing workflow
            logger.info("Refining existing workflow")
            result = await workflow_service.refine_workflow(
                current_workflow=session.current_workflow,
                modification_request=request.message,
                conversation_history=session.messages
            )
        
        # Create assistant response message
        assistant_message = Message(
            id=uuid4(),
            role="assistant",
            content=result.explanation,
            timestamp=datetime.utcnow(),
            metadata={
                "success": result.success,
                "validation_errors": result.validation_errors,
                "suggestions": result.suggestions,
                "agents_used": result.agents_used
            }
        )
        
        session = await session_manager.add_message(session_id, assistant_message)
        
        # Update workflow if one was generated/modified
        if result.workflow_json is not None:
            session = await session_manager.update_workflow(session_id, result.workflow_json)
        
        logger.info(f"Successfully processed message for session {session_id}")
        
        # Convert to response schema
        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
            expires_at=session.expires_at,
            messages=[
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in session.messages
            ],
            current_workflow=session.current_workflow,
            workflow_history=session.workflow_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get(
    "/chat/sessions/{session_id}",
    response_model=ChatSessionResponse,
    summary="Get chat session",
    description="Retrieve a chat session with its messages and workflow state"
)
async def get_chat_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ChatSessionResponse:
    """
    Retrieve a chat session with its messages and workflow state.
    
    This endpoint implements Requirement 3.1: Retrieve stateful sessions with
    conversation history and current workflow state.
    
    Args:
        session_id: Chat session ID
        db: Database session
        
    Returns:
        ChatSessionResponse with session details
        
    Raises:
        HTTPException: If session not found
    """
    try:
        logger.info(f"Retrieving chat session {session_id}")
        
        # Create chat session manager
        session_manager = ChatSessionManager(db)
        
        # Get session
        session = await session_manager.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session {session_id} not found"
            )
        
        logger.info(f"Retrieved chat session {session_id} with {len(session.messages)} messages")
        
        # Convert to response schema
        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
            expires_at=session.expires_at,
            messages=[
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in session.messages
            ],
            current_workflow=session.current_workflow,
            workflow_history=session.workflow_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chat session: {str(e)}"
        )


@router.delete(
    "/chat/sessions/{session_id}",
    summary="Delete chat session",
    description="Delete a chat session and its data"
)
async def delete_chat_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a chat session and its data.
    
    This endpoint implements session cleanup functionality, allowing users
    to delete sessions they no longer need.
    
    Args:
        session_id: Chat session ID
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If session not found or deletion fails
    """
    try:
        logger.info(f"Deleting chat session {session_id}")
        
        # Create chat session manager
        session_manager = ChatSessionManager(db)
        
        # Check if session exists
        session = await session_manager.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session {session_id} not found"
            )
        
        # Delete session
        await session_manager.delete_session(session_id)
        
        logger.info(f"Successfully deleted chat session {session_id}")
        
        return {
            "message": f"Chat session {session_id} deleted successfully",
            "session_id": str(session_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chat session: {str(e)}"
        )


@router.post(
    "/chat/sessions/{session_id}/save",
    response_model=WorkflowSaveResponse,
    summary="Save workflow from session",
    description="Save the current workflow from a chat session to the system"
)
async def save_workflow_from_session(
    session_id: UUID,
    request: WorkflowSaveRequest,
    db: AsyncSession = Depends(get_db)
) -> WorkflowSaveResponse:
    """
    Save the current workflow from a chat session to the system.
    
    This endpoint implements Requirement 6.1: Create workflow definitions via
    the workflow API with unique names and proper error handling.
    
    Args:
        session_id: Chat session ID
        request: Workflow save request with name and description
        db: Database session
        
    Returns:
        WorkflowSaveResponse with workflow ID and URL
        
    Raises:
        HTTPException: If session not found, no workflow exists, or save fails
    """
    try:
        logger.info(f"Saving workflow from session {session_id}")
        
        # Create managers and services
        session_manager = ChatSessionManager(db)
        workflow_service = WorkflowGenerationService(db)
        
        # Get session
        session = await session_manager.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session {session_id} not found"
            )
        
        # Check if session has a workflow
        if session.current_workflow is None:
            raise HTTPException(
                status_code=400,
                detail="No workflow to save in this session"
            )
        
        # Save workflow
        try:
            result = await workflow_service.save_workflow(
                workflow_json=session.current_workflow,
                name=request.name,
                description=request.description
            )
            
            logger.info(f"Successfully saved workflow '{result['name']}' with ID: {result['workflow_id']}")
            
            # Mark session as completed
            from api.models.ai_workflow import ChatSessionModel
            from sqlalchemy import select, update
            
            await db.execute(
                update(ChatSessionModel)
                .where(ChatSessionModel.id == session_id)
                .values(status="completed")
            )
            await db.commit()
            
            # Convert to response schema
            return WorkflowSaveResponse(
                workflow_id=result['workflow_id'],
                name=result['name'],
                url=result.get('link', f"/workflows/{result['workflow_id']}")
            )
            
        except ValueError as e:
            logger.error(f"Failed to save workflow: {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving workflow from session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save workflow: {str(e)}"
        )


@router.get(
    "/chat/sessions/{session_id}/export",
    summary="Export workflow JSON",
    description="Export the current workflow JSON from a session as a downloadable file"
)
async def export_workflow(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Export the current workflow JSON from a session.
    
    This endpoint implements Requirement 8.3: Provide workflow JSON as a
    downloadable file for users to review or share.
    
    Args:
        session_id: Chat session ID
        db: Database session
        
    Returns:
        JSON response with workflow data and download headers
        
    Raises:
        HTTPException: If session not found or no workflow exists
    """
    try:
        logger.info(f"Exporting workflow from session {session_id}")
        
        # Create chat session manager
        session_manager = ChatSessionManager(db)
        
        # Get session
        session = await session_manager.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session {session_id} not found"
            )
        
        # Check if session has a workflow
        if session.current_workflow is None:
            raise HTTPException(
                status_code=400,
                detail="No workflow to export in this session"
            )
        
        logger.info(f"Exporting workflow from session {session_id}")
        
        # Generate filename
        workflow_name = session.current_workflow.get('name', 'workflow')
        # Sanitize filename
        import re
        safe_name = re.sub(r'[^\w\-_]', '_', workflow_name)
        filename = f"{safe_name}.json"
        
        # Return workflow JSON with download headers
        return JSONResponse(
            content=session.current_workflow,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/json"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export workflow: {str(e)}"
        )


@router.post(
    "/agents/suggest",
    response_model=AgentSuggestionResponse,
    summary="Suggest agents for capability",
    description="Get agent suggestions for a required capability with descriptions and alternatives"
)
async def suggest_agents(
    request: AgentSuggestionRequest,
    db: AsyncSession = Depends(get_db)
) -> AgentSuggestionResponse:
    """
    Suggest agents for a given capability requirement.
    
    This endpoint implements Requirements 4.3, 4.4, and 4.5:
    - 4.3: Handle no-match scenarios with alternatives
    - 4.4: Include agent descriptions in suggestions
    - 4.5: Present multi-agent choices for ambiguous cases
    
    Args:
        request: Agent suggestion request with capability description
        db: Database session
        
    Returns:
        AgentSuggestionResponse with suggestions, explanations, and alternatives
        
    Raises:
        HTTPException: If suggestion generation fails
    """
    try:
        logger.info(f"Suggesting agents for capability: {request.capability_description[:100]}...")
        
        # Create workflow generation service
        service = WorkflowGenerationService(db)
        
        # Get agent suggestions
        result = await service.suggest_agents_for_capability(
            capability_description=request.capability_description
        )
        
        # Convert suggestions to response format
        suggestion_items = []
        for suggestion in result.suggestions:
            suggestion_items.append(AgentSuggestionItem(
                agent_name=suggestion.agent.name,
                agent_url=suggestion.agent.url,
                agent_description=suggestion.agent.description,
                capabilities=suggestion.agent.capabilities,
                relevance_score=suggestion.relevance_score,
                reason=suggestion.reason
            ))
        
        # Build response
        return AgentSuggestionResponse(
            suggestions=suggestion_items,
            is_ambiguous=result.is_ambiguous,
            requires_user_choice=result.requires_user_choice,
            no_match=result.no_match,
            alternatives=result.alternatives,
            explanation=result.explanation
        )
        
    except Exception as e:
        logger.error(f"Error suggesting agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to suggest agents: {str(e)}"
        )

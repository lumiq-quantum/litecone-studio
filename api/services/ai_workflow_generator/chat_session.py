"""Chat session manager for stateful workflow refinement conversations."""

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from api.models.ai_workflow import ChatSessionModel
from api.config import settings


class Message:
    """Chat message."""
    
    def __init__(
        self,
        id: UUID,
        role: str,
        content: str,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            id=UUID(data["id"]),
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


class ChatSession:
    """Chat session for workflow refinement."""
    
    def __init__(
        self,
        id: UUID,
        user_id: Optional[str],
        created_at: datetime,
        updated_at: datetime,
        expires_at: datetime,
        status: str,
        messages: List[Message],
        current_workflow: Optional[Dict[str, Any]] = None,
        workflow_history: Optional[List[Dict[str, Any]]] = None
    ):
        self.id = id
        self.user_id = user_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.expires_at = expires_at
        self.status = status
        self.messages = messages
        self.current_workflow = current_workflow
        self.workflow_history = workflow_history or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status,
            "messages": [msg.to_dict() for msg in self.messages],
            "current_workflow": self.current_workflow,
            "workflow_history": self.workflow_history
        }
    
    @classmethod
    def from_model(cls, model: ChatSessionModel) -> "ChatSession":
        """Create session from database model."""
        messages = [Message.from_dict(msg) for msg in (model.messages or [])]
        return cls(
            id=model.id,
            user_id=model.user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            expires_at=model.expires_at,
            status=model.status,
            messages=messages,
            current_workflow=model.current_workflow,
            workflow_history=model.workflow_history or []
        )


class ChatSessionManager:
    """Manager for chat sessions."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the chat session manager.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_session(
        self,
        initial_description: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            initial_description: Optional initial workflow description
            user_id: Optional user ID
            
        Returns:
            Created chat session
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=settings.session_timeout_minutes)
        
        # Create initial messages if description provided
        messages = []
        if initial_description:
            message = Message(
                id=uuid4(),
                role="user",
                content=initial_description,
                timestamp=now
            )
            messages.append(message)
        
        # Create database model
        session_model = ChatSessionModel(
            id=uuid4(),
            user_id=user_id,
            status="active",
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            messages=[msg.to_dict() for msg in messages],
            current_workflow=None,
            workflow_history=[]
        )
        
        self.db.add(session_model)
        await self.db.commit()
        await self.db.refresh(session_model)
        
        return ChatSession.from_model(session_model)
    
    async def get_session(
        self,
        session_id: UUID
    ) -> Optional[ChatSession]:
        """
        Get an existing chat session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Chat session or None if not found
        """
        result = await self.db.execute(
            select(ChatSessionModel).where(ChatSessionModel.id == session_id)
        )
        session_model = result.scalar_one_or_none()
        
        if session_model is None:
            return None
        
        # Check if session has expired
        if session_model.expires_at < datetime.utcnow():
            session_model.status = "expired"
            await self.db.commit()
        
        return ChatSession.from_model(session_model)
    
    async def add_message(
        self,
        session_id: UUID,
        message: Message
    ) -> ChatSession:
        """
        Add a message to a session.
        
        Args:
            session_id: Session ID
            message: Message to add
            
        Returns:
            Updated chat session
        """
        result = await self.db.execute(
            select(ChatSessionModel).where(ChatSessionModel.id == session_id)
        )
        session_model = result.scalar_one_or_none()
        
        if session_model is None:
            raise ValueError(f"Session {session_id} not found")
        
        # Add message to list
        messages = session_model.messages or []
        messages.append(message.to_dict())
        session_model.messages = messages
        session_model.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(session_model)
        
        return ChatSession.from_model(session_model)
    
    async def update_workflow(
        self,
        session_id: UUID,
        workflow_json: Dict[str, Any]
    ) -> ChatSession:
        """
        Update the workflow in a session.
        
        Args:
            session_id: Session ID
            workflow_json: New workflow JSON
            
        Returns:
            Updated chat session
        """
        result = await self.db.execute(
            select(ChatSessionModel).where(ChatSessionModel.id == session_id)
        )
        session_model = result.scalar_one_or_none()
        
        if session_model is None:
            raise ValueError(f"Session {session_id} not found")
        
        # Save current workflow to history if it exists
        if session_model.current_workflow is not None:
            history = session_model.workflow_history or []
            history.append({
                "workflow": session_model.current_workflow,
                "timestamp": datetime.utcnow().isoformat()
            })
            session_model.workflow_history = history
        
        # Update current workflow
        session_model.current_workflow = workflow_json
        session_model.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(session_model)
        
        return ChatSession.from_model(session_model)
    
    async def delete_session(
        self,
        session_id: UUID
    ) -> None:
        """
        Delete a chat session.
        
        Args:
            session_id: Session ID
        """
        await self.db.execute(
            delete(ChatSessionModel).where(ChatSessionModel.id == session_id)
        )
        await self.db.commit()
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        
        # First, mark expired sessions
        result = await self.db.execute(
            select(ChatSessionModel).where(
                ChatSessionModel.expires_at < now,
                ChatSessionModel.status == "active"
            )
        )
        expired_sessions = result.scalars().all()
        
        for session in expired_sessions:
            session.status = "expired"
        
        await self.db.commit()
        
        # Delete expired sessions that have been expired for more than 24 hours
        cleanup_threshold = now - timedelta(hours=24)
        result = await self.db.execute(
            delete(ChatSessionModel).where(
                ChatSessionModel.status == "expired",
                ChatSessionModel.expires_at < cleanup_threshold
            )
        )
        await self.db.commit()
        
        return result.rowcount if result.rowcount else 0

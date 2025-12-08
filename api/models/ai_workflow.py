"""Database models for AI workflow generator."""

from sqlalchemy import Column, String, DateTime, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from api.database import Base


class ChatSessionModel(Base):
    """Database model for chat sessions."""
    
    __tablename__ = "ai_chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    current_workflow = Column(JSON, nullable=True)
    workflow_history = Column(JSON, nullable=True, default=list)
    messages = Column(JSON, nullable=False, default=list)
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, status={self.status})>"

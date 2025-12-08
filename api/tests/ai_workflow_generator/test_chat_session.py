"""Tests for chat session manager."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.ai_workflow_generator.chat_session import (
    ChatSessionManager,
    ChatSession,
    Message
)
from api.models.ai_workflow import ChatSessionModel


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def chat_session_manager(mock_db_session):
    """Create a ChatSessionManager instance."""
    return ChatSessionManager(mock_db_session)


@pytest.fixture
def sample_message():
    """Create a sample message."""
    return Message(
        id=uuid4(),
        role="user",
        content="Create a workflow for data processing",
        timestamp=datetime.utcnow(),
        metadata={"source": "test"}
    )


@pytest.fixture
def sample_workflow_json():
    """Sample workflow JSON."""
    return {
        "name": "test-workflow",
        "description": "Test workflow",
        "start_step": "step1",
        "steps": {
            "step1": {
                "agent": "test-agent",
                "input_mapping": {},
                "next_step": None
            }
        }
    }


class TestMessage:
    """Tests for Message class."""
    
    def test_message_creation(self):
        """Test creating a message."""
        msg_id = uuid4()
        timestamp = datetime.utcnow()
        
        message = Message(
            id=msg_id,
            role="user",
            content="Test message",
            timestamp=timestamp,
            metadata={"key": "value"}
        )
        
        assert message.id == msg_id
        assert message.role == "user"
        assert message.content == "Test message"
        assert message.timestamp == timestamp
        assert message.metadata == {"key": "value"}
    
    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg_id = uuid4()
        timestamp = datetime.utcnow()
        
        message = Message(
            id=msg_id,
            role="assistant",
            content="Response",
            timestamp=timestamp
        )
        
        msg_dict = message.to_dict()
        
        assert msg_dict["id"] == str(msg_id)
        assert msg_dict["role"] == "assistant"
        assert msg_dict["content"] == "Response"
        assert msg_dict["timestamp"] == timestamp.isoformat()
        assert msg_dict["metadata"] == {}
    
    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        msg_id = uuid4()
        timestamp = datetime.utcnow()
        
        msg_dict = {
            "id": str(msg_id),
            "role": "user",
            "content": "Test",
            "timestamp": timestamp.isoformat(),
            "metadata": {"test": "data"}
        }
        
        message = Message.from_dict(msg_dict)
        
        assert message.id == msg_id
        assert message.role == "user"
        assert message.content == "Test"
        assert message.metadata == {"test": "data"}


class TestChatSession:
    """Tests for ChatSession class."""
    
    def test_session_creation(self):
        """Test creating a chat session."""
        session_id = uuid4()
        now = datetime.utcnow()
        expires = now + timedelta(minutes=30)
        
        session = ChatSession(
            id=session_id,
            user_id="test-user",
            created_at=now,
            updated_at=now,
            expires_at=expires,
            status="active",
            messages=[],
            current_workflow=None,
            workflow_history=[]
        )
        
        assert session.id == session_id
        assert session.user_id == "test-user"
        assert session.status == "active"
        assert len(session.messages) == 0
        assert session.current_workflow is None
        assert len(session.workflow_history) == 0
    
    def test_session_to_dict(self):
        """Test converting session to dictionary."""
        session_id = uuid4()
        now = datetime.utcnow()
        expires = now + timedelta(minutes=30)
        
        message = Message(
            id=uuid4(),
            role="user",
            content="Test",
            timestamp=now
        )
        
        session = ChatSession(
            id=session_id,
            user_id="test-user",
            created_at=now,
            updated_at=now,
            expires_at=expires,
            status="active",
            messages=[message],
            current_workflow={"test": "workflow"}
        )
        
        session_dict = session.to_dict()
        
        assert session_dict["id"] == str(session_id)
        assert session_dict["user_id"] == "test-user"
        assert session_dict["status"] == "active"
        assert len(session_dict["messages"]) == 1
        assert session_dict["current_workflow"] == {"test": "workflow"}
    
    def test_session_from_model(self):
        """Test creating session from database model."""
        session_id = uuid4()
        now = datetime.utcnow()
        expires = now + timedelta(minutes=30)
        
        msg_dict = {
            "id": str(uuid4()),
            "role": "user",
            "content": "Test",
            "timestamp": now.isoformat(),
            "metadata": {}
        }
        
        model = ChatSessionModel(
            id=session_id,
            user_id="test-user",
            status="active",
            created_at=now,
            updated_at=now,
            expires_at=expires,
            messages=[msg_dict],
            current_workflow={"test": "workflow"},
            workflow_history=[]
        )
        
        session = ChatSession.from_model(model)
        
        assert session.id == session_id
        assert session.user_id == "test-user"
        assert session.status == "active"
        assert len(session.messages) == 1
        assert session.current_workflow == {"test": "workflow"}


class TestChatSessionManager:
    """Tests for ChatSessionManager."""
    
    @pytest.mark.asyncio
    async def test_create_session_without_description(self, chat_session_manager, mock_db_session):
        """Test creating a session without initial description."""
        session_id = uuid4()
        now = datetime.utcnow()
        
        # Mock database operations
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Mock the refresh to set the ID
        async def mock_refresh(obj):
            obj.id = session_id
            obj.created_at = now
            obj.updated_at = now
            obj.expires_at = now + timedelta(minutes=30)
        
        mock_db_session.refresh.side_effect = mock_refresh
        
        session = await chat_session_manager.create_session(user_id="test-user")
        
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert session.user_id == "test-user"
        assert session.status == "active"
        assert len(session.messages) == 0
    
    @pytest.mark.asyncio
    async def test_create_session_with_description(self, chat_session_manager, mock_db_session):
        """Test creating a session with initial description."""
        session_id = uuid4()
        now = datetime.utcnow()
        
        # Mock database operations
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Mock the refresh to set the ID
        async def mock_refresh(obj):
            obj.id = session_id
            obj.created_at = now
            obj.updated_at = now
            obj.expires_at = now + timedelta(minutes=30)
        
        mock_db_session.refresh.side_effect = mock_refresh
        
        session = await chat_session_manager.create_session(
            initial_description="Create a data processing workflow",
            user_id="test-user"
        )
        
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert session.user_id == "test-user"
        assert len(session.messages) == 1
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "Create a data processing workflow"
    
    @pytest.mark.asyncio
    async def test_get_session_found(self, chat_session_manager, mock_db_session):
        """Test getting an existing session."""
        session_id = uuid4()
        now = datetime.utcnow()
        expires = now + timedelta(minutes=30)
        
        # Create mock session model
        mock_model = ChatSessionModel(
            id=session_id,
            user_id="test-user",
            status="active",
            created_at=now,
            updated_at=now,
            expires_at=expires,
            messages=[],
            current_workflow=None,
            workflow_history=[]
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        
        session = await chat_session_manager.get_session(session_id)
        
        assert session is not None
        assert session.id == session_id
        assert session.user_id == "test-user"
        assert session.status == "active"
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, chat_session_manager, mock_db_session):
        """Test getting a non-existent session."""
        session_id = uuid4()
        
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        session = await chat_session_manager.get_session(session_id)
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_get_session_expired(self, chat_session_manager, mock_db_session):
        """Test getting an expired session."""
        session_id = uuid4()
        now = datetime.utcnow()
        expires = now - timedelta(minutes=1)  # Expired 1 minute ago
        
        # Create mock session model
        mock_model = ChatSessionModel(
            id=session_id,
            user_id="test-user",
            status="active",
            created_at=now - timedelta(hours=1),
            updated_at=now - timedelta(hours=1),
            expires_at=expires,
            messages=[],
            current_workflow=None,
            workflow_history=[]
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        
        session = await chat_session_manager.get_session(session_id)
        
        assert session is not None
        assert session.status == "expired"
        assert mock_db_session.commit.called
    
    @pytest.mark.asyncio
    async def test_add_message(self, chat_session_manager, mock_db_session, sample_message):
        """Test adding a message to a session."""
        session_id = uuid4()
        now = datetime.utcnow()
        
        # Create mock session model
        mock_model = ChatSessionModel(
            id=session_id,
            user_id="test-user",
            status="active",
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(minutes=30),
            messages=[],
            current_workflow=None,
            workflow_history=[]
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        session = await chat_session_manager.add_message(session_id, sample_message)
        
        assert mock_db_session.commit.called
        assert len(session.messages) == 1
        assert session.messages[0].content == sample_message.content
    
    @pytest.mark.asyncio
    async def test_add_message_session_not_found(self, chat_session_manager, mock_db_session, sample_message):
        """Test adding a message to a non-existent session."""
        session_id = uuid4()
        
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(ValueError, match="Session .* not found"):
            await chat_session_manager.add_message(session_id, sample_message)
    
    @pytest.mark.asyncio
    async def test_update_workflow(self, chat_session_manager, mock_db_session, sample_workflow_json):
        """Test updating workflow in a session."""
        session_id = uuid4()
        now = datetime.utcnow()
        
        # Create mock session model
        mock_model = ChatSessionModel(
            id=session_id,
            user_id="test-user",
            status="active",
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(minutes=30),
            messages=[],
            current_workflow=None,
            workflow_history=[]
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        session = await chat_session_manager.update_workflow(session_id, sample_workflow_json)
        
        assert mock_db_session.commit.called
        assert session.current_workflow == sample_workflow_json
        assert len(session.workflow_history) == 0  # No previous workflow
    
    @pytest.mark.asyncio
    async def test_update_workflow_with_history(self, chat_session_manager, mock_db_session, sample_workflow_json):
        """Test updating workflow when there's already a workflow."""
        session_id = uuid4()
        now = datetime.utcnow()
        
        old_workflow = {"name": "old-workflow", "steps": {}}
        
        # Create mock session model with existing workflow
        mock_model = ChatSessionModel(
            id=session_id,
            user_id="test-user",
            status="active",
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(minutes=30),
            messages=[],
            current_workflow=old_workflow,
            workflow_history=[]
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        session = await chat_session_manager.update_workflow(session_id, sample_workflow_json)
        
        assert mock_db_session.commit.called
        assert session.current_workflow == sample_workflow_json
        assert len(session.workflow_history) == 1
        assert session.workflow_history[0]["workflow"] == old_workflow
    
    @pytest.mark.asyncio
    async def test_update_workflow_session_not_found(self, chat_session_manager, mock_db_session, sample_workflow_json):
        """Test updating workflow for a non-existent session."""
        session_id = uuid4()
        
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(ValueError, match="Session .* not found"):
            await chat_session_manager.update_workflow(session_id, sample_workflow_json)
    
    @pytest.mark.asyncio
    async def test_delete_session(self, chat_session_manager, mock_db_session):
        """Test deleting a session."""
        session_id = uuid4()
        
        # Mock database delete
        mock_result = MagicMock()
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        
        await chat_session_manager.delete_session(session_id)
        
        assert mock_db_session.execute.called
        assert mock_db_session.commit.called
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, chat_session_manager, mock_db_session):
        """Test cleaning up expired sessions."""
        now = datetime.utcnow()
        
        # Create mock expired sessions
        expired_session1 = ChatSessionModel(
            id=uuid4(),
            user_id="user1",
            status="active",
            created_at=now - timedelta(hours=25),
            updated_at=now - timedelta(hours=25),
            expires_at=now - timedelta(hours=24, minutes=30),
            messages=[],
            current_workflow=None,
            workflow_history=[]
        )
        
        expired_session2 = ChatSessionModel(
            id=uuid4(),
            user_id="user2",
            status="active",
            created_at=now - timedelta(hours=26),
            updated_at=now - timedelta(hours=26),
            expires_at=now - timedelta(hours=25),
            messages=[],
            current_workflow=None,
            workflow_history=[]
        )
        
        # Mock database queries
        mock_select_result = MagicMock()
        mock_select_result.scalars.return_value.all.return_value = [expired_session1, expired_session2]
        
        mock_delete_result = MagicMock()
        mock_delete_result.rowcount = 2
        
        mock_db_session.execute = AsyncMock(side_effect=[mock_select_result, mock_delete_result])
        mock_db_session.commit = AsyncMock()
        
        count = await chat_session_manager.cleanup_expired_sessions()
        
        assert count == 2
        assert mock_db_session.commit.call_count == 2
        assert expired_session1.status == "expired"
        assert expired_session2.status == "expired"

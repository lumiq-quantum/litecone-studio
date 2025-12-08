"""Integration tests for chat session manager demonstrating full workflow."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from api.services.ai_workflow_generator.chat_session import (
    ChatSessionManager,
    Message
)
from api.models.ai_workflow import ChatSessionModel


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def chat_session_manager(mock_db_session):
    """Create a ChatSessionManager instance."""
    return ChatSessionManager(mock_db_session)


class TestChatSessionIntegration:
    """Integration tests for chat session workflow."""
    
    @pytest.mark.asyncio
    async def test_full_chat_workflow(self, chat_session_manager, mock_db_session):
        """Test a complete chat workflow from creation to workflow updates."""
        session_id = uuid4()
        now = datetime.utcnow()
        
        # Step 1: Create session with initial description
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
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
        
        assert session.user_id == "test-user"
        assert len(session.messages) == 1
        assert session.messages[0].content == "Create a data processing workflow"
        
        # Step 2: Add assistant response
        mock_model = ChatSessionModel(
            id=session_id,
            user_id="test-user",
            status="active",
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(minutes=30),
            messages=[session.messages[0].to_dict()],
            current_workflow=None,
            workflow_history=[]
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        assistant_message = Message(
            id=uuid4(),
            role="assistant",
            content="I'll create a workflow with data processing steps",
            timestamp=datetime.utcnow()
        )
        
        session = await chat_session_manager.add_message(session_id, assistant_message)
        assert len(session.messages) == 2
        
        # Step 3: Update workflow
        workflow_v1 = {
            "name": "data-processing",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "agent": "data-processor",
                    "input_mapping": {}
                }
            }
        }
        
        session = await chat_session_manager.update_workflow(session_id, workflow_v1)
        assert session.current_workflow == workflow_v1
        assert len(session.workflow_history) == 0
        
        # Step 4: User requests modification
        mock_model.current_workflow = workflow_v1
        user_message = Message(
            id=uuid4(),
            role="user",
            content="Add a validation step",
            timestamp=datetime.utcnow()
        )
        
        session = await chat_session_manager.add_message(session_id, user_message)
        assert len(session.messages) == 3
        
        # Step 5: Update workflow with modification
        workflow_v2 = {
            "name": "data-processing",
            "start_step": "step1",
            "steps": {
                "step1": {
                    "agent": "data-processor",
                    "input_mapping": {},
                    "next_step": "step2"
                },
                "step2": {
                    "agent": "validator",
                    "input_mapping": {}
                }
            }
        }
        
        session = await chat_session_manager.update_workflow(session_id, workflow_v2)
        assert session.current_workflow == workflow_v2
        assert len(session.workflow_history) == 1
        assert session.workflow_history[0]["workflow"] == workflow_v1
    
    @pytest.mark.asyncio
    async def test_session_lifecycle(self, chat_session_manager, mock_db_session):
        """Test complete session lifecycle including cleanup."""
        session_id = uuid4()
        now = datetime.utcnow()
        
        # Create session
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        async def mock_refresh(obj):
            obj.id = session_id
            obj.created_at = now
            obj.updated_at = now
            obj.expires_at = now + timedelta(minutes=30)
        
        mock_db_session.refresh.side_effect = mock_refresh
        
        session = await chat_session_manager.create_session(user_id="test-user")
        assert session.status == "active"
        
        # Get session
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
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        retrieved_session = await chat_session_manager.get_session(session_id)
        assert retrieved_session is not None
        assert retrieved_session.id == session_id
        
        # Delete session
        mock_db_session.execute = AsyncMock()
        await chat_session_manager.delete_session(session_id)
        assert mock_db_session.commit.called

"""Add AI chat sessions table

Revision ID: 002_ai_chat_sessions
Revises: 001_initial
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_ai_chat_sessions'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ai_chat_sessions table."""
    op.create_table(
        'ai_chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('current_workflow', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('workflow_history', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('messages', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for common queries
    op.create_index('ix_ai_chat_sessions_user_id', 'ai_chat_sessions', ['user_id'])
    op.create_index('ix_ai_chat_sessions_status', 'ai_chat_sessions', ['status'])
    op.create_index('ix_ai_chat_sessions_expires_at', 'ai_chat_sessions', ['expires_at'])


def downgrade() -> None:
    """Drop ai_chat_sessions table."""
    op.drop_index('ix_ai_chat_sessions_expires_at', table_name='ai_chat_sessions')
    op.drop_index('ix_ai_chat_sessions_status', table_name='ai_chat_sessions')
    op.drop_index('ix_ai_chat_sessions_user_id', table_name='ai_chat_sessions')
    op.drop_table('ai_chat_sessions')

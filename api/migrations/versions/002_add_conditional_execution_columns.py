"""Add conditional execution columns

Revision ID: 002_conditional
Revises: 70b7d11bef31
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_conditional'
down_revision = '70b7d11bef31'
branch_labels = None
depends_on = None


def upgrade():
    """Add columns for conditional execution tracking."""
    # Add conditional execution tracking columns to step_executions table
    op.add_column('step_executions', 
        sa.Column('condition_expression', sa.Text(), nullable=True))
    op.add_column('step_executions', 
        sa.Column('condition_result', sa.Boolean(), nullable=True))
    op.add_column('step_executions', 
        sa.Column('branch_taken', sa.String(50), nullable=True))


def downgrade():
    """Remove conditional execution columns."""
    op.drop_column('step_executions', 'branch_taken')
    op.drop_column('step_executions', 'condition_result')
    op.drop_column('step_executions', 'condition_expression')

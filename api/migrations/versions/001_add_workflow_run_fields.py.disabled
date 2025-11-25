"""Add workflow_definition_id, input_data, triggered_by, cancelled_at, cancelled_by to workflow_runs

Revision ID: 001
Revises: 
Create Date: 2025-11-07 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add new fields to workflow_runs table."""
    # Add workflow_definition_id column
    op.add_column(
        'workflow_runs',
        sa.Column('workflow_definition_id', sa.String(255), nullable=True)
    )
    
    # Add input_data column
    op.add_column(
        'workflow_runs',
        sa.Column('input_data', JSONB, nullable=True)
    )
    
    # Add triggered_by column
    op.add_column(
        'workflow_runs',
        sa.Column('triggered_by', sa.String(255), nullable=True)
    )
    
    # Add cancelled_at column
    op.add_column(
        'workflow_runs',
        sa.Column('cancelled_at', sa.DateTime(), nullable=True)
    )
    
    # Add cancelled_by column
    op.add_column(
        'workflow_runs',
        sa.Column('cancelled_by', sa.String(255), nullable=True)
    )
    
    # Create index on workflow_definition_id for faster lookups
    op.create_index(
        'idx_run_workflow_definition_id',
        'workflow_runs',
        ['workflow_definition_id']
    )


def downgrade() -> None:
    """Downgrade schema - remove added fields from workflow_runs table."""
    # Drop index first
    op.drop_index('idx_run_workflow_definition_id', table_name='workflow_runs')
    
    # Drop columns in reverse order
    op.drop_column('workflow_runs', 'cancelled_by')
    op.drop_column('workflow_runs', 'cancelled_at')
    op.drop_column('workflow_runs', 'triggered_by')
    op.drop_column('workflow_runs', 'input_data')
    op.drop_column('workflow_runs', 'workflow_definition_id')

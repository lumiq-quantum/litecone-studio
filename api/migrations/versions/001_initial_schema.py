"""Initial schema - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2025-11-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for the workflow management system."""
    
    # =========================================================================
    # EXECUTION TRACKING TABLES (from src/database/models.py)
    # =========================================================================
    
    # Create workflow_runs table
    op.create_table(
        'workflow_runs',
        sa.Column('run_id', sa.String(255), primary_key=True),
        sa.Column('workflow_id', sa.String(255), nullable=False),
        sa.Column('workflow_name', sa.String(255), nullable=False),
        sa.Column('workflow_definition_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('input_data', JSONB, nullable=True),
        sa.Column('triggered_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.String(255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_index('idx_run_status', 'workflow_runs', ['status'])
    op.create_index('idx_run_workflow_definition_id', 'workflow_runs', ['workflow_definition_id'])
    
    # Create step_executions table
    op.create_table(
        'step_executions',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('run_id', sa.String(255), sa.ForeignKey('workflow_runs.run_id'), nullable=False),
        sa.Column('step_id', sa.String(255), nullable=False),
        sa.Column('step_name', sa.String(255), nullable=False),
        sa.Column('agent_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('input_data', JSONB, nullable=False),
        sa.Column('output_data', JSONB, nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('parent_step_id', sa.String(255), nullable=True),
        sa.Column('branch_name', sa.String(255), nullable=True),
        sa.Column('join_policy', sa.String(50), nullable=True),
    )
    op.create_index('idx_step_run_id', 'step_executions', ['run_id'])
    op.create_index('idx_step_status', 'step_executions', ['status'])
    op.create_index('idx_step_branch', 'step_executions', ['run_id', 'parent_step_id', 'branch_name'])
    
    # =========================================================================
    # API MANAGEMENT TABLES (from api/models/)
    # =========================================================================
    
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('url', sa.String(512), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('auth_type', sa.String(50), nullable=True),
        sa.Column('auth_config', JSONB, nullable=True),
        sa.Column('timeout_ms', sa.Integer(), nullable=False, server_default='30000'),
        sa.Column('retry_config', JSONB, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_agents_name', 'agents', ['name'])
    op.create_index('idx_agents_status', 'agents', ['status'])
    op.create_index(op.f('ix_agents_name'), 'agents', ['name'], unique=True)
    op.create_index(op.f('ix_agents_status'), 'agents', ['status'])
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=True),
        sa.Column('changes', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_entity_id', 'audit_logs', ['entity_id'])
    op.create_index('idx_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('idx_audit_logs_entity_type_id', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'])
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'])
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'])
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'])
    
    # Create workflow_definitions table
    op.create_table(
        'workflow_definitions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('workflow_data', JSONB, nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_workflow_definitions_name', 'workflow_definitions', ['name'])
    op.create_index('idx_workflow_definitions_name_version', 'workflow_definitions', ['name', 'version'], unique=True)
    op.create_index('idx_workflow_definitions_status', 'workflow_definitions', ['status'])
    op.create_index('idx_workflow_definitions_version', 'workflow_definitions', ['version'])
    op.create_index(op.f('ix_workflow_definitions_name'), 'workflow_definitions', ['name'])
    op.create_index(op.f('ix_workflow_definitions_status'), 'workflow_definitions', ['status'])
    
    # Create workflow_steps table
    op.create_table(
        'workflow_steps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workflow_id', UUID(as_uuid=True), sa.ForeignKey('workflow_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_id', sa.String(255), nullable=False),
        sa.Column('agent_id', UUID(as_uuid=True), sa.ForeignKey('agents.id'), nullable=True),
        sa.Column('next_step_id', sa.String(255), nullable=True),
        sa.Column('input_mapping', JSONB, nullable=True),
        sa.Column('step_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_workflow_steps_workflow_id', 'workflow_steps', ['workflow_id'])
    op.create_index('idx_workflow_steps_workflow_step', 'workflow_steps', ['workflow_id', 'step_id'], unique=True)
    op.create_index(op.f('ix_workflow_steps_workflow_id'), 'workflow_steps', ['workflow_id'])


def downgrade() -> None:
    """Drop all tables."""
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index(op.f('ix_workflow_steps_workflow_id'), table_name='workflow_steps')
    op.drop_index('idx_workflow_steps_workflow_step', table_name='workflow_steps')
    op.drop_index('idx_workflow_steps_workflow_id', table_name='workflow_steps')
    op.drop_table('workflow_steps')
    
    op.drop_index(op.f('ix_workflow_definitions_status'), table_name='workflow_definitions')
    op.drop_index(op.f('ix_workflow_definitions_name'), table_name='workflow_definitions')
    op.drop_index('idx_workflow_definitions_version', table_name='workflow_definitions')
    op.drop_index('idx_workflow_definitions_status', table_name='workflow_definitions')
    op.drop_index('idx_workflow_definitions_name_version', table_name='workflow_definitions')
    op.drop_index('idx_workflow_definitions_name', table_name='workflow_definitions')
    op.drop_table('workflow_definitions')
    
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity_type_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity_type', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index(op.f('ix_agents_status'), table_name='agents')
    op.drop_index(op.f('ix_agents_name'), table_name='agents')
    op.drop_index('idx_agents_status', table_name='agents')
    op.drop_index('idx_agents_name', table_name='agents')
    op.drop_table('agents')
    
    op.drop_index('idx_step_branch', table_name='step_executions')
    op.drop_index('idx_step_status', table_name='step_executions')
    op.drop_index('idx_step_run_id', table_name='step_executions')
    op.drop_table('step_executions')
    
    op.drop_index('idx_run_workflow_definition_id', table_name='workflow_runs')
    op.drop_index('idx_run_status', table_name='workflow_runs')
    op.drop_table('workflow_runs')

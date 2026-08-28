"""Add activity_logs table

Revision ID: 006
Revises: 005
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'activity_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('entity_type', sa.String(20), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(30), nullable=False),
        sa.Column('description', sa.String(300), nullable=False),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_activity_logs_entity_type', 'activity_logs', ['entity_type'])
    op.create_index('idx_activity_logs_created_at', 'activity_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_activity_logs_created_at', table_name='activity_logs')
    op.drop_index('idx_activity_logs_entity_type', table_name='activity_logs')
    op.drop_table('activity_logs')

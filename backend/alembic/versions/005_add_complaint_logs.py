"""Add complaint_logs table

Revision ID: 005
Revises: 004
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'complaint_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('complaint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(30), nullable=False),
        sa.Column('description', sa.String(300), nullable=False),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_complaint_logs_complaint_id', 'complaint_logs', ['complaint_id'])


def downgrade() -> None:
    op.drop_index('idx_complaint_logs_complaint_id', table_name='complaint_logs')
    op.drop_table('complaint_logs')

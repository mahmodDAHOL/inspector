"""Add complaint_minutes table — investigation minutes (محضر تحقيق) and
meeting minutes (محضر اجتماع), each linked to a complaint with one PDF
attachment.

Revision ID: 009
Revises: 008
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'complaint_minutes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('complaint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('minute_type', sa.String(20), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('minute_date', sa.DateTime(), nullable=False),
        sa.Column('attendees', sa.LargeBinary()),
        sa.Column('summary', sa.LargeBinary(), nullable=False),
        sa.Column('stored_file_name', sa.String(255), nullable=False),
        sa.Column('original_file_name', sa.String(255), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_index('ix_complaint_minutes_complaint_id', 'complaint_minutes', ['complaint_id'])


def downgrade() -> None:
    op.drop_index('ix_complaint_minutes_complaint_id', table_name='complaint_minutes')
    op.drop_table('complaint_minutes')

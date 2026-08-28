"""Add first_response_at to complaints

Revision ID: 004
Revises: 003
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('complaints', sa.Column('first_response_at', sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    op.drop_column('complaints', 'first_response_at')

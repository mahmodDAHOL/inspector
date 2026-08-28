"""Add missing timestamps

Revision ID: 002
Revises: 001
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')))
    op.add_column('users', sa.Column('failed_login_attempts', sa.String(10), server_default=sa.text("'0'")))
    op.add_column('users', sa.Column('locked_until', sa.TIMESTAMP(), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('complaints', sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')))
    op.add_column('complaints', sa.Column('closed_at', sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    op.drop_column('complaints', 'closed_at')
    op.drop_column('complaints', 'updated_at')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'updated_at')

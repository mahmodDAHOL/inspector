"""Add trusted_devices table — lets a specific app install skip TOTP on later
logins (password is still required every time; only the second factor is
skipped, and only for that one device, for a limited time, revocably).

Revision ID: 008
Revises: 007
Create Date: 2026-08-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'trusted_devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('label', sa.String(100)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('last_used_at', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), server_default=sa.text('false')),
    )
    op.create_index('ix_trusted_devices_user_id', 'trusted_devices', ['user_id'])
    op.create_index('ix_trusted_devices_device_id', 'trusted_devices', ['device_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_trusted_devices_device_id', table_name='trusted_devices')
    op.drop_index('ix_trusted_devices_user_id', table_name='trusted_devices')
    op.drop_table('trusted_devices')

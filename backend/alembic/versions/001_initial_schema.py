"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'departments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('name_ar', sa.String(100), nullable=False),
        sa.Column('name_en', sa.String(100)),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('departments.id')),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name_ar', sa.String(100), nullable=False),
        sa.Column('full_name_en', sa.String(100)),
        sa.Column('email', sa.LargeBinary(), nullable=False),
        sa.Column('phone', sa.LargeBinary()),
        sa.Column('role', sa.String(30), nullable=False),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('departments.id')),
        sa.Column('totp_secret', sa.LargeBinary(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('TRUE')),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'complaints',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('complaint_number', sa.String(20), unique=True, nullable=False),
        sa.Column('title_ar', sa.String(200), nullable=False),
        sa.Column('title_en', sa.String(200)),
        sa.Column('description', sa.LargeBinary(), nullable=False),
        sa.Column('complainant_name', sa.LargeBinary()),
        sa.Column('complainant_phone', sa.LargeBinary()),
        sa.Column('complainant_email', sa.LargeBinary()),
        sa.Column('source', sa.String(10), nullable=False),
        sa.Column('category', sa.String(30), nullable=False),
        sa.Column('priority', sa.String(10), nullable=False),
        sa.Column('status', sa.String(30), server_default=sa.text("'received'"), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('erp_reference_id', sa.String(50)),
        sa.Column('is_anonymous', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
    )

    op.create_index('idx_complaints_status', 'complaints', ['status'])
    op.create_index('idx_complaints_priority', 'complaints', ['priority'])

    op.create_table(
        'investigation_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('complaint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('note_content', sa.LargeBinary(), nullable=False),
        sa.Column('note_type', sa.String(20), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_confidential', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('table_name', sa.String(50), nullable=False),
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(10), nullable=False),
        sa.Column('old_values', sa.LargeBinary()),
        sa.Column('new_values', sa.LargeBinary()),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('ip_address_hash', sa.String(64), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'digital_signatures',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('signer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('signature_data', sa.LargeBinary(), nullable=False),
        sa.Column('certificate_thumbprint', sa.String(64), nullable=False),
        sa.Column('signed_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
    )

    op.execute("INSERT INTO departments (name_ar, name_en, code) VALUES ('مديرية الرقابة والتفتيش', 'Inspection Directorate', 'INSP')")


def downgrade() -> None:
    op.drop_table('digital_signatures')
    op.drop_table('audit_logs')
    op.drop_table('investigation_notes')
    op.drop_table('complaints')
    op.drop_table('users')
    op.drop_table('departments')

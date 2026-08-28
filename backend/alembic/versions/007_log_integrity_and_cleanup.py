"""Tamper-evident logs (hash chain + append-only triggers) and drop the unused audit_logs table

The project now has two working, actively-used activity logs (complaint_logs,
activity_logs) that superseded the never-wired-up AuditLogger/audit_logs design.
This migration commits to that decision: audit_logs is dropped, and the two
real log tables are hardened to be genuinely tamper-evident (a hash chain
column pair, application-populated) and append-only (DB-level trigger blocks
UPDATE/DELETE, even for the table owner).

Revision ID: 007
Revises: 006
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('complaint_logs', sa.Column('prev_hash', sa.String(64), nullable=True))
    op.add_column('complaint_logs', sa.Column('row_hash', sa.String(64), nullable=True))
    op.add_column('activity_logs', sa.Column('prev_hash', sa.String(64), nullable=True))
    op.add_column('activity_logs', sa.Column('row_hash', sa.String(64), nullable=True))

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_log_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'This table is append-only: % is not permitted', TG_OP;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER complaint_logs_immutable
        BEFORE UPDATE OR DELETE ON complaint_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_log_mutation();
    """)
    op.execute("""
        CREATE TRIGGER activity_logs_immutable
        BEFORE UPDATE OR DELETE ON activity_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_log_mutation();
    """)

    op.drop_table('audit_logs')


def downgrade() -> None:
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

    op.execute("DROP TRIGGER IF EXISTS activity_logs_immutable ON activity_logs;")
    op.execute("DROP TRIGGER IF EXISTS complaint_logs_immutable ON complaint_logs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_log_mutation();")

    op.drop_column('activity_logs', 'row_hash')
    op.drop_column('activity_logs', 'prev_hash')
    op.drop_column('complaint_logs', 'row_hash')
    op.drop_column('complaint_logs', 'prev_hash')

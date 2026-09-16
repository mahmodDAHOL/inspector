"""Add structured investigation reports.

Revision ID: 010
Revises: 009
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investigation_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("scope", sa.LargeBinary(), nullable=False),
        sa.Column("methodology", sa.LargeBinary(), nullable=False),
        sa.Column("findings", sa.LargeBinary(), nullable=False),
        sa.Column("evidence_summary", sa.LargeBinary(), nullable=False),
        sa.Column("conclusion", sa.LargeBinary(), nullable=False),
        sa.Column("recommendations", sa.LargeBinary(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("finalized_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("finalized_at", sa.DateTime()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("signature_data", sa.LargeBinary()),
        sa.Column("signature_algorithm", sa.String(40)),
        sa.Column("certificate_thumbprint", sa.String(64)),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_investigation_reports_complaint_id", "investigation_reports", ["complaint_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_investigation_reports_complaint_id", table_name="investigation_reports")
    op.drop_table("investigation_reports")
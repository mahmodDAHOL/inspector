"""Add immutable complaint evidence files."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "complaint_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.LargeBinary(), nullable=False),
        sa.Column("stored_file_name", sa.String(255), nullable=False, unique=True),
        sa.Column("original_file_name", sa.LargeBinary(), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_complaint_evidence_complaint_id", "complaint_evidence", ["complaint_id"])


def downgrade() -> None:
    op.drop_index("ix_complaint_evidence_complaint_id", table_name="complaint_evidence")
    op.drop_table("complaint_evidence")
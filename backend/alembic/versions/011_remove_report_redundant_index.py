"""Remove the redundant explicit index created with the unique constraint."""
from alembic import op


revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_investigation_reports_complaint_id", table_name="investigation_reports")


def downgrade() -> None:
    op.create_index(
        "ix_investigation_reports_complaint_id",
        "investigation_reports",
        ["complaint_id"],
        unique=True,
    )
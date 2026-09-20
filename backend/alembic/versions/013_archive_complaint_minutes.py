"""Add auditable soft-archive fields to complaint minutes."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("complaint_minutes", sa.Column("archived_at", sa.DateTime()))
    op.add_column("complaint_minutes", sa.Column("archived_by", postgresql.UUID(as_uuid=True)))
    op.create_foreign_key(
        "fk_complaint_minutes_archived_by",
        "complaint_minutes",
        "users",
        ["archived_by"],
        ["id"],
    )
    op.create_index("ix_complaint_minutes_archived_at", "complaint_minutes", ["archived_at"])


def downgrade() -> None:
    op.drop_index("ix_complaint_minutes_archived_at", table_name="complaint_minutes")
    op.drop_constraint("fk_complaint_minutes_archived_by", "complaint_minutes", type_="foreignkey")
    op.drop_column("complaint_minutes", "archived_by")
    op.drop_column("complaint_minutes", "archived_at")
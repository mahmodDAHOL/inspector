"""Store the reason for cancelling a complaint minute."""
from alembic import op
import sqlalchemy as sa


revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("complaint_minutes", sa.Column("archived_reason", sa.LargeBinary()))


def downgrade() -> None:
    op.drop_column("complaint_minutes", "archived_reason")
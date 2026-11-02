"""Separate, attributed photo assets from language content."""
from alembic import op
import sqlalchemy as sa
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("media_asset", sa.Column("id", sa.String(), primary_key=True), sa.Column("kind", sa.String(), nullable=False), sa.Column("theme", sa.String(), nullable=False), sa.Column("label_fr", sa.String(), nullable=False), sa.Column("status", sa.String(), nullable=False), sa.Column("data", sa.JSON(), nullable=False))

def downgrade():
    op.drop_table("media_asset")

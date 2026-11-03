"""Semantic topics and lexical concepts, independent of the source chapter."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    for name in ("topic_keys", "matched_concepts"):
        op.add_column(
            "content",
            sa.Column(name, JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        )
        op.create_index("ix_content_" + name, "content", [name], postgresql_using="gin")
    for name, length in [("concept_key", 100), ("learning_role", 24), ("organization_version", 32)]:
        op.add_column("content", sa.Column(name, sa.String(length), nullable=True))
    op.add_column(
        "content", sa.Column("learning_rank", sa.Integer(), nullable=False, server_default="999")
    )
    op.create_index("ix_content_concept", "content", ["kind", "concept_key", "learning_rank"])


def downgrade():
    op.drop_index("ix_content_concept", table_name="content")
    for name in ("topic_keys", "matched_concepts"):
        op.drop_index("ix_content_" + name, table_name="content")
    for name in (
        "topic_keys",
        "matched_concepts",
        "concept_key",
        "learning_role",
        "organization_version",
        "learning_rank",
    ):
        op.drop_column("content", name)

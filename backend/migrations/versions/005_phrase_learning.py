"""Indexed phrase difficulty, audio availability and exact lexical lookup."""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("content", sa.Column("learning_band", sa.String(16), nullable=True))
    op.add_column(
        "content", sa.Column("has_audio", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column("content", sa.Column("lexeme_key", sa.String(64), nullable=True))
    op.create_index(
        "ix_content_learning", "content", ["kind", "has_audio", "learning_band", "theme"]
    )
    op.create_index("ix_content_lexeme", "content", ["lexeme_key"])


def downgrade():
    op.drop_index("ix_content_lexeme", table_name="content")
    op.drop_index("ix_content_learning", table_name="content")
    for name in ("lexeme_key", "has_audio", "learning_band"):
        op.drop_column("content", name)

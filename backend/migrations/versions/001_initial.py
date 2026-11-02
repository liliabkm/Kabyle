"""Initial content, attempts and spaced repetition tables."""
from alembic import op
import sqlalchemy as sa
revision = "001"
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("content",sa.Column("id",sa.String(),primary_key=True),sa.Column("kind",sa.String(),nullable=False),sa.Column("variety",sa.String(),nullable=False),sa.Column("script",sa.String(),nullable=False),sa.Column("theme",sa.String(),nullable=False),sa.Column("status",sa.String(),nullable=False),sa.Column("data",sa.JSON(),nullable=False))
    op.create_table("progress",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("learner",sa.String(),nullable=False),sa.Column("content_id",sa.String(),sa.ForeignKey("content.id"),nullable=False),sa.Column("correct",sa.Integer(),nullable=False),sa.Column("errors",sa.Integer(),nullable=False),sa.Column("streak",sa.Integer(),nullable=False),sa.Column("due",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("learner","content_id"))
    op.create_index("ix_progress_learner","progress",["learner"])
    op.create_table("attempt",sa.Column("id",sa.String(),primary_key=True),sa.Column("learner",sa.String(),nullable=False),sa.Column("content_id",sa.String(),sa.ForeignKey("content.id"),nullable=False),sa.Column("correct",sa.Boolean(),nullable=False))
def downgrade():
    op.drop_table("attempt");op.drop_table("progress");op.drop_table("content")

"""Persist reusable word and phrase lesson definitions."""
from alembic import op
import sqlalchemy as sa
revision='003'
down_revision='002'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('lesson',sa.Column('id',sa.String(),primary_key=True),sa.Column('title',sa.String(),nullable=False),sa.Column('theme',sa.String(),nullable=False),sa.Column('status',sa.String(),nullable=False),sa.Column('data',sa.JSON(),nullable=False))

def downgrade():
    op.drop_table('lesson')

"""Search and filtering support for large public corpora."""
from alembic import op
import sqlalchemy as sa
revision='004'
down_revision='003'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('content',sa.Column('search_text',sa.Text(),nullable=False,server_default=''))
    op.add_column('content',sa.Column('pair_key',sa.String(64),nullable=True))
    op.create_index('ix_content_pair_key','content',['pair_key'])
    op.create_index('ix_content_catalog','content',['kind','status','theme'])

def downgrade():
    op.drop_index('ix_content_pair_key',table_name='content')
    op.drop_column('content','pair_key')
    op.drop_index('ix_content_catalog',table_name='content')
    op.drop_column('content','search_text')

"""
Initialisation.

Revision ID: 86a245a136db
Revises:
Create Date: 2025-03-14 09:37:20.912382
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '86a245a136db'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # check if the table already exists
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    all_table_names = insp.get_table_names()
    table_exists = 'doi' in all_table_names

    if not table_exists:
        op.create_table(
            'doi',
            sa.Column('identifier', sa.UnicodeText, primary_key=True),
            sa.Column(
                'package_id',
                sa.UnicodeText,
                sa.ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
                nullable=False,
                unique=True,
            ),
            sa.Column('published', sa.DateTime, nullable=True),
        )


def downgrade():
    op.drop_table('doi')

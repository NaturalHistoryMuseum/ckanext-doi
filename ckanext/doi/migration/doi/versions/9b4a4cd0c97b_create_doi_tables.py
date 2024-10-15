"""Create doi tables

Revision ID: 9b4a4cd0c97b
Revises: 
Create Date: 2024-09-18 14:48:00.090825

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '9b4a4cd0c97b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    if "doi" in tables:
        return

    op.create_table(
        "doi",
        sa.Column('identifier', sa.types.UnicodeText, primary_key=True),
        sa.Column('package_id',
            sa.types.UnicodeText,
            sa.ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False,
            unique=True,),
        sa.Column('published', sa.types.DateTime, nullable=True),
    )


def downgrade():
    op.drop_table("doi")

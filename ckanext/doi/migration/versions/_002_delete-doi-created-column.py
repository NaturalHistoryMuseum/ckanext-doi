from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Remove the created column
    migrate_engine.execute('ALTER TABLE doi DROP COLUMN created;')

def downgrade(migrate_engine):
    raise NotImplementedError()

from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    meta = MetaData()

    a1 = Table('a1', meta,
      Column('id', Integer() ,  primary_key=True, nullable=False),
      Column('name', Unicode(100)),
    )

    meta.bind = migrate_engine
    meta.create_all()

def downgrade(migrate_engine):
    raise NotImplementedError()

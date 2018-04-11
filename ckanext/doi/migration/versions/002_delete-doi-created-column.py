#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    '''

    :param migrate_engine: 

    '''
    # Remove the created column
    migrate_engine.execute(u'ALTER TABLE doi DROP COLUMN created;')

def downgrade(migrate_engine):
    '''

    :param migrate_engine: 

    '''
    raise NotImplementedError()

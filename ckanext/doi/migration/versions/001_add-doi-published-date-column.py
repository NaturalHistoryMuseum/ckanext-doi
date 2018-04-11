#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK


def upgrade(migrate_engine):
    '''

    :param migrate_engine: 

    '''
    # Add the published date column
    migrate_engine.execute(u'''
        ALTER TABLE doi
            ADD COLUMN published timestamp without time zone;
    '''
    )

    # Copy original created date to the new published column
    migrate_engine.execute(u'''
        UPDATE doi SET published = created;
    '''
    )

def downgrade(migrate_engine):
    '''

    :param migrate_engine: 

    '''
    raise NotImplementedError()

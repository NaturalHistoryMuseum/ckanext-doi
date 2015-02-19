
def upgrade(migrate_engine):
    # Add the published date column
    migrate_engine.execute('''
        ALTER TABLE doi
            ADD COLUMN published timestamp without time zone;
    '''
    )

    # Copy original created date to the new published column
    migrate_engine.execute('''
        UPDATE doi SET published = created;
    '''
    )

def downgrade(migrate_engine):
    raise NotImplementedError()

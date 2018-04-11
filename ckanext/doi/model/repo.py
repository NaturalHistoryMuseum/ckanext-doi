
#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import vdm.sqlalchemy
from vdm.sqlalchemy.base import SQLAlchemySession
import ckanext.doi.migration


class Repository(vdm.sqlalchemy.Repository):
    '''Uses the SQLAlchemy migrate API to allow us to handle DB migrations
    
    This uses the same migrate_version table to keep track of versions,
    with repository id DOI - see doi.migration/migrate.cfg
    
    Called from doi.commands.doi.upgrade_db


    '''

    migrate_repository = ckanext.doi.migration.__path__[0]

    def upgrade(self, version=None):
        '''

        :param version:  (Default value = None)

        '''
        import migrate.versioning.api as mig
        self.setup_migration_version_control(version)
        version_before = mig.db_version(self.metadata.bind, self.migrate_repository)
        mig.upgrade(self.metadata.bind, self.migrate_repository, version=version)
        version_after = mig.db_version(self.metadata.bind, self.migrate_repository)
        if version_after != version_before:
            print u'CKAN database version upgraded: %s -> %s' % (version_before, version_after)
        else:
            print u'CKAN database version remains as: %s' % version_after

    def setup_migration_version_control(self, version):
        '''

        :param version: 

        '''
        import migrate.exceptions
        import migrate.versioning.api as mig
        # set up db version control (if not already)
        try:
            mig.version_control(self.metadata.bind,
                    self.migrate_repository, version)
        except migrate.exceptions.DatabaseAlreadyControlledError:
            pass

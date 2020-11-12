#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK


import logging

from ckan.model import Session, meta
from ckan.plugins import toolkit
from ckanext.doi.lib.api import DataciteClient
from ckanext.doi.model.doi import DOI
from ckanext.doi.model.repo import Repository

log = logging.getLogger(__name__)


class DOICommand(toolkit.CkanCommand):
    '''DOI-related paster commands.

    paster doi delete-tests -c /etc/ckan/default/development.ini
    paster doi upgrade-db -c /etc/ckan/default/development.ini

    '''
    summary = __doc__.split(u'\n')[0]
    usage = __doc__
    max_args = 2
    min_args = 1

    def command(self):
        ''' '''

        if not self.args or self.args[0] in [u'--help', u'-h', u'help']:
            print self.__doc__
            return

        self._load_config()

        cmd = self.args[0]

        if cmd == u'delete-dois':
            self.delete_dois()
        elif cmd == u'upgrade-db':
            self.upgrade_db()
        else:
            print u'Command %s not recognized' % cmd

    def delete_dois(self):
        '''Delete all DOIs from the database.'''
        to_delete = Session.query(DOI).filter(
            DOI.identifier.like(u'%' + DataciteClient.get_prefix() + u'%'))
        if to_delete.count() == 0:
            print(u'Nothing to delete.')
            return
        confirm = raw_input(u'Delete {0} DOIs from the database? [y/N] '.format(to_delete.count()))
        if confirm.lower() == 'y':
            to_delete.delete(synchronize_session=False)
            Session.commit()
        else:
            print(u'Aborted.')

    def upgrade_db(self):
        '''Upgrade script for updating the DOI DB model.
        Based on CKANs db upgrade command.

        '''
        repo = Repository(meta.metadata, meta.Session)

        if len(self.args) > 1:
            repo.upgrade(self.args[1])
        else:
            repo.upgrade()

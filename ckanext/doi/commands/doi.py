#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK


import logging
from ckan.lib.cli import CkanCommand
from ckanext.doi.model.doi import DOI
from ckanext.doi.model.repo import Repository
from ckanext.doi.config import TEST_PREFIX
from ckan.model import Session, meta

log = logging.getLogger(__name__)

class DOICommand(CkanCommand):
    '''Delete all test DOIs
    
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

        if cmd == u'delete-tests':
            self.delete_tests()
        elif cmd == u'upgrade-db':
            self.upgrade_db()
        else:
            print u'Command %s not recognized' % cmd

    def delete_tests(self):
        ''' '''

        print u'Deleting all test DOIs'
        Session.query(DOI).filter(DOI.identifier.like(u'%' + TEST_PREFIX + u'%')).delete(synchronize_session=False)
        Session.commit()

    def upgrade_db(self):
        '''Upgrade script for updating the DOI DB model
        Based on CKANs db upgrade command


        '''
        repo = Repository(meta.metadata, meta.Session)

        if len(self.args) > 1:
            repo.upgrade(self.args[1])
        else:
            repo.upgrade()

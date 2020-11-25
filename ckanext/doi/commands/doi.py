#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK


import logging

from ckan.model import Session, meta
from ckan.plugins import toolkit
from ckanext.doi.lib.api import DataciteClient
from ckanext.doi.lib.metadata import build_metadata_dict, build_xml_dict
from ckanext.doi.model.crud import DOIQuery
from ckanext.doi.model.doi import DOI
from ckanext.doi.model.repo import Repository
from datacite.errors import DataCiteError

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
        elif cmd == u'update-doi':
            self.update_doi(self.args[1] if len(self.args) > 1 else None)
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

    def update_doi(self, pkg_id):
        if pkg_id is None:
            dois_to_update = Session.query(DOI).all()
        else:
            dois_to_update = []
            doi_record = DOIQuery.read_package(pkg_id)
            if doi_record is not None:
                dois_to_update = [doi_record]

        if len(dois_to_update) == 0:
            print(u'Nothing to update.')
            return

        for record in dois_to_update:
            pkg_dict = toolkit.get_action(u'package_show')({}, {
                u'id': record.package_id
            })
            title = pkg_dict.get(u'title', record.package_id)

            if record.published is None:
                print(u'"{0}" does not have a published DOI; not updating.'.format(title))
                continue
            if pkg_dict.get(u'state', u'active') != u'active' or pkg_dict.get(u'private', False):
                print(u'"{0}" is inactive or private; not updating.'.format(title))
                continue

            metadata_dict = build_metadata_dict(pkg_dict)
            xml_dict = build_xml_dict(metadata_dict)

            client = DataciteClient()

            same = client.check_for_update(record.identifier, xml_dict)
            if not same:
                try:
                    client.set_metadata(record.identifier, xml_dict)
                    print(u'Updated "{0}".'.format(title))
                except DataCiteError as e:
                    print(u'Error while trying to update "{0}" (DOI {1}): {2}'.format(title,
                                                                                      record.identifier,
                                                                                      e.message))
            else:
                print(u'"{0}" does not need updating.'.format(title))

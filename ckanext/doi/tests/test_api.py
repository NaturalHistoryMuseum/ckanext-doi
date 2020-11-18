#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import mock
import nose
import os
from ckanext.doi.lib.api import DataciteClient
from ckanext.doi.model.doi import doi_table
from ckantest.models import TestBase
from datacite.errors import DataCiteError

import constants


class TestAPI(TestBase):
    plugins = [u'doi']
    persist = {
        u'ckanext.doi.debug': True
    }

    @classmethod
    def setup_class(cls):
        super(TestAPI, cls).setup_class()
        cls.data_factory().refresh()
        doi_table.create(checkfirst=True)

    def run(self, result=None):
        with mock.patch('ckan.lib.helpers.session', self._session):
            super(TestAPI, self).run(result)

    @property
    def pkg_record(self):
        if self.data_factory().packages.get('pkg_record', None) is None:
            pkg_data = {
                u'author': u'Author, Test',
                u'title': u'Test Package',
                u'doi_date_published': u'2020-01-01'
            }
            self.data_factory().package(name='pkg_record', activate=False, **pkg_data)
        return self.data_factory().packages['pkg_record']

    def _env_credentials(self):
        mapping = {
            u'ckanext.doi.prefix': u'DATACITE_PREFIX',
            u'ckanext.doi.account_name': u'DATACITE_ACCOUNT_NAME',
            u'ckanext.doi.account_password': u'DATACITE_ACCOUNT_PASSWORD'
        }
        for k, v in mapping.items():
            if self.config.current.get(k) is None:
                self.config.update({
                                       k: os.environ.get(v)
                                   })

    def test_generate_new_doi(self):
        self._env_credentials()
        api = DataciteClient()
        doi = api.generate_doi()
        nose.tools.assert_is_instance(doi, (str, unicode))

    def test_mint_new_doi(self):
        self._env_credentials()
        api = DataciteClient()
        doi = api.generate_doi()
        pkg_id = self.pkg_record[u'id']
        with nose.tools.assert_raises(DataCiteError):
            api.mint_doi(doi, pkg_id)
        api.set_metadata(doi, constants.XML_DICT)
        api.mint_doi(doi, pkg_id)

    def test_datacite_authentication(self):
        self._env_credentials()
        api = DataciteClient()
        nose.tools.assert_is_not_none(api.client.username)
        nose.tools.assert_is_not_none(api.client.password)

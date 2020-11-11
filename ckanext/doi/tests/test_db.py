#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import mock
import nose
from ckan.model import Session
from ckanext.doi.model.doi import DOI, doi_table
from ckantest.models import TestBase


class TestDatabase(TestBase):
    plugins = [u'doi']
    persist = {
        u'ckanext.doi.debug': True
    }

    def __init__(self, *args, **kwargs):
        super(TestDatabase, self).__init__(*args, **kwargs)
        self._doi_record = None

    @classmethod
    def setup_class(cls):
        super(TestDatabase, cls).setup_class()
        cls.data_factory().refresh()
        doi_table.create(checkfirst=True)

    def run(self, result=None):
        with mock.patch('ckan.lib.helpers.session', self._session):
            super(TestDatabase, self).run(result)

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

    def test_added_for_new_package(self):
        pkg_id = self.pkg_record[u'id']
        found_record = Session.query(DOI).filter(DOI.package_id == pkg_id)
        nose.tools.assert_is_not_none(found_record)

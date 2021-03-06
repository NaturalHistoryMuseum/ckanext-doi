#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import mock
import nose
import pkg_resources
from ckanext.doi.lib.metadata import build_metadata_dict, build_xml_dict
from ckanext.doi.model.doi import doi_table
from ckantest.models import TestBase
from datacite.jsonutils import validator_factory

import constants


class TestGenerate(TestBase):
    plugins = [u'doi', u'datastore']
    persist = {
        u'ckanext.doi.test_mode': True,
        u'ckanext.doi.publisher': 'Example Publisher'
    }

    @classmethod
    def setup_class(cls):
        super(TestGenerate, cls).setup_class()
        cls.data_factory().refresh()
        doi_table.create(checkfirst=True)

    def run(self, result=None):
        with mock.patch('ckan.lib.helpers.session', self._session):
            super(TestGenerate, self).run(result)

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

    def test_extracts_metadata(self):
        metadata_dict = build_metadata_dict(constants.PKG_DICT)
        nose.tools.assert_is_instance(metadata_dict, dict)
        for k in [u'creators', u'titles', u'publisher', u'publicationYear', u'resourceType']:
            nose.tools.assert_in(k, metadata_dict)
        nose.tools.assert_equal(1, len(metadata_dict[u'creators']))
        nose.tools.assert_equal(1, len(metadata_dict[u'titles']))
        nose.tools.assert_equal(constants.PKG_DICT[u'title'], metadata_dict[u'titles'][0][u'title'])
        nose.tools.assert_equal(metadata_dict[u'publisher'], u'Example Publisher')
        nose.tools.assert_is_instance(metadata_dict[u'publicationYear'], int)
        nose.tools.assert_equal(constants.PKG_DICT[u'type'], metadata_dict[u'resourceType'])

    def test_handles_bad_data(self):
        bad_pkg_dict = {k: v for k, v in constants.PKG_DICT.items()}
        bad_pkg_dict[u'resources'] = None
        bad_pkg_dict[u'author'] = {
            u'given_name': u'Test',
            u'family_name': u'Author'
        }
        bad_pkg_dict[u'license_id'] = None
        build_metadata_dict(bad_pkg_dict)

        del bad_pkg_dict[u'author']
        del bad_pkg_dict[u'resources']
        del bad_pkg_dict[u'license_id']
        build_metadata_dict(bad_pkg_dict)

    def test_generate_xml(self):
        xml_dict = build_xml_dict(constants.METADATA_DICT)
        xml_dict[u'identifier'] = {
            u'identifierType': u'DOI',
            u'identifier': u'10.0000/this-would-be-a-doi'
        }
        validator = validator_factory(pkg_resources.resource_filename(
            'datacite',
            'schemas/datacite-v4.2.json'
        ))
        errors = [e for e in validator.iter_errors(xml_dict)]
        nose.tools.assert_equal(0, len(errors))

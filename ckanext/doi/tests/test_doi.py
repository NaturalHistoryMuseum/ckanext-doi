#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from logging import getLogger

import ckanext.doi.lib as doi_lib
import mock
import nose
from ckantest.factories.data import DataConstants
from ckantest.helpers.mocking import Response
from ckantest.models import TestBase

from ckan.plugins import toolkit

log = getLogger(__name__)


class TestDOI(TestBase):
    plugins = [u'doi']

    @classmethod
    def setup_class(cls):
        super(TestDOI, cls).setup_class()
        with mock.patch('ckan.lib.helpers.session', cls._session):
            cls.package_dict = cls.data_factory().package(author=DataConstants.authors_short,
                                                          activate=False)

    def test_get_config_params(self):
        account_name = toolkit.config.get(u'ckanext.doi.account_name')
        account_password = toolkit.config.get(u'ckanext.doi.account_password')
        nose.tools.assert_is_not_none(account_name)
        nose.tools.assert_is_not_none(account_password)

    def test_create_identifier(self):
        '''Test a DOI has been created with the package
        We won't have tried pushing to the DataCite service
        '''
        identifier = doi_lib.get_or_create_doi(self.package_dict[u'id'])
        nose.tools.assert_is_instance(identifier, doi_lib.DOI)
        nose.tools.assert_equal(identifier.package_id, self.package_dict[u'id'])
        nose.tools.assert_is_none(identifier.published)

    def test_create_metadata(self):
        doi = doi_lib.get_or_create_doi(self.package_dict[u'id'])

        # Build the metadata dict to pass to DataCite service
        metadata_dict = doi_lib.build_metadata(self.package_dict, doi)

        # Perform some basic checks against the data - we require at the very least
        # title and author fields - they're mandatory in the DataCite Schema
        # This will only be an issue if another plugin has removed a mandatory field
        doi_lib.validate_metadata(metadata_dict)

    @mock.patch('ckanext.doi.api.requests.put', return_value=Response(status_code=201))
    def test_publish_to_datacite(self, mock_request):
        doi = doi_lib.get_or_create_doi(self.package_dict[u'id'])
        metadata_dict = doi_lib.build_metadata(self.package_dict, doi)
        doi_lib.validate_metadata(metadata_dict)

        doi_lib.publish_doi(self.package_dict[u'id'], **metadata_dict)

#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from logging import getLogger

from nose.tools import (assert_equal, assert_is_instance, assert_is_none,
                        assert_is_not_none)

from ckan import model
from ckan.lib.create_test_data import CreateTestData
from ckan.plugins import toolkit
from ckan.tests import helpers

log = getLogger(__name__)


class TestDOI(helpers.FunctionalTestBase):
    '''Test creating DOIs
    nosetests -s --ckan --with-pylons=/Users/bens3/Projects/NHM/DataPortal/etc/default
    /test-core.ini ckanext.doi

    '''

    context = None
    engine = None
    _load_plugins = [u'doi']

    @classmethod
    def setup_class(cls):
        '''Prepare the test'''
        super(TestDOI, cls).setup_class()

        #  We need to actually create a dataset as DOI has foreign key constraint to
        # dataset table
        CreateTestData.create()

        cls.context = {
            u'user': model.User.get(u'testsysadmin').name
            }

        cls.package = model.Package.get(u'annakarenina')
        cls.package_dict = toolkit.get_action(u'package_show')(cls.context, {
            u'id': cls.package.id
            })

        # Add the author field
        cls.package_dict[u'author'] = u'Ben'

    @classmethod
    def teardown_class(cls):
        '''Clean up'''
        super(TestDOI, cls).teardown_class()
        helpers.reset_db()

    def test_doi_config(self):
        '''Test we are receiving params from the config file
        :return:

        '''
        account_name = toolkit.config.get(u'ckanext.doi.account_name')
        account_password = toolkit.config.get(u'ckanext.doi.account_password')
        assert_is_not_none(account_name)
        assert_is_not_none(account_password)

    def test_doi_create_identifier(self):
        '''Test a DOI has been created with the package
        We won't have tried pushing to the DataCite service
        :return:

        '''

        # Import now otherwise we get model creation errors
        import ckanext.doi.lib as doi_lib

        # Show the package - which will load the DOI
        identifier = doi_lib.create_unique_identifier(self.package_dict[u'id'])

        # Make sure we have a DOI model
        assert_is_instance(identifier, doi_lib.DOI)

        # And the package ID is correct
        assert_equal(identifier.package_id, self.package_dict[u'id'])

        # And published should be none
        assert_is_none(identifier.published)

    def test_doi_metadata(self):
        '''Test the creation and validation of metadata
        :return:

        '''

        import ckanext.doi.lib as doi_lib

        doi = doi_lib.get_doi(self.package_dict[u'id'])

        if not doi:
            doi = doi_lib.create_unique_identifier(self.package_dict[u'id'])

        # Build the metadata dict to pass to DataCite service
        metadata_dict = doi_lib.build_metadata(self.package_dict, doi)

        # Perform some basic checks against the data - we require at the very least
        # title and author fields - they're mandatory in the DataCite Schema
        # This will only be an issue if another plugin has removed a mandatory field
        doi_lib.validate_metadata(metadata_dict)

    def test_doi_publish_datacite(self):
        ''' '''

        import ckanext.doi.lib as doi_lib

        doi = doi_lib.get_doi(self.package_dict[u'id'])

        if not doi:
            doi = doi_lib.create_unique_identifier(self.package_dict[u'id'])

        # Build the metadata dict to pass to DataCite service
        metadata_dict = doi_lib.build_metadata(self.package_dict, doi)

        # Perform some basic checks against the data - we require at the very least
        # title and author fields - they're mandatory in the DataCite Schema
        # This will only be an issue if another plugin has removed a mandatory field
        doi_lib.validate_metadata(metadata_dict)

        doi_lib.publish_doi(self.package_dict[u'id'], **metadata_dict)

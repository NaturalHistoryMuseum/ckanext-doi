#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import paste.fixture
from logging import getLogger
from pylons import config
import nose
from sqlalchemy import create_engine

import ckan
import ckan.tests as tests
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckan.lib.create_test_data as ctd
import ckan.model as model
import ckan.config.middleware as middleware
from nose.tools import assert_equal, assert_true, assert_false, assert_in, assert_raises, assert_is_not_none, assert_is_none, assert_is_instance

log = getLogger(__name__)

class TestDOI(tests.WsgiAppCase):
    '''Test creating DOIs
    nosetests -s --ckan --with-pylons=/Users/bens3/Projects/NHM/DataPortal/etc/default/test-core.ini ckanext.doi


    '''

    context = None
    engine = None

    @classmethod
    def setup_class(cls):
        '''Prepare the test'''

        # Setup a test app
        wsgiapp = middleware.make_app(config[u'global_conf'], **config)
        cls.app = paste.fixture.TestApp(wsgiapp)

        # Load plugins
        p.load(u'doi')

        #  We need to actually create a dataset as DOI has foreign key constraint to dataset table
        ctd.CreateTestData.create()

        cls.context = {u'model': ckan.model,
                       u'session': ckan.model.Session,
                       u'user': ckan.model.User.get(u'testsysadmin').name}

        cls.package = model.Package.get(u'annakarenina')
        cls.package_dict = toolkit.get_action(u'package_show')(cls.context, {u'id': cls.package.id})

        # Add the author field
        cls.package_dict[u'author'] = u'Ben'

    @classmethod
    def teardown_class(cls):
        '''Clean up'''
        p.unload(u'doi')
        model.repo.rebuild_db()

    def test_doi_config(self):
        '''Test we are receiving params from the config file
        :return:


        '''
        account_name = config.get(u'ckanext.doi.account_name')
        account_password = config.get(u'ckanext.doi.account_password')
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
    #
    # def create_dataset(self):
    #     """
    #     TODO: Create a dataset and assert DOI exists
    #
    #     ctd.CreateTestData.create() creates using the model and bypasses
    #     plugin hooks - so we'll create using CKAN actions and then text the DOI exists
    #
    #     :return:
    #     """
    #     pass








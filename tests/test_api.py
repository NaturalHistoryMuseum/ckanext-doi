#!/usr/bin/env python3
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import xml.etree.ElementTree as ET

import pytest
from datacite.errors import DataCiteError, DataCiteNotFoundError
from unittest.mock import patch, MagicMock

from . import constants
from ckanext.doi.lib.api import DataciteClient


def first_then(first, then):
    '''
    Convenience generator which yields the first parameter and then yields the then parameter
    forever. Handy for MagicMock object side_effects where the first time the function is run first
    parameter should be return and then the then parameter after that.

    :param first: the first value to yield, once
    :param then: the parameter to yield on subsequent next calls, forever
    '''
    yield first
    while True:
        yield then


@pytest.mark.ckan_config('ckanext.doi.prefix', 'testing')
class TestGenerateNewDOI:
    '''
    In each of these tests we could assert the number of calls to the db and datacite client mocks
    but this feels like a bit too much of a reach into the internal logic of the function. We care
    about the result based on the scenario not how it gets there (unless we think we should test
    that the function checks the db before checking datacite for performance but I don't think this
    is really needed tbh.
    '''

    def test_no_existing_dois(self):
        # no dois in datacite
        mock_client = MagicMock(metadata_get=MagicMock(side_effect=DataCiteNotFoundError()))
        # no dois in the database
        mock_read_doi = MagicMock(return_value=None)

        with patch('ckanext.doi.lib.api.DataCiteMDSClient', MagicMock(return_value=mock_client)):
            with patch('ckanext.doi.lib.api.DOIQuery.read_doi', mock_read_doi):
                api = DataciteClient()
                doi = api.generate_doi()
                assert isinstance(doi, str)
                # both the client and the database should be called once and only once (yes this
                # goes against the comment at the start of this class but it felt relevant here to
                # check that this was the case)
                assert mock_client.metadata_get.call_count == 1
                assert mock_read_doi.call_count == 1

    def test_one_existing_db_doi(self):
        # no dois in datacite
        mock_client = MagicMock(metadata_get=MagicMock(side_effect=DataCiteNotFoundError()))
        # one doi in the database that hits the first call, but then the next time is fine
        mock_read_doi = MagicMock(side_effect=first_then(MagicMock(), None))

        with patch('ckanext.doi.lib.api.DataCiteMDSClient', MagicMock(return_value=mock_client)):
            with patch('ckanext.doi.lib.api.DOIQuery.read_doi', mock_read_doi):
                api = DataciteClient()
                doi = api.generate_doi()
                assert isinstance(doi, str)

    def test_one_existing_on_datacite(self):
        # the first call to the datacite client returns a (mock) doi but then the next one succeeds
        mock_client = MagicMock(
            metadata_get=MagicMock(side_effect=first_then(MagicMock(), DataCiteNotFoundError())))
        # no dois in the db
        mock_read_doi = MagicMock(return_value=None)

        with patch('ckanext.doi.lib.api.DataCiteMDSClient', MagicMock(return_value=mock_client)):
            with patch('ckanext.doi.lib.api.DOIQuery.read_doi', mock_read_doi):
                api = DataciteClient()
                doi = api.generate_doi()
                assert isinstance(doi, str)

    def test_one_existing_on_datacite_and_one_in_the_db(self):
        # the first call to the datacite client returns a (mock) doi but then the next one succeeds
        mock_client = MagicMock(
            metadata_get=MagicMock(side_effect=first_then(MagicMock(), DataCiteNotFoundError())))
        # the first call to the db returns a result but then after that we're all good
        mock_read_doi = MagicMock(side_effect=first_then(MagicMock(), None))

        with patch('ckanext.doi.lib.api.DataCiteMDSClient', MagicMock(return_value=mock_client)):
            with patch('ckanext.doi.lib.api.DOIQuery.read_doi', mock_read_doi):
                api = DataciteClient()
                doi = api.generate_doi()
                assert isinstance(doi, str)

    def test_it_fails_when_it_cannot_generate_a_unique_doi(self):
        # the datacite client returns an existing (mock) doi every time, so unlikely!
        mock_client = MagicMock(metadata_get=MagicMock())
        # the db returns an existing (mock) doi every time, so unlikely!
        mock_read_doi = MagicMock()

        with patch('ckanext.doi.lib.api.DataCiteMDSClient', mock_client):
            with patch('ckanext.doi.lib.api.DOIQuery.read_doi', mock_read_doi):
                api = DataciteClient()
                with pytest.raises(Exception, match='Failed to generate a DOI'):
                    api.generate_doi()


class MockDataciteMDSClient(object):
    '''
    Mock client so that we can replicate the functionality of the datacite API without actually
    calling it. Specifically, you have to post the metadata before you post the doi.
    '''

    def __init__(self, *args, **kwargs):
        self.metadata = set()
        self.dois = set()

    def doi_post(self, doi, *args, **kwargs):
        if doi not in self.metadata:
            raise DataCiteError()

        self.dois.add(doi)

    def metadata_post(self, xml_doc, *args, **kwargs):
        tree = ET.fromstring(xml_doc)
        doi = tree.findtext('{http://datacite.org/schema/kernel-4}identifier')
        self.metadata.add(doi)


@pytest.mark.ckan_config('ckanext.doi.prefix', 'testing')
@patch('ckanext.doi.lib.api.DataCiteMDSClient', MockDataciteMDSClient)
@patch('ckanext.doi.lib.api.DOIQuery')
class TestMintNewDOI(object):

    def test_datacite_api_order(self, mock_crud):
        mock_crud.read_doi = MagicMock(return_value=None)
        mock_crud.read_package = MagicMock(return_value=None)

        api = DataciteClient()
        doi = constants.XML_DICT['identifiers'][0]['identifier']
        pkg_id = MagicMock()

        with pytest.raises(DataCiteError):
            api.mint_doi(doi, pkg_id)

        api.set_metadata(doi, constants.XML_DICT)
        api.mint_doi(doi, pkg_id)

    def test_new_doi(self, mock_crud):
        mock_crud.read_doi = MagicMock(return_value=None)
        mock_crud.read_package = MagicMock(return_value=None)

        api = DataciteClient()
        doi = constants.XML_DICT['identifiers'][0]['identifier']
        pkg_id = MagicMock()

        api.set_metadata(doi, constants.XML_DICT)
        api.mint_doi(doi, pkg_id)

        assert mock_crud.create.called
        assert not mock_crud.update_package.called
        assert mock_crud.update_doi.called

    def test_existing_doi(self, mock_crud):
        mock_crud.read_doi = MagicMock(return_value=MagicMock())
        mock_crud.read_package = MagicMock(return_value=None)

        api = DataciteClient()
        doi = constants.XML_DICT['identifiers'][0]['identifier']
        pkg_id = MagicMock()

        api.set_metadata(doi, constants.XML_DICT)
        api.mint_doi(doi, pkg_id)

        assert not mock_crud.create.called
        assert not mock_crud.update_package.called
        assert mock_crud.update_doi.called

    def test_existing_package(self, mock_crud):
        mock_crud.read_doi = MagicMock(return_value=None)
        mock_crud.read_package = MagicMock(return_value=MagicMock())

        api = DataciteClient()
        doi = constants.XML_DICT['identifiers'][0]['identifier']
        pkg_id = MagicMock()

        api.set_metadata(doi, constants.XML_DICT)
        api.mint_doi(doi, pkg_id)

        assert not mock_crud.create.called
        assert mock_crud.update_package.called
        assert mock_crud.update_doi.called

    def test_both_exist(self, mock_crud):
        mock_crud.read_doi = MagicMock(return_value=MagicMock())
        mock_crud.read_package = MagicMock(return_value=MagicMock())

        api = DataciteClient()
        doi = constants.XML_DICT['identifiers'][0]['identifier']
        pkg_id = MagicMock()

        api.set_metadata(doi, constants.XML_DICT)
        api.mint_doi(doi, pkg_id)

        assert not mock_crud.create.called
        assert not mock_crud.update_package.called
        assert mock_crud.update_doi.called


@pytest.mark.ckan_config('ckanext.doi.prefix', 'testing')
@pytest.mark.ckan_config('ckanext.doi.account_name', 'goat!')
@pytest.mark.ckan_config('ckanext.doi.account_password', 'hammocks?')
@patch('ckanext.doi.lib.api.DataCiteMDSClient')
class TestDataciteClientCreation(object):

    @pytest.mark.ckan_config('ckanext.doi.test_mode', False)
    def test_basics(self, mock_client):
        DataciteClient()
        assert mock_client.called_once_with(username='goat!', password='hammocks?',
                                            prefix='testing', test_mode=False)
        assert 'url' not in mock_client.call_args.kwargs

    @pytest.mark.ckan_config('ckanext.doi.test_mode', True)
    def test_test_mode_true(self, mock_client):
        DataciteClient()
        assert mock_client.called_once_with(username='goat!', password='hammocks?',
                                            prefix='testing', test_mode=True,
                                            url=DataciteClient.test_url)

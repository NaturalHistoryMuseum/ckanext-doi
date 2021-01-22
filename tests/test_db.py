#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK
import pytest
from datacite.errors import DataCiteNotFoundError
from mock import patch, MagicMock

from ckan.model import Session
from ckan.tests import factories
from ckanext.doi.model.doi import DOI, doi_table


@pytest.fixture
def with_doi_table(reset_db):
    '''
    Simple fixture which resets the database and creates the doi table.
    '''
    reset_db()
    doi_table.create(checkfirst=True)


@pytest.mark.filterwarnings(u'ignore::sqlalchemy.exc.SADeprecationWarning')
@pytest.mark.ckan_config(u'ckan.plugins', u'doi')
@pytest.mark.ckan_config(u'ckanext.doi.prefix', u'testing')
@pytest.mark.usefixtures(u'with_doi_table', u'with_plugins')
@patch(u'ckanext.doi.lib.api.DataCiteMDSClient')
def test_doi_is_created_automatically(mock_client):
    # this test ensures that when a package is created, a DOI is created
    mock_client.return_value = MagicMock(
        metadata_get=MagicMock(side_effect=DataCiteNotFoundError()))
    package = factories.Dataset()
    found_record = Session.query(DOI).filter(DOI.package_id == package[u'id']).one()
    assert found_record is not None

#!/usr/bin/env python3
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import pkg_resources
import pytest
from datacite.jsonutils import validator_factory

from ckanext.doi.lib.metadata import build_metadata_dict, build_xml_dict
from . import constants


@pytest.mark.ckan_config('ckanext.doi.publisher', 'Example Publisher')
def test_extracts_metadata():
    metadata_dict = build_metadata_dict(constants.PKG_DICT)
    assert isinstance(metadata_dict, dict)
    for k in ['creators', 'titles', 'publisher', 'publicationYear', 'resourceType']:
        assert k in metadata_dict
    assert 1 == len(metadata_dict['creators'])
    assert 1 == len(metadata_dict['titles'])
    assert constants.PKG_DICT['title'] == metadata_dict['titles'][0]['title']
    assert metadata_dict['publisher'] == 'Example Publisher'
    assert isinstance(metadata_dict['publicationYear'], int)
    assert constants.PKG_DICT['type'] == metadata_dict['resourceType']


@pytest.mark.ckan_config('ckanext.doi.publisher', 'Example Publisher')
def test_handles_bad_data():
    bad_pkg_dict = {k: v for k, v in constants.PKG_DICT.items()}
    bad_pkg_dict['resources'] = None
    bad_pkg_dict['author'] = {
        'given_name': 'Test',
        'family_name': 'Author'
    }
    bad_pkg_dict['license_id'] = None
    build_metadata_dict(bad_pkg_dict)

    del bad_pkg_dict['author']
    del bad_pkg_dict['resources']
    del bad_pkg_dict['license_id']
    build_metadata_dict(bad_pkg_dict)


@pytest.mark.ckan_config('ckanext.doi.publisher', 'Example Publisher')
def test_generate_xml():
    xml_dict = build_xml_dict(constants.METADATA_DICT)
    xml_dict['identifier'] = {
        'identifierType': 'DOI',
        'identifier': '10.0000/this-would-be-a-doi'
    }
    validator = validator_factory(pkg_resources.resource_filename(
        'datacite',
        'schemas/datacite-v4.2.json'
    ))
    assert validator.is_valid(xml_dict)

#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import pkg_resources
import pytest
from datacite.jsonutils import validator_factory

from . import constants
from ckanext.doi.lib.metadata import build_metadata_dict, build_xml_dict


@pytest.mark.ckan_config(u'ckanext.doi.publisher', u'Example Publisher')
def test_extracts_metadata():
    metadata_dict = build_metadata_dict(constants.PKG_DICT)
    assert isinstance(metadata_dict, dict)
    for k in [u'creators', u'titles', u'publisher', u'publicationYear', u'resourceType']:
        assert k in metadata_dict
    assert 1 == len(metadata_dict[u'creators'])
    assert 1 == len(metadata_dict[u'titles'])
    assert constants.PKG_DICT[u'title'] == metadata_dict[u'titles'][0][u'title']
    assert metadata_dict[u'publisher'] == u'Example Publisher'
    assert isinstance(metadata_dict[u'publicationYear'], int)
    assert constants.PKG_DICT[u'type'] == metadata_dict[u'resourceType']


@pytest.mark.ckan_config(u'ckanext.doi.publisher', u'Example Publisher')
def test_handles_bad_data():
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


@pytest.mark.ckan_config(u'ckanext.doi.publisher', u'Example Publisher')
def test_generate_xml():
    xml_dict = build_xml_dict(constants.METADATA_DICT)
    xml_dict[u'identifier'] = {
        u'identifierType': u'DOI',
        u'identifier': u'10.0000/this-would-be-a-doi'
    }
    validator = validator_factory(pkg_resources.resource_filename(
        u'datacite',
        u'schemas/datacite-v4.2.json'
    ))
    assert validator.is_valid(xml_dict)

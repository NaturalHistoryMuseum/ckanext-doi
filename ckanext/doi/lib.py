#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

from ckanext.doi.api import MetadataDataCiteAPI, DOIDataCiteAPI
from pylons import config

TEST_PREFIX = '10.5072'

def get_prefix():
    """
    Get the prefix to use for DOIs
    @return: test prefix if we're in test mode, otherwise config prefix setting
    """

    test_mode = config.get("ckanext.doi.test_mode")
    return TEST_PREFIX if test_mode else config.get("ckanext.doi.prefix")


def upsert_doi(identifier, url, title, creator, publisher, publisher_year, **kwargs):
    """
    Helper function for minting a new doi
    Need to create metadata first
    And then create DOI => URI association
    See MetadataDataCiteAPI.metadata_to_xml for param information
    @param identifier:
    @param title:
    @param creator:
    @param publisher:
    @param publisher_year:
    @param kwargs:
    @return: request response
    """

    metadata = MetadataDataCiteAPI()
    metadata.upsert(identifier, title, creator, publisher, publisher_year, **kwargs)
    doi = DOIDataCiteAPI()
    r = doi.upsert(doi=identifier, url=url)
    assert r.status_code == 201, 'Operation failed ERROR CODE: %s' % r.status_code
    return r.text == 'OK'




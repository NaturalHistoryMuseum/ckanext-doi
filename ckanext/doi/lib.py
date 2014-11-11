#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

import os
import random
import dateutil.parser as parser
from datetime import datetime
from requests.exceptions import HTTPError
from ckanext.doi.config import get_prefix
from ckanext.doi.api import MetadataDataCiteAPI, DOIDataCiteAPI


def mint_doi(identifier, url, title, creator, publisher, publisher_year, **kwargs):
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


def get_unique_identifier():
    """
    Loop generating a unique identifier
    Checks if it already exists - if it doesn't we can use it
    If it does already exist, generate another one
    We check against the datacite repository, rather than our own internal database
    As multiple services can be minting DOIs
    @return:
    """

    api = DOIDataCiteAPI()

    while True:
        identifier = os.path.join(get_prefix(), '{0:07}'.format(random.randint(1, 100000)))
        try:
            api.get(identifier)
        except HTTPError:
            return identifier


def get_metadata_created_datetime(pkg_dict):

    """
    Get metadata created value, parsed into datetime if it's not already
    @param pkg_dict:
    @return:
    """
    if not isinstance(pkg_dict['metadata_created'], datetime):
        pkg_dict['metadata_created'] = parser.parse(pkg_dict['metadata_created'])

    return pkg_dict['metadata_created']
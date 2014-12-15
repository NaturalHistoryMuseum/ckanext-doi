#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

import os
import random
from logging import getLogger
from pylons import config
from ckan.model import Session
from requests.exceptions import HTTPError
from ckanext.doi.config import get_prefix, get_site_url, TEST_PREFIX
from ckanext.doi.api import MetadataDataCiteAPI, DOIDataCiteAPI
from ckanext.doi.model import DOI


log = getLogger(__name__)


UNIQUE_LOOKUP_LIMIT = 10


def get_unique_identifier():
    """
    Loop generating a unique identifier
    Checks if it already exists - if it doesn't we can use it
    If it does already exist, generate another one
    We check against the datacite repository, rather than our own internal database
    As multiple services can be minting DOIs
    @return:
    """
    metadata = MetadataDataCiteAPI()

    # BS: Bugfix. This was using while True to keep calling until a unique identifier was found
    # However, DataCite have just updated their API so calling DOIDataCiteAPI.get() for an
    # unknown DOI now returns http://www.datacite.org/testprefix. Switched to using
    # metadata look up service, and limit number of attempts to UNIQUE_LOOKUP_LIMIT
    for _ in range(UNIQUE_LOOKUP_LIMIT):
        identifier = os.path.join(get_prefix(), '{0:07}'.format(random.randint(1, 100000)))
        try:
            metadata.get(identifier)
            log.info('Identifier %s already exists', identifier)
        except HTTPError:
            return identifier

    raise Exception('Could not find unique identifier after %s attempts' % UNIQUE_LOOKUP_LIMIT)


def create_doi(package_id, **kwargs):

    """
    Helper function for minting a new doi
    Need to create metadata first
    And then create DOI => URI association
    See MetadataDataCiteAPI.metadata_to_xml for param information
    @param package_id:
    @param title:
    @param creator:
    @param publisher:
    @param publisher_year:
    @param kwargs:
    @return: request response
    """
    identifier = get_unique_identifier()
    kwargs['identifier'] = identifier

    metadata = MetadataDataCiteAPI()
    metadata.upsert(**kwargs)

    # The ID of a dataset never changes, so use that for the URL
    url = os.path.join(get_site_url(), 'dataset', package_id)

    doi = DOIDataCiteAPI()
    r = doi.upsert(doi=identifier, url=url)
    assert r.status_code == 201, 'Operation failed ERROR CODE: %s' % r.status_code

    # If we have created the DOI, save it to the database
    if r.text == 'OK':
        doi = DOI(package_id=package_id, identifier=identifier)
        Session.add(doi)

    log.debug('Created new DOI for package %s' % package_id)


def update_doi(package_id, **kwargs):

    doi = get_doi(package_id)
    kwargs['identifier'] = doi.identifier

    metadata = MetadataDataCiteAPI()
    metadata.upsert(**kwargs)


def get_doi(package_id):
    doi = Session.query(DOI).filter(DOI.package_id==package_id).first()
    return doi

def doi_is_test(doi):
    """
    Evaluate whether a DOI is a test one or not
    (contains TEST_PREFIX)
    @param doi:
    @return:
    """

    return bool(TEST_PREFIX in doi.identifier)

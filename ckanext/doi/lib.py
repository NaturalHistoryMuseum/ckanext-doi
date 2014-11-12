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
from ckanext.doi.config import get_prefix
from ckanext.doi.api import MetadataDataCiteAPI, DOIDataCiteAPI
from ckanext.doi.model import DOI

log = getLogger(__name__)


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
    site_url = config.get('ckan.site_url', '').rstrip('/')
    # TEMP: Override development
    site_url = 'http://data.nhm.ac.uk'
    url = os.path.join(site_url, 'dataset', package_id)

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
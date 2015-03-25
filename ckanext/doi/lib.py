#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

import os
import random
import datetime
from logging import getLogger
from ckan.model import Session
from requests.exceptions import HTTPError
from ckanext.doi.config import get_prefix, get_site_url, TEST_PREFIX
from ckanext.doi.api import MetadataDataCiteAPI, DOIDataCiteAPI
from ckanext.doi.model.doi import DOI


log = getLogger(__name__)


def create_unique_identifier(package_id):
    """
    Create a unique identifier, using the prefix and a random number: 10.5072/0044634
    Checks the random number doesn't exist in the table or the datacite repository
    All unique identifiers are created with
    @return:
    """
    datacite_api = DOIDataCiteAPI()

    while True:

        identifier = os.path.join(get_prefix(), '{0:07}'.format(random.randint(1, 100000)))

        # Check this identifier doesn't exist in the table
        if not Session.query(DOI).filter(DOI.identifier == identifier).count():

            # And check against the datacite service
            try:
                datacite_doi = datacite_api.get(identifier)
            except HTTPError:
                pass
            else:
                if datacite_doi.text:
                    continue

        doi = DOI(package_id=package_id, identifier=identifier)
        Session.add(doi)
        Session.commit()

        return doi


def publish_doi(package_id, **kwargs):

    """
    Publish a DOI to DataCite

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
    identifier = kwargs.get('identifier')

    metadata = MetadataDataCiteAPI()
    metadata.upsert(**kwargs)

    # The ID of a dataset never changes, so use that for the URL
    url = os.path.join(get_site_url(), 'dataset', package_id)

    doi = DOIDataCiteAPI()
    r = doi.upsert(doi=identifier, url=url)
    assert r.status_code == 201, 'Operation failed ERROR CODE: %s' % r.status_code

    # If we have created the DOI, save it to the database
    if r.text == 'OK':
        # Update status for this package and identifier
        num_affected = Session.query(DOI).filter_by(package_id=package_id, identifier=identifier).update({"published": datetime.datetime.now()})
        # Raise an error if update has failed - should never happen unless
        # DataCite and local db get out of sync - in which case requires investigating
        assert num_affected == 1, 'Updating local DOI failed'

    log.debug('Created new DOI for package %s' % package_id)


def update_doi(package_id, **kwargs):
    doi = get_doi(package_id)
    kwargs['identifier'] = doi.identifier
    metadata = MetadataDataCiteAPI()
    metadata.upsert(**kwargs)


def get_doi(package_id):
    doi = Session.query(DOI).filter(DOI.package_id==package_id).first()
    return doi
#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

import os
import random
import datetime
import itertools
from logging import getLogger
from ckan.model import Session
from pylons import config
from requests.exceptions import HTTPError
import ckan.model as model
from ckan.lib import helpers as h
import ckan.plugins as p
from ckanext.doi.api import MetadataDataCiteAPI, DOIDataCiteAPI
from ckanext.doi.model.doi import DOI
from ckanext.doi.datacite import get_prefix
from ckanext.doi.interfaces import IDoi
from ckanext.doi.exc import DOIMetadataException
from ckanext.doi.helpers import package_get_year

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
    @param kwargs contains metadata:
        @param title:
        @param creator:
        @param publisher:
        @param publisher_year:
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


def get_site_url():
    """
    Get the site URL
    Try and use ckanext.doi.site_url but if that's not set use ckan.site_url
    @return:
    """
    site_url = config.get("ckanext.doi.site_url")

    if not site_url:
        site_url = config.get('ckan.site_url')

    return site_url.rstrip('/')


def build_metadata(pkg_dict, doi):

    # Build the datacite metadata - all of these are core CKAN fields which should
    # be the same across all CKAN sites
    # This builds a dictionary keyed by the datacite metadata xml schema
    metadata_dict = {
        'identifier': doi.identifier,
        'title': pkg_dict['title'],
        'creator': pkg_dict['author'],
        'publisher': config.get("ckanext.doi.publisher"),
        'publisher_year': package_get_year(pkg_dict),
        'description': pkg_dict['notes'],
    }

    # Convert the format to comma delimited
    try:
        # Filter out empty strings in the array (which is what we have if nothing is entered)
        # We want to make sure all None values are removed so we can compare
        # the dict here, with one loaded via action.package_show which doesn't
        # return empty values
        pkg_dict['res_format'] = filter(None, pkg_dict['res_format'])
        if pkg_dict['res_format']:
            metadata_dict['format'] = ', '.join([f for f in pkg_dict['res_format']])
    except KeyError:
        pass

    # If we have tag_string use that to build subject
    if 'tag_string' in pkg_dict:
        metadata_dict['subject'] = pkg_dict.get('tag_string', '').split(',').sort()
    elif 'tags' in pkg_dict:
        # Otherwise use the tags list itself
        metadata_dict['subject'] = list(set([tag['name'] if isinstance(tag, dict) else tag for tag in pkg_dict['tags']])).sort()

    if pkg_dict['license_id'] != 'notspecified':

        licenses = model.Package.get_license_options()

        for license_title, license_id in licenses:
            if license_id == pkg_dict['license_id']:
                metadata_dict['rights'] = license_title
                break

    if pkg_dict.get('version', None):
        metadata_dict['version'] = pkg_dict['version']

    # Try and get spatial
    if 'extras_spatial' in pkg_dict and pkg_dict['extras_spatial']:
        geometry = h.json.loads(pkg_dict['extras_spatial'])

        if geometry['type'] == 'Point':
            metadata_dict['geo_point'] = '%s %s' % tuple(geometry['coordinates'])
        elif geometry['type'] == 'Polygon':
            # DataCite expects box coordinates, not geo pairs
            # So dedupe to get the box and join into a string
            metadata_dict['geo_box'] = ' '.join([str(coord) for coord in list(set(itertools.chain.from_iterable(geometry['coordinates'][0])))])

    # Allow plugins to alter the datacite DOI metadata
    # So other CKAN instances can add their own custom fields - and we can
    # Add our data custom to NHM
    for plugin in p.PluginImplementations(IDoi):
        plugin.build_metadata(pkg_dict, metadata_dict)

    return metadata_dict


def validate_metadata(metadata_dict):
    """
    Validate the metadata - loop through mandatory fields and check they are populated
    """

    # Check we have mandatory DOI fields
    mandatory_fields = ['title', 'creator']

    # Make sure our mandatory fields are populated
    for field in mandatory_fields:
        if not metadata_dict.get(field, None):
            raise DOIMetadataException('Missing DataCite required field %s' % field)
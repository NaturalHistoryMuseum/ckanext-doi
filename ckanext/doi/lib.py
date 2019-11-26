# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import datetime
import itertools
import json
import random
from logging import getLogger

import os
from ckanext.doi.api import DOIDataCiteAPI, MetadataDataCiteAPI
from ckanext.doi.datacite import get_prefix
from ckanext.doi.exc import DOIMetadataException
from ckanext.doi.helpers import package_get_year
from ckanext.doi.interfaces import IDoi
from ckanext.doi.model.doi import DOI
from requests.exceptions import HTTPError

from ckan.model import Package, Session
from ckan.plugins import PluginImplementations, toolkit

log = getLogger(__name__)


def get_or_create_doi(package_id):
    '''Create or retrieve the unique identifier for this package_id.

    :param package_id:

    '''
    datacite_api = DOIDataCiteAPI()

    doi = get_doi(package_id)
    if doi is None:
        while True:
            identifier = os.path.join(get_prefix(),
                                      u'{0:07}'.format(random.randint(1, 100000)))

            # Check this identifier doesn't exist in the table
            if Session.query(DOI).filter(DOI.identifier == identifier).count():
                continue

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
            break

    return doi


def publish_doi(package_id, **kwargs):
    '''Publish a DOI to DataCite

    Need to create metadata first
    And then create DOI => URI association
    See MetadataDataCiteAPI.metadata_to_xml for param information

    :param package_id: param kwargs contains metadata:
    :param title: param creator:
    :param publisher: param publisher_year:
    :param **kwargs:
    :returns: request response

    '''
    identifier = kwargs.get(u'identifier')

    metadata = MetadataDataCiteAPI()
    metadata.upsert(**kwargs)

    # The ID of a dataset never changes, so use that for the URL
    url = os.path.join(get_site_url(), u'dataset', package_id)

    doi = DOIDataCiteAPI()
    r = doi.upsert(doi=identifier, url=url)
    assert r.status_code == 201, u'Operation failed ERROR CODE: %s' % r.status_code
    # If we have created the DOI, save it to the database
    if r.text == u'OK':
        # Update status for this package and identifier
        num_affected = Session.query(DOI).filter_by(package_id=package_id,
                                                    identifier=identifier).update({
            u'published': datetime.datetime.now()
            })
        # Raise an error if update has failed - should never happen unless
        # DataCite and local db get out of sync - in which case requires investigating
        assert num_affected == 1, u'Updating local DOI failed'

    log.debug(u'Created new DOI for package %s' % package_id)


def update_doi(package_id, **kwargs):
    '''

    :param package_id:
    :param **kwargs:

    '''
    doi = get_doi(package_id)
    kwargs[u'identifier'] = doi.identifier
    metadata = MetadataDataCiteAPI()
    metadata.upsert(**kwargs)


def get_doi(package_id):
    '''

    :param package_id:

    '''
    doi = Session.query(DOI).filter(DOI.package_id == package_id).first()
    return doi


def get_site_url():
    '''Get the site URL
    Try and use ckanext.doi.site_url but if that's not set use ckan.site_url


    '''
    site_url = toolkit.config.get(u'ckanext.doi.site_url')

    if not site_url:
        site_url = toolkit.config.get(u'ckan.site_url')

    return site_url.rstrip('/')


def build_metadata(pkg_dict, doi):
    '''

    :param pkg_dict:
    :param doi:

    '''

    # Build the datacite metadata - all of these are core CKAN fields which should
    # be the same across all CKAN sites
    # This builds a dictionary keyed by the datacite metadata xml schema
    metadata_dict = {
        u'identifier': doi.identifier,
        u'title': pkg_dict[u'title'],
        u'creator': pkg_dict[u'author'],
        u'publisher': toolkit.config.get(u'ckanext.doi.publisher'),
        u'publisher_year': package_get_year(pkg_dict),
        u'description': pkg_dict[u'notes'],
        }

    # Convert the format to comma delimited
    try:
        # Filter out empty strings in the array (which is what we have if nothing is
        # entered)
        # We want to make sure all None values are removed so we can compare
        # the dict here, with one loaded via action.package_show which doesn't
        # return empty values
        pkg_dict[u'res_format'] = filter(None, pkg_dict[u'res_format'])
        if pkg_dict[u'res_format']:
            metadata_dict[u'format'] = u', '.join([f for f in pkg_dict[u'res_format']])
    except KeyError:
        pass

    # If we have tag_string use that to build subject
    if u'tag_string' in pkg_dict:
        tags = pkg_dict.get(u'tag_string', u'').split(u',').sort()
        if tags:
            metadata_dict[u'subject'] = tags
    elif u'tags' in pkg_dict:
        # Otherwise use the tags list itself
        metadata_dict[u'subject'] = list(set(
            [tag[u'name'] if isinstance(tag, dict) else tag for tag in
             pkg_dict[u'tags']])).sort()

    if pkg_dict.get(u'license_id', u'notspecified') != u'notspecified':

        licenses = Package.get_license_options()

        for license_title, license_id in licenses:
            if license_id == pkg_dict[u'license_id']:
                metadata_dict[u'rights'] = license_title
                break

    if pkg_dict.get(u'version', None):
        metadata_dict[u'version'] = pkg_dict[u'version']

    # Try and get spatial
    if u'extras_spatial' in pkg_dict and pkg_dict[u'extras_spatial']:
        geometry = json.loads(pkg_dict[u'extras_spatial'])

        if geometry[u'type'] == u'Point':
            metadata_dict[u'geo_point'] = u'%s %s' % tuple(geometry[u'coordinates'])
        elif geometry[u'type'] == u'Polygon':
            # DataCite expects box coordinates, not geo pairs
            # So dedupe to get the box and join into a string
            metadata_dict[u'geo_box'] = u' '.join([str(coord) for coord in list(
                set(itertools.chain.from_iterable(geometry[u'coordinates'][0])))])

    # Allow plugins to alter the datacite DOI metadata
    # So other CKAN instances can add their own custom fields - and we can
    # Add our data custom to NHM
    for plugin in PluginImplementations(IDoi):
        plugin.build_metadata(pkg_dict, metadata_dict)

    return metadata_dict


def validate_metadata(metadata_dict):
    '''Validate the metadata - loop through mandatory fields and check they are populated

    :param metadata_dict:

    '''

    # Check we have mandatory DOI fields
    mandatory_fields = [u'title', u'creator']

    # Make sure our mandatory fields are populated
    for field in mandatory_fields:
        if not metadata_dict.get(field, None):
            raise DOIMetadataException(u'Missing DataCite required field %s' % field)

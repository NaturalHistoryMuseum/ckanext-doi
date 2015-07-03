#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

import os
import abc
import requests
from requests import ConnectionError
from pylons import config
from xmltodict import unparse
from ckanext.doi.datacite import get_endpoint
from logging import getLogger
import ckan.plugins as p
from ckanext.doi.interfaces import IDoi

log = getLogger(__name__)

class DataCiteAPI(object):

    @abc.abstractproperty
    def path(self):
        return None

    def _call(self, **kwargs):

        account_name = config.get("ckanext.doi.account_name")
        account_password = config.get("ckanext.doi.account_password")
        endpoint = os.path.join(get_endpoint(), self.path)

        try:
            path_extra = kwargs.pop('path_extra')
        except KeyError:
            pass
        else:
            endpoint = os.path.join(endpoint, path_extra)

        try:
            method = kwargs.pop('method')
        except KeyError:
            method = 'get'

        # Add authorisation to request
        kwargs['auth'] = (account_name, account_password)

        log.info("Calling %s:%s - %s", endpoint, method, kwargs)

        r = getattr(requests, method)(endpoint, **kwargs)
        r.raise_for_status()
        # Return the result
        return r


class MetadataDataCiteAPI(DataCiteAPI):
    """
    Calls to DataCite metadata API
    """
    path = 'metadata'

    def get(self, doi):
        """
        URI: https://datacite.org/mds/metadata/{doi} where {doi} is a specific DOI.
        @param doi:
        @return: The most recent version of metadata associated with a given DOI.
        """
        return self._call(path_extra=doi)

    @staticmethod
    def metadata_to_xml(identifier, title, creator, publisher, publisher_year, **kwargs):
        """
        Pass in variables and return XML in the format ready to send to DataCite API

        @param identifier: DOI
        @param title: A descriptive name for the resource
        @param creator: The author or producer of the data. There may be multiple Creators, in which case they should be listed in order of priority
        @param publisher: The data holder. This is usually the repository or data centre in which the data is stored
        @param publisher_year: The year when the data was (or will be) made publicly available.
        @param kwargs: optional metadata
        @return:
        """

        # Make sure a var is a list so we can easily loop through it
        # Useful for properties were multiple is optional
        def _ensure_list(var):
            return var if isinstance(var, list) else [var]

        # Encode title ready for posting
        title = title.encode('unicode-escape')

        # Optional metadata properties
        subject = kwargs.get('subject')
        description = kwargs.get('description').encode('unicode-escape')
        size = kwargs.get('size')
        format = kwargs.get('format')
        version = kwargs.get('version')
        rights = kwargs.get('rights')
        geo_point = kwargs.get('geo_point')
        geo_box = kwargs.get('geo_box')

        # Optional metadata properties, with defaults
        resource_type = kwargs.get('resource_type', 'Dataset')
        language = kwargs.get('language', 'eng')

        # Create basic metadata with mandatory metadata properties
        xml_dict = {
            'resource': {
                '@xmlns': 'http://datacite.org/schema/kernel-3',
                '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                '@xsi:schemaLocation': 'http://datacite.org/schema/kernel-3 http://schema.datacite.org/meta/kernel-3/metadata.xsd',
                'identifier': {'@identifierType': 'DOI', '#text': identifier},
                'titles': {
                    'title': {'#text': title}
                },
                'creators': {
                    'creator': [{'creatorName': c.encode('unicode-escape')} for c in _ensure_list(creator)],
                },
                'publisher': publisher,
                'publicationYear': publisher_year,
            }
        }

        # Add subject (if it exists)
        if subject:
            xml_dict['resource']['subjects'] = {
                'subject': [c for c in _ensure_list(subject)]
            }

        if description:
            xml_dict['resource']['descriptions'] = {
                'description': {
                    '@descriptionType': 'Abstract',
                    '#text': description
                }
            }

        if size:
            xml_dict['resource']['sizes'] = {
                'size': size
            }

        if format:
            xml_dict['resource']['formats'] = {
                'format': format
            }

        if version:
            xml_dict['resource']['version'] = version

        if rights:
            xml_dict['resource']['rightsList'] = {
                'rights': rights
            }

        if resource_type:
            xml_dict['resource']['resourceType'] = {
                '@resourceTypeGeneral': 'Dataset',
                '#text': resource_type
            }

        if language:
            xml_dict['resource']['language'] = language

        if geo_point:
            xml_dict['resource']['geoLocations'] = {
                'geoLocation': {
                    'geoLocationPoint': geo_point
                }
            }

        if geo_box:
            xml_dict['resource']['geoLocations'] = {
                'geoLocation': {
                    'geoLocationBox': geo_box
                }
            }

        for plugin in p.PluginImplementations(IDoi):
            xml_dict = plugin.metadata_to_xml(xml_dict, kwargs)

        return unparse(xml_dict, pretty=True, full_document=False)

    def upsert(self, identifier, title, creator, publisher, publisher_year, **kwargs):
        """
        URI: https://test.datacite.org/mds/metadata
        This request stores new version of metadata. The request body must contain valid XML.
        @param metadata_dict: dict to convert to xml
        @return: URL of the newly stored metadata
        """
        xml = self.metadata_to_xml(identifier, title, creator, publisher, publisher_year, **kwargs)
        r = self._call(method='post', data=xml, headers={'Content-Type': 'application/xml'})
        assert r.status_code == 201, 'Operation failed ERROR CODE: %s' % r.status_code
        return r

    def delete(self, doi):
        """
        URI: https://test.datacite.org/mds/metadata/{doi} where {doi} is a specific DOI.
        This request marks a dataset as 'inactive'.
        @param doi: DOI
        @return: Response code
        """
        return self._call(path_extra=doi, method='delete')


class DOIDataCiteAPI(DataCiteAPI):
    """
    Calls to DataCite DOI API
    """
    path = 'doi'

    def get(self, doi):
        """
        Get a specific DOI
        URI: https://datacite.org/mds/doi/{doi} where {doi} is a specific DOI.

        @param doi: DOI
        @return: This request returns an URL associated with a given DOI.
        """
        r = self._call(path_extra=doi)
        return r

    def list(self):
        """
        list all DOIs
        URI: https://datacite.org/mds/doi

        @return: This request returns a list of all DOIs for the requesting data centre. There is no guaranteed order.
        """
        return self._call()

    def upsert(self, doi, url):
        """
        URI: https://datacite.org/mds/doi
        POST will mint new DOI if specified DOI doesn't exist. This method will attempt to update URL if you specify existing DOI. Standard domains and quota restrictions check will be performed. A Datacentre's doiQuotaUsed will be increased by 1. A new record in Datasets will be created.

        @param doi: doi to mint
        @param url: url doi points to
        @return:
        """
        return self._call(
            # Send as data rather than params so it's posted as x-www-form-urlencoded
            data={
                'doi': doi,
                'url': url
            },
            method='post',
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

class MediaDataCiteAPI(DataCiteAPI):
    """
    Calls to DataCite Metadata API
    """
    pass


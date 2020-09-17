# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from logging import getLogger

import abc
import os
import requests
from ckanext.doi.datacite import get_endpoint, get_test_mode
from ckanext.doi.interfaces import IDoi
from requests import ConnectionError, HTTPError
from xmltodict import unparse

from ckan.plugins import PluginImplementations, toolkit

log = getLogger(__name__)


class DataCiteAPI(object):
    ''' '''

    @abc.abstractproperty
    def path(self):
        ''' '''
        return None

    def _call(self, **kwargs):
        '''

        :param **kwargs:

        '''

        account_name = toolkit.config.get(u'ckanext.doi.account_name')
        account_password = toolkit.config.get(u'ckanext.doi.account_password')
        endpoint = os.path.join(get_endpoint(), self.path)

        try:
            path_extra = kwargs.pop(u'path_extra')
        except KeyError:
            pass
        else:
            endpoint = os.path.join(endpoint, path_extra)

        try:
            method = kwargs.pop(u'method')
        except KeyError:
            method = u'get'

        # Add authorisation to request
        kwargs[u'auth'] = (account_name, account_password)

        if get_test_mode():
            kwargs[u'verify'] = False

        log.info(u'Calling %s:%s - %s', endpoint, method, kwargs)

        try:
            r = getattr(requests, method)(endpoint, **kwargs)
            r.raise_for_status()
            assert r.status_code == 201, u'Operation failed ERROR CODE: %s' % \
                                         r.status_code
        except ConnectionError, e:
            log.error(u'Creating DOI Failed - %s', e)
            raise
        except HTTPError, e:
            log.error(u'Creating DOI Failed - %s', e)
            log.error(u'Creating DOI Failed - error code %s', r.status_code)
            log.error(u'Creating DOI Failed - error %s', r.content)
            raise
        except AssertionError:
            log.error(u'Creating DOI Failed - error code %s', r.status_code)
            log.error(u'Creating DOI Failed - error %s', r.content)
            raise
        else:
            return r


class MetadataDataCiteAPI(DataCiteAPI):
    '''Calls to DataCite metadata API'''
    path = u'metadata'

    def get(self, doi):
        '''URI: https://datacite.org/mds/metadata/{doi} where {doi} is a specific DOI.

        :param doi: return: The most recent version of metadata associated with a
        given DOI.
        :returns: The most recent version of metadata associated with a given DOI.

        '''
        return self._call(path_extra=doi)

    @staticmethod
    def metadata_to_xml(identifier, title, creator, publisher, publisher_year, **kwargs):
        '''Pass in variables and return XML in the format ready to send to DataCite API

        :param identifier: DOI
        :param title: A descriptive name for the resource
        :param creator: The author or producer of the data. There may be multiple
        Creators, in which case they should be listed in order of priority
        :param publisher: The data holder. This is usually the repository or data
        centre in which the data is stored
        :param publisher_year: The year when the data was (or will be) made publicly
        available.
        :param kwargs: optional metadata
        :param **kwargs:

        '''

        # Make sure a var is a list so we can easily loop through it
        # Useful for properties were multiple is optional
        def _ensure_list(var):
            '''

            :param var:

            '''
            return var if isinstance(var, list) else [var]

        # Encode title ready for posting
        title = title.encode(u'unicode-escape')

        # Optional metadata properties
        subject = kwargs.get(u'subject')
        description = kwargs.get(u'description').encode(u'unicode-escape')
        size = kwargs.get(u'size')
        format = kwargs.get(u'format')
        version = kwargs.get(u'version')
        rights = kwargs.get(u'rights')
        geo_point = kwargs.get(u'geo_point')
        geo_box = kwargs.get(u'geo_box')

        # Optional metadata properties, with defaults
        resource_type = kwargs.get(u'resource_type', u'Dataset')
        language = kwargs.get(u'language', u'en')  # use ISO 639-1 language codes

        # Create basic metadata with mandatory metadata properties
        xml_dict = {
            u'resource': {
                u'@xmlns': u'http://datacite.org/schema/kernel-4',
                u'@xmlns:xsi': u'http://www.w3.org/2001/XMLSchema-instance',
                u'@xsi:schemaLocation': u'http://datacite.org/schema/kernel-4 '
                                        u'http://schema.datacite.org/meta/kernel-4.3/metadata.xsd',
                u'identifier': {
                    u'@identifierType': u'DOI',
                    u'#text': identifier
                    },
                u'titles': {
                    u'title': {
                        u'#text': title
                        }
                    },
                u'creators': {
                    u'creator': [{
                        u'creatorName': c.encode(u'unicode-escape')
                        } for c in _ensure_list(creator)],
                    },
                u'publisher': publisher,
                u'publicationYear': publisher_year,
                }
            }

        # Add subject (if it exists)
        if subject:
            xml_dict[u'resource'][u'subjects'] = {
                u'subject': [c for c in _ensure_list(subject)]
                }

        if description:
            xml_dict[u'resource'][u'descriptions'] = {
                u'description': {
                    u'@descriptionType': u'Abstract',
                    u'#text': description
                    }
                }

        if size:
            xml_dict[u'resource'][u'sizes'] = {
                u'size': size
                }

        if format:
            xml_dict[u'resource'][u'formats'] = {
                u'format': format
                }

        if version:
            xml_dict[u'resource'][u'version'] = version

        if rights:
            xml_dict[u'resource'][u'rightsList'] = {
                u'rights': rights
                }

        if resource_type:
            xml_dict[u'resource'][u'resourceType'] = {
                u'@resourceTypeGeneral': u'Dataset',
                u'#text': resource_type
                }

        if language:
            xml_dict[u'resource'][u'language'] = language

        if geo_point:
            xml_dict[u'resource'][u'geoLocations'] = {
                u'geoLocation': {
                    u'geoLocationPoint': geo_point
                    }
                }

        if geo_box:
            xml_dict[u'resource'][u'geoLocations'] = {
                u'geoLocation': {
                    u'geoLocationBox': geo_box
                    }
                }
        for plugin in PluginImplementations(IDoi):
            xml_dict = plugin.metadata_to_xml(xml_dict, kwargs)
        return unparse(xml_dict, pretty=True, full_document=False)

    def upsert(self, identifier, title, creator, publisher, publisher_year, **kwargs):
        '''URI: https://test.datacite.org/mds/metadata
        This request stores new version of metadata. The request body must contain
        valid XML.

        :param metadata_dict: dict to convert to xml
        :param identifier:
        :param title:
        :param creator:
        :param publisher:
        :param publisher_year:
        :param **kwargs:
        :returns: URL of the newly stored metadata

        '''
        xml = self.metadata_to_xml(identifier, title, creator, publisher, publisher_year,
                                   **kwargs)
        try:
            r = self._call(method=u'put', data=xml, headers={
                u'Content-Type': u'application/xml'
                }, path_extra=identifier)
        except HTTPError as e:
            r = {u'success': False, u'error': {u'message': e.message, u'__type': e.response.status_code}}
        return r

    def delete(self, doi):
        '''URI: https://test.datacite.org/mds/metadata/{doi} where {doi} is a specific
        DOI.
        This request marks a dataset as 'inactive'.

        :param doi: DOI
        :returns: Response code

        '''
        return self._call(path_extra=doi, method=u'delete')


class DOIDataCiteAPI(DataCiteAPI):
    '''Calls to DataCite DOI API'''
    path = u'doi'

    def get(self, doi):
        '''Get a specific DOI
        URI: https://datacite.org/mds/doi/{doi} where {doi} is a specific DOI.

        :param doi: DOI
        :returns: This request returns an URL associated with a given DOI.

        '''
        r = self._call(path_extra=doi)
        return r

    def list(self):
        '''list all DOIs
        URI: https://datacite.org/mds/doi


        :returns: This request returns a list of all DOIs for the requesting data
        centre. There is no guaranteed order.

        '''
        return self._call()

    def upsert(self, doi, url):
        '''URI: https://datacite.org/mds/doi
        POST will mint new DOI if specified DOI doesn't exist. This method will
        attempt to update URL if you specify existing DOI. Standard domains and quota
        restrictions check will be performed. A Datacentre's doiQuotaUsed will be
        increased by 1. A new record in Datasets will be created.

        :param doi: doi to mint
        :param url: url doi points to

        '''
        return self._call(
            # Send as data rather than params so it's posted as x-www-form-urlencoded
            data={
                u'doi': doi,
                u'url': url
                },
            method=u'put',
            headers={
                u'Content-Type': u'application/x-www-form-urlencoded'
                },
            path_extra=doi
            )


class MediaDataCiteAPI(DataCiteAPI):
    '''Calls to DataCite Media API'''
    pass

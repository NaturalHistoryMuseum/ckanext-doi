#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import logging
import random
import string
from datetime import datetime as dt

import xmltodict
from ckan.plugins import toolkit
from ckanext.doi.model.crud import DOIQuery
from datacite import DataCiteMDSClient, schema42
from datacite.errors import DataCiteError, DataCiteNotFoundError
from paste.deploy.converters import asbool

log = logging.getLogger(__name__)


class DataciteClient(object):
    test_url = u'https://mds.test.datacite.org'

    def __init__(self):
        self.username = toolkit.config.get(u'ckanext.doi.account_name')
        self.password = toolkit.config.get(u'ckanext.doi.account_password')
        self._test_mode = None
        self.prefix = self.get_prefix()
        client_config = {
            u'username': self.username,
            u'password': self.password,
            u'prefix': self.prefix,
            u'test_mode': self.test_mode
        }
        if self.test_mode:
            # temporary fix because datacite 1.0.1 isn't updated for the test prefix deprecation
            client_config[u'url'] = self.test_url
        self.client = DataCiteMDSClient(**client_config)

    @property
    def test_mode(self):
        '''Whether to run in test mode. Defaults to true.
        :return: test mode enabled as boolean (true=enabled)
        '''
        if self._test_mode is None:
            self._test_mode = asbool(toolkit.config.get(u'ckanext.doi.test_mode', True))
        return self._test_mode

    @classmethod
    def get_prefix(cls):
        '''Get the prefix to use for DOIs.
        :return: config prefix setting
        '''
        DEPRECATED_TEST_PREFIX = u'10.5072'
        prefix = toolkit.config.get(u'ckanext.doi.prefix')
        if prefix is None:
            raise TypeError(u'You must set the ckanext.doi.prefix config value')
        if prefix == DEPRECATED_TEST_PREFIX:
            raise ValueError(
                u'The test prefix {0} has been retired; use a prefix defined in your datacite '
                u'test account'.format(DEPRECATED_TEST_PREFIX))
        return prefix

    def generate_doi(self):
        '''
        Generate a new DOI which isn't currently in use. The database is checked for previous
        usage, as is Datacite itself. Use whatever value is retuned from this function quickly to
        avoid double use as this function uses no locking.
        :return: the full, unique DOI
        '''
        # the list of valid characters is larger than just lowercase and the digits but we don't
        # need that many options and URLs with just alphanumeric characters in them are nicer. We
        # just use lowercase characters to avoid any issues with case being ignored
        valid_characters = string.ascii_lowercase + string.digits

        attempts = 5

        while attempts > 0:
            # generate a random 8 character identifier
            identifier = u''.join(random.choice(valid_characters) for _ in range(8))
            # form the doi using the prefix
            doi = u'{}/{}'.format(self.prefix, identifier)

            # check this doi doesn't exist in the table
            if DOIQuery.read_doi(doi) is not None:
                continue

            # check against the datacite service
            try:
                self.client.metadata_get(doi)
                # if a doi is found, we need to try again
                continue
            except DataCiteNotFoundError:
                # if no doi is found, we're good!
                pass
            except DataCiteError as e:
                log.warn(
                    u'Error whilst checking new DOIs with DataCite. DOI: {}, error: {}'.format(doi,
                                                                                               e.message))
                attempts -= 1
                continue

            # if we've made it this far the doi isn't in the database
            # and it's not in datacite already
            return doi
        else:
            raise Exception(u'Failed to generate a DOI')

    def mint_doi(self, doi, package_id):
        '''
        Mints the given DOI on datacite. Does not add metadata, just creates the DOI.
        :param doi: the doi (full, prefix and suffix)
        :param package_id: the id of the package this doi is for
        '''

        # create the URL the DOI will point to, i.e. the package page
        site = toolkit.config.get(u'ckan.site_url')
        if site[-1] != u'/':
            site += u'/'
        permalink = site + u'dataset/' + package_id
        # mint the DOI
        self.client.doi_post(doi, permalink)
        if DOIQuery.read_doi(doi) is None and DOIQuery.read_package(package_id) is None:
            DOIQuery.create(doi, package_id)
        elif DOIQuery.read_doi(doi) is None:
            # in case this was previously attempted but no DOI was added
            DOIQuery.update_package(package_id, identifier=doi)
        DOIQuery.update_doi(doi, published=dt.now())

    def set_metadata(self, doi, xml_dict):
        '''
        Update or create the metadata for a given DOI on datacite.
        :param doi: the DOI to update the metadata for
        :param xml_dict: the metadata as an xml dict (generated from build_xml_dict)
        :return:
        '''
        xml_dict[u'identifier'] = {
            u'identifierType': u'DOI',
            u'identifier': doi
        }

        # use an assert here because the data should be valid every time, otherwise it's
        # something the developer is going to have to fix
        assert schema42.validate(xml_dict)

        xml_doc = schema42.tostring(xml_dict)
        # create the metadata on datacite
        self.client.metadata_post(xml_doc)

    def get_metadata(self, doi):
        '''
        Retrieve metadata for a given DOI on datacite.
        :param doi: the DOI for which to retrieve the stored metadata
        :return:
        '''
        try:
            metadata = self.client.metadata_get(doi)
        except DataCiteNotFoundError:
            metadata = None
        return metadata

    def check_for_update(self, doi, xml_dict):
        '''
        Compare generated xml_dict against the one already posted on datacite.
        :param doi: the DOI of the package
        :param xml_dict: the xml_dict generated by build_xml_dict
        :return: True if the two are the same, False if not
        '''
        posted_xml = self.get_metadata(doi)
        if posted_xml is None or posted_xml.strip() == u'':
            return False
        posted_xml_dict = dict(xmltodict.parse(posted_xml).get(u'resource', {}))
        new_xml_dict = dict(xmltodict.parse(schema42.tostring(xml_dict))[u'resource'])
        if u'identifier' in posted_xml_dict:
            del posted_xml_dict[u'identifier']
        has_dates = u'dates' in posted_xml_dict and u'date' in posted_xml_dict[u'dates']
        if has_dates:
            posted_xml_dict[u'dates'][u'date'] = [d for d in posted_xml_dict[u'dates'][u'date']
                                                  if d[u'@dateType'] != u'Updated']
            new_xml_dict[u'dates'][u'date'] = [d for d in new_xml_dict[u'dates'][u'date']
                                               if d[u'@dateType'] != u'Updated']
            return cmp(posted_xml_dict, new_xml_dict) == 0
        else:
            # if the original doesn't have any dates, it's definitely different
            return False

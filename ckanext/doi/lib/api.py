#!/usr/bin/env python3
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import string

import logging
import random
import xmltodict
from ckan.plugins import toolkit
from ckanext.doi.model.crud import DOIQuery
from datacite import DataCiteMDSClient, schema42
from datacite.errors import DataCiteError, DataCiteNotFoundError
from datetime import datetime as dt

from crossref.restful import Depositor

from ckanext.doi.lib.helpers import doi_test_mode, get_doi_platform

log = logging.getLogger(__name__)

DEPRECATED_TEST_PREFIX = '10.5072'


class DOIClient:
    test_url = None
    client_name = ""

    def __init__(self):
        self.username = toolkit.config.get('ckanext.doi.account_name')
        self.password = toolkit.config.get('ckanext.doi.account_password')
        self._test_mode = False
        self.prefix = self.get_prefix()
        client_config = {
            'username': self.username,
            'password': self.password,
            'prefix': self.prefix,
            'test_mode': self.test_mode,
        }
        if self.test_mode:
            # temporary fix because datacite 1.0.1 isn't updated for the test prefix deprecation
            client_config['url'] = self.test_url
        self.client = DataCiteMDSClient(**client_config)

    @property
    def test_mode(self):
        """
        Whether to run in test mode.

        Defaults to true.
        :return: test mode enabled as boolean (true=enabled)
        """
        if self._test_mode is False:
            self._test_mode = doi_test_mode()
        return self._test_mode

    @classmethod
    def get_prefix(cls):
        """
        Get the prefix to use for DOIs.

        :return: config prefix setting
        """
        prefix = toolkit.config.get('ckanext.doi.prefix')
        if prefix is None:
            raise TypeError('You must set the ckanext.doi.prefix config value')
        if prefix == DEPRECATED_TEST_PREFIX:
            raise ValueError(
                f'The test prefix {DEPRECATED_TEST_PREFIX} has been retired; use a '
                f'prefix defined in your datacite test account'
            )
        return prefix

    def generate_doi(self):
        """
        Generate a new DOI which isn't currently in use.

        The database is checked for previous
        usage, as is Datacite itself. Use whatever value is retuned from this function quickly to
        avoid double use as this function uses no locking.
        :return: the full, unique DOI
        """
        # the list of valid characters is larger than just lowercase and the digits but we don't
        # need that many options and URLs with just alphanumeric characters in them are nicer. We
        # just use lowercase characters to avoid any issues with case being ignored
        valid_characters = string.ascii_lowercase + string.digits

        attempts = 5

        while attempts > 0:
            # generate a random 8 character identifier
            identifier = ''.join(random.choice(valid_characters) for _ in range(8))
            # form the doi using the prefix
            doi = f'{self.prefix}/{identifier}'

            if DOIQuery.read_doi(doi) is None:
                try:
                    self.client.metadata_get(doi)
                except DataCiteNotFoundError:
                    return doi
                except DataCiteError as e:
                    log.warning(
                        f'Error whilst checking new DOIs with DataCite. DOI: {doi}, '
                        f'error: {e}'
                    )
            attempts -= 1
        raise Exception('Failed to generate a DOI')


class DataciteClient(DOIClient):
    test_url = 'https://mds.test.datacite.org'
    client_name = "DataCite"

    def mint_doi(self, doi, package_id):
        """
        Mints the given DOI on datacite. Does not add metadata, just creates the DOI.

        :param doi: the doi (full, prefix and suffix)
        :param package_id: the id of the package this doi is for
        """

        # create the URL the DOI will point to, i.e. the package page
        site = toolkit.config.get('ckan.site_url')
        if site[-1] != '/':
            site += '/'
        permalink = f'{site}dataset/{package_id}'
        # mint the DOI
        self.client.doi_post(doi, permalink)
        if DOIQuery.read_doi(doi) is None and DOIQuery.read_package(package_id) is None:
            DOIQuery.create(doi, package_id)
        elif DOIQuery.read_doi(doi) is None:
            # in case this was previously attempted but no DOI was added
            DOIQuery.update_package(package_id, identifier=doi)
        DOIQuery.update_doi(doi, published=dt.now())

    def set_metadata(self, doi, xml_dict):
        """
        Update or create the metadata for a given DOI on datacite.

        :param doi: the DOI to update the metadata for
        :param xml_dict: the metadata as an xml dict (generated from build_xml_dict)
        :return:
        """
        xml_dict['identifiers'] = [{'identifierType': 'DOI', 'identifier': doi}]

        # check that the data is valid, this will raise a JSON schema exception if there are issues
        schema42.validator.validate(xml_dict)

        xml_doc = schema42.tostring(xml_dict)
        # create the metadata on datacite
        self.client.metadata_post(xml_doc)

    def get_metadata(self, doi):
        """
        Retrieve metadata for a given DOI on datacite.

        :param doi: the DOI for which to retrieve the stored metadata
        :return:
        """
        try:
            metadata = self.client.metadata_get(doi)
        except DataCiteNotFoundError:
            metadata = None
        return metadata

    def check_for_update(self, doi, xml_dict):
        """
        Compare generated xml_dict against the one already posted on datacite.

        :param doi: the DOI of the package
        :param xml_dict: the xml_dict generated by build_xml_dict
        :return: True if the two are the same, False if not
        """
        posted_xml = self.get_metadata(doi)
        if posted_xml is None or posted_xml.strip() == '':
            return False
        posted_xml_dict = dict(xmltodict.parse(posted_xml).get('resource', {}))
        new_xml_dict = dict(xmltodict.parse(schema42.tostring(xml_dict))['resource'])
        if 'identifier' in posted_xml_dict:
            del posted_xml_dict['identifier']
        has_dates = 'dates' in posted_xml_dict and 'date' in posted_xml_dict['dates']
        if has_dates:
            posted_xml_dict['dates']['date'] = [
                d
                for d in posted_xml_dict['dates']['date']
                if d['@dateType'] != 'Updated'
            ]
            new_xml_dict['dates']['date'] = [
                d for d in new_xml_dict['dates']['date'] if d['@dateType'] != 'Updated'
            ]
            return posted_xml_dict == new_xml_dict
        else:
            # if the original doesn't have any dates, it's definitely different
            return False


class CrossrefClient(DOIClient):
    test_url = 'https://test.crossref.org'
    client_name = "Crossref"

    def set_metadata(self, doi, xml_dict):
        """
        Prepares and send metadata to Crossref to generate DOI.

        :param doi: DOI identifier
        :param xml_dict: the metadata as an xml dict (generated from build_xml_dict)
        :return:
        """
        self.make_crossref_request(self, doi, xml_dict)

    def make_crossref_request(self, doi, xml_dict):
        error_msg = None
        elements = doi.split("/")

        if len(elements) == 2:
            ds_doi = elements[1]
            depositor = Depositor(
                self.get_prefix,
                self.username,
                self.password,
                use_test_server=self._test_mode,
            )

            # Temporary solution until "register_doi" method is fixed by the library.
            endpoint = depositor.get_endpoint("deposit")
            files = {"mdFile": ("%s.xml" % ds_doi, xml_dict)}

            params = {
                "operation": "doMDUpload",
                "login_id": self.username,
                "login_passwd": self.password,
            }

            request = depositor.do_http_request(
                "post",
                endpoint,
                data=params,
                files=files,
                custom_header=depositor.custom_header,
                timeout=1000,
            )

            if request.status_code == 200:
                resp_text = request.text

                if "Not Accessible" in resp_text:
                    error_msg = 'There is an issue with credentials,' \
                        ' please re-check them and try again.'
                elif "<title>FAILURE</title>" in resp_text:
                    error_msg = 'Response returend with a failure.'
            else:
                error_msg = (
                    f'Request was returned with a {request.status_code} status code.'
                )

        if error_msg:
            log.warning(error_msg)
        else:
            DOIQuery.update_doi(doi, published=dt.now())

        return error_msg

    def mint_doi(self, doi, package_id):
        # Crossref doesn't have this step. Passing.
        pass

    def check_for_update(self, doi, xml_dict):
        # Will update each Dataset update
        return False


def get_client():
    platform = get_doi_platform()
    clients = {
        "datacite": DataciteClient,
        "crossref": CrossrefClient,
    }
    return clients[platform]()

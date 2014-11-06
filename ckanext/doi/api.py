#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

import os
import abc
import requests
from pylons import config
from xmltodict import unparse

ENDPOINT = 'https://test.datacite.org/mds'
TEST_ENDPOINT = 'https://test.datacite.org/mds'
TEST_PREFIX = '10.5072'


class DataCiteAPI(object):

    @abc.abstractproperty
    def path(self):
        return None

    def _call(self, **kwargs):

        try:
            method = kwargs.pop('method')
        except KeyError:
            method = 'get'

        test_mode = config.get("ckanext.doi.test_mode")
        test_mode = True
        account_name = 'BL.NHM'
        account_password = '842877dm'

        # If we're in test mode, use test endpoint
        endpoint = os.path.join(TEST_ENDPOINT if test_mode else ENDPOINT, self.path)

        # Add authorisation to request
        kwargs['auth'] =  (account_name, account_password)

        # Perform the request
        r = getattr(requests, method)(endpoint, **kwargs)

        print r

        # Raise exception if we have an error
        r.raise_for_status()

        # Return the test result
        return r.content


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
        self.path = os.path.join(self.path, doi)
        return self._call()

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

        # Optional metadata properties
        subject = kwargs.get('subject')
        contributor = kwargs.get('contributor')
        description = kwargs.get('description')
        size = kwargs.get('size')
        format = kwargs.get('format')
        version = kwargs.get('version')
        rights = kwargs.get('rights')

        # Optional metadata properties, with defaults
        resource_type = kwargs.get('resource_type', 'Dataset')
        language = kwargs.get('language', 'eng')

        # Create basic metadata with mandatory metadata properties
        metadata = {
            'resource': {
                '@xmlns': 'http://datacite.org/schema/kernel-3',
                '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                '@xsi:schemaLocation': 'http://datacite.org/schema/kernel-3 http://schema.datacite.org/meta/kernel-3/metadata.xsd',
                'identifier': {'@identifierType': 'DOI', '#text': identifier},
                'titles': {
                    'title': {'#text': title}
                },
                'creators': {
                    'creator': [{'creatorName': c} for c in _ensure_list(creator)],
                },
                'publisher': publisher,
                'publicationYear': publisher_year,
            }
        }

        # Add subject (if it exists)
        if subject:
            metadata['resource']['subjects'] = {
                'subject': [c for c in _ensure_list(subject)]
            }

        # Add contributors (if it exists)
        if contributor:
            metadata['resource']['contributors'] = {
                'contributor': [{'contributorName': c} for c in _ensure_list(contributor)]
            }

        if description:
            metadata['resource']['descriptions']['description'] = {
                '@descriptionType': 'Abstract',
                '#text': description
            }

        if size:
            metadata['resource']['sizes'] = {
                'size': size
            }

        if format:
            metadata['resource']['formats'] = {
                'format': format
            }

        if version:
            metadata['resource']['version'] = version

        if rights:
            metadata['resource']['rights'] = rights

        if resource_type:
            metadata['resource']['resourceType'] = {
                '@resourceTypeGeneral': resource_type,
                '#text': resource_type
            }

        if language:
            metadata['resource']['language'] = language

        return unparse(metadata, pretty=True, full_document=False)

    def upsert(self, identifier, title, creator, publisher, publisher_year, **kwargs):
        """
        URI: https://test.datacite.org/mds/metadata
        This request stores new version of metadata. The request body must contain valid XML.
        @param metadata_dict: dict to convert to xml
        @return: URL of the newly stored metadata
        """
        xml = self.metadata_to_xml(identifier, title, creator, publisher, publisher_year, **kwargs)

        # print xml
        #
        # xml = """
        #     <resource xmlns="http://datacite.org/schema/kernel-3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://datacite.org/schema/kernel-3 http://schema.datacite.org/meta/kernel-3/metadata.xsd">
        #     <creators>
        #     <creator>
        #     <creatorName>Fosmire, Michael</creatorName>
        #     </creator>
        #     <creator>
        #     <creatorName>Wertz, Ruth</creatorName>
        #     </creator>
        #     <creator>
        #     <creatorName>Purzer, Senay</creatorName>
        #     </creator>
        #     </creators>
        #     <titles>
        #     <title>Critical Engineering Literacy Test (CELT)</title>
        #     </titles>
        #     <publisher>Purdue University Research Repository (PURR)</publisher>
        #     <publicationYear>2013</publicationYear>
        #     <subjects>
        #     <subject>Assessment</subject>
        #     <subject>Information Literacy</subject>
        #     <subject>Engineering</subject>
        #     <subject>Undergraduate Students</subject>
        #     <subject>CELT</subject>
        #     <subject>Purdue University</subject>
        #     </subjects>
        #     <language>eng</language>
        #     <resourceType resourceTypeGeneral="Dataset">Dataset</resourceType>
        #     <version>1</version>
        #     <descriptions>
        #     <description descriptionType="Abstract">
        #     We developed an instrument, Critical Engineering Literacy Test (CELT), which is a multiple choice instrument designed to measure undergraduate students’ scientific and information literacy skills. It requires students to first read a technical memo and, based on the memo’s arguments, answer eight multiple choice and six open-ended response questions. We collected data from 143 first-year engineering students and conducted an item analysis. The KR-20 reliability of the instrument was .39. Item difficulties ranged between .17 to .83. The results indicate low reliability index but acceptable levels of item difficulties and item discrimination indices. Students were most challenged when answering items measuring scientific and mathematical literacy (i.e., identifying incorrect information).
        #     </description>
        #     </descriptions>
        #     <identifier identifierType="DOI">10.5072/D3P26Q35R-Test3</identifier>
        #     </resource>
        #
        # """

        print xml

        return self._call(method='post', data=xml, headers={'Content-Type': 'application/xml'})

    def delete(self, doi):
        """
        URI: https://test.datacite.org/mds/metadata/{doi} where {doi} is a specific DOI.
        This request marks a dataset as 'inactive'.
        @param doi: DOI
        @return: Response code
        """
        self.path = os.path.join(self.path, doi)
        return self._call(method='delete')


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
        self.path = os.path.join(self.path, doi)
        return self._call(doi)

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
            params={'doi': doi, 'url': url},
            method='post'
        )

class MediaDataCiteAPI(DataCiteAPI):
    """
    Calls to DataCite Metadata API
    """
    pass





if __name__ == "__main__":

    api = MetadataDataCiteAPI()
    print api.upsert('10.5072/EXAMPLE/EG5', 'Example title', ['Ben Scott', 'Lovermore'], 'Natural History Museum', 2014, contributor=['one', 'two'], subject=['one', 'two'])

    # print doi
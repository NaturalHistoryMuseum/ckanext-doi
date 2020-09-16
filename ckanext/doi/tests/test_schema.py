#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import ckanext.doi.api as doi_api
import ckanext.doi.lib as doi_lib
import mock
import requests
from ckantest.factories import DataConstants
from ckantest.models import TestBase
from lxml import etree


class Resolver(etree.Resolver):
    def resolve(self, url, pubid, context):
        r = requests.get(url)
        return self.resolve_string(r.content, context)


class TestSchema(TestBase):
    plugins = [u'doi']
    base_url = u'https://schema.datacite.org/meta/kernel-3/'

    @classmethod
    def setup_class(cls):
        super(TestSchema, cls).setup_class()
        r = requests.get(cls.base_url + 'metadata.xsd')
        parser = etree.XMLParser(no_network=False)
        parser.resolvers.add(Resolver())
        xml_etree = etree.fromstring(r.content,
                                     base_url=cls.base_url,
                                     parser=parser)
        cls.schema = etree.XMLSchema(xml_etree)
        with mock.patch('ckan.lib.helpers.session', cls._session):
            cls.package_dict = cls.data_factory().package(author=DataConstants.authors_short,
                                                          activate=False)

    def test_validate_schema(self):
        doi = doi_lib.get_or_create_doi(self.package_dict[u'id'])
        metadata_dict = doi_lib.build_metadata(self.package_dict, doi)
        api = doi_api.MetadataDataCiteAPI()
        xml_string = api.metadata_to_xml(**metadata_dict)
        xml_tree = etree.fromstring(xml_string)
        self.schema.assertValid(xml_tree)

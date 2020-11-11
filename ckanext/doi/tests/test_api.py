#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import time

import nose
from ckanext.doi.lib.api import DataciteClient
from ckantest.models import TestBase
from datacite.errors import DataCiteError

import constants


class TestAPI(TestBase):
    plugins = [u'doi']
    persist = {
        u'ckanext.doi.debug': True
    }

    def test_generate_new_doi(self):
        api = DataciteClient()
        doi = api.generate_doi()
        nose.tools.assert_is_instance(doi, (str, unicode))

    def test_mint_new_doi(self):
        api = DataciteClient()
        doi = api.generate_doi()
        pkg_id = u'abcd1234'
        with nose.tools.assert_raises(DataCiteError):
            api.mint_doi(doi, pkg_id)
        api.set_metadata(doi, constants.XML_DICT)
        api.mint_doi(doi, pkg_id)
        time.sleep(10)  # give datacite time to update
        datacite_url = api.client.doi_get(doi)
        nose.tools.assert_is_not_none(datacite_url)

    def test_datacite_authentication(self):
        api = DataciteClient()
        nose.tools.assert_is_not_none(api.client)

#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import mock
import nose
from ckantest.factories.data import DataConstants
from ckantest.helpers.mocking import Response
from ckantest.models import TestBase
from ckanext.doi.lib.api import DataciteClient


class TestAPI(TestBase):

    def test_generate_new_doi(self):
        api = DataciteClient()
        doi = api.generate_doi()
        nose.tools.assert_is_instance(doi, str)

    def test_mint_new_doi(self):
        pass

    def test_update_existing_doi(self):
        pass

    def test_datacite_authentication(self):
        api = DataciteClient()
        nose.tools.assert_is_not_none(api.client)

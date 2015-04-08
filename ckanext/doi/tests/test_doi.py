import paste.fixture
import pylons.config as config
from logging import getLogger

import ckan.model as model
import ckan.tests as tests
import ckan.plugins as plugins
import ckan.lib.helpers as h
import ckanext.pdfview.plugin as plugin
import ckan.lib.create_test_data as create_test_data
import ckan.config.middleware as middleware
from nose.tools import assert_equal, assert_true, assert_false, assert_in, assert_raises, assert_is_not_none

log = getLogger(__name__)

class TestDOI(tests.WsgiAppCase):
    """
    Test creating DOIs

    nosetests --ckan --with-pylons=test-core.ini ckanext.doi

    """

    def test_doi_config(self):

        account_name = config.get("ckanext.doi.account_name")
        account_password = config.get("ckanext.doi.account_password")

        assert_is_not_none(account_name)
        assert_is_not_none(account_password)
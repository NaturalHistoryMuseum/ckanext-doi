
#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from pylons import config
from paste.deploy.converters import asbool

TEST_PREFIX = u'10.5072'

ENDPOINT = u'https://mds.datacite.org'
TEST_ENDPOINT = u'https://mds.test.datacite.org'


def get_test_mode():
    '''Get test mode as boolean'''
    return asbool(config.get(u'ckanext.doi.test_mode', True))


def get_prefix():
    '''Get the prefix to use for DOIs


    :returns: test prefix if we're in test mode, otherwise config prefix setting

    '''

    return TEST_PREFIX if get_test_mode() else config.get(u'ckanext.doi.prefix')


def get_endpoint():

    '''Get the DataCite endpoint


    :returns: test endpoint if we're in test mode

    '''
    return TEST_ENDPOINT if get_test_mode() else ENDPOINT

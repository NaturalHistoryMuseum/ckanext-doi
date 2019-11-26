# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from paste.deploy.converters import asbool

from ckan.plugins import toolkit

TEST_PREFIX = u'10.5072'

ENDPOINT = u'https://mds.datacite.org'
TEST_ENDPOINT = u'https://mds.test.datacite.org'


def get_test_mode():
    '''Get test mode as boolean'''
    return asbool(toolkit.config.get(u'ckanext.doi.test_mode', True))


def get_prefix():
    """
    Get the prefix to use for DOIs
    @return: config prefix setting
    """
    prefix = toolkit.config.get("ckanext.doi.prefix")

    if prefix == None:
      raise TypeError('You must set the ckanext.doi.prefix config value')

    if prefix == TEST_PREFIX:
      raise ValueError('The test prefix ' + TEST_PREFIX + ' has been retired, use a prefix defined in your datacite test account')

    return prefix


def get_endpoint():
    '''Get the DataCite endpoint


    :returns: test endpoint if we're in test mode

    '''
    return TEST_ENDPOINT if get_test_mode() else ENDPOINT

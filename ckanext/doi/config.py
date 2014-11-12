#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

from pylons import config

TEST_PREFIX = '10.5072'

ENDPOINT = 'https://test.datacite.org/mds'
TEST_ENDPOINT = 'https://test.datacite.org/mds'


def get_prefix():
    """
    Get the prefix to use for DOIs
    @return: test prefix if we're in test mode, otherwise config prefix setting
    """

    test_mode = config.get("ckanext.doi.test_mode")
    return TEST_PREFIX if test_mode else config.get("ckanext.doi.prefix")


def get_endpoint():

    """
    Get the DataCite endpoint
    @return: test endpoint if we're in test mode
    """

    test_mode = config.get("ckanext.doi.test_mode")
    return TEST_ENDPOINT if test_mode else ENDPOINT
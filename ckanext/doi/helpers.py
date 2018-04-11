# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from datetime import datetime

import dateutil.parser as parser

from ckan.plugins import toolkit


def package_get_year(pkg_dict):
    '''Helper function to return the package year published

    :param pkg_dict: return:

    '''
    if not isinstance(pkg_dict[u'metadata_created'], datetime):
        pkg_dict[u'metadata_created'] = parser.parse(pkg_dict[u'metadata_created'])

    return pkg_dict[u'metadata_created'].year


def get_site_title():
    '''Helper function to return the config site title, if it exists


    :returns: str site title

    '''
    return toolkit.config.get(u'ckanext.doi.site_title')


def now():
    ''' '''
    return datetime.now()

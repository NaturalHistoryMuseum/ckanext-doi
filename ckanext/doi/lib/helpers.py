# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from datetime import datetime

import dateutil.parser as parser
from ckan.plugins import toolkit


def package_get_year(pkg_dict):
    """
    Helper function to return the package year published.

    :param pkg_dict: return:
    """
    if not isinstance(pkg_dict['metadata_created'], datetime):
        pkg_dict['metadata_created'] = parser.parse(pkg_dict['metadata_created'])

    return pkg_dict['metadata_created'].year


def get_site_title():
    """
    Helper function to return the config site title, if it exists.

    :returns: str site title
    """
    return toolkit.config.get('ckanext.doi.site_title')


def get_site_url():
    """
    Get the site URL.

    Try and use ckanext.doi.site_url but if that's not set use ckan.site_url.
    """
    site_url = toolkit.config.get(
        'ckanext.doi.site_url', toolkit.config.get('ckan.site_url', '')
    )
    return site_url.rstrip('/')


def date_or_none(date_object_or_string):
    """
    Try and convert the given object into a datetime; if not possible, return None.

    :param date_object_or_string: a datetime or date string
    :return: datetime or None
    """
    if isinstance(date_object_or_string, datetime):
        return date_object_or_string
    elif isinstance(date_object_or_string, str):
        return parser.parse(date_object_or_string)
    else:
        return None

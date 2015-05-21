
#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

from pylons import config
from datetime import datetime
import dateutil.parser as parser

def package_get_year(pkg_dict):
    """
    Helper function to return the package year published
    @param pkg_dict:
    @return:
    """
    if not isinstance(pkg_dict['metadata_created'], datetime):
        pkg_dict['metadata_created'] = parser.parse(pkg_dict['metadata_created'])

    return pkg_dict['metadata_created'].year

def get_site_title():
    """
    Helper function to return the config site title, if it exists
    @return: str site title
    """
    return config.get("ckanext.doi.site_title")

def now():
    return datetime.now()


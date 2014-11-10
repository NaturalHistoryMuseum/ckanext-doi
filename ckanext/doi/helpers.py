
#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

import datetime
import dateutil.parser as parser

def package_get_doi(pkg_dict):
    """
    Retrieve the DOI from the package extras dict
    @param pkg_dict:
    @return:
    """
     # Try and extract the DOI from the extras values
    if 'extras' in pkg_dict:
        for extra in pkg_dict['extras']:
            if extra['key'] == u'doi':
                return extra['value']

    return None

def package_get_year(pkg_dict):
    """
    Helper function to retrieve year from created date
    @param pkg_dict:
    @return:
    """
    return parser.parse(pkg_dict['metadata_created']).year

def now():
    return datetime.datetime.now()

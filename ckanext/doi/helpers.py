
#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

from datetime import datetime, timedelta
import dateutil.parser as parser
from ckanext.doi.lib import get_doi

# The number of days a mandatory field is editable for
DAYS_EDITABLE = 10


def mandatory_field_is_editable(**kwargs):
    """
    Are mandatory fields still editable?
    Mandatory DOI fields should not be editable
    DataCite recommend locking fields down after a couple of days
    This checks time past against metadata creation date
    @return: Boolean. True if fields are still editable
    """

    package_id = kwargs.get('package_id', None)

    if package_id:
        doi = get_doi(package_id)
    else:
        doi = kwargs.get('doi', None)

    if doi:
        return doi.created > (datetime.now() - timedelta(hours=DAYS_EDITABLE))
    else:
        return True


def package_get_year(pkg_dict):
    """
    Helper function to return the package year published
    @param pkg_dict:
    @return:
    """

    if not isinstance(pkg_dict['metadata_created'], datetime):
        pkg_dict['metadata_created'] = parser.parse(pkg_dict['metadata_created'])

    return pkg_dict['metadata_created'].year


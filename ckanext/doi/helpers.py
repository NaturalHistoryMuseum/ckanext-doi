
#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""

from ckanext.doi.lib import get_metadata_created_datetime
from datetime import datetime, timedelta

# The number of days a mandatory field is editable for
DAYS_EDITABLE = 1

def mandatory_field_is_editable(pkg_dict):
    """
    Are mandatory fields still editable?
    Mandatory DOI fields should not be editable
    DataCite recommend locking fields down after a couple of days
    This checks time past against metadata creation date
    @return: Boolean. True if fields are still editable
    """

    try:
        if pkg_dict['doi']:
            return get_metadata_created_datetime(pkg_dict) > (datetime.now() - timedelta(minutes=DAYS_EDITABLE))
    except KeyError:
        # If metadata_created doesn't exist, this is a new dataset
        pass

    return True

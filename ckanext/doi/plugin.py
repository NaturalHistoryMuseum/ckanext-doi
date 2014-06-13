"""
CKAN Contact Extension
"""
import os
from logging import getLogger
import ckan.plugins as p
from ckanext.contact.auth import send_contact
from dateutil import parser

log = getLogger(__name__)

class DOIPlugin(p.SingletonPlugin):
    """
    CKAN DOI Extension
    """
    p.implements(p.IConfigurer)
    p.implements(p.IPackageController, inherit=True)

    ## IConfigurer
    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'theme/templates')

    def after_create(self, context, pkg_dict):
        # TODO: Retrieve DOI for datacite API
        pass

    ## IConfigurer
    def after_show(self, context, pkg_dict):

        # Just set up a dummy DOI

        # Parse date
        date = parser.parse(pkg_dict['metadata_created'])

        pkg_dict['doi'] = '{author} ({year}): {title} data.nhm.ac.uk. http://dx.doi.org/00.0000/10000'.format(
            author=pkg_dict.get('author'),
            year=date.year,
            title=pkg_dict.get('title'),
        )

        return pkg_dict
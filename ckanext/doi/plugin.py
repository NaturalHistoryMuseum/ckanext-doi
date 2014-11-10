"""
CKAN Contact Extension
"""
import os
from logging import getLogger
import ckan.plugins as p
from ckan.lib.base import config
from ckanext.doi.lib import get_prefix, upsert_doi
from ckanext.doi.api import DOIDataCiteAPI
from requests.exceptions import HTTPError
from ckanext.doi.helpers import package_get_doi, package_get_year, now
import random
import ckan.logic as logic
from ckan.common import c
import ckan.model as model

get_action = logic.get_action

log = getLogger(__name__)

class DOIPlugin(p.SingletonPlugin):
    """
    CKAN DOI Extension
    """

    p.implements(p.IConfigurer)
    p.implements(p.IPackageController, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)

    ## IConfigurer
    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'theme/templates')

    ## IPackageController
    def edit(self, entity):
        """
        Implements IPackageController.edit
        Alter the package entity prior to saving it to the DB
        If we do not have a DOI, create one and assign to entity extras
        @param entity: package
        @return: None
        """

        # We do not want to assign a DOI if this is a draft or private
        if not entity.state.startswith('draft'):

            # Load the package
            context = {'model': model, 'session': model.Session, 'api_version': 3, 'for_edit': True, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
            pkg_dict = get_action('package_show')(context, {'id': entity.name})

            doi = package_get_doi(pkg_dict)

            if not doi:
                # If we do not have a DOI, create one
                log.warning('No DOI: Minting DOI for dataset %s', entity.title)
                entity.extras['doi'] = self._mint_doi(pkg_dict)
            else:
                # If we do have a DOI, assign to extras so it persists
                entity.extras['doi'] = doi

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'package_get_doi': package_get_doi,
            'package_get_year': package_get_year,
            'now': now
        }

    def _mint_doi(self, pkg_dict):
        """
        Mint a new DOI for a dataset package
        @param pkg_dict:
        @return: identifier on success. None on failure
        """

       # If private we do not want to create a DOI
        if not pkg_dict['private']:

            # Dataset name is used in the path, so is unique
            # We can use this at point of creation as it's more descriptive than ID
            identifier = self.get_unique_identifier()

            # The ID of a dataset never changes, so use that for the URL
            site_url = config.get('ckan.site_url', '').rstrip('/')

            # TEMP: Override development
            site_url = 'http://data.nhm.ac.uk'

            url = os.path.join(site_url, 'dataset', pkg_dict['id'])
            year_published = package_get_year(pkg_dict)

            optional_metadata = {
                # Derive format from the attached resources
                'format': ', '.join([res['format'] for res in pkg_dict['resources'] if res['format']]),
                'description': pkg_dict['notes']
            }

            if 'tags' in pkg_dict:
                optional_metadata['subject'] = [tag['display_name'] for tag in pkg_dict['tags']]


            if pkg_dict['license_id'] != 'notspecified':
                optional_metadata['rights'] = pkg_dict['license_title']

            if pkg_dict['dataset_type']:
                optional_metadata['resource_type'] = pkg_dict['dataset_type'][0]

            if upsert_doi(identifier, url, pkg_dict['title'], pkg_dict['author'], config.get("ckanext.doi.publisher"), year_published, **optional_metadata):
                return identifier

    @staticmethod
    def get_unique_identifier():
        """
        Loop generating a unique identifier
        Checks if it already exists - if it doesn't we can use it
        If it does already exist, generate another one
        We check against the datacite repository, rather than our own internal database
        As multiple services can be minting DOIs
        @return:
        """

        api = DOIDataCiteAPI()

        while True:
            identifier = os.path.join(get_prefix(), '{0:07}'.format(random.randint(1, 100000)))
            try:
                api.get(identifier)
            except HTTPError:
                return identifier
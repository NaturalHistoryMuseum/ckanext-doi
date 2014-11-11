"""
CKAN Contact Extension
"""
import os
import datetime
from logging import getLogger
import ckan.plugins as p
from ckan.lib.base import config
from itertools import groupby
from ckanext.doi.lib import mint_doi, get_unique_identifier, get_metadata_created_datetime
from ckanext.doi.api import MetadataDataCiteAPI, DOIDataCiteAPI
import ckanext.doi.logic.schema as doi_schema
from ckanext.doi.helpers import mandatory_field_is_editable
import ckan.logic as logic
import ckan.lib.helpers as h
from ckan.common import c, _
import ckan.model as model
from ckan.logic.schema import (
    default_create_package_schema,
    default_update_package_schema,
    default_show_package_schema
    )

get_action = logic.get_action

log = getLogger(__name__)

class DOIPlugin(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):
    """
    CKAN DOI Extension
    """

    p.implements(p.IConfigurer)
    p.implements(p.IDatasetForm, inherit=True)
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

        if not (entity.state.startswith('draft') or entity.private):

            try:
                doi = entity.extras['doi']
            except KeyError:
                doi = None

            # If we don't have a DOI, create one
            if not doi:

                # FIXME: If an entity is being updated from private to public, and tags changed at the same time, this will not update the tags
                pkg_dict = entity.as_dict()
                # Create DOI and assign to extras
                entity.extras['doi'] = self.create_doi(pkg_dict)
                h.flash_success(_('DOI %s has been created.' % entity.extras['doi']))

    def after_update(self, context, pkg_dict):
        """
        After a dataset is updated
        @param context:
        @param pkg_dict:
        @return:
        """

        # State is only set on newly created dataset
        try:
            pkg_dict['state']
            is_new = True
        except KeyError:
            is_new = False

        # If we're editing a dataset, update the metadata
        # This is called after creating a dataset, so make sure dataset isn't new
        if not is_new and pkg_dict['doi']:
            # Package dict at this point is missing date created - add them back in
            pkg_dict['metadata_created'] = context['package'].metadata_created
            pkg_dict['resources'] = [r.as_dict() for r in context['package'].resources]
            self.update_doi(pkg_dict)

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'mandatory_field_is_editable': mandatory_field_is_editable,
            'now': datetime.datetime.now
        }

    ## IDatasetForm
    def package_types(self):
        return []

    def is_fallback(self):
        return True

    def create_package_schema(self):
        return doi_schema.create_package_schema()

    def update_package_schema(self):
        return doi_schema.update_package_schema()

    def show_package_schema(self):
        return doi_schema.show_package_schema()

    def update_doi(self, pkg_dict):

        year_published = get_metadata_created_datetime(pkg_dict).year
        optional_metadata = self._get_optional_metadata(pkg_dict)
        identifier = pkg_dict['doi']

        metadata_api = MetadataDataCiteAPI()
        metadata_api.upsert(identifier, pkg_dict['title'], pkg_dict['author'], config.get("ckanext.doi.publisher"), year_published, **optional_metadata)

    @staticmethod
    def _get_optional_metadata(pkg_dict):

        optional_metadata = {
            # Derive format from the attached resources
            'format': ', '.join([res['format'] for res in pkg_dict['resources'] if res['format']]),
            'description': pkg_dict['notes']
        }

        if 'tags' in pkg_dict:
            optional_metadata['subject'] = list(set([tag['name'] if isinstance(tag, dict) else tag for tag in pkg_dict['tags']]))

        if pkg_dict['license_id'] != 'notspecified':

            licenses = model.Package.get_license_options()

            for license_title, license_id in licenses:
                if license_id == pkg_dict['license_id']:
                    optional_metadata['rights'] = license_title
                    break

        if 'dataset_type' in pkg_dict:
            optional_metadata['resource_type'] = pkg_dict['dataset_type'][0]

        if 'version' in pkg_dict:
            optional_metadata['version'] = pkg_dict['version']

        return optional_metadata

    def create_doi(self, pkg_dict):
        """
        Mint a new DOI for a dataset package
        @param pkg_dict:
        @return: identifier on success. None on failure
        """

        # Dataset name is used in the path, so is unique
        # We can use this at point of creation as it's more descriptive than ID
        identifier = get_unique_identifier()

        # The ID of a dataset never changes, so use that for the URL
        site_url = config.get('ckan.site_url', '').rstrip('/')

        # TEMP: Override development
        site_url = 'http://data.nhm.ac.uk'

        url = os.path.join(site_url, 'dataset', pkg_dict['id'])

        year_published = get_metadata_created_datetime(pkg_dict).year

        optional_metadata = self._get_optional_metadata(pkg_dict)

        if mint_doi(identifier, url, pkg_dict['title'], pkg_dict['author'], config.get("ckanext.doi.publisher"), year_published, **optional_metadata):
            return identifier
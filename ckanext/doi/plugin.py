"""
CKAN Contact Extension
"""
import os
import datetime
import itertools
from logging import getLogger
import ckan.plugins as p
import ckan.logic as logic
import ckan.model as model
from ckan.lib.helpers import json
from pylons import config
from ckan.common import c
from ckanext.doi import model as doi_model
from ckanext.doi.lib import get_doi, create_doi, update_doi
from ckanext.doi.helpers import package_get_year, mandatory_field_is_editable
from ckanext.doi.config import get_site_url

get_action = logic.get_action

log = getLogger(__name__)


class DOIPlugin(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):
    """
    CKAN DOI Extension
    """

    p.implements(p.IConfigurable)
    p.implements(p.IConfigurer)
    p.implements(p.IPackageController, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)

    ## IConfigurable
    def configure(self, config):
        """
        Called at the end of CKAN setup.

        Create DOI table
        """
        doi_model.doi_table.create(checkfirst=True)

    ## IPackageController
    def before_index(self, pkg_dict):

        package_id = pkg_dict.get('id')

        if pkg_dict['state'] == 'active' and not pkg_dict['private']:

            doi = get_doi(pkg_dict['id'])

            metadata = {
                'package_id': package_id,
                'title': pkg_dict['title'],
                'creator': pkg_dict['author'],
                'publisher': config.get("ckanext.doi.publisher"),
                'publisher_year': package_get_year(pkg_dict),
                # Derive format from the attached resources
                'format': ', '.join([f for f in pkg_dict['res_format']]),
                'description': pkg_dict['notes'],
            }

            if 'tags' in pkg_dict:
                metadata['subject'] = list(set([tag['name'] if isinstance(tag, dict) else tag for tag in pkg_dict['tags']]))

            if pkg_dict['license_id'] != 'notspecified':

                licenses = model.Package.get_license_options()

                for license_title, license_id in licenses:
                    if license_id == pkg_dict['license_id']:
                        metadata['rights'] = license_title
                        break

            if 'dataset_type' in pkg_dict:
                metadata['resource_type'] = pkg_dict['dataset_type'][0]

            if 'version' in pkg_dict:
                metadata['version'] = pkg_dict['version']

            # Try and get spatial
            if 'extras_spatial' in pkg_dict and pkg_dict['extras_spatial']:
                geometry = json.loads(pkg_dict['extras_spatial'])

                if geometry['type'] == 'Point':
                    metadata['geo_point'] = '%s %s' % tuple(geometry['coordinates'])
                elif geometry['type'] == 'Polygon':
                    # DataCite expects box coordinates, not geo pairs
                    # So dedupe to get the box and join into a string
                    metadata['geo_box'] = ' '.join([str(coord) for coord in list(set(itertools.chain.from_iterable(geometry['coordinates'][0])))])

            if doi:
                update_doi(**metadata)
            else:
                create_doi(**metadata)

        return pkg_dict

    ## IPackageController
    def edit(self, package):
        """
        Implementation of IPackageController.edit()

        DataCite core metadata fields should not be updated after a certain time
        These are locked in the theme layer, but just perform a sanity check here

        We also validate IDatasetForm interface, but then we'll run into
        IDatasetForm.package_types() and IDatasetForm.is_fallback() collisions as
        there can be only one plugin per package type. But there are schema alter functions
        available in ckanext.doi.schema

        """

        mandatory_fields = ['title', 'author']

        # Make sure our mandatory fields are populated
        for field in mandatory_fields:
            if not getattr(package, field):
                log.critical('DataCite field %s is required', field)

        doi = get_doi(package.id)

        # If we have a DOI for this dataset, check
        if doi:
            context = {'model': model, 'session': model.Session, 'api_version': 3, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
            pkg_dict = get_action('package_show')(context, {'id': package.id})

            if not mandatory_field_is_editable(doi=doi):
                for field in mandatory_fields:
                    if getattr(package, field) != pkg_dict.get(field):
                        log.critical('Mandatory DataCite field %s is no longer editable', field)

    ## IPackageController
    def after_show(self, context, pkg_dict):
        # Load the DOI ready to display

        doi = get_doi(pkg_dict['id'])

        mandatory_field_is_editable(doi=doi)

        if doi:
            pkg_dict['doi'] = doi.identifier
            pkg_dict['domain'] = get_site_url().replace('http://', '')

    ## IConfigurer
    def update_config(self, config):
        # Add our templates
        p.toolkit.add_template_directory(config, 'theme/templates')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'mandatory_field_is_editable': mandatory_field_is_editable,
            'package_get_year': package_get_year,
            'now': datetime.datetime.now
        }
"""
CKAN DOI Plugin
"""
import datetime
import itertools
from logging import getLogger
import ckan.plugins as p
import ckan.logic as logic
import ckan.model as model
from ckan.lib import helpers as h
from ckan.common import c
from pylons import config
from ckanext.doi.model import doi as doi_model
from ckanext.doi.lib import get_doi, publish_doi, update_doi, create_unique_identifier
from ckanext.doi.helpers import package_get_year
from ckanext.doi.config import get_site_url
from ckanext.doi.interfaces import IDoi
from ckanext.doi.exc import DOIMetadataException

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

    ## IConfigurer
    def update_config(self, config):
        # Add templates
        p.toolkit.add_template_directory(config, 'theme/templates')

    ## IPackageController
    def after_create(self, context, pkg_dict):
        """
        A new dataset has been created, so we need to create a new DOI
        NB: This is called after creation of a dataset, and before resources have been added so state = draft
        @param context:
        @param pkg_dict:
        @return:
        """
        create_unique_identifier(pkg_dict['id'])

    ## IPackageController
    def after_update(self, context, pkg_dict):
        """
        Dataset has been created / updated
        Check status of the dataset to determine if we should publish DOI to datacite network

        @param pkg_dict:
        @return: pkg_dict
        """

        # Is this active and public? If so we need to make sure we have an active DOI
        if pkg_dict.get('state', 'active') == 'active' and not pkg_dict.get('private', False):

            package_id = pkg_dict['id']

            # Load the original package, so we can determine if user has changed any fields
            orig_pkg_dict = get_action('package_show')(context, {'id': package_id})

            # Metadata created isn't populated in pkg_dict - so copy from the original
            pkg_dict['metadata_created'] = orig_pkg_dict['metadata_created']

            # Load the local DOI
            doi = get_doi(package_id)

            # Build the metadata dict to pass to DataCite service
            metadata_dict = self.build_metadata(pkg_dict, doi)

            # Perform some basic checks against the data - we require at the very least
            # title and author fields - they're mandatory in the DataCite Schema
            # This will only be an issue if another plugin has removed a mandatory field
            self.validate_metadata(metadata_dict)

            # Is this an existing DOI? Update it
            if doi.published:

                # Before updating, check if any of the metadata has been changed - otherwise
                # We end up sending loads of revisions to DataCite for minor edits
                # Load the current version
                orig_metadata_dict = self.build_metadata(orig_pkg_dict, doi)

                # Check if the two dictionaries are the same
                if cmp(orig_metadata_dict, metadata_dict) != 0:
                    # Not the same, so we want to update the metadata
                    update_doi(package_id, **metadata_dict)
                    h.flash_success('DataCite DOI metadata updated')

                # TODO: If editing a dataset older than 5 days, create DOI revision

            # New DOI - publish to datacite
            else:
                h.flash_success('DataCite DOI created')
                publish_doi(package_id, **metadata_dict)

        return pkg_dict

    @staticmethod
    def build_metadata(pkg_dict, doi):

        # Build the datacite metadata - all of these are core CKAN fields which should
        # be the same across all CKAN sites
        # This builds a dictionary keyed by the datacite metadata xml schema
        metadata_dict = {
            'identifier': doi.identifier,
            'title': pkg_dict['title'],
            'creator': pkg_dict['author'],
            'publisher': config.get("ckanext.doi.publisher"),
            'publisher_year': package_get_year(pkg_dict),
            'description': pkg_dict['notes'],
        }

        # Convert the format to comma delimited
        try:
            # Filter out empty strings in the array (which is what we have if nothing is entered)
            # We want to make sure all None values are removed so we can compare
            # the dict here, with one loaded via action.package_show which doesn't
            # return empty values
            pkg_dict['res_format'] = filter(None, pkg_dict['res_format'])
            if pkg_dict['res_format']:
                metadata_dict['format'] = ', '.join([f for f in pkg_dict['res_format']])
        except KeyError:
            pass

        # If we have tag_string use that to build subject
        if 'tag_string' in pkg_dict:
            metadata_dict['subject'] = pkg_dict.get('tag_string', '').split(',').sort()
        elif 'tags' in pkg_dict:
            # Otherwise use the tags list itself
            metadata_dict['subject'] = list(set([tag['name'] if isinstance(tag, dict) else tag for tag in pkg_dict['tags']])).sort()

        if pkg_dict['license_id'] != 'notspecified':

            licenses = model.Package.get_license_options()

            for license_title, license_id in licenses:
                if license_id == pkg_dict['license_id']:
                    metadata_dict['rights'] = license_title
                    break

        if pkg_dict.get('version', None):
            metadata_dict['version'] = pkg_dict['version']

        # Try and get spatial
        if 'extras_spatial' in pkg_dict and pkg_dict['extras_spatial']:
            geometry = h.json.loads(pkg_dict['extras_spatial'])

            if geometry['type'] == 'Point':
                metadata_dict['geo_point'] = '%s %s' % tuple(geometry['coordinates'])
            elif geometry['type'] == 'Polygon':
                # DataCite expects box coordinates, not geo pairs
                # So dedupe to get the box and join into a string
                metadata_dict['geo_box'] = ' '.join([str(coord) for coord in list(set(itertools.chain.from_iterable(geometry['coordinates'][0])))])

        # Allow plugins to alter the datacite DOI metadata
        # So other CKAN instances can add their own custom fields - and we can
        # Add our data custom to NHM
        for plugin in p.PluginImplementations(IDoi):
            plugin.build_metadata(pkg_dict, metadata_dict)

        return metadata_dict

    @staticmethod
    def validate_metadata(metadata_dict):
        """
        Validate the metadata - loop through mandatory fields and check they are populated
        """

        # Check we have mandatory DOI fields
        mandatory_fields = ['title', 'creator']

        # Make sure our mandatory fields are populated
        for field in mandatory_fields:
            if not metadata_dict.get(field, None):
                raise DOIMetadataException('Missing DataCite required field %s' % field)

    ## IPackageController
    def after_show(self, context, pkg_dict):

        # Load the DOI ready to display
        doi = get_doi(pkg_dict['id'])

        if doi:
            pkg_dict['doi'] = doi.identifier
            pkg_dict['doi_status'] = True if doi.published else False
            pkg_dict['domain'] = get_site_url().replace('http://', '')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'package_get_year': package_get_year,
            'now': datetime.datetime.now
        }
#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from pylons import config
from datetime import datetime
from logging import getLogger
import ckan.plugins as p
import ckan.logic as logic
from ckan.lib import helpers as h
from ckan import model
from ckanext.doi.model import doi as doi_model
from ckanext.doi.lib import get_doi, publish_doi, update_doi, create_unique_identifier, get_site_url, build_metadata, validate_metadata
from ckanext.doi.helpers import package_get_year, now, get_site_title

get_action = logic.get_action

log = getLogger(__name__)


class DOIPlugin(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):
    '''CKAN DOI Extension'''
    p.implements(p.IConfigurable)
    p.implements(p.IConfigurer)
    p.implements(p.IPackageController, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)

    ## IConfigurable
    def configure(self, config):
        '''Called at the end of CKAN setup.
        Create DOI table

        :param config: 

        '''
        if model.package_table.exists():
            doi_model.doi_table.create(checkfirst=True)

    ## IConfigurer
    def update_config(self, config):
        '''

        :param config: 

        '''
        # Add templates
        p.toolkit.add_template_directory(config, u'theme/templates')

    ## IPackageController
    def after_create(self, context, pkg_dict):
        '''A new dataset has been created, so we need to create a new DOI
        NB: This is called after creation of a dataset, and before resources have been added so state = draft

        :param context: param pkg_dict:
        :param pkg_dict: 

        '''
        create_unique_identifier(pkg_dict[u'id'])

    ## IPackageController
    def after_update(self, context, pkg_dict):
        '''Dataset has been created / updated
        Check status of the dataset to determine if we should publish DOI to datacite network

        :param pkg_dict: return: pkg_dict
        :param context: 
        :returns: pkg_dict

        '''
        # Is this active and public? If so we need to make sure we have an active DOI
        if pkg_dict.get(u'state', u'active') == u'active' and not pkg_dict.get(u'private', False):

            package_id = pkg_dict[u'id']

            # Load the original package, so we can determine if user has changed any fields
            orig_pkg_dict = get_action(u'package_show')(context, {u'id': package_id})

            # Metadata created isn't populated in pkg_dict - so copy from the original
            pkg_dict[u'metadata_created'] = orig_pkg_dict[u'metadata_created']

            # Load the local DOI
            doi = get_doi(package_id)

            # If we don't have a DOI, create one
            # This could happen if the DOI module is enabled after a dataset has been created
            if not doi:
                doi = create_unique_identifier(package_id)

            # Build the metadata dict to pass to DataCite service
            metadata_dict = build_metadata(pkg_dict, doi)

            # Perform some basic checks against the data - we require at the very least
            # title and author fields - they're mandatory in the DataCite Schema
            # This will only be an issue if another plugin has removed a mandatory field
            validate_metadata(metadata_dict)

            # Is this an existing DOI? Update it
            if doi.published:

                # Before updating, check if any of the metadata has been changed - otherwise
                # We end up sending loads of revisions to DataCite for minor edits
                # Load the current version
                orig_metadata_dict = build_metadata(orig_pkg_dict, doi)
                # Check if the two dictionaries are the same
                if cmp(orig_metadata_dict, metadata_dict) != 0:
                    # Not the same, so we want to update the metadata
                    update_doi(package_id, **metadata_dict)
                    h.flash_success(u'DataCite DOI metadata updated')

                    # TODO: If editing a dataset older than 5 days, create DOI revision

            # New DOI - publish to datacite
            else:
                h.flash_success(u'DataCite DOI created')
                publish_doi(package_id, **metadata_dict)

        return pkg_dict

    # IPackageController
    def after_show(self, context, pkg_dict):
        '''

        :param context: 
        :param pkg_dict: 

        '''
        # Load the DOI ready to display
        doi = get_doi(pkg_dict[u'id'])
        if doi:
            pkg_dict[u'doi'] = doi.identifier
            pkg_dict[u'doi_status'] = True if doi.published else False
            pkg_dict[u'domain'] = get_site_url().replace(u'http://', u'')
            pkg_dict[u'doi_date_published'] = datetime.strftime(doi.published, u'%Y-%m-%d') if doi.published else None
            pkg_dict[u'doi_publisher'] = config.get(u'ckanext.doi.publisher')

    # ITemplateHelpers
    def get_helpers(self):
        ''' '''
        return {
            u'package_get_year': package_get_year,
            u'now': now,
            u'get_site_title': get_site_title
        }

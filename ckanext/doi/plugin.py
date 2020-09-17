#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from datetime import datetime
from logging import getLogger

from ckanext.doi.helpers import get_site_title, now, package_get_year
from ckanext.doi.lib import (build_metadata, get_doi, get_or_create_doi, get_site_url, publish_doi,
                             update_doi, validate_metadata)
from ckanext.doi.model import doi as doi_model

from ckan import model
from ckan.plugins import SingletonPlugin, implements, interfaces, toolkit

log = getLogger(__name__)


class DOIPlugin(SingletonPlugin, toolkit.DefaultDatasetForm):
    '''CKAN DOI Extension'''
    implements(interfaces.IConfigurable)
    implements(interfaces.IConfigurer)
    implements(interfaces.IPackageController, inherit=True)
    implements(interfaces.ITemplateHelpers, inherit=True)

    ## IConfigurable
    def configure(self, config):
        '''Called at the end of CKAN setup. Creates DOI table.
        '''
        if model.package_table.exists():
            doi_model.doi_table.create(checkfirst=True)

    ## IConfigurer
    def update_config(self, config):
        '''Adds templates.
        '''
        toolkit.add_template_directory(config, u'theme/templates')

    ## IPackageController
    def after_create(self, context, pkg_dict):
        '''A new dataset has been created, so we need to create a new DOI.
        NB: This is called after creation of a dataset, before resources have been
        added, so state = draft.
        '''
        get_or_create_doi(pkg_dict[u'id'])

    ## IPackageController
    def after_update(self, context, pkg_dict):
        '''Dataset has been created/updated. Check status of the dataset to determine if we should
        publish DOI to datacite network.
        '''
        # Is this active and public? If so we need to make sure we have an active DOI
        if pkg_dict.get(u'state', u'active') == u'active' and not pkg_dict.get(u'private', False):
            package_id = pkg_dict[u'id']

            # remove user-defined update schemas first (if needed)
            context.pop(u'schema', None)
            # Load the original package, so we can determine if user has changed any fields FIXME
            orig_pkg_dict = toolkit.get_action(u'package_show')(context, {
                u'id': package_id
            })

            # If metadata_created isn't populated in pkg_dict, copy from the original
            if u'metadata_created' not in pkg_dict:
                pkg_dict[u'metadata_created'] = orig_pkg_dict.get(u'metadata_created', u'')

            # Load or create the local DOI (package may not have a DOI if extension was loaded
            # after package creation)
            doi = get_or_create_doi(package_id)

            # Build the metadata dict to pass to DataCite service
            metadata_dict = build_metadata(pkg_dict, doi)

            # Perform some basic checks against the data - we require at the very least
            # title and author fields - they're mandatory in the DataCite Schema
            # This will only be an issue if another plugin has removed a mandatory field
            validate_metadata(metadata_dict)

            if doi.published:
                # Before updating, check if any of the metadata has been changed - otherwise we
                # end up sending loads of revisions to DataCite for minor edits
                orig_metadata_dict = build_metadata(orig_pkg_dict, doi)
                # Check if the two dictionaries are the same
                if cmp(orig_metadata_dict, metadata_dict) != 0:
                    # Not the same, so we want to update the metadata
                    update_doi(package_id, **metadata_dict)
                    toolkit.h.flash_success(u'DataCite DOI metadata updated')

                    # TODO: If editing a dataset older than 5 days, create DOI revision
            else:
                # New DOI - publish to datacite
                publish_doi(package_id, **metadata_dict)
                toolkit.h.flash_success(u'DataCite DOI created')

        return pkg_dict

    # IPackageController
    def after_show(self, context, pkg_dict):
        '''Add the DOI details to the pkg_dict so it can be displayed.
        '''
        doi = get_doi(pkg_dict[u'id'])
        if doi:
            pkg_dict[u'doi'] = doi.identifier
            pkg_dict[u'doi_status'] = True if doi.published else False
            pkg_dict[u'domain'] = get_site_url().replace(u'http://', u'')
            pkg_dict[u'doi_date_published'] = datetime.strftime(doi.published,
                                                                u'%Y-%m-%d') if \
                doi.published else None
            pkg_dict[u'doi_publisher'] = toolkit.config.get(u'ckanext.doi.publisher')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            u'package_get_year': package_get_year,
            u'now': now,
            u'get_site_title': get_site_title
        }

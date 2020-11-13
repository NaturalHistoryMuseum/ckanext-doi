#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from datetime import datetime
from logging import getLogger

from ckan import model
from ckan.plugins import SingletonPlugin, implements, interfaces, toolkit
from ckanext.doi.lib.api import DataciteClient
from ckanext.doi.lib.helpers import get_site_title, get_site_url, package_get_year
from ckanext.doi.lib.metadata import build_metadata_dict, build_xml_dict, convert_package_update
from ckanext.doi.model import doi as doi_model
from ckanext.doi.model.crud import DOIQuery

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
        DOIQuery.read_package(pkg_dict[u'id'], create_if_none=True)

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

            # Load the original package
            orig_pkg_dict = toolkit.get_action(u'package_show')(context, {
                u'id': package_id
            })

            # If metadata_created isn't populated in pkg_dict, copy from the original
            if u'metadata_created' not in pkg_dict:
                pkg_dict[u'metadata_created'] = orig_pkg_dict.get(u'metadata_created', u'')

            # Load or create the local DOI (package may not have a DOI if extension was loaded
            # after package creation)
            doi = DOIQuery.read_package(package_id, create_if_none=True)

            converted_pkg_dict = convert_package_update(pkg_dict)
            metadata_dict = build_metadata_dict(converted_pkg_dict)
            xml_dict = build_xml_dict(metadata_dict)

            client = DataciteClient()

            if doi.published is None:
                # metadata gets created before minting
                client.set_metadata(doi.identifier, xml_dict)
                client.mint_doi(doi.identifier, package_id)
                toolkit.h.flash_success(u'DataCite DOI created')
            else:
                # Before updating, check if any of the metadata has been changed - otherwise we
                # end up sending loads of revisions to DataCite for minor edits
                orig_metadata_dict = build_metadata_dict(orig_pkg_dict)
                # Check if the two dictionaries are the same
                same = True
                for k, new_value in metadata_dict.items():
                    old_value = orig_metadata_dict.get(k)
                    if k == u'dates':
                        new_dates = {d[u'dateType']: d for d in new_value}
                        old_dates = {d[u'dateType']: d for d in old_value}
                        diff = [new_dates.get(date_type) == old_dates.get(date_type) for
                                date_type in set(new_dates.keys() + old_dates.keys()) if
                                date_type not in ['Updated', 'Issued']]
                        if not all(diff):
                            same = False
                    else:
                        try:
                            if isinstance(new_value, dict) and isinstance(old_value, dict):
                                same = cmp(new_value, old_value) != 0
                            elif isinstance(new_value, list) and isinstance(old_value, list):
                                same = sorted(new_value) == sorted(old_value)
                            else:
                                same = new_value == old_value
                        except:
                            same = False
                    if not same:
                        break
                if not same:
                    # Not the same, so we want to update the metadata
                    client.set_metadata(doi.identifier, xml_dict)
                    toolkit.h.flash_success(u'DataCite DOI metadata updated')

        return pkg_dict

    # IPackageController
    def after_show(self, context, pkg_dict):
        '''Add the DOI details to the pkg_dict so it can be displayed.
        '''
        doi = DOIQuery.read_package(pkg_dict[u'id'])
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
            u'now': datetime.now,
            u'get_site_title': get_site_title
        }

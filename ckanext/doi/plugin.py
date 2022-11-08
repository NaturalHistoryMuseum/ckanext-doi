#!/usr/bin/env python3
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from datetime import datetime
from logging import getLogger

from ckan.plugins import SingletonPlugin, implements, interfaces, toolkit

from ckanext.doi import cli
from ckanext.doi.lib.api import DataciteClient
from ckanext.doi.lib.helpers import get_site_title, get_site_url, package_get_year
from ckanext.doi.lib.metadata import build_metadata_dict, build_xml_dict
from ckanext.doi.model.crud import DOIQuery

log = getLogger(__name__)


class DOIPlugin(SingletonPlugin, toolkit.DefaultDatasetForm):
    """
    CKAN DOI Extension.
    """

    implements(interfaces.IConfigurer)
    implements(interfaces.IPackageController, inherit=True)
    implements(interfaces.ITemplateHelpers, inherit=True)
    implements(interfaces.IClick)

    ## IClick
    def get_commands(self):
        return cli.get_commands()

    ## IConfigurer
    def update_config(self, config):
        """
        Adds templates.
        """
        toolkit.add_template_directory(config, 'theme/templates')

    ## IPackageController
    def after_create(self, context, pkg_dict):
        """
        A new dataset has been created, so we need to create a new DOI.

        NB: This is called after creation of a dataset, before resources have been
        added, so state = draft.
        """
        DOIQuery.read_package(pkg_dict['id'], create_if_none=True)

    ## IPackageController
    def after_update(self, context, pkg_dict):
        """
        Dataset has been created/updated.

        Check status of the dataset to determine if we should publish DOI to datacite
        network.
        """
        # Is this active and public? If so we need to make sure we have an active DOI
        if pkg_dict.get('state', 'active') == 'active' and not pkg_dict.get(
            'private', False
        ):
            package_id = pkg_dict['id']

            # remove user-defined update schemas first (if needed)
            context.pop('schema', None)

            # Load the package_show version of the dict
            pkg_show_dict = toolkit.get_action('package_show')(
                context, {'id': package_id}
            )

            # Load or create the local DOI (package may not have a DOI if extension was loaded
            # after package creation)
            doi = DOIQuery.read_package(package_id, create_if_none=True)

            metadata_dict = build_metadata_dict(pkg_show_dict)
            xml_dict = build_xml_dict(metadata_dict)

            client = DataciteClient()

            if doi.published is None:
                # metadata gets created before minting
                client.set_metadata(doi.identifier, xml_dict)
                client.mint_doi(doi.identifier, package_id)
                toolkit.h.flash_success('DataCite DOI created')
            else:
                same = client.check_for_update(doi.identifier, xml_dict)
                if not same:
                    # Not the same, so we want to update the metadata
                    client.set_metadata(doi.identifier, xml_dict)
                    toolkit.h.flash_success('DataCite DOI metadata updated')

        return pkg_dict

    # IPackageController
    def after_show(self, context, pkg_dict):
        """
        Add the DOI details to the pkg_dict so it can be displayed.
        """
        doi = DOIQuery.read_package(pkg_dict['id'])
        if doi:
            pkg_dict['doi'] = doi.identifier
            pkg_dict['doi_status'] = True if doi.published else False
            pkg_dict['domain'] = get_site_url().replace('http://', '')
            pkg_dict['doi_date_published'] = (
                datetime.strftime(doi.published, '%Y-%m-%d') if doi.published else None
            )
            pkg_dict['doi_publisher'] = toolkit.config.get('ckanext.doi.publisher')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'package_get_year': package_get_year,
            'now': datetime.now,
            'get_site_title': get_site_title,
        }

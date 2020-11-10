#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import logging

from ckan.lib.helpers import lang as ckan_lang
from ckan.model import Package
from ckan.plugins import PluginImplementations, toolkit
from ckanext.doi.interfaces import IDoi
from ckanext.doi.lib import xml_utils
from ckanext.doi.lib.helpers import date_or_none, get_site_url, package_get_year
import datetime

log = logging.getLogger(__name__)


def build_metadata_dict(pkg_dict):
    '''
    Build/extract a basic dict of metadata that can then be passed to build_xml_dict.
    :param pkg_dict: dict of package details
    '''
    metadata_dict = {}

    # collect errors instead of throwing them immediately; some data may not be correctly handled
    # by this base method but will be handled correctly by plugins that implement IDoi
    errors = {}

    # required fields first (identifier will be added later)
    required = {
        u'creators': [],
        u'titles': [],
        u'publisher': None,
        u'publicationYear': None,
        u'resourceType': None
    }

    def _add_required(key, get_func):
        try:
            required[key] = get_func()
        except Exception as e:
            errors[key] = e

    # CREATORS
    _add_required(u'creators', lambda: [{
        u'full_name': pkg_dict.get(u'author')
    }])

    # TITLES
    _add_required(u'titles', lambda: [{
        u'title': pkg_dict.get(u'title')
    }])

    # PUBLISHER
    _add_required(u'publisher', lambda: toolkit.config.get(u'ckanext.doi.publisher'))

    # PUBLICATION YEAR
    _add_required(u'publicationYear', lambda: package_get_year(pkg_dict))

    # TYPE
    _add_required(u'resourceType', lambda: pkg_dict.get(u'type'))

    # now the optional fields
    optional = {
        u'subjects': [],
        u'contributors': [],
        u'dates': [],
        u'language': u'',
        u'alternateIdentifiers': [],
        u'relatedIdentifiers': [],
        u'sizes': [],
        u'formats': [],
        u'version': u'',
        u'rightsList': [],
        u'descriptions': [],
        u'geolocations': [],
        u'fundingReferences': []
    }

    # SUBJECTS
    # use the tag list
    try:
        tags = pkg_dict.get(u'tag_string', u'').split(u',')
        tags += [tag[u'name'] if isinstance(tag, dict) else tag for tag in
                 pkg_dict.get(u'tags', [])]
        optional[u'subjects'] = sorted(list(set([{u'subject': t} for t in tags if t != u''])))
    except Exception as e:
        errors[u'subjects'] = e

    # CONTRIBUTORS
    # use the author and maintainer; no splitting or parsing for either
    # no try/except for this because it's just a simple .get() and if that doesn't work then we
    # want to know
    author = pkg_dict.get(u'author')
    maintainer = pkg_dict.get(u'maintainer')
    if author is not None:
        optional[u'contributors'].append(
            {
                u'contributor_type': u'Researcher',
                u'full_name': author
            })
    if maintainer is not None:
        optional[u'contributors'].append({
            u'contributor_type': u'DataManager',
            u'full_name': maintainer
        })

    # DATES
    # created, updated, and doi publish date
    date_errors = {}
    try:
        optional[u'dates'].append({
            u'dateType': u'Created',
            u'date': date_or_none(pkg_dict.get(u'metadata_created'))
        })
    except Exception as e:
        date_errors[u'created'] = e
    try:
        optional[u'dates'].append({
            u'dateType': u'Updated',
            u'date': date_or_none(pkg_dict.get(u'metadata_modified'))
        })
    except Exception as e:
        date_errors[u'updated'] = e
    if u'doi_date_published' in pkg_dict:
        try:
            optional[u'dates'].append({
                u'dateType': u'Issued',
                u'date': date_or_none(pkg_dict.get(u'doi_date_published'))
            })
        except Exception as e:
            date_errors[u'doi_date_published'] = e

    # LANGUAGE
    # use language set in CKAN
    try:
        optional[u'language'] = ckan_lang()
    except Exception as e:
        errors[u'language'] = e

    # ALTERNATE IDENTIFIERS
    # add permalink back to this site
    try:
        permalink = get_site_url() + '/dataset/' + pkg_dict[u'id']
        optional[u'alternateIdentifiers'] = [{
            u'alternateIdentifierType': 'URL',
            u'alternateIdentifier': permalink
        }]
    except Exception as e:
        errors['alternateIdentifiers'] = e

    # RELATED IDENTIFIERS
    # nothing relevant in default schema

    # SIZES
    # sum up given sizes from resources in the package and convert from bytes to kilobytes
    try:
        resource_sizes = [r.get(u'size') or 0 for r in pkg_dict.get(u'resources', []) or []]
        total_size = [u'{0} kb'.format(int(sum(resource_sizes) / 1024))]
        optional[u'sizes'] = total_size
    except Exception as e:
        errors[u'sizes'] = e

    # FORMATS
    # list unique formats from package resources
    try:
        formats = list(
            set(filter(None, [r.get(u'format') for r in pkg_dict.get(u'resources', []) or []])))
        optional[u'formats'] = formats
    except Exception as e:
        errors[u'formats'] = e

    # VERSION
    # doesn't matter if there's no version, it'll get filtered out later
    optional[u'version'] = pkg_dict.get(u'version')

    # RIGHTS
    # use the package license and get details from CKAN's license register
    license_id = pkg_dict.get(u'license_id', u'notspecified')
    try:
        if license_id != u'notspecified' and license_id is not None:
            license_register = Package.get_license_register()
            license = license_register.get(license_id)
            if license is not None:
                optional[u'rightsList'] = [
                    {
                        u'url': license.url,
                        u'identifier': license.id
                    }
                ]
    except Exception as e:
        errors[u'rightsList'] = e

    # DESCRIPTIONS
    # use package notes
    optional[u'descriptions'] = [
        {
            u'descriptionType': u'Other',
            u'description': pkg_dict.get(u'notes', u'')
        }
    ]

    # GEOLOCATIONS
    # nothing relevant in default schema

    # FUNDING
    # nothing relevant in default schema

    metadata_dict.update(required)
    metadata_dict.update(optional)

    for plugin in PluginImplementations(IDoi):
        # implementations should remove relevant errors from the errors dict if they successfully
        # handle an item
        metadata_dict, errors = plugin.build_metadata_dict(pkg_dict, metadata_dict, errors)

    required_errors = {k: e for k, e in errors.items() if k in required}
    if len(required_errors) > 0:
        error_msg = 'Could not extract metadata for the following required keys: {0}'.format(
            ', '.join(required_errors))
        log.exception(error_msg)
        for k, e in required_errors.items():
            log.exception('{0}: {1}'.format(k, e))
        raise MetadataException(error_msg)

    optional_errors = {k: e for k, e in errors.items() if k in optional}
    if len(required_errors) > 0:
        error_msg = 'Could not extract metadata for the following optional keys: {0}'.format(
            ', '.join(optional_errors))
        log.debug(error_msg)
        for k, e in optional_errors.items():
            log.debug('{0}: {1}'.format(k, e))

    return metadata_dict


def build_xml_dict(metadata_dict):
    '''
    Builds a dictionary that can be passed directly to datacite.schema42.tostring() to generate xml.
    Previously named metadata_to_xml but renamed as it's not actually producing any xml,
    it's just formatting the metadata so a separate function can then generate the xml.
    :param metadata_dict: a dict of metadata generated from build_metadata_dict
    :return: dict that can be passed directly to datacite.schema42.tostring()
    '''

    # required fields first (DOI will be added later)
    xml_dict = {
        u'creators': [],
        u'titles': metadata_dict.get(u'titles', []),
        u'publisher': metadata_dict.get(u'publisher'),
        u'publicationYear': str(metadata_dict.get(u'publicationYear')),
        u'types': {
            u'resourceType': metadata_dict.get(u'resourceType'),
            u'resourceTypeGeneral': u'Dataset'
        },
        u'schemaVersion': u'http://datacite.org/schema/kernel-4',
    }

    for creator in metadata_dict.get(u'creators', []):
        xml_dict[u'creators'].append(xml_utils.create_contributor(**creator))

    optional = [
        u'subjects',
        u'contributors',
        u'dates',
        u'language',
        u'alternateIdentifiers',
        u'relatedIdentifiers',
        u'sizes',
        u'formats',
        u'version',
        u'rightsList',
        u'descriptions',
        u'geolocations',
        u'fundingReferences'
    ]

    for k in optional:
        v = metadata_dict.get(k)
        try:
            has_value = v is not None and len(v) > 0
        except:
            has_value = False
        if not has_value:
            continue
        if k == u'contributors':
            xml_dict[u'contributors'] = []
            for contributor in v:
                xml_dict[u'contributors'].append(xml_utils.create_contributor(**contributor))
        elif k == u'dates':
            item = []
            for date_entry in v:
                date_entry[u'date'] = str(date_entry[u'date'])
                item.append(date_entry)
            xml_dict[k] = item
        else:
            xml_dict[k] = v

    return xml_dict


class MetadataException(Exception):
    pass

#!/usr/bin/env python3
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import logging
import uuid
from datetime import datetime
from typing import Any
from xml.etree.ElementTree import Element,tostring

from ckan.lib.helpers import lang as ckan_lang
from ckan.model import Package
from ckan.plugins import PluginImplementations, toolkit

from ckanext.doi.interfaces import IDoi
from ckanext.doi.lib import xml_utils
from ckanext.doi.lib.errors import DOIMetadataException
from ckanext.doi.lib.helpers import (
    date_or_none,
    get_site_url,
    package_get_year,
    get_doi_platform
    )

log = logging.getLogger(__name__)


def build_metadata_dict(pkg_dict):
    platform = get_doi_platform()

    metadata_func = {
        'datacite': datacite_build_medatata_dict,
        'crossref': crossref_build_medatata_dict,
    }

    return metadata_func[platform](pkg_dict)


def datacite_build_medatata_dict(pkg_dict):
    """
    Build/extract a basic dict of metadata that can then be passed to build_xml_dict.

    :param pkg_dict: dict of package details
    """
    metadata_dict = {}

    # collect errors instead of throwing them immediately; some data may not be correctly handled
    # by this base method but will be handled correctly by plugins that implement IDoi
    errors = {}

    # required fields first (identifier will be added later)
    required = {
        'creators': [],
        'titles': [],
        'publisher': None,
        'publicationYear': None,
        'resourceType': None,
    }

    def _add_required(key, get_func):
        try:
            required[key] = get_func()
        except Exception as e:
            errors[key] = e

    # CREATORS
    _add_required('creators', lambda: [{'full_name': pkg_dict.get('author')}])

    # TITLES
    _add_required('titles', lambda: [{'title': pkg_dict.get('title')}])

    # PUBLISHER
    _add_required('publisher', lambda: toolkit.config.get('ckanext.doi.publisher'))

    # PUBLICATION YEAR
    _add_required('publicationYear', lambda: package_get_year(pkg_dict))

    # TYPE
    _add_required('resourceType', lambda: pkg_dict.get('type'))

    # now the optional fields
    optional = {
        'subjects': [],
        'contributors': [],
        'dates': [],
        'language': '',
        'alternateIdentifiers': [],
        'relatedIdentifiers': [],
        'sizes': [],
        'formats': [],
        'version': '',
        'rightsList': [],
        'descriptions': [],
        'geolocations': [],
        'fundingReferences': [],
    }

    # SUBJECTS
    # use the tag list
    try:
        tags = pkg_dict.get('tag_string', '').split(',')
        tags += [
            tag['name'] if isinstance(tag, dict) else tag
            for tag in pkg_dict.get('tags', [])
        ]
        optional['subjects'] = [
            {'subject': tag} for tag in sorted({t for t in tags if t != ''})
        ]
    except Exception as e:
        errors['subjects'] = e

    # CONTRIBUTORS
    # use the author and maintainer; no splitting or parsing for either
    # no try/except for this because it's just a simple .get() and if that doesn't work then we
    # want to know
    author = pkg_dict.get('author')
    maintainer = pkg_dict.get('maintainer')
    if author is not None:
        optional['contributors'].append(
            {'contributor_type': 'Researcher', 'full_name': author}
        )
    if maintainer is not None:
        optional['contributors'].append(
            {'contributor_type': 'DataManager', 'full_name': maintainer}
        )

    # DATES
    # created, updated, and doi publish date
    date_errors = {}
    try:
        optional['dates'].append(
            {
                'dateType': 'Created',
                'date': date_or_none(pkg_dict.get('metadata_created')),
            }
        )
    except Exception as e:
        date_errors['created'] = e
    try:
        optional['dates'].append(
            {
                'dateType': 'Updated',
                'date': date_or_none(pkg_dict.get('metadata_modified')),
            }
        )
    except Exception as e:
        date_errors['updated'] = e
    if 'doi_date_published' in pkg_dict:
        try:
            optional['dates'].append(
                {
                    'dateType': 'Issued',
                    'date': date_or_none(pkg_dict.get('doi_date_published')),
                }
            )
        except Exception as e:
            date_errors['doi_date_published'] = e

    # LANGUAGE
    # use language set in CKAN
    try:
        # remove any localisation of the language, e.g. en from en_GB.
        # default to english in case nothing is set, because it's ckan's default
        optional['language'] = (ckan_lang() or 'en')[:2]
    except Exception as e:
        errors['language'] = e

    # ALTERNATE IDENTIFIERS
    # add permalink back to this site
    try:
        permalink = f'{get_site_url()}/dataset/{pkg_dict["id"]}'
        optional['alternateIdentifiers'] = [
            {'alternateIdentifierType': 'URL', 'alternateIdentifier': permalink}
        ]
    except Exception as e:
        errors['alternateIdentifiers'] = e

    # RELATED IDENTIFIERS
    # nothing relevant in default schema

    # SIZES
    # sum up given sizes from resources in the package and convert from bytes to kilobytes
    try:
        resource_sizes = [
            r.get('size') or 0 for r in pkg_dict.get('resources', []) or []
        ]
        total_size = [f'{int(sum(resource_sizes) / 1024)} kb']
        optional['sizes'] = total_size
    except Exception as e:
        errors['sizes'] = e

    # FORMATS
    # list unique formats from package resources
    try:
        formats = list(
            set(
                filter(
                    None, [r.get('format') for r in pkg_dict.get('resources', []) or []]
                )
            )
        )
        optional['formats'] = formats
    except Exception as e:
        errors['formats'] = e

    # VERSION
    # doesn't matter if there's no version, it'll get filtered out later
    optional['version'] = pkg_dict.get('version')

    # RIGHTS
    # use the package license and get details from CKAN's license register
    license_id = pkg_dict.get('license_id', 'notspecified')
    try:
        if license_id != 'notspecified' and license_id is not None:
            license_register = Package.get_license_register()
            license = license_register.get(license_id)
            if license is not None:
                optional['rightsList'] = [
                    {'rightsURI': license.url, 'rightsIdentifier': license.id}
                ]
    except Exception as e:
        errors['rightsList'] = e

    # DESCRIPTIONS
    # use package notes
    optional['descriptions'] = [
        {'descriptionType': 'Other', 'description': pkg_dict.get('notes', '')}
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
        metadata_dict, errors = plugin.build_metadata_dict(
            pkg_dict, metadata_dict, errors
        )

    for k in required:
        if metadata_dict.get(k) is None and errors.get(k) is None:
            errors[k] = DOIMetadataException('Required field cannot be None')

    required_errors = {k: e for k, e in errors.items() if k in required}
    if len(required_errors) > 0:
        error_msg = (
            f'Could not extract metadata for the following required keys: '
            f'{", ".join(required_errors)}'
        )
        log.exception(error_msg)
        for k, e in required_errors.items():
            log.exception(f'{k}: {e}')
        raise DOIMetadataException(error_msg)

    optional_errors = {k: e for k, e in errors.items() if k in optional}
    if len(required_errors) > 0:
        error_msg = (
            f'Could not extract metadata for the following optional keys: '
            f'{", ".join(optional_errors)}'
        )
        log.debug(error_msg)
        for k, e in optional_errors.items():
            log.debug(f'{k}: {e}')

    return metadata_dict


def build_xml_dict(metadata_dict):
    platform = get_doi_platform()

    xml_func = {
        'datacite': datacite_build_xml_dict,
        'crossref': crossref_build_xml_dict,
    }

    return xml_func[platform](metadata_dict)


def datacite_build_xml_dict(metadata_dict):
    """
    Builds a dictionary that can be passed directly to datacite.schema42.tostring() to
    generate xml. Previously named metadata_to_xml but renamed as it's not actually
    producing any xml, it's just formatting the metadata so a separate function can then
    generate the xml.

    :param metadata_dict: a dict of metadata generated from build_metadata_dict
    :return: dict that can be passed directly to datacite.schema42.tostring()
    """

    # required fields first (DOI will be added later)
    xml_dict = {
        'creators': [],
        'titles': metadata_dict.get('titles', []),
        'publisher': metadata_dict.get('publisher'),
        'publicationYear': str(metadata_dict.get('publicationYear')),
        'types': {
            'resourceType': metadata_dict.get('resourceType'),
            'resourceTypeGeneral': 'Dataset',
        },
        'schemaVersion': 'http://datacite.org/schema/kernel-4',
    }

    for creator in metadata_dict.get('creators', []):
        xml_dict['creators'].append(xml_utils.create_contributor(**creator))

    optional = [
        'subjects',
        'contributors',
        'dates',
        'language',
        'alternateIdentifiers',
        'relatedIdentifiers',
        'sizes',
        'formats',
        'version',
        'rightsList',
        'descriptions',
        'geolocations',
        'fundingReferences',
    ]

    for k in optional:
        v = metadata_dict.get(k)
        try:
            has_value = v is not None and len(v) > 0
        except:
            has_value = False
        if not has_value:
            continue
        if k == 'contributors':
            xml_dict['contributors'] = []
            for contributor in v:
                xml_dict['contributors'].append(
                    xml_utils.create_contributor(**contributor)
                )
        elif k == 'dates':
            item = []
            for date_entry in v:
                date_entry_copy = {k: v for k, v in date_entry.items()}
                date_entry_copy['date'] = str(date_entry_copy['date'])
                item.append(date_entry_copy)
            xml_dict[k] = item
        else:
            xml_dict[k] = v

    for plugin in PluginImplementations(IDoi):
        xml_dict = plugin.build_xml_dict(metadata_dict, xml_dict)

    return xml_dict


def crossref_build_medatata_dict(pkg_dict):
    metadata_dict: dict[str, Any] = {
        "attrs": [
            {"version": "5.3.1"},
            {"xmlns": "http://www.crossref.org/schema/5.3.1"},
            {"xmlns:jats": "http://www.ncbi.nlm.nih.gov/JATS1"}
        ],
        "head" : {
            "doi_batch_id": str(uuid.uuid4()),
            "timestamp": round(datetime.utcnow().timestamp()),
            "depositor": {
                "depositor_name": toolkit.config.get("ckanext.doi.publisher", ""),
                "email_address": toolkit.config.get("ckanext.doi.account_name", ""),
            },
            "registrant": toolkit.config.get("ckanext.doi.account_name", ""),
        },
        "body": {
            "database": {
                "database_metadata": {
                    "attrs": [
                        {"language": "en"},
                    ],
                    "titles": {
                        "title": "Dataset",
                    },
                    "institution": {
                        "institution_name": toolkit.config.get("ckanext.doi.publisher", "")
                    },
                },
                "dataset": {
                    "contributors": {
                        "organization": {
                            "attrs": [
                                {"sequence": "first"},
                                {"contributor_role": "author"}
                            ],
                            'item_value': pkg_dict.get("organization", {}).get("title", "")
                        },
                    },
                    "titles": {
                        "title": pkg_dict['title'],
                    },
                    "doi_data": {
                        "doi": pkg_dict.get("doi", ""),
                        "resource": f"{get_site_url()}/dataset/{pkg_dict['id']}"
                    },
                }
            }
        }
    }

    for plugin in PluginImplementations(IDoi):
        metadata_dict, errors = plugin.build_metadata_dict(
            pkg_dict, metadata_dict, errors
        )

    return metadata_dict


def crossref_build_xml_dict(metadata_dict):
    def _dict_to_xml(tag, data):
        elem: Element = Element(tag)

        if isinstance(data, dict):
            if data.get('attrs'):
                attrs = data.pop('attrs')
                for attr in attrs:
                    for attr_name, attr_value in attr.items():
                        elem.set(attr_name, attr_value)

            if len(data) == 1 and data.get('item_value'):
                elem.text = str(data.get('item_value'))
            else:
                for key, value in data.items():
                    if isinstance(value, dict):
                        child_elem: Element = _dict_to_xml(key, value)

                        elem.append(child_elem)
                    else:
                        child_elem: Element = Element(key)
                        child_elem.text = str(value)
                        elem.append(child_elem)
        else:
            elem.text = str(data)

        return elem

    e= _dict_to_xml('doi_batch', metadata_dict)

    return str(tostring(e, encoding='utf8', method='xml').decode('utf8'))

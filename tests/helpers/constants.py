#!/usr/bin/env python3
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import datetime

PKG_DICT = {
    'domain': 'data.nhm.ac.uk',
    'license_title': 'CC0-1.0',
    'maintainer': 'Maintainer, Data',
    'relationships_as_object': [],
    'doi_status': False,
    'private': False,
    'maintainer_email': None,
    'num_tags': 2,
    'id': '919379ef-ea08-4a5f-b370-7845e24117b4',
    'metadata_created': '2020-11-09T17:14:06.700561',
    'owner_org': '2dc787a8-17c3-4425-bed7-2b97c81789d0',
    'metadata_modified': '2020-11-09T17:14:07.225364',
    'author': 'Author, Test',
    'author_email': None,
    'state': 'active',
    'version': '1',
    'license_id': 'CC0-1.0',
    'type': 'dataset',
    'resources': [],
    'num_resources': 0,
    'tags': [
        {
            'vocabulary_id': None,
            'state': 'active',
            'display_name': 'not-a-real-package',
            'id': 'a3169a9a-e03c-4844-8694-0bd0cfaaaeae',
            'name': 'not-a-real-package',
        },
        {
            'vocabulary_id': None,
            'state': 'active',
            'display_name': 'testing',
            'id': 'cbd1ad22-d75e-4641-8d47-d29bbd758e0c',
            'name': 'testing',
        },
    ],
    'groups': [],
    'creator_user_id': '21ff8eeb-38e5-4348-8c1d-f409b2a9ca03',
    'relationships_as_subject': [],
    'doi_publisher': 'Natural History Museum',
    'doi': '10.4124/gqcx00k4',
    'name': 'test_pkg',
    'isopen': False,
    'url': None,
    'notes': 'These are some notes about the package.',
    'title': 'Test Package',
    'extras': [],
    'organization': {
        'description': 'Just another test organization.',
        'title': 'Test Organization',
        'created': '2020-11-09T17:14:06.583496',
        'approval_status': 'approved',
        'is_organization': True,
        'state': 'active',
        'image_url': 'http://placekitten.com/g/200/100',
        'revision_id': '2b0d57a6-5d2f-46c3-859e-32635bfcf741',
        'type': 'organization',
        'id': '2dc787a8-17c3-4425-bed7-2b97c81789d0',
        'name': 'test_org_00',
    },
    'revision_id': 'c71800fb-60b7-421f-a7f2-56dc8efaf21d',
    'doi_date_published': None,
}

METADATA_DICT = {
    'fundingReferences': [],
    'contributors': [
        {'full_name': 'Author, Test', 'contributor_type': 'Researcher'},
        {'full_name': 'Maintainer, Data', 'contributor_type': 'DataManager'},
    ],
    'geolocations': [],
    'dates': [
        {
            'date': datetime.datetime(2020, 11, 9, 17, 14, 6, 700561),
            'dateType': 'Created',
        },
        {
            'date': datetime.datetime(2020, 11, 9, 17, 14, 7, 225364),
            'dateType': 'Updated',
        },
        {'date': None, 'dateType': 'Issued'},
    ],
    'relatedIdentifiers': [],
    'titles': [{'title': 'Test Package'}],
    'descriptions': [
        {
            'descriptionType': 'Other',
            'description': 'These are some notes about the package.',
        }
    ],
    'subjects': [],
    'publisher': 'Natural History Museum',
    'publicationYear': 2020,
    'rightsList': [],
    'language': '',
    'sizes': ['0 kb'],
    'resourceType': 'dataset',
    'alternateIdentifiers': [
        {
            'alternateIdentifierType': 'URL',
            'alternateIdentifier': 'http://data.nhm.ac.uk/dataset/919379ef-ea08-4a5f-b370-7845e24117b4',
        }
    ],
    'version': '1',
    'formats': [],
    'creators': [{'full_name': 'Author, Test'}],
}

# minimal example from https://datacite.readthedocs.io/en/latest
XML_DICT = {
    'identifiers': [
        {
            'identifierType': 'DOI',
            'identifier': '10.4124/abcd1234',
        }
    ],
    'creators': [
        {'name': 'Smith, John'},
    ],
    'titles': [
        {
            'title': 'Minimal Test Case',
        }
    ],
    'publisher': 'Invenio Software',
    'publicationYear': '2015',
    'types': {'resourceType': 'Dataset', 'resourceTypeGeneral': 'Dataset'},
    'schemaVersion': 'http://datacite.org/schema/kernel-4',
}

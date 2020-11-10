#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

import datetime

PKG_DICT = {
    u'domain': u'data.nhm.ac.uk',
    'license_title': u'CC0-1.0',
    'maintainer': u'Maintainer, Data',
    'relationships_as_object': [],
    u'doi_status': False,
    'private': False,
    'maintainer_email': None,
    'num_tags': 2,
    'id': u'919379ef-ea08-4a5f-b370-7845e24117b4',
    'metadata_created': '2020-11-09T17:14:06.700561',
    'owner_org': u'2dc787a8-17c3-4425-bed7-2b97c81789d0',
    'metadata_modified': '2020-11-09T17:14:07.225364',
    'author': u'Author, Test',
    'author_email': None,
    'state': u'active',
    'version': u'1',
    'license_id': u'CC0-1.0',
    'type': u'dataset',
    'resources': [],
    'num_resources': 0,
    'tags': [{
        'vocabulary_id': None,
        'state': u'active',
        'display_name': u'not-a-real-package',
        'id': u'a3169a9a-e03c-4844-8694-0bd0cfaaaeae',
        'name': u'not-a-real-package'
    }, {
        'vocabulary_id': None,
        'state': u'active',
        'display_name': u'testing',
        'id': u'cbd1ad22-d75e-4641-8d47-d29bbd758e0c',
        'name': u'testing'
    }],
    'groups': [],
    'creator_user_id': u'21ff8eeb-38e5-4348-8c1d-f409b2a9ca03',
    'relationships_as_subject': [],
    u'doi_publisher': 'Natural History Museum',
    u'doi': u'10.4124/gqcx00k4',
    'name': u'test_pkg',
    'isopen': False,
    'url': None,
    'notes': u'These are some notes about the package.',
    'title': u'Test Package',
    'extras': [],
    'organization': {
        'description': u'Just another test organization.',
        'title': u'Test Organization',
        'created': '2020-11-09T17:14:06.583496',
        'approval_status': u'approved',
        'is_organization': True,
        'state': u'active',
        'image_url': u'http://placekitten.com/g/200/100',
        'revision_id': u'2b0d57a6-5d2f-46c3-859e-32635bfcf741',
        'type': u'organization',
        'id': u'2dc787a8-17c3-4425-bed7-2b97c81789d0',
        'name': u'test_org_00'
    },
    'revision_id': u'c71800fb-60b7-421f-a7f2-56dc8efaf21d',
    u'doi_date_published': None
}

METADATA_DICT = {
    u'fundingReferences': [],
    u'contributors': [{
        u'full_name': u'Author, Test',
        u'contributor_type': u'Researcher'
    }, {
        u'full_name': u'Maintainer, Data',
        u'contributor_type': u'DataManager'
    }],
    u'geolocations': [],
    u'dates': [{
        u'date': datetime.datetime(2020, 11, 9, 17, 14, 6, 700561),
        u'dateType': u'Created'
    }, {
        u'date': datetime.datetime(2020, 11, 9, 17, 14, 7, 225364),
        u'dateType': u'Updated'
    }, {
        u'date': None,
        u'dateType': u'Issued'
    }],
    u'relatedIdentifiers': [],
    u'titles': [{
        u'title': u'Test Package'
    }],
    u'descriptions': [{
        u'descriptionType': u'Other',
        u'description': u'These are some notes about the package.'
    }],
    u'subjects': [],
    u'publisher': 'Natural History Museum',
    u'publicationYear': 2020,
    u'rightsList': [],
    u'language': u'',
    u'sizes': [u'0 kb'],
    u'resourceType': u'dataset',
    u'alternateIdentifiers': [{
        u'alternateIdentifierType': 'URL',
        u'alternateIdentifier': u'http://data.nhm.ac.uk/dataset/919379ef-ea08-4a5f-b370'
                                u'-7845e24117b4'
    }],
    u'version': u'1',
    u'formats': [],
    u'creators': [{
        u'full_name': u'Author, Test'
    }]
}

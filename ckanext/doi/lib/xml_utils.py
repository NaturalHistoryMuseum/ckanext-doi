#!/usr/bin/env python3
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK


def create_contributor(
    full_name=None,
    family_name=None,
    given_name=None,
    is_org=False,
    contributor_type=None,
    affiliations=None,
    identifiers=None,
):
    """
    Create a dictionary representation of a contributing entity (either a person or an
    organisation) for use in an xml_dict.

    :param full_name: the full name of the creator, in the format "FamilyName, GivenName";
    can be omitted if family_name and given_name are provided
    :param family_name: family name of the creator; will be ignored if given_name is None
    :param given_name: given name(s) or initials of the creator; will be ignored if
    family_name is None
    :param is_org: sets name type to Organizational if true
    :param contributor_type: the contributor type to set
    :param affiliations: affiliations of the contributor, either a string or list of strings
    :param identifiers: a list of dicts with "identifier", "scheme", and (optionally) "scheme_uri"
    :return: a dict
    """
    if is_org and full_name is None:
        raise ValueError('Creator name must be supplied as full_name="Org Name"')
    if full_name is None and (family_name is None or given_name is None):
        raise ValueError(
            'Creator name must be supplied, either as full_name="FamilyName, '
            'GivenName" or separately as family_name and given_name'
        )
    if full_name is None:
        full_name = f'{family_name}, {given_name}'
    if (family_name is None or given_name is None) and not is_org:
        # try to extract the family and given names from the full name
        name_parts = full_name.split(',', 1)
        if len(name_parts) > 1:
            family_name, given_name = [x.strip() for x in name_parts]
        else:
            # assume it was formatted incorrectly and split by spaces instead
            # if that doesn't work then there isn't much we can do
            name_parts = full_name.split(' ')
            family_name = name_parts[-1].strip()
            given_name = ' '.join(name_parts[0:-1]).strip()
    contributor = {
        'name': full_name,
        'nameType': 'Organizational' if is_org else 'Personal',
    }
    if not is_org:
        contributor['familyName'] = family_name
        contributor['givenName'] = given_name
    if contributor_type is not None:
        contributor['contributorType'] = contributor_type
    if affiliations is not None:
        contributor['affiliations'] = []
        if isinstance(affiliations, str):
            affiliations = [affiliations]
        for affiliation in affiliations:
            contributor['affiliations'].append({'affiliation': affiliation})
    if identifiers:
        contributor['nameIdentifiers'] = []
        for _id in identifiers:
            if 'identifier' not in _id or 'scheme' not in _id:
                continue
            id_dict = {
                'nameIdentifier': _id['identifier'],
                'nameIdentifierScheme': _id['scheme'],
            }
            if 'scheme_uri' in _id:
                id_dict['schemeUri'] = _id['scheme_uri']
            contributor['nameIdentifiers'].append(id_dict)
    return contributor

#!/usr/bin/env python3
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK


def create_contributor(full_name=None, family_name=None, given_name=None, is_org=False,
                       contributor_type=None, affiliations=None):
    '''
    Create a dictionary representation of a contributing entity (either a person or an
    organisation) for use in an xml_dict.

    :param full_name: the full name of the creator, in the format "FamilyName, GivenName";
    can be omitted if family_name and given_name are provided
    :param family_name: family name of the creator; will be ignored if given_name is None
    :param given_name: given name(s) or initials of the creator; will be ignored if
    family_name is None
    :param is_org: sets name type to Organization if true
    :param contributor_type: the contributor type to set
    :param affiliations: affiliations of the contributor, either a string or list of strings
    :return: a dict
    '''
    if full_name is None and (family_name is None or given_name is None):
        raise ValueError('Creator name must be supplied, either as full_name="FamilyName, '
                         'GivenName" or separately as family_name and given_name')
    if full_name is None:
        full_name = f'{family_name}, {given_name}'
    if family_name is None or given_name is None:
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
    person = {
        'name': full_name,
        'familyName': family_name,
        'givenName': given_name,
        'nameType': 'Organization' if is_org else 'Personal'
    }
    if contributor_type is not None:
        person['contributorType'] = contributor_type
    if affiliations is not None:
        person['affiliations'] = []
        if isinstance(affiliations, str):
            affiliations = [affiliations]
        for affiliation in affiliations:
            person['affiliations'].append({'affiliation': affiliation})
    return person

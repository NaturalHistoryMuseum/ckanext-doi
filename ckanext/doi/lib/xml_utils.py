#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK


def create_contributor(full_name=None, family_name=None, given_name=None, is_org=False, contributor_type=None):
    '''
    Create a dictionary representation of a contributing entity (either a person or an
    organisation) for use in an xml_dict.
    :param full_name: the full name of the creator, in the format "FamilyName, GivenName";
    can be omitted if family_name and given_name are provided
    :param family_name: family name of the creator; will be ignored if given_name is None
    :param given_name: given name(s) or initials of the creator; will be ignored if
    family_name is None
    :param is_org: sets name type to Organization if true
    :return:
    '''
    if full_name is None and (family_name is None or given_name is None):
        raise ValueError(
            u'Creator name must be supplied, either as full_name="FamilyName, GivenName" or '
            u'separately as family_name and given_name')
    if full_name is None:
        full_name = u'{0}, {1}'.format(family_name, given_name)
    if family_name is None or given_name is None:
        # try to extract the family and given names from the full name
        name_parts = full_name.split(u',', 1)
        if len(name_parts) > 1:
            family_name, given_name = [x.strip() for x in name_parts]
        else:
            # assume it was formatted incorrectly and split by spaces instead
            # if that doesn't work then there isn't much we can do
            name_parts = full_name.split(u' ')
            family_name = name_parts[-1].strip()
            given_name = u' '.join(name_parts[0:-1]).strip()
    person = {
        u'name': full_name,
        u'familyName': family_name,
        u'givenName': given_name,
        u'nameType': u'Organization' if is_org else u'Personal'
    }
    if contributor_type is not None:
        person[u'contributorType'] = contributor_type
    return person

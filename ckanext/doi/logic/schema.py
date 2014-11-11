import ckan.plugins as p

from ckan.logic.schema import (
    default_create_package_schema,
    default_update_package_schema,
    default_show_package_schema
    )

from ckanext.doi.logic.validators import editable_mandatory_field

get_validator = p.toolkit.get_validator
get_converter = p.toolkit.get_converter

# Core validators and converters
not_empty = get_validator('not_empty')
ignore_missing = get_validator('ignore_missing')

def create_package_schema():
    """
    Title and author are mandatory DataCite metadata fields
    @return: schema
    """
    schema = default_create_package_schema()


    return schema


def update_package_schema():
    """
    Mandatory metadata fields should not be updated after they have been created
    @return: schema
    """
    schema = default_update_package_schema()
    _modify_schema(schema)

    # Mandatory metadata fields should not be updated after they have been created
    schema['title'].append(editable_mandatory_field)
    schema['author'].append(editable_mandatory_field)

    return schema

def _modify_schema(schema):

    convert_to_extras = get_converter('convert_to_extras')

    schema['title'] = [not_empty, unicode]
    schema['author'] = [not_empty, unicode]
    schema['doi'] = [ignore_missing, unicode, convert_to_extras]


def show_package_schema():

    convert_from_extras = get_converter('convert_from_extras')
    schema = default_show_package_schema()
    schema['doi'] = [convert_from_extras, ignore_missing]

    return schema

import ckan.plugins as p

from ckan.logic.schema import (
    default_create_package_schema,
    default_update_package_schema,
    default_show_package_schema
    )

from ckanext.doi.logic.validators import string_max_length

get_converter = p.toolkit.get_converter
get_validator = p.toolkit.get_validator

# Core validators and converters
not_empty = get_validator('not_empty')
ignore_missing = get_validator('ignore_missing')
not_missing = get_validator('not_missing')
resource_id_exists = get_validator('resource_id_exists')
int_validator = get_validator('int_validator')
boolean_validator = get_validator('boolean_validator')


def create_package_schema():
    schema = default_create_package_schema()
    _modify_schema(schema)
    return schema


def update_package_schema():
    schema = default_update_package_schema()
    _modify_schema(schema)
    return schema


def _modify_schema(schema):
    schema['doi'] = [not_empty, string_max_length(255), unicode]


def show_package_schema():

    convert_from_extras = get_converter('convert_from_extras')
    schema = default_show_package_schema()
    schema['doi'] = [convert_from_extras]

    return schema
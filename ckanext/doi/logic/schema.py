import ckan.plugins as p

from ckan.logic.schema import (
    default_create_package_schema,
    default_update_package_schema,
    default_show_package_schema
    )

from ckanext.doi.logic.validators import editable_mandatory_field

get_validator = p.toolkit.get_validator

# Core validators and converters
not_empty = get_validator('not_empty')

mandatory_fields = ['title', 'author']


def _modify_update_package_schema(schema):

    _modify_create_package_schema(schema)

    # Mandatory metadata fields should not be updated after they have been created
    for field in mandatory_fields:
        schema[field].append(editable_mandatory_field)


def _modify_create_package_schema(schema):

    # Make mandatory fields required
    for field in mandatory_fields:
        if not_empty not in schema[field]:
            schema[field].append(not_empty)
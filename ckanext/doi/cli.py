import click
from ckan import model
from ckan.model import Session
from ckan.plugins import toolkit
from datacite.errors import DataCiteError

from ckanext.doi.lib.api import DataciteClient
from ckanext.doi.lib.metadata import build_metadata_dict, build_xml_dict
from ckanext.doi.model import doi as doi_model
from ckanext.doi.model.crud import DOIQuery
from ckanext.doi.model.doi import DOI


def get_commands():
    return [doi]


@click.group()
def doi():
    pass


@doi.command(name='initdb')
def init_db():
    if not model.package_table.exists():
        click.secho(
            'Package table must exist before initialising the DOI table', fg='red'
        )
        raise click.Abort()

    if doi_model.doi_table.exists():
        click.secho('DOI table already exists', fg='green')
    else:
        doi_model.doi_table.create()
        click.secho('DOI table created', fg='green')


@doi.command(name='delete-dois')
def delete_dois():
    """
    Delete all DOIs from the database.
    """
    to_delete = Session.query(DOI).filter(
        DOI.identifier.like(f'%{DataciteClient.get_prefix()}%')
    )
    doi_count = to_delete.count()
    if doi_count == 0:
        click.secho('Nothing to delete', fg='green')
        return
    if click.confirm(f'Delete {doi_count} DOIs from the database?', abort=True):
        to_delete.delete(synchronize_session=False)
        Session.commit()
        click.secho(f'Deleted {doi_count} DOIs from the database')


@doi.command(name='update-doi')
@click.option(
    '-p', '--package_id', 'package_ids', multiple=True, help='Package id(s) to update'
)
def update_doi(package_ids):
    """
    Update either all DOIs in the system or the ones associated with the given packages.
    """
    if not package_ids:
        dois_to_update = Session.query(DOI).all()
    else:
        dois_to_update = list(filter(None, map(DOIQuery.read_package, package_ids)))

    if len(dois_to_update) == 0:
        click.secho('No DOIs found to update', fg='green')
        return

    for record in dois_to_update:
        pkg_dict = toolkit.get_action('package_show')({}, {'id': record.package_id})
        title = pkg_dict.get('title', record.package_id)

        if record.published is None:
            click.secho(
                f'"{title}" does not have a published DOI; ignoring', fg='yellow'
            )
            continue
        if pkg_dict.get('state', 'active') != 'active' or pkg_dict.get(
            'private', False
        ):
            click.secho(f'"{title}" is inactive or private; ignoring', fg='yellow')
            continue

        metadata_dict = build_metadata_dict(pkg_dict)
        xml_dict = build_xml_dict(metadata_dict)

        client = DataciteClient()

        same = client.check_for_update(record.identifier, xml_dict)
        if not same:
            try:
                client.set_metadata(record.identifier, xml_dict)
                click.secho(f'Updated "{title}"', fg='green')
            except DataCiteError as e:
                click.secho(
                    f'Error while updating "{title}" (DOI {record.identifier}): {e})',
                    fg='red',
                )
        else:
            click.secho(f'"{title}" is already up to date', fg='green')

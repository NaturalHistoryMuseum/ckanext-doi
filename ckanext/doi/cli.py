import click
from ckanext.doi.lib.api import DataciteClient
from ckanext.doi.lib.metadata import build_metadata_dict, build_xml_dict
from ckanext.doi.model import doi as doi_model
from ckanext.doi.model.crud import DOIQuery
from ckanext.doi.model.doi import DOI
from datacite.errors import DataCiteError

from ckan import model
from ckan.model import Session
from ckan.plugins import toolkit


def get_commands():
    return [doi]


@click.group()
def doi():
    pass


@doi.command(name=u'initdb')
def init_db():
    if not model.package_table.exists():
        click.secho(u'Package table must exist before initialising the DOI table', fg=u'red')
        raise click.Abort()

    if doi_model.doi_table.exists():
        click.secho(u'DOI table already exists', fg=u'green')
    else:
        doi_model.doi_table.create()
        click.secho(u'DOI table created', fg=u'green')


@doi.command(name=u'delete-dois')
def delete_dois():
    '''
    Delete all DOIs from the database.
    '''
    to_delete = Session.query(DOI).filter(
        DOI.identifier.like(u'%' + DataciteClient.get_prefix() + u'%'))
    doi_count = to_delete.count()
    if doi_count == 0:
        click.secho(u'Nothing to delete', fg=u'green')
        return
    if click.confirm(u'Delete {} DOIs from the database?'.format(doi_count), abort=True):
        to_delete.delete(synchronize_session=False)
        Session.commit()
        click.secho(u'Deleted {} DOIs from the database'.format(doi_count))


@doi.command(name=u'update-doi')
@click.option(u'-p', u'--package_id', u'package_ids', multiple=True,
              help=u'The package id(s) to update')
def update_doi(package_ids):
    '''
    Update either all DOIs in the system or the ones associated with the given packages.
    '''
    if not package_ids:
        dois_to_update = Session.query(DOI).all()
    else:
        dois_to_update = list(filter(None, map(DOIQuery.read_package, package_ids)))

    if len(dois_to_update) == 0:
        click.secho(u'No DOIs found to update', fg=u'green')
        return

    for record in dois_to_update:
        pkg_dict = toolkit.get_action(u'package_show')({}, {
            u'id': record.package_id
        })
        title = pkg_dict.get(u'title', record.package_id)

        if record.published is None:
            click.secho(u'"{}" does not have a published DOI; ignoring'.format(title), fg=u'yellow')
            continue
        if pkg_dict.get(u'state', u'active') != u'active' or pkg_dict.get(u'private', False):
            click.secho(u'"{}" is inactive or private; ignoring'.format(title), fg=u'yellow')
            continue

        metadata_dict = build_metadata_dict(pkg_dict)
        xml_dict = build_xml_dict(metadata_dict)

        client = DataciteClient()

        same = client.check_for_update(record.identifier, xml_dict)
        if not same:
            try:
                client.set_metadata(record.identifier, xml_dict)
                click.secho(u'Updated "{}"'.format(title), fg=u'green')
            except DataCiteError as e:
                click.secho(
                    u'Error while trying to update "{}" (DOI {}): {})'.format(title,
                                                                              record.identifier,
                                                                              e.message), fg=u'red')
        else:
            click.secho(u'"{}" is already up to date'.format(title), fg=u'green')

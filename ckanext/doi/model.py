from logging import getLogger

import sqlalchemy as sa
from sqlalchemy import types, Table, ForeignKey, Column, DateTime
from sqlalchemy.sql.expression import or_
from sqlalchemy.orm import relation, backref
from ckan import model
from ckan.model import meta, User, Package, Session, Resource, Group
from ckan.model.types import make_uuid
import ckan.lib.helpers as h
from ckan.model.domain_object import DomainObject
from datetime import datetime

log = getLogger(__name__)

doi_table = Table('doi', meta.metadata,
                  Column('identifier', types.UnicodeText, primary_key=True),
                  Column('package_id', types.UnicodeText, ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, unique=True),
                  Column('created', types.DateTime, default=datetime.now, nullable=False)
)


class DOI(DomainObject):
    """
    DOI Object
    """
    pass


meta.mapper(DOI, doi_table, properties={
    'dataset': relation(model.Package,
                        backref=backref('doi', cascade='all, delete-orphan'),
                        primaryjoin=doi_table.c.package_id.__eq__(Package.id)
    )
}
)




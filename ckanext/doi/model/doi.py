#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

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

doi_table = Table(u'doi', meta.metadata,
                  Column(u'identifier', types.UnicodeText, primary_key=True),
                  Column(u'package_id', types.UnicodeText, ForeignKey(u'package.id', onupdate=u'CASCADE', ondelete=u'CASCADE'), nullable=False, unique=True),
                  Column(u'published', types.DateTime, nullable=True),  # Date DOI was published to DataCite
)

class DOI(DomainObject):
    '''DOI Object'''
    pass


meta.mapper(DOI, doi_table, properties={
    u'dataset': relation(model.Package,
                        backref=backref(u'doi', cascade=u'all, delete-orphan'),
                        primaryjoin=doi_table.c.package_id.__eq__(Package.id)
    )
}
)




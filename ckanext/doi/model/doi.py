#!/usr/bin/env python3
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from ckan.model import Package, meta
from ckan.model.domain_object import DomainObject
from sqlalchemy import Column, ForeignKey, Table, types
from sqlalchemy.orm import backref, relation

doi_table = Table(
    'doi',
    meta.metadata,
    Column('identifier', types.UnicodeText, primary_key=True),
    Column(
        'package_id',
        types.UnicodeText,
        ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    ),
    # Date DOI was published to DataCite
    Column('published', types.DateTime, nullable=True),
)


class DOI(DomainObject):
    """
    DOI Object.
    """

    pass


meta.mapper(
    DOI,
    doi_table,
    properties={
        'dataset': relation(
            Package,
            backref=backref('doi', cascade='all, delete-orphan'),
            primaryjoin=doi_table.c.package_id.__eq__(Package.id),
        )
    },
)

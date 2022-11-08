#!/usr/bin/env python3
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from ckan.model import Session

from ckanext.doi.model.doi import DOI, doi_table


class DOIQuery:
    # convenience properties
    m = DOI
    cols = [c.name for c in doi_table.c]

    @classmethod
    def create(cls, identifier, package_id, published=None):
        """
        Create a new record in the DOI table.

        :param identifier: a new DOI string
        :param package_id: the id of the package this DOI represents
        :param published: when this DOI was published (datetime, nullable)
        :return: the newly created record object
        """
        new_record = DOI(
            identifier=identifier, package_id=package_id, published=published
        )
        Session.add(new_record)
        Session.commit()
        return new_record

    @classmethod
    def read_doi(cls, identifier):
        """
        Retrieve a record with a given DOI.

        :param identifier: the DOI string
        :return: the record object
        """
        return Session.query(DOI).get(identifier)

    @classmethod
    def read_package(cls, package_id, create_if_none=False):
        """
        Retrieve a record associated with a given package.

        :param package_id: the id of the package
        :param create_if_none: generate a new DOI and add a record if no record is found for the
                               given package
        :return: the record object
        """
        from ckanext.doi.lib.api import DataciteClient

        record = Session.query(DOI).filter(DOI.package_id == package_id).first()
        if record is None and create_if_none:
            client = DataciteClient()
            new_doi = client.generate_doi()
            record = cls.create(new_doi, package_id)
        return record

    @classmethod
    def update_doi(cls, identifier, **kwargs):
        """
        Update the package_id and/or published fields of a record with a given DOI.

        :param identifier: the DOI string
        :param kwargs: the values to be updated
        :return: the updated record object
        """
        update_dict = {k: v for k, v in kwargs.items() if k in cls.cols}
        Session.query(DOI).filter(DOI.identifier == identifier).update(update_dict)
        Session.commit()
        return cls.read_doi(identifier)

    @classmethod
    def update_package(cls, package_id, **kwargs):
        """
        Update the package_id and/or published fields of a record associated with a
        given package.

        :param package_id: the id of the package
        :param kwargs: the values to be updated
        :return: the updated record object
        """
        update_dict = {k: v for k, v in kwargs.items() if k in cls.cols}
        Session.query(DOI).filter(DOI.package_id == package_id).update(update_dict)
        Session.commit()
        return cls.read_package(package_id)

    @classmethod
    def delete_doi(cls, identifier):
        """
        Delete the record with a given DOI.

        :param identifier: the DOI string
        :return: True if a record was deleted, False if not
        """
        to_delete = cls.read_doi(identifier)
        if to_delete is not None:
            Session.delete(to_delete)
            Session.commit()
            return True
        else:
            return False

    @classmethod
    def delete_package(cls, package_id):
        """
        Delete the record associated with a given package.

        :param package_id: the id of the package
        :return: True if a record was deleted, False if not
        """
        to_delete = cls.read_package(package_id)
        if to_delete is not None:
            Session.delete(to_delete)
            Session.commit()
            return True
        else:
            return False

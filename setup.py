#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from setuptools import find_packages, setup

__version__ = u'2.0.2'

with open(u'README.md', u'r') as f:
    __long_description__ = f.read()

setup(
    name=u'ckanext-doi',
    version=__version__,
    description=u'A CKAN extension for assigning a digital object identifier (DOI) to datasets, using the DataCite DOI service.',
    long_description=__long_description__,
    classifiers=[
        u'Development Status :: 3 - Alpha',
        u'Framework :: Flask',
        u'Programming Language :: Python :: 2.7'
    ],
    keywords=u'CKAN data doi',
    author=u'Natural History Museum',
    author_email=u'data@nhm.ac.uk',
    url=u'https://github.com/NaturalHistoryMuseum/ckanext-doi',
    license=u'GNU GPLv3',
    packages=find_packages(exclude=[u'tests']),
    namespace_packages=[u'ckanext', u'ckanext.doi'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'requests',
        'xmltodict==0.9.0',
        'jsonschema==3.0.0'
        ],
    entry_points= \
        u'''
        [ckan.plugins]
            doi=ckanext.doi.plugin:DOIPlugin

        [paste.paster_command]
            doi=ckanext.doi.commands.doi:DOICommand
        ''',
    )

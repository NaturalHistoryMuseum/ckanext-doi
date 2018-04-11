#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from setuptools import find_packages, setup

version = u'0.2'

setup(
    name=u'ckanext-doi',
    version=version,
    description=u'CKAN extension for assigning a DOI to datasets',
    classifiers=[],
    keywords=u'',
    author=u'Ben Scott',
    author_email=u'ben@benscott.co.uk',
    url=u'',
    license=u'',
    packages=find_packages(exclude=[u'tests']),
    namespace_packages=[u'ckanext', u'ckanext.doi'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        u'requests',
        u'xmltodict'
        ],
    entry_points= \
        u'''
        [ckan.plugins]
            doi=ckanext.doi.plugin:DOIPlugin
    
        [paste.paster_command]
            doi=ckanext.doi.commands.doi:DOICommand
        ''',
    )

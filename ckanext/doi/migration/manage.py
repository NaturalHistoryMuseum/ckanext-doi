#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from migrate.versioning.shell import main

main(repository=u'doi/migration')

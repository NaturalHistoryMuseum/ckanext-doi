#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-doi
# Created by the Natural History Museum in London, UK

from ckan.plugins import interfaces


class IDoi(interfaces.Interface):
    '''Hook into IDoi'''

    def build_metadata(self, pkg_dict, metadata_dict):
        '''Plugin interface for building metadata dictionary,
        This will be passed to DOI DataCite minting service

        :param pkg_dict: package dictionary
        :param metadata_dict: 
        :returns: metadata_dict

        '''
        return metadata_dict

    def metadata_to_xml(self, xml_dict, metadata):
        '''Plugin interface for converting metadata into XML dict

        :param xml_dict: XML dict to pass to datacite
        :param metadata: 
        :returns: metadata_dict

        '''
        return xml_dict

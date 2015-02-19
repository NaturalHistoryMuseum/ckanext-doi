import itertools
from pylons import config
import ckan.model as model
from ckan.common import c
from ckan.lib.helpers import json
import ckan.plugins.interfaces as interfaces
from ckanext.doi.helpers import package_get_year

class IDoi(interfaces.Interface):
    """
    Hook into contact form
    """
    def build_metadata(self, pkg_dict, metadata_dict):
        """
        Plugin interface for building metadata dictionary,
        This will be passed to DOI DataCite minting service

        @param pkg_dict: package dictionary
        @return: metadata_dict
        """
        return metadata_dict
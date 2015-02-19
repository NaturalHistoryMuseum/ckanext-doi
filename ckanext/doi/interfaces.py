import ckan.plugins.interfaces as interfaces

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
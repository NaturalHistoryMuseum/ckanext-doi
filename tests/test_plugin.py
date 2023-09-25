from unittest.mock import patch, MagicMock

import pytest
from datacite.errors import DataCiteNotFoundError

from ckan.tests import factories
from ckan.tests.helpers import call_action
from ckanext.doi.model.crud import DOIQuery


@pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SADeprecationWarning")
@pytest.mark.ckan_config("ckan.plugins", "doi")
@pytest.mark.ckan_config("ckanext.doi.prefix", "testing")
@pytest.mark.usefixtures("with_doi_table", "with_plugins")
class TestDOIPlugin:
    def test_after_dataset_create(self):
        # as well as testing the after_dataset_create functionality works on some level,
        # this test is also here to confirm that after_dataset_create is called
        # correctly whether you are on CKAN 2.9 or CKAN 2.10.

        with patch("ckanext.doi.lib.api.DataCiteMDSClient") as mock_client_class:
            # mock the datacite API to make it look like the DOI generated is new
            mock_client = MagicMock(
                metadata_get=MagicMock(side_effect=DataCiteNotFoundError())
            )
            mock_client_class.return_value = mock_client

            # create a new dataset
            dataset = factories.Dataset()

        # check that a DOI is created in the database for this new dataset
        assert DOIQuery.read_package(dataset["id"], create_if_none=False)

    @pytest.mark.ckan_config("ckanext.doi.publisher", "argh!")
    def test_after_dataset_update(self):
        # as well as testing the after_dataset_update functionality works on some level,
        # this test is also here to confirm that after_dataset_update is called
        # correctly whether you are on CKAN 2.9 or CKAN 2.10.

        # the udpate function has flashes in it which we don't care about
        with patch("ckan.plugins.toolkit.h.flash_success"):
            with patch("ckanext.doi.lib.api.DataCiteMDSClient") as mock_client_class:
                # mock the datacite API to make it look like the DOI generated is new
                mock_client = MagicMock(
                    metadata_get=MagicMock(side_effect=DataCiteNotFoundError())
                )
                mock_client_class.return_value = mock_client

                # create a new dataset
                dataset = factories.Dataset(title="test", author="Author, Test")

                # reset our mock
                mock_client.reset()

                # update the dataset's title, this should trigger after_dataset_update
                call_action("package_patch", id=dataset["id"], title="different")

                # check that attempts have been made to mint the DOI
                assert mock_client.metadata_post.called
                assert mock_client.doi_post.called

    @pytest.mark.ckan_config("ckanext.doi.publisher", "argh!")
    @pytest.mark.ckan_config("ckanext.doi.site_url", "http://dois.are.great.org")
    def test_after_dataset_show(self):
        # as well as testing the after_dataset_show functionality works on some level,
        # this test is also here to confirm that after_dataset_show is called correctly
        # whether you are on CKAN 2.9 or CKAN 2.10.

        with patch("ckanext.doi.lib.api.DataCiteMDSClient") as mock_client_class:
            # mock the datacite API to make it look like the DOI generated is new
            mock_client = MagicMock(
                metadata_get=MagicMock(side_effect=DataCiteNotFoundError())
            )
            mock_client_class.return_value = mock_client

            # create a new dataset
            dataset = factories.Dataset()

        doi = DOIQuery.read_package(dataset["id"], create_if_none=False)
        package = call_action("package_show", id=dataset["id"])
        assert package["doi"] == doi.identifier
        assert package["doi_status"] is False
        assert package["domain"] == "dois.are.great.org"
        assert package["doi_date_published"] is None
        assert package["doi_publisher"] == "argh!"

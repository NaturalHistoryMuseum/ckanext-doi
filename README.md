<!--header-start-->
<img src="https://data.nhm.ac.uk/images/nhm_logo.svg" align="left" width="150px" height="100px" hspace="40"/>

# ckanext-doi

[![Tests](https://img.shields.io/github/actions/workflow/status/NaturalHistoryMuseum/ckanext-doi/main.yml?style=flat-square)](https://github.com/NaturalHistoryMuseum/ckanext-doi/actions/workflows/main.yml)
[![Coveralls](https://img.shields.io/coveralls/github/NaturalHistoryMuseum/ckanext-doi/main?style=flat-square)](https://coveralls.io/github/NaturalHistoryMuseum/ckanext-doi)
[![CKAN](https://img.shields.io/badge/ckan-2.9.9%20%7C%202.10.1-orange.svg?style=flat-square)](https://github.com/ckan/ckan)
[![Python](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue.svg?style=flat-square)](https://www.python.org/)
[![Docs](https://img.shields.io/readthedocs/ckanext-doi?style=flat-square)](https://ckanext-doi.readthedocs.io)

_A CKAN extension for assigning a digital object identifier (DOI) to datasets, using the DataCite DOI service._

<!--header-end-->

# Overview

<!--overview-start-->
This extension assigns a digital object identifier (DOI) to datasets, using the DataCite DOI service.

When a new dataset is created it is assigned a new DOI. This DOI will be in the format:

`https://doi.org/[prefix]/[8 random alphanumeric characters]`

If the new dataset is active and public, the DOI and metadata will be registered with DataCite.

If the dataset is draft or private, the DOI will not be registered with DataCite. When the dataset is made active & public, the DOI will be registered.
This allows datasets to be embargoed, but still provides a DOI to be referenced in publications.

You will need a DataCite account to use this extension.

## DOI Metadata

This extension currently uses [DataCite Metadata Schema v4.2](https://schema.datacite.org/meta/kernel-4.2/index.html).

Dataset package fields and CKAN config settings are mapped to the DataCite Schema with default values, but these can be overwritten by [implementing `IDoi` interface methods](https://ckanext-doi.readthedocs.io/en/latest/usage/#interfaces).

### Required fields

| CKAN Field                    | DataCite Schema |
|-------------------------------|-----------------|
| dataset:title                 | title           |
| dataset:author                | creator         |
| config:ckanext.doi.publisher  | publisher       |
| dataset:metadata_created.year | publicationYear |
| dataset:type                  | resourceType    |

See [`metadata.py`](https://github.com/NaturalHistoryMuseum/ckanext-doi/blob/main/ckanext/doi/lib/metadata.py) for full mapping details.

<!--overview-end-->

# Installation

<!--installation-start-->
Path variables used below:
- `$INSTALL_FOLDER` (i.e. where CKAN is installed), e.g. `/usr/lib/ckan/default`
- `$CONFIG_FILE`, e.g. `/etc/ckan/default/development.ini`

## Installing from PyPI

```shell
pip install ckanext-doi
```

## Installing from source

1. Clone the repository into the `src` folder:
   ```shell
   cd $INSTALL_FOLDER/src
   git clone https://github.com/NaturalHistoryMuseum/ckanext-doi.git
   ```

2. Activate the virtual env:
   ```shell
   . $INSTALL_FOLDER/bin/activate
   ```

3. Install via pip:
   ```shell
   pip install $INSTALL_FOLDER/src/ckanext-doi
   ```

### Installing in editable mode

Installing from a `pyproject.toml` in editable mode (i.e. `pip install -e`) requires `setuptools>=64`; however, CKAN 2.9 requires `setuptools==44.1.0`. See [our CKAN fork](https://github.com/NaturalHistoryMuseum/ckan) for a version of v2.9 that uses an updated setuptools if this functionality is something you need.

## Post-install setup

1. Add 'doi' to the list of plugins in your `$CONFIG_FILE`:
   ```ini
   ckan.plugins = ... doi
   ```

2. Initialise the database:
   ```shell
   ckan -c $CONFIG_FILE doi initdb
   ```

3. This extension will only work if you have signed up for an account with [DataCite](https://datacite.org). You will need a development/test account to use this plugin in test mode, and a live account to mint active DOIs.

<!--installation-end-->

# Configuration

<!--configuration-start-->
These are the options that can be specified in your .ini config file.

## DateCite Credentials **[REQUIRED]**

DataCite Repository account credentials are used to register DOIs. A Repository account is administered by a DataCite Member.

| Name                           | Description                                                                                             | Example    |
|--------------------------------|---------------------------------------------------------------------------------------------------------|------------|
| `ckanext.doi.account_name`     | Your DataCite Repository account name                                                                   | `ABC.DEFG` |
| `ckanext.doi.account_password` | Your DataCite Repository account password                                                               |            |
| `ckanext.doi.prefix`           | The prefix taken from your DataCite Repository account (from your test account if running in test mode) | `10.1234`  |

## Institution Name **[REQUIRED]**

You also need to provide the name of the institution publishing the DOIs (e.g. Natural History Museum).

| Name                    | Description                                    |
|-------------------------|------------------------------------------------|
| `ckanext.doi.publisher` | The name of the institution publishing the DOI |

## Test/Debug Mode **[REQUIRED]**

If test mode is set to true, the DOIs will use the DataCite test site. The test site uses a separate account, so you must also change your credentials and prefix.

| Name                    | Description          | Options    |
|-------------------------|----------------------|------------|
| `ckanext.doi.test_mode` | Enable dev/test mode | True/False |

Note that the DOIs will still display on your web interface as `https://doi.org/YOUR-DOI`, but they _will not resolve_. Log in to your test account to view all your minted test DOIs, or replace `https://doi.org/` with `https://doi.test.datacite.org/dois/` in a single URL to view a specific DOI.

## Other options

| Name                     | Description                                | Default         |
|--------------------------|--------------------------------------------|-----------------|
| `ckanext.doi.site_url`   | Used to build the link back to the dataset | `ckan.site_url` |
| `ckanext.doi.site_title` | Site title to use in the citation          | None            |

<!--configuration-end-->

# Usage

<!--usage-start-->
## Commands

### `doi`

1. `delete-dois`: delete all DOIs from the database (_not_ datacite).
    ```bash
    ckan -c $CONFIG_FILE doi delete-dois
    ```

2. `update-doi`: update the datacite metadata for one or all packages.
    ```bash
    ckan -c $CONFIG_FILE doi update-doi [PACKAGE_ID]
    ```

## Interfaces

The `IDoi` interface allows plugins to extend the `build_metadata_dict` and `build_xml_dict`
methods.

### `build_metadata_dict(pkg_dict, metadata_dict, errors)`

**Breaking changes from v1:**

1. previously called `build_metadata`
2. new parameter: `errors`
3. new return value: tuple of `metadata_dict`, `errors`

Extracts metadata from a pkg_dict for use in generating datacite DOIs. The base method from this extension is run first, then the metadata dict is passed through all the implementations of this method. After running these, if any of the required values (see above) are still in the `errors` dict (i.e. they still could not be handled by any other extension), a `DOIMetadataException` will be thrown.

| Parameter       | Description                                                                                                                                               |
|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `pkg_dict`      | The original package dictionary from which the metadata were extracted.                                                                                   |
| `metadata_dict` | The current metadata dict, created by the ckanext-doi extension and any previous plugins implementing IDoi.                                               |
| `errors`        | A dictionary of metadata keys and errors generated by previous plugins; this method should remove any keys that it successfully processes and overwrites. |

### `build_xml_dict(metadata_dict, xml_dict)`

**Breaking changes from v1:**

1. previously called `metadata_to_xml`
2. parameters rearranged (previously `xml_dict`, `metadata`)

Converts the metadata_dict into an xml_dict that can be passed to the `datacite` library's `schema42.tostring()` and `schema42.validate()` methods. The base method from this extension is run first, then the xml dict is passed through all the implementations of this method.

| Parameter       | Description                                                                                            |
|-----------------|--------------------------------------------------------------------------------------------------------|
| `metadata_dict` | The original metadata dictionary from which the xml attributes are extracted.                          |
| `xml_dict`      | The current xml dict, created by the ckanext-doi extension and any previous plugins implementing IDoi. |

## Templates

### Package citation snippet

```html+jinja
{% snippet "doi/snippets/package_citation.html", pkg_dict=g.pkg_dict %}
```

### Resource citation snippet

```html+jinja
{% snippet "doi/snippets/resource_citation.html", pkg_dict=g.pkg_dict, res=res %}
```

<!--usage-end-->

# Testing

<!--testing-start-->
There is a Docker compose configuration available in this repository to make it easier to run tests. The ckan image uses the Dockerfile in the `docker/` folder.

To run the tests can be run against ckan 2.9.x and 2.10.x on Python3:

1. Build the required images:
   ```shell
   docker-compose build
   ```

2. Then run the tests.
   The root of the repository is mounted into the ckan container as a volume by the Docker compose configuration, so you should only need to rebuild the ckan image if you change the extension's dependencies.
   ```shell
   # run tests against ckan 2.9.x
   docker-compose run latest

   # run tests against ckan 2.10.x
   docker-compose run next
   ```

Note that the tests mock the DataCite API and therefore don't require an internet connection nor your DataCite credentials to run.

<!--testing-end-->

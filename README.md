<img src=".github/nhm-logo.svg" align="left" width="150px" height="100px" hspace="40"/>

# ckanext-doi

[![Travis](https://img.shields.io/travis/NaturalHistoryMuseum/ckanext-doi/master.svg?style=flat-square)](https://travis-ci.org/NaturalHistoryMuseum/ckanext-doi)
[![Coveralls](https://img.shields.io/coveralls/github/NaturalHistoryMuseum/ckanext-doi/master.svg?style=flat-square)](https://coveralls.io/github/NaturalHistoryMuseum/ckanext-doi)
[![CKAN](https://img.shields.io/badge/ckan-2.9.1-orange.svg?style=flat-square)](https://github.com/ckan/ckan)
[![Python](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue.svg?style=flat-square)](https://www.python.org/)

_A CKAN extension for assigning a digital object identifier (DOI) to datasets, using the DataCite DOI service._


# Overview

This extension assigns a digital object identifier (DOI) to datasets, using the DataCite DOI service.

When a new dataset is created it is assigned a new DOI. This DOI will be in the format:

`https://doi.org/[prefix]/[8 random alphanumeric characters]`

If the new dataset is active and public, the DOI and metadata will be registered with DataCite.

If the dataset is draft or private, the DOI will not be registered with DataCite.  When the dataset is made active & public, the DOI will be submitted.
This allows datasets to be embargoed, but still provides a DOI to be referenced in publications.

You will need an account with a DataCite DOI service provider to use this extension.

## DOI Metadata
Uses [DataCite Metadata Schema v4.2](https://schema.datacite.org/meta/kernel-4.2/index.html).

Dataset package fields and CKAN config settings are mapped to the DataCite Schema with default values, but these can be overwritten by implementing `IDoi` interface methods.

### Required fields

|CKAN Field                         |DataCite Schema
|---                                | ---
|dataset:title                      |title
|dataset:author                     |creator
|config:ckanext.doi.publisher       |publisher
|dataset:metadata_created.year      |publicationYear
|dataset:type                       |resourceType

See [`metadata.py`](./ckanext/doi/lib/metadata.py) for full mapping details.

# Installation

Path variables used below:
- `$INSTALL_FOLDER` (i.e. where CKAN is installed), e.g. `/usr/lib/ckan/default`
- `$CONFIG_FILE`, e.g. `/etc/ckan/default/development.ini`

1. Clone the repository into the `src` folder:

  ```bash
  cd $INSTALL_FOLDER/src
  git clone https://github.com/NaturalHistoryMuseum/ckanext-doi.git
  ```

2. Activate the virtual env:

  ```bash
  . $INSTALL_FOLDER/bin/activate
  ```

3. Install the requirements from requirements.txt:

  ```bash
  cd $INSTALL_FOLDER/src/ckanext-doi
  pip install -r requirements.txt
  ```

4. Run setup.py:

  ```bash
  cd $INSTALL_FOLDER/src/ckanext-doi
  python setup.py develop
  ```

5. Add 'doi' to the list of plugins in your `$CONFIG_FILE`:

  ```ini
  ckan.plugins = ... doi
  ```


# Configuration

There are a number of options that can be specified in your .ini config file.

## DateCite Credentials **[REQUIRED]**

These will be given to you by your DataCite provider.

```ini
ckanext.doi.account_name = DATACITE-ACCOUNT-NAME
ckanext.doi.account_password = DATACITE-ACCOUNT-PASSWORD
ckanext.doi.prefix = DATACITE-PREFIX
```

## Institution Name **[REQUIRED]**

You also need to provide the name of the institution publishing the DOIs (e.g. Natural History Museum).

```ini
ckanext.doi.publisher = PUBLISHING-INSTITUTION
```

## Test/Debug Mode **[REQUIRED]**

If test mode is set to true, the DOIs will use the DataCite test prefix 10.5072.

```ini
ckanext.doi.test_mode = True or False
```

## Other options

Name|Description|Default
--|---|--
`ckanext.doi.site_url`|Used to build the link back to the dataset|`ckan.site_url`
`ckanext.doi.site_title`|Site title to use in the citation|


# Further Setup

This extension will only work if you have signed up for an account with [DataCite](https://datacite.org).

You will need a development/test account to use this plugin in test mode, and a live account to mint active DOIs.


# Usage

## Commands

### `doi`

1. `delete-dois`: delete all DOIs from the database (_not_ datacite).
    ```bash
    paster --plugin=ckanext-doi doi delete-dois -c $CONFIG_FILE
    ```

2. `update-doi`: update the datacite metadata for one or all packages.
    ```bash
    paster --plugin=ckanext-doi doi update-doi [PACKAGE_ID] -c $CONFIG_FILE
    ```

## Interfaces

The `IDoi` interface allows plugins to extend the `build_metadata_dict` and `build_xml_dict` methods.

### `build_metadata_dict(pkg_dict, metadata_dict, errors)`
**Breaking changes from v1:**
1. previously called `build_metadata`
2. new parameter: `errors`
3. new return value: tuple of `metadata_dict`, `errors`

Extracts metadata from a pkg_dict for use in generating datacite DOIs. The base method from this extension is run first, then the metadata dict is passed through all the implementations of this method. After running these, if any of the required values (see above) are still in the `errors` dict (i.e. they still could not be handled by any other extension), a `DOIMetadataException` will be thrown.

Parameter|Description
---------|-----------
`pkg_dict`|The original package dictionary from which the metadata were extracted.
`metadata_dict`|The current metadata dict, created by the ckanext-doi extension and any previous plugins implementing IDoi.
`errors`|A dictionary of metadata keys and errors generated by previous plugins; this method should remove any keys that it successfully processes and overwrites.


### `build_xml_dict(metadata_dict, xml_dict)`
**Breaking changes from v1:**
1. previously called `metadata_to_xml`
2. parameters rearranged (previously `xml_dict`, `metadata`)

Converts the metadata_dict into an xml_dict that can be passed to the datacite library's schema42.tostring() and schema42.validate() methods. The base method from this extension is run first, then the xml dict is passed through all the implementations of this method.

Parameter|Description
---------|-----------
`metadata_dict`|The original metadata dictionary from which the xml attributes are extracted.
`xml_dict`|The current xml dict, created by the ckanext-doi extension and any previous plugins implementing IDoi.


## Templates

### Package citation snippet
```html+jinja
{% snippet "doi/snippets/package_citation.html", pkg_dict=g.pkg_dict %}
```

### Resource citation snippet
```html+jinja
{% snippet "doi/snippets/resource_citation.html", pkg_dict=g.pkg_dict, res=res %}
```


# Testing
_Test coverage is currently extremely limited._

To run the tests in this extension, there is a Docker compose configuration available in this
repository to make it easy.

To run the tests against ckan 2.9.x on Python3:

1. Build the required images
```bash
# first build the containers
docker-compose build
```

2. Then run the tests.
   The root of the repository is mounted into the ckan container as a volume by the Docker compose
   configuration, so you should only need to rebuild the ckan image if you change the extension's
   dependencies.
```bash
docker-compose run ckan
```

The ckan image uses the Dockerfile in the `docker/` folder which is based on `openknowledge/ckan-dev:2.9`.

Note that currently the tests mock the Datacite API and therefore don't require an internet
connection nor your Datacite credentials to run.

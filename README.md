<img src=".github/nhm-logo.svg" align="left" width="150px" height="100px" hspace="40"/>

# ckanext-doi

[![Travis](https://img.shields.io/travis/NaturalHistoryMuseum/ckanext-doi/master.svg?style=flat-square)](https://travis-ci.org/NaturalHistoryMuseum/ckanext-doi)
[![Coveralls](https://img.shields.io/coveralls/github/NaturalHistoryMuseum/ckanext-doi/master.svg?style=flat-square)](https://coveralls.io/github/NaturalHistoryMuseum/ckanext-doi)
[![CKAN](https://img.shields.io/badge/ckan-2.9.0a-orange.svg?style=flat-square)](https://github.com/ckan/ckan)

_A CKAN extension for assigning a digital object identifier (DOI) to datasets, using the DataCite DOI service._


# Overview

This extension assigns a digital object identifier (DOI) to datasets, using the DataCite DOI service.

When a new dataset is created it is assigned a new DOI. This DOI will be in the format:

`https://doi.org/[prefix]/[random 7 digit integer]`

If the new dataset is active and public, the DOI and metadata will be registered with DataCite.

If the dataset is draft or private, the DOI will not be registered with DataCite.  When the dataset is made active & public, the DOI will be submitted.
This allows datasets to be embargoed, but still provides a DOI to be referenced in publications.     

You will need an account with a DataCite DOI service provider to use this extension.

## DOI Metadata
Uses DataCite Metadata Schema v 3.1 https://schema.datacite.org/meta/kernel-3.1/index.html

Dataset package fields and CKAN config settings are mapped to the DataCite Schema  

|CKAN Dataset Field                 |DataCite Schema
|--- | ---
|dataset:title                      |title
|dataset:creator                    |author
|config:ckanext.doi.publisher       |publisher
|dataset:notes                      |description
|resource formats                   |format
|dataset:tags                       |subject
|dataset:licence (title)            |rights
|dataset:version                    |version
|dataset:extras spacial             |geo_box


DataCite title and author are mandatory metadata fields, so dataset title and creator fields are made required fields.
This has been implemented in the theme layer, with another check in IPackageController.after_update, which raises a DOIMetadataException if the title or author fields do not exist.

It is recommended plugins implementing DOIs add additional validation checks to their schema.


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

## Test/Deug Mode **[REQUIRED]**

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

1. `delete-tests`: delete all test DOIs.
    ```bash
    paster --plugin=ckanext-doi doi delete-tests -c $CONFIG_FILE
    ```

## Interfaces

This plugin implements a build_metadata interface, so the metadata can be customised.
See [ckanext-nhm](https://github.com/NaturalHistoryMuseum/ckanext-nhm) for an implementation of this interface.

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

To run the tests, use nosetests inside your virtualenv. The `--nocapture` flag will allow you to see the debug statements.
```bash
nosetests --ckan --with-pylons=$TEST_CONFIG_FILE --where=$INSTALL_FOLDER/src/ckanext-doi --nologcapture --nocapture
```

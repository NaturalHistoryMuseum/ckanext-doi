ckanext-doi
===========

Overview
--------

CKAN extension for assigning a digital object identifier (DOI) to datasets, using the DataCite DOI service.

When a new dataset is created it is assigned a new DOI. This DOI will be in the format:
 
http://dx.doi.org/[prefix]/[random 7 digit integer]

If the new dataset is active and public, the DOI and metadata will be registered with DataCite.
 
If the dataset is draft or private, the DOI will not be registered with DataCite.  When the dataset is made active & public, the DOI will be submitted. 
This allows datasets to be embargoed, but still provides a DOi to be referenced in publications.     

You will need an account with a DataCite DOI service provider to use this extension.

Installation
------------

This extension can be installed in the same way as any other - download it, activate it and enable the plugin. http://docs.ckan.org/en/latest/extensions/tutorial.html#installing-the-extension

However it will only work if you have signed up for an account with DataCite.  

You will need a development / test account to use this plugin in test mode.  And to mint active DOIs you will need a live DataCite account.


DOI Metadata
------------

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
This has been implemented in the theme layer, with another check in IPackageController.after_update, which raises
an exception if the title or author fields do not exist. 

It is recommended plugins implementing DOIs add additional validation checks to their schema.


This plugin implements a build_metadata interface, so the metadata can be customised.
 
See [Natural History Museum extension](https://github.com/NaturalHistoryMuseum/ckanext-nhm) for an implementation of this interface. 


Configuration
-------------

```python
ckanext.doi.account_name =
ckanext.doi.account_password =
ckanext.doi.prefix = 
ckanext.doi.publisher = 
ckanext.doi.test_mode = True or False
ckanext.doi.site_url =  # Defaults to ckan.site_url if not set 
ckanext.doi.site_title = # Optional - site title to use in the citation - eg Natural History Museum Data Portal (data.nhm.ac.uk)
```

Account name, password and prefix will be provided by your DataCite provider.
 
Publisher is the name of the publishing institution - eg: Natural History Museum.

The site URL is used to build the link back to the dataset:

http://[site_url]/datatset/package_id

If site_url is not set, ckan.site_url will be used instead.


If test mode is set to true, the DOIs will use the DataCite test prefix 10.5072

To delete all test prefixes, use the command:

```python
paster doi delete-tests -c /etc/ckan/default/development.ini
```

Releases
--------

### 0.1

Initial release

### 0.2

A DOI will be created regardless od Dataset status. 
Only when a dataset is active and public will the DOI and MetaData be published to DataCite.

Removed locking of DOI metadata fields after 10 days.  This is an interim solution before implementing DOI versioning. 

Added build_metadata interface (and moved custom NHM metadata fields to ckanext-nhm).

Added schema migration command.


Upgrade notes
-------------

### 0.2

Requires a schema change 001 & 002 - adds DOI published date and removes DOI created columns. See ckanext.doi.migration

Run with:

```python
paster doi upgrade-db -c /etc/ckan/default/development.ini
```

Roadmap
-------

Features planned for development.

1. DOI versioning - allow option to create a new DOI on update (or if core metadata fields are updated).  This new DOI will be linked to the master/original DOI.

2. Embargoed for set length of time. User can select date on which the dataset is to be made public, and the DOI submitted to DataCite. 
 
3. Tests. There are no tests.

ckanext-doi
===========

Overview
--------

CKAN extension for assigning a digital object identifier (DOI) to datasets, using DataCite DOI service.

When a new dataset is created it will be assigned a new DOI. This DOI will be in the format:
 
http://dx.doi.org/[prefix]/[random 7 digit integer]

If the new dataset is active and public, the DOI will be registered with DataCite.
 
If the dataset is draft or private, the DOI will not be registered with DataCite. 
When the dataset is made active & public, the DOI will be submitted. 
This allows datasets to be embargoed, but still provides a DOi to be referenced in publications.     

You will need an account with a DataCite DOI service provider to use this extension.


DOI Metadata
------------

Uses DataCite Metadata Schema v 3.1 https://schema.datacite.org/meta/kernel-3.1/index.html

Dataset package fields and CKAN config settings are mapped to the DataCite Schema  

|CKAN Dataset Field                 |DataCite Schema
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

ckanext.doi.account_name 
ckanext.doi.account_password
ckanext.doi.publisher = 
ckanext.doi.prefix = 
ckanext.doi.test_mode = True or False
ckanext.doi.site_url =  # Defaults to ckan.site_url if not set 


If test mode is set to true, the DOIs will use the DataCite test prefix 10.5072

To delete all 

paster delete-test-doi -c /etc/ckan/default/development.ini

Enable the module

Releases
--------

### 0.1

Initial release

### 0.2

Added dataset embargoing. If a dataset is created in draft or not

Removed locking of 

Release notes 




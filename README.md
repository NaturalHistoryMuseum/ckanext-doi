ckanext-doi
===========

CKAN extension for assigning a digital object identifier (DOI) to datasets

ckanext.doi.account_name 
ckanext.doi.account_password
ckanext.doi.publisher = 
ckanext.doi.prefix = 
ckanext.doi.test_mode = True or False
ckanext.doi.site_url =  # Defaults to ckan.site_url if not set 

On launch, delete all test DOIs:

paster delete-test-doi -c /etc/ckan/default/development.ini



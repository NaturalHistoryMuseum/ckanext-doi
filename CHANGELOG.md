# Changelog

(This file may not be historically complete, as it is a recent addition to the project).

## Roadmap

Features planned for development.

1. DOI versioning - allow option to create a new DOI on update (or if core metadata fields are updated).  This new DOI will be linked to the master/original DOI.

2. Embargoed for set length of time. User can select date on which the dataset is to be made public, and the DOI submitted to DataCite.

3. Tests. There are no tests.


## [1.0.0-alpha] - 2019-07-23

- Updated to work with CKAN 2.9.0a, e.g.:
    - uses toolkit wherever possible
    - references to Pylons removed
- Standardised README, CHANGELOG, setup.py and .github files to match other Museum extensions


## 0.2

- A DOI will be created regardless of Dataset status.
  - Only when a dataset is active and public will the DOI and MetaData be published to DataCite.
- Removed locking of DOI metadata fields after 10 days.  This is an interim solution before implementing DOI versioning.
- Added build_metadata interface (and moved custom NHM metadata fields to ckanext-nhm).
- Added schema migration command.r

### Upgrade notes

Requires a schema change 001 & 002 - adds DOI published date and removes DOI created columns. See ckanext.doi.migration


## 0.1

- Initial release

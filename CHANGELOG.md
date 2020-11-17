# Changelog

(This file may not be historically complete, as it is a recent addition to the project).

## Roadmap

Features planned for development.

1. DOI versioning - allow option to create a new DOI on update (or if core metadata fields are updated).  This new DOI will be linked to the master/original DOI.

2. Embargoed for set length of time. User can select date on which the dataset is to be made public, and the DOI submitted to DataCite.

3. Tests. There are no tests.

## [2.0.0-alpha] - 2020-11-12

- Refactored to organise the code better and align with similar extensions like [`ckanext-query-dois`](https://github.com/NaturalHistoryMuseum/ckanext-query-dois)
- Now uses [datacite](https://github.com/inveniosoftware/datacite) Python library
- Uses Datacite [schema 4.2](https://schema.datacite.org/meta/kernel-4.2)
- Breaking `IDoi` interface changes:
    - `build_metadata` changed to `build_metadata_dict`
    - `build_metadata_dict` has additional `errors` parameter and return value (a dict of metadata keys and any errors encountered while attempting to retrieve a value)
    - `metadata_to_xml` changed to `build_xml_dict` (because it wasn't actually creating any xml)
    - `build_xml_dict` parameters rearranged (to better match `build_metadata_dict`)
    - the dict used is now the `package_show` dict instead of the `package_update` dict because it has more information
- Changes in metadata are checked directly against the xml stored in Datacite
- New command for updating datacite metadata without updating the package: `update-doi`


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

# Changelog

## v4.0.2 (2025-06-09)

### Fix

- remove auto-added pyproject fields

## v4.0.1 (2025-06-09)

### Build System(s)

- add ruff lint select rules
- remove pylint, add ruff lint ignore rules
- update ckantools

### CI System(s)

- set ruff target py version, add more ignores - avoid using fixes that don't work for python 3.8 (our current version) - ignore recommended ruff formatter conflicts - ignore more docstring rules
- update pre-commit repo versions

## v4.0.0 (2025-03-17)

### Breaking Changes

- switch to alembic migration scripts

## v3.1.17 (2024-11-04)

### Docs

- use variable logo based on colour scheme
- fix tests badge tests workflow file was renamed

## v3.1.16 (2024-11-04)

### Docs

- standardise returns field

### Style

- automatic reformat auto reformat with ruff/docformatter/prettier after config changes

### Build System(s)

- update ckantools version
- remove version from docker compose file version specifier is deprecated

### CI System(s)

- fix python setup action version
- add merge to valid commit types
- add docformatter args and dependency docformatter currently can't read from pyproject.toml without tomli
- only apply auto-fixes in pre-commit F401 returns linting errors as well as auto-fixes, so this disables the errors and just applies the fixes
- update tool config update pre-commit repo versions and switch black to ruff
- add pull request validation workflow new workflow to check commit format and code style against pre-commit config
- update workflow files standardise format, change name of tests file

### Chores/Misc

- add pull request template
- update tool details in contributing guide

## v3.1.15 (2024-08-20)

## v3.1.14 (2024-06-10)

### Fix

- use first two chars of ckan lang code

## v3.1.13 (2024-05-07)

### Fix

- update rightsList fields to match datacite schema

## v3.1.12 (2024-02-13)

### Fix

- correct casing for schemeURI property

## v3.1.11 (2024-01-15)

### Docs

- update readme to clarify wording, fix links, and fix whitespace

### Chores/Misc

- add build section to read the docs config

## v3.1.10 (2023-12-04)

### Fix

- update ckantools to patch bug with get_setting
- add helper to correctly determine test mode status

### Style

- use single quotes

### Chores/Misc

- add regex for version line in citation file
- add citation.cff to list of files with version
- add contributing guidelines
- add code of conduct
- add citation file
- update support.md links

## v3.1.9 (2023-09-25)

### Fix

- add new functions to support CKAN 2.10

### Docs

- update docs with updated test info

### Tests

- add tests to confirm plugin CKAN 2.9/2.10 differences work ok
- move with_doi_table fixture to conftest so others can use
- add testing on ckan 2.10.x as well as 2.9.x

### CI System(s)

- switch back to a single workflow test file but with multiple jobs
- run CI tests against ckan 2.9.x and 2.10.x

## v3.1.8 (2023-07-17)

### Docs

- update logos

## v3.1.7 (2023-04-11)

### Build System(s)

- fix postgres not loading when running tests in docker

### Chores/Misc

- add action to sync branches when commits are pushed to main

## v3.1.6 (2023-02-20)

### Docs

- fix api docs generation script

### Chores/Misc

- small fixes to align with other extensions

## v3.1.5 (2023-01-31)

### Docs

- **readme**: change logo url from blob to raw

## v3.1.4 (2023-01-31)

### Docs

- **readme**: direct link to logo in readme
- **readme**: fix github actions badge

## v3.1.3 (2023-01-30)

### Build System(s)

- **docker**: use 'latest' tag for test docker image

## v3.1.2 (2022-12-12)

### Style

- change quotes in setup.py to single quotes

### Build System(s)

- include top-level data files in theme folder
- add package data

## v3.1.1 (2022-12-01)

### Docs

- **readme**: format test section
- **readme**: update installation steps, add test mode details

## v3.1.0 (2022-11-28)

### Fix

- change case on plugin name
- unpin ckantools version

### Docs

- fix markdown-include references
- add section delimiter

### Style

- apply formatting changes

### Build System(s)

- set changelog generation to incremental
- pin ckantools minor version
- add include-markdown plugin to mkdocs

### CI System(s)

- add cz_nhm dependency
- **commitizen**: fix message template
- add pypi release action

### Chores/Misc

- clear old changelog
- use cz_nhm commitizen config
- improve commitizen message template
- move cz config into separate file
- standardise package files

## v3.0.7 (2022-06-20)

## v3.0.6 (2022-05-23)

## v3.0.5 (2022-05-17)

## v3.0.4 (2022-03-03)

## v3.0.3 (2021-04-15)

## v3.0.1 (2021-04-01)

## v3.0.0 (2021-03-09)

## v2.0.2 (2020-11-25)

## v1.0.0-alpha (2019-07-23)

## v0.0.3 (2018-05-08)

## v0.0.2 (2018-01-09)

## v0.0.1 (2017-08-24)

..
    This file is part of Invenio.
    Copyright (C) 2015-2026 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 4.0.0 (2026-03-01)
---------------------------

**Major version bump aligning the meta-package with the current Invenio
ecosystem.**

The ``invenio`` meta-package pins were 2--6 major versions behind every
module it bundled. Applications (``invenio-app-rdm``, ``invenio-app-ils``)
had already migrated to modern module versions independently. This release
brings the meta-package in line with the active ecosystem.

Breaking changes:

- All module pins updated to current major versions (see table below).
  Users on ``invenio==3.4.x`` who depend on v1.x module APIs must migrate.
- Dropped ``invenio-iiif`` from the ``files`` bundle (removed upstream).
- Dropped ``elasticsearch5`` and ``elasticsearch6`` extras (both EOL).
- Minimum Python version raised to 3.9 (from 3.6).
- Minimum ``invenio-db`` raised to 2.0 (from 1.0).
- Minimum ``invenio-search`` raised to 3.0 (from 1.4).

New features:

- Added ``opensearch1`` and ``opensearch2`` extras for OpenSearch support.
- Added ``python_requires='>=3.9'`` to prevent installation on EOL Python.

Module version changes:

- ``invenio-app``: 1.3 -> 3.0
- ``invenio-base``: 1.2 -> 2.1
- ``invenio-cache``: 1.1 -> 3.0
- ``invenio-celery``: 1.2 -> 2.0
- ``invenio-i18n``: 1.3 -> 3.0
- ``invenio-admin``: 1.3 -> 1.6
- ``invenio-assets``: 1.2 -> 4.0
- ``invenio-formatter``: 1.1 -> 4.0
- ``invenio-logging``: 1.3 -> 4.0
- ``invenio-mail``: 1.0 -> 2.0
- ``invenio-rest``: 1.2 -> 3.0
- ``invenio-theme``: 1.3 -> 4.0
- ``invenio-access``: 1.4 -> 5.0
- ``invenio-accounts``: 1.4 -> 7.0
- ``invenio-oauth2server``: 1.3 -> 4.0
- ``invenio-oauthclient``: 1.5 -> 7.0
- ``invenio-userprofiles``: 1.2 -> 5.0
- ``invenio-indexer``: 1.2 -> 4.0
- ``invenio-jsonschemas``: 1.1 -> 2.0
- ``invenio-oaiserver``: 1.4 -> 4.0
- ``invenio-pidstore``: 1.2 -> 3.0
- ``invenio-records-rest``: 1.9 -> 4.0
- ``invenio-records-ui``: 1.2 -> 3.0
- ``invenio-records``: 1.6 -> 4.0
- ``invenio-search-ui``: 2.0 -> 4.0
- ``invenio-files-rest``: 1.3 -> 4.0
- ``invenio-previewer``: 1.3 -> 4.0
- ``invenio-records-files``: 1.2 -> 2.0
- ``invenio-db``: 1.0 -> 2.0
- ``invenio-search``: 1.4 -> 3.0
- ``pytest-invenio``: 1.4 -> 4.0

CI/CD modernization:

- GitHub Actions: ``actions/checkout@v4``, ``actions/setup-python@v5``,
  ``actions/cache@v4``
- Runner: ``ubuntu-latest`` (was ``ubuntu-20.04``)
- Python test matrix: 3.9, 3.10, 3.11, 3.12 (was 3.7, 3.8, 3.9)
- Database matrix: PostgreSQL 13/16, MySQL 8 (dropped PostgreSQL 10,
  MySQL 5)
- Search matrix: Elasticsearch 7, OpenSearch 2 (was Elasticsearch 7 only)
- PyPI publish workflow modernized with security fixes
- Added ``SECURITY.md`` vulnerability reporting policy

Version 3.5.0a4 (2022-02-28)
-----------------------------

- Alpha pre-release, never stabilised.

Version 3.4.1 (2021-05-12)
---------------------------

- Last stable release of the 3.x series.

Version 3.4.0 (2020-12-17)
---------------------------

- Added support for Elasticsearch 7.

Version 3.3.0 (2020-05-15)
---------------------------

- Invenio v3.3 release.

Version 3.2.1 (2020-05-11)
---------------------------

- Minor fix release.

Version 3.1.0 (2019-03-12)
---------------------------

- Invenio v3.1 release.

Version 3.0.0 (2019-03-12)
---------------------------

- Invenio v3.0 release. Complete rewrite from Invenio v1/v2.

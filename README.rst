..
    This file is part of Invenio.
    Copyright (C) 2015-2026 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


==================
 Invenio Framework
==================

**Open Source framework for large-scale digital repositories.**

.. image:: https://img.shields.io/github/license/inveniosoftware/invenio.svg
    :target: https://github.com/inveniosoftware/invenio/blob/master/LICENSE

.. image:: https://img.shields.io/badge/Discord-join%20chat-%237289da
    :target: https://discord.gg/8qatqBC

Invenio Framework is like a Swiss Army knife of battle-tested, safe and secure
modules providing you with all the features you need to build a trusted digital
repository.

What is this package?
---------------------

The ``invenio`` package on PyPI is a **meta-package** -- it does not contain
application code itself. Instead, it bundles together the 30+ individual
Invenio modules (``invenio-records``, ``invenio-search``,
``invenio-accounts``, etc.) into curated installation extras so you can
install a coherent, tested set of dependencies with a single command::

    pip install invenio[base,auth,metadata,files,postgresql,opensearch2]

The individual modules are developed and released independently. This
meta-package defines which versions are known to work together.

Applications built on Invenio
-----------------------------

`InvenioRDM <https://inveniosoftware.org/products/rdm/>`_
    Turn-key Research Data Management platform. The most actively developed
    Invenio application. Install via ``invenio-app-rdm``.

`InvenioILS <https://inveniosoftware.org/products/ils/>`_
    Modern Integrated Library System. Install via ``invenio-app-ils``.

Both applications manage their own dependency sets and do not require
installing the ``invenio`` meta-package directly.

Installation extras
-------------------

+------------------+---------------------------------------------+
| Extra            | What it installs                            |
+==================+=============================================+
| ``base``         | Admin, assets, logging, mail, REST, theming |
+------------------+---------------------------------------------+
| ``auth``         | Access control, accounts, OAuth             |
+------------------+---------------------------------------------+
| ``metadata``     | Records, indexing, OAI-PMH, search UI       |
+------------------+---------------------------------------------+
| ``files``        | File storage, preview, records-files bridge |
+------------------+---------------------------------------------+
| ``postgresql``   | PostgreSQL database backend                 |
+------------------+---------------------------------------------+
| ``mysql``        | MySQL database backend                      |
+------------------+---------------------------------------------+
| ``opensearch2``  | OpenSearch 2.x search backend               |
+------------------+---------------------------------------------+
| ``opensearch1``  | OpenSearch 1.x search backend               |
+------------------+---------------------------------------------+
| ``elasticsearch7``| Elasticsearch 7.x search backend           |
+------------------+---------------------------------------------+

See examples on https://inveniosoftware.org/products/framework/ and
https://inveniosoftware.org/showcase/.

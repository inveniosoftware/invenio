..
    This file is part of Invenio.
    Copyright (C) 2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _bundles:

Bundles
=======
Invenio is a highly modular framework with many modules that provide various
different functionality. We are packing related modules into bundles which is
released together at the same time.

Each module has a separate documentation which you can find linked below.

Base bundle
-----------
The base bundle contains all modules related to the generic web application.
This includes the Flask/Celery application factories, configuration management,
I18N, logging, database management, assets/theme management, mail handling and
administration interface.

Included modules:

- `invenio-admin <https://invenio-admin.readthedocs.io>`_
    - Administration interface for Invenio based on Flask-Admin.
- `invenio-app <https://invenio-app.readthedocs.io>`_
    - Flask, WSGI, Celery and CLI applications for Invenio including
      security-related headers and rate limiting.
- `invenio-assets <https://invenio-assets.readthedocs.io>`_
    - Static files management and Webpack integration for Invenio.
- `invenio-base <https://invenio-base.readthedocs.io>`_
    - Flask application factories implementing the application loading patterns
      with entry points in Invenio.
- `invenio-cache <https://invenio-cache.readthedocs.io>`_
    - Caching module for Invenio, supporting Redis and Memcached as backends.
- `invenio-celery <https://invenio-celery.readthedocs.io>`_
    - Task discovery and default configuration of Celery for Invenio.
- `invenio-config <https://invenio-config.readthedocs.io>`_
    - Configuration loading pattern responsible for loading configuration from
      Python modules, instance folder and environment variables.
- `invenio-db <https://invenio-db.readthedocs.io>`_
    - Database connection management for Invenio.
- `invenio-formatter <https://invenio-formatter.readthedocs.io>`_
    - Jinja template engine utilities for Invenio.
- `invenio-i18n <https://invenio-i18n.readthedocs.io>`_
    - I18N utilities like user locale detection, message catalog merging and
      views for language change.
- `invenio-logging <https://invenio-logging.readthedocs.io>`_
    - Configuration of logging to both console, files and log aggregation
      engines like `sentry.io <https://sentry.io/>`_
- `invenio-mail <https://invenio-mail.readthedocs.io>`_
    - Mail sending for Invenio using Flask-Mail.
- `invenio-rest <https://invenio-rest.readthedocs.io>`_
    - REST API utilities including Cross Origin Resource Sharing (CORS) and
      Content Negotiation versioning support.
- `invenio-theme <https://invenio-theme.readthedocs.io>`_
    - Jinja templates implementing a basic theme for Invenio as well as menus
      and breadcrumbs support.
- `docker-invenio <https://docker-invenio.readthedocs.io>`_
    - Docker base images based on CentOS 7 for Invenio.
- `pytest-invenio <https://pytest-invenio.readthedocs.io>`_
    - Testing utilities for Invenio modules and applications.

Auth bundle
-----------
The auth bundle contains all modules related to account and access management,
user profiles, session management and OAuth (provider and client)

Included modules:

- `invenio-access <https://invenio-access.readthedocs.io>`_
    - Role Based Access Control (RBAC) with object level permissions.
- `invenio-accounts <https://invenio-accounts.readthedocs.io>`_
    - User/role management, registration, password recovery, email
      verification, session theft protection, strong cryptographic hashing of
      passwords, hash migration, session activity tracking and CSRF protection
      of REST API via JSON Web Tokens.
- `invenio-oauth2server <https://invenio-oauth2server.readthedocs.io>`_
    - OAuth 2.0 Provider for REST API authentication via access tokens.
- `invenio-oauthclient <https://invenio-oauthclient.readthedocs.io>`_
    - User identity management and support for login via ORCID, GitHub, Google
      or other OAuth providers.
- `invenio-userprofiles <https://invenio-userprofiles.readthedocs.io>`_
    - User profiles for integration into registration forms.

The modules relies heavily on a suite of open source community projects:

- `flask-security <https://pythonhosted.org/Flask-Security/>`_
- `flask-login <https://flask-login.readthedocs.io/>`_
- `flask-principal <https://pythonhosted.org/Flask-Principal/>`_
- `flask-oauthlib <https://flask-oauthlib.readthedocs.io/>`_
- `passlib <https://passlib.readthedocs.io/en/stable/>`_

Metadata bundle
---------------
The metadata bundle contains all modules related to records and metadata
management including e.g. records storage, persistent identifier management,
search engine indexing, an OAI-PMH server and REST APIs for records.

Included modules:

- `invenio-indexer <https://invenio-indexer.readthedocs.io>`_
    - Highly scalable record bulk indexing.
- `invenio-jsonschemas <https://invenio-jsonschemas.readthedocs.io>`_
    - JSONSchema registry for Invenio.
- `invenio-oaiserver <https://invenio-oaiserver.readthedocs.io>`_
    - OAI-PMH server implementation for Invenio.
- `invenio-pidstore <https://invenio-pidstore.readthedocs.io>`_
    - Management, registration and resolution of persistent identifiers
      including e.g DOIs.
- `invenio-records <https://invenio-records.readthedocs.io>`_
    - JSON document storage with revision history and JSONSchema validation.
- `invenio-records-rest <https://invenio-records-rest.readthedocs.io>`_
    - REST APIs for search and CRUD operations on records and persistent
      identifiers.
- `invenio-records-ui <https://invenio-records-ui.readthedocs.io>`_
    - User interface for displaying records.
- `invenio-search <https://invenio-search.readthedocs.io>`_
    - Elasticsearch integration module for Invenio.
- `invenio-search-js <https://inveniosoftware.github.io/invenio-search-js/>`_
    - AngularJS search application for displaying records from the REST API.
- `invenio-search-ui <https://invenio-search-ui.readthedocs.io>`_
    - User interface for searching records.

Files bundle
------------

The files bundle contains all modules related to files management,
an object storage REST API, storage backends, file previewers,
IIIF image APIs and an integration layer between files and records.

Included modules:

- `invenio-files-rest <https://invenio-files-rest.readthedocs.io>`_
    - Object storage REST API for Invenio with many supported backend storage
      protocols and file integrity checking.
- `invenio-iiif <https://invenio-iiif.readthedocs.io>`_
    - International Image Interoperability Framework (IIIF) server for making
      thumbnails and zooming images.
- `invenio-previewer <https://invenio-previewer.readthedocs.io>`_
    - Previewer for Markdown, JSON/XML, CSV, PDF, JPEG, PNG, TIFF, GIF and ZIP
      files.
- `invenio-records-files <https://invenio-records-files.readthedocs.io>`_
    - Integration layer between object storage and records.

Statistics bundle (beta)
------------------------

.. note::

    This bundle is in beta. The modules are being used in production systems
    but are still missing some minor changes as well as documentation.

The statistics bundle contains all modules related to counting statistics such
as file downloads, record views or any other type of events. It supports the
COUNTER Code of Practice as well as Making Data Count Code of Practice
including e.g. double-click detection.

Included modules:

- `invenio-stats <https://invenio-stats.readthedocs.io>`_
    - Event collection, processing and aggregation in time-based indicies in
      Elasticsearch.
- `invenio-queues <https://invenio-queues.readthedocs.io>`_
    - Event queue management module.
- `counter-robots <https://counter-robots.readthedocs.io>`_
    - Module providing the list of robots according to the COUNTER Code of
      Practice.

Deposit bundle (alpha)
----------------------

.. note::

    This bundle is in alpha. The modules are being used in production systems
    but are very likely subject to change and are missing documentation.

Included modules:

- `invenio-deposit <https://invenio-deposit.readthedocs.io>`_
    - REST API for managing deposit of records into Invenio with support for
      in progress editing of records.
- `invenio-files-js <https://www.npmjs.com/package/invenio-files-js>`_
    - AngularJS application for uploading files to Invenio via streaming the
      binary files in an HTTP request.
- `invenio-records-js <https://invenio-records-js.readthedocs.io>`_
    - AngularJS application for interacting with the deposit REST API and
      rendering forms based on angular schema forms.
- `invenio-sipstore <https://invenio-sipstore.readthedocs.io>`_
    - Submission Information Package (SIP) store with bagit support.


Invenio modules (alpha)
-----------------------
.. note::

    These modules are in alpha. The modules are being used in production
    systems but are most likely subject to changes and are missing
    documentation.

In addition to above bundles, we have a number of other individual modules
which are all being used in production systems, but which are likely subject
to change prior to final release and in most cases are missing documentation.

- `invenio-accounts-rest <https://invenio-accounts-rest.readthedocs.io>`_
    - REST APIs for account management.
- `invenio-charts-js <https://invenio-charts-js.readthedocs.io>`_
    - AngularJS application for producing charts.
- `invenio-csl-js <https://invenio-csl-js.readthedocs.io>`_
    - AngularJS application for rendering citation strings via the records
      REST API and the CSL REST API.
- `invenio-csl-rest <https://invenio-csl-rest.readthedocs.io>`_
    - REST API for retrieving Citation Style Language (CSL) style files.
- `invenio-github <https://invenio-github.readthedocs.io>`_
    - GitHub integration with automatic archiving of new releases in Invenio.
- `invenio-openaire <https://invenio-openaire.readthedocs.io>`_
    - Integration with OpenAIRE, including support for harvesting Open Funder
      Regsitry and the OpenAIRE grants database, as well as REST APIs for
      funders and grants.
- `invenio-opendefinition <https://invenio-opendefinition.readthedocs.io>`_
    - REST API for licenses from OpenDefinition and SPDX.
- `invenio-pages <https://invenio-pages.readthedocs.io>`_
    - Static pages module for Invenio.
- `invenio-pidrelations <https://invenio-pidrelations.readthedocs.io>`_
    - Persistent identifier relations management to support e.g. DOI
      versioning.
- `invenio-previewer-ispy <https://invenio-previewer-ispy.readthedocs.io>`_
    - ISPY previewer.
- `invenio-query-parser <https://invenio-query-parser.readthedocs.io>`_
    - Invenio v1 compatible query parser for Invenio v3. Note the module is GPL
      licensed due to a GPL-licensed dependency.
- `invenio-s3 <https://invenio-s3.readthedocs.io>`_
    - Support for the S3 storage protocol in Invenio.
- `invenio-saml <https://invenio-saml.readthedocs.io>`_
    - SAML support for Invenio.
- `invenio-sequencegenerator <https://invenio-sequencegenerator.readthedocs.io>`_
    - Module for minting and tracking multiple sequences for e.g. report
      numbers, journals etc.
- `invenio-sse <https://invenio-sse.readthedocs.io>`_
    - Server-Sent Events (SSE) integration in Invenio.
- `invenio-webhooks <https://invenio-webhooks.readthedocs.io>`_
    - REST API for receiving and processing webhook calls from third-party
      services.
- `invenio-xrootd <https://invenio-xrootd.readthedocs.io>`_
    - Support for the storage protocol XRootD in Invenio.
- `react-searchkit <https://invenio-react-searchkit.readthedocs.io>`_
    - Modular React library for implementing search interfaces on top of
      Invenio, Elasticsearch or other search APIs. Replacement for
      Invenio-Search-JS.

Utility libraries
-----------------

Above Invenio modules dependent on a number of smaller utility libraries we
have developed to take care of e.g. identifier normalization, DataCite/Dublin
Core metadata generation, testing and citation formatting.

- `citeproc-py-styles <https://citeproc-py-styles.readthedocs.io>`_
    - Citation Style Language (CSL) style files packaged as a Python module
- `datacite <https://datacite.readthedocs.io>`_
    - Python library for generating DataCite XML from Python dictionaries and
      registering DOIs with the DataCite DOI registration service.
- `dcxml <https://dcxml.readthedocs.io>`_
    - Python library for generating Dublin Core XML from Python dictionaries.
- `dictdiffer <https://dictdiffer.readthedocs.io>`_
    - Python library for diffing/patching/merging JSON documents.
- `dojson <https://dojson.readthedocs.io>`_
    - JSON to JSON rule-based transformation library.
- `flask-breadcrumbs <https://flask-breadcrumbs.readthedocs.io>`_
    - Flask extension for managing breadcrumbs in web applications.
- `flask-celeryext <https://flask-celeryext.readthedocs.io>`_
    - Celery integration for Flask.
- `flask-iiif <https://flask-iiif.readthedocs.io>`_
    - IIIF server for Flask.
- `flask-menu <https://flask-menu.readthedocs.io>`_
    - Menu generation support for Flask.
- `flask-sitemap <https://flask-sitemap.readthedocs.io>`_
    - Sitemaps XML generation for Flask.
- `flask-webpack <https://flask-webpack.readthedocs.io>`_
    - Webpack integration for Flask.
- `idutils <https://idutils.readthedocs.io>`_
    - Persistent identifier validation, identification and normalization.
- `jsonresolver <https://jsonresolver.readthedocs.io>`_
    - JSONRef resolver with support for local plugins.
- `pynpm <https://pynpm.readthedocs.io>`_
    - NPM integration for Python.
- `pywebpack <https://pywebpack.readthedocs.io>`_
    - Webpack integration library for Python.
- `requirements-builder <https://requirements-builder.readthedocs.io>`_
    - Python CLI tool for testing multiple versions of different Python
      libraries in you continuous integration system.
- `xrootdpyfs <https://xrootdpyfs.readthedocs.io>`_
    - PyFilesystem plugin adding XRootD support.

Scaffolding
-----------
Following modules provide templates for getting started with Invenio:

- `cookiecutter-invenio-instance <https://github.com/inveniosoftware/cookiecutter-invenio-instance>`_
    - Template for new Invenio instances.
- `cookiecutter-invenio-datamodel <https://github.com/inveniosoftware/cookiecutter-invenio-datamodel>`_
    - Template for new data models.
- `cookiecutter-invenio-module <https://github.com/inveniosoftware/cookiecutter-invenio-module>`_
    - Template for a reusable Invenio module.

Notes on license
----------------
Invenio is undergoing a change of license from GPLv2 to MIT License in most
cases. Thus, you may especially for alpha and beta modules see that the license
is still GPL v2 in the source code. This will be changed to MIT License for
all repositories before being finally released. The only module we are
currently aware of that can not be converted is Invenio-Query-Parser, which
has a dependency on a GPL-licensed library. Invenio-Query-Parser is however not
needed by most installations, as it only provides an Invenio v1.x compatible
query parser.

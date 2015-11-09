.. This file is part of Invenio
   Copyright (C) 2015 CERN.

   Invenio is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   Invenio is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with Invenio; if not, write to the Free Software Foundation, Inc.,
   59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


Base modules
============

The **base modules** provide interfaces to the Flask ecosystem, the Database,
and other system tools and technologies that the Invenio ecosystem uses.
Example: ``Invenio-Celery`` that talks to the Celery worker system.

invenio-access
++++++++++++++

A module providing role based access control.

- source code: `<http://github.com/inveniosoftware/invenio-access>`_
- releases: `<http://github.com/inveniosoftware/invenio-access/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-access/issues>`_
- documentation: `<http://pythonhosted.org/invenio-access>`_

invenio-accounts
++++++++++++++++

User management and authentication.

- source code: `<http://github.com/inveniosoftware/invenio-accounts>`_
- releases: `<http://github.com/inveniosoftware/invenio-accounts/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-accounts/issues>`_
- documentation: `<http://pythonhosted.org/invenio-accounts>`_

invenio-base
++++++++++++

Base package for building Invenio application.

- source code: `<http://github.com/inveniosoftware/invenio-base>`_
- releases: `<http://github.com/inveniosoftware/invenio-base/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-base/issues>`_
- documentation: `<http://pythonhosted.org/invenio-base>`_

invenio-celery
++++++++++++++

Interfacing to Celery.

- source code: `<http://github.com/inveniosoftware/invenio-celery>`_
- releases: `<http://github.com/inveniosoftware/invenio-celery/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-celery/issues>`_
- documentation: `<http://pythonhosted.org/invenio-celery>`_

invenio-cloudconnector
++++++++++++++++++++++

Cloud filesystems integration.

- source code: `<http://github.com/inveniosoftware/invenio-cloudconnector>`_
- releases: `<http://github.com/inveniosoftware/invenio-cloudconnector/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-cloudconnector/issues>`_
- documentation: `<http://pythonhosted.org/invenio-cloudconnector>`_

invenio-config
++++++++++++++

Configuration module.

- source code: `<http://github.com/inveniosoftware/invenio-config>`_
- releases: `<http://github.com/inveniosoftware/invenio-config/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-config/issues>`_
- documentation: `<http://pythonhosted.org/invenio-config>`_

invenio-db
++++++++++

Integration with SQLAlchemy and databases.

- source code: `<http://github.com/inveniosoftware/invenio-db>`_
- releases: `<http://github.com/inveniosoftware/invenio-db/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-db/issues>`_
- documentation: `<http://pythonhosted.org/invenio-db>`_

invenio-ext
+++++++++++

Integration with Flask extensions.

- source code: `<http://github.com/inveniosoftware/invenio-ext>`_
- releases: `<http://github.com/inveniosoftware/invenio-ext/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-ext/issues>`_
- documentation: `<http://pythonhosted.org/invenio-ext>`_

invenio-jsonschemas
+++++++++++++++++++

A module for building and serving JSON Schemas.

- source code: `<http://github.com/inveniosoftware/invenio-jsonschemas>`_
- releases: `<http://github.com/inveniosoftware/invenio-jsonschemas/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-jsonschemas/issues>`_
- documentation: `<http://pythonhosted.org/invenio-jsonschemas>`_

invenio-testing
+++++++++++++++

Provides unit testing utilities for Invenio.

- source code: `<http://github.com/inveniosoftware/invenio-testing>`_
- releases: `<http://github.com/inveniosoftware/invenio-testing/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-testing/issues>`_
- documentation: `<http://pythonhosted.org/invenio-testing>`_

invenio-upgrader
++++++++++++++++

Upgrade engine.

- source code: `<http://github.com/inveniosoftware/invenio-upgrader>`_
- releases: `<http://github.com/inveniosoftware/invenio-upgrader/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-upgrader/issues>`_
- documentation: `<http://pythonhosted.org/invenio-upgrader>`_

Core feature modules
====================

The **core feature modules** provide most common functionality that each digital
library instance is likely interested in using. Example: ``Invenio-Records``
provide record object store.

invenio-collections
+++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-collections>`_
- releases: `<http://github.com/inveniosoftware/invenio-collections/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-collections/issues>`_
- documentation: `<http://pythonhosted.org/invenio-collections>`_

invenio-communities
+++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-communities>`_
- releases: `<http://github.com/inveniosoftware/invenio-communities/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-communities/issues>`_
- documentation: `<http://pythonhosted.org/invenio-communities>`_

invenio-deposit
+++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-deposit>`_
- releases: `<http://github.com/inveniosoftware/invenio-deposit/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-deposit/issues>`_
- documentation: `<http://pythonhosted.org/invenio-deposit>`_

invenio-documents
+++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-documents>`_
- releases: `<http://github.com/inveniosoftware/invenio-documents/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-documents/issues>`_
- documentation: `<http://pythonhosted.org/invenio-documents>`_

invenio-formatter
+++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-formatter>`_
- releases: `<http://github.com/inveniosoftware/invenio-formatter/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-formatter/issues>`_
- documentation: `<http://pythonhosted.org/invenio-formatter>`_

invenio-groups
++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-groups>`_
- releases: `<http://github.com/inveniosoftware/invenio-groups/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-groups/issues>`_
- documentation: `<http://pythonhosted.org/invenio-groups>`_

invenio-pidstore
++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-pidstore>`_
- releases: `<http://github.com/inveniosoftware/invenio-pidstore/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-pidstore/issues>`_
- documentation: `<http://pythonhosted.org/invenio-pidstore>`_

invenio-previewer
+++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-previewer>`_
- releases: `<http://github.com/inveniosoftware/invenio-previewer/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-previewer/issues>`_
- documentation: `<http://pythonhosted.org/invenio-previewer>`_

invenio-query-parser
++++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-query-parser>`_
- releases: `<http://github.com/inveniosoftware/invenio-query-parser/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-query-parser/issues>`_
- documentation: `<http://pythonhosted.org/invenio-query-parser>`_

invenio-records
+++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-records>`_
- releases: `<http://github.com/inveniosoftware/invenio-records/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-records/issues>`_
- documentation: `<http://pythonhosted.org/invenio-records>`_

invenio-search
++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-search>`_
- releases: `<http://github.com/inveniosoftware/invenio-search/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-search/issues>`_
- documentation: `<http://pythonhosted.org/invenio-search>`_

Additional feature modules
==========================

The **additional feature modules** offer additional functionality suitable for
various particular use cases, such as the Integrated Library System, the
Multimedia Store, or the Data Repository. Example: ``Invenio-Circulation``
offers circulation and holdings capabilities.

invenio-annotations
+++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-annotations>`_
- releases: `<http://github.com/inveniosoftware/invenio-annotations/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-annotations/issues>`_
- documentation: `<http://pythonhosted.org/invenio-annotations>`_

invenio-classifier
++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-classifier>`_
- releases: `<http://github.com/inveniosoftware/invenio-classifier/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-classifier/issues>`_
- documentation: `<http://pythonhosted.org/invenio-classifier>`_

invenio-client
++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-client>`_
- releases: `<http://github.com/inveniosoftware/invenio-client/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-client/issues>`_
- documentation: `<http://pythonhosted.org/invenio-client>`_

invenio-comments
++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-comments>`_
- releases: `<http://github.com/inveniosoftware/invenio-comments/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-comments/issues>`_
- documentation: `<http://pythonhosted.org/invenio-comments>`_

invenio-knowledge
+++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-knowledge>`_
- releases: `<http://github.com/inveniosoftware/invenio-knowledge/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-knowledge/issues>`_
- documentation: `<http://pythonhosted.org/invenio-knowledge>`_

invenio-news
++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-news>`_
- releases: `<http://github.com/inveniosoftware/invenio-news/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-news/issues>`_
- documentation: `<http://pythonhosted.org/invenio-news>`_

invenio-oaiharvester
++++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-oaiharvester>`_
- releases: `<http://github.com/inveniosoftware/invenio-oaiharvester/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-oaiharvester/issues>`_
- documentation: `<http://pythonhosted.org/invenio-oaiharvester>`_

invenio-oauth2server
++++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-oauth2server>`_
- releases: `<http://github.com/inveniosoftware/invenio-oauth2server/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-oauth2server/issues>`_
- documentation: `<http://pythonhosted.org/invenio-oauth2server>`_

invenio-oauthclient
+++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-oauthclient>`_
- releases: `<http://github.com/inveniosoftware/invenio-oauthclient/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-oauthclient/issues>`_
- documentation: `<http://pythonhosted.org/invenio-oauthclient>`_

invenio-pages
+++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-pages>`_
- releases: `<http://github.com/inveniosoftware/invenio-pages/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-pages/issues>`_
- documentation: `<http://pythonhosted.org/invenio-pages>`_

invenio-previewer-ispy
++++++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-previewer-ispy>`_
- releases: `<http://github.com/inveniosoftware/invenio-previewer-ispy/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-previewer-ispy/issues>`_
- documentation: `<http://pythonhosted.org/invenio-previewer-ispy>`_

invenio-redirector
++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-redirector>`_
- releases: `<http://github.com/inveniosoftware/invenio-redirector/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-redirector/issues>`_
- documentation: `<http://pythonhosted.org/invenio-redirector>`_

invenio-sequencegenerator
+++++++++++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-sequencegenerator>`_
- releases: `<http://github.com/inveniosoftware/invenio-sequencegenerator/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-sequencegenerator/issues>`_
- documentation: `<http://pythonhosted.org/invenio-sequencegenerator>`_

invenio-tags
++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-tags>`_
- releases: `<http://github.com/inveniosoftware/invenio-tags/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-tags/issues>`_
- documentation: `<http://pythonhosted.org/invenio-tags>`_

invenio-unapi
+++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-unapi>`_
- releases: `<http://github.com/inveniosoftware/invenio-unapi/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-unapi/issues>`_
- documentation: `<http://pythonhosted.org/invenio-unapi>`_

invenio-utils
+++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-utils>`_
- releases: `<http://github.com/inveniosoftware/invenio-utils/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-utils/issues>`_
- documentation: `<http://pythonhosted.org/invenio-utils>`_

invenio-webhooks
++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-webhooks>`_
- releases: `<http://github.com/inveniosoftware/invenio-webhooks/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-webhooks/issues>`_
- documentation: `<http://pythonhosted.org/invenio-webhooks>`_

invenio-workflows
+++++++++++++++++

- source code: `<http://github.com/inveniosoftware/invenio-workflows>`_
- releases: `<http://github.com/inveniosoftware/invenio-workflows/releases>`_
- known issues: `<https://github.com/inveniosoftware/invenio-workflows/issues>`_
- documentation: `<http://pythonhosted.org/invenio-workflows>`_


..
    This file is part of Invenio.
    Copyright (C) 2018-2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _requirements:

Requirements
============

Following is a brief overview of the requirements of Invenio:

- Supported Python versions:
    - Python 3: v3.6, v3.7 and 3.8.
- Supported databases:
    - PostgreSQL v9.6+, MySQL 5.6+ or SQLite (for testing).
- Supported search engines:
    - Elasticsearch v6 or v7.
- Supported memory caches:
    - Redis or Memcache.
- Supported message queues:
    - RabbitMQ, Redis.
- Supported storage protocols:
    - Local, S3, WebDAV, XRootD and many more.
- Supported WSGI servers:
    - Gunicorn
    - uWSGI
    - mod_wsgi
- Supported Flask versions:
    - v1.0.4+
- Supported Celery versions:
    - v5.0, v4.4
- Supported operating systems:
    - macOS: Newer releases
    - Linux: Newer distributions such as Ubuntu 18 or CentOS 7.

System requirements
-------------------
Invenio can run in both Docker, virtual machines and physical machines. Invenio
can run on a single machine or a cluster of 100s of machines. It all
depends on exactly how much data you are handling and your performance
requirements.

Following is an estimate of a small, medium and large installation of Invenio.
The purpose is only to provide a **very rough** idea about how an Invenio
installation could look like.

**Small installation:**

- Web/app/background servers and Redis: 1 node
- Database: 1 node
- Elasticsearch: 1 node

**Medium installation:**

- Load balancer: 1 node
- Web/app servers and background workers: 2 nodes
- Database: 1 node
- Elasticsearch: 3 nodes
- Redis/RabbitMQ: 1 node

**Large installation:**

- Load balancer: 2 node (with DNS load balancing)
- Web/app servers: 3+ nodes
- Background workers: 3+ nodes
- Database: 2 nodes (master/slave)
- Elasticsearch: 5 nodes (3 data, 2 clients)
- Redis: 3 nodes (HA setup)
- RabbitMQ: 2 nodes (HA setup)

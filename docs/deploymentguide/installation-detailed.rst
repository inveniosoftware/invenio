..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _installation_detailed:

Detailed installation guide
===========================

.. admonition:: CAVEAT LECTOR

   Invenio v3.0 alpha is a bleeding-edge developer preview version.

Introduction
------------

In this installation guide, we'll create an Invenio digital library instance
using a multi-machine setup where separate services (such as the database server
and the web server) run on separate dedicated machines. Such a multi-machine
setup emulates to what one would typically use in production. (However, it is
very well possible to follow this guide and install all the services onto the
same "localhost", if one wants to.)

We'll use six dedicated machines running the following services:

============= ============= ====================
node          IP            runs
============= ============= ====================
web           192.168.50.10 Invenio web application
postgresql    192.168.50.11 `PostgreSQL <http://www.postgresql.org/>`_ database server
redis         192.168.50.12 `Redis <http://redis.io/>`_ caching service
elasticsearch 192.168.50.13 `Elasticsearch <https://www.elastic.co/products/elasticsearch>`_ information retrieval service
rabbitmq      192.168.50.14 `RabbitMQ <http://www.rabbitmq.com/>`_ messaging service
worker        192.168.50.15 `Celery <http://www.celeryproject.org/>`_ worker node
============= ============= ====================

The instructions below are tested on Ubuntu 14.04 LTS (Trusty Tahr) and CentOS 7
operating systems. For other operating systems such as Mac OS X, you may want to
check out the "kickstart" set of scripts coming with the Invenio source code
that perform the below-quoted installation steps in an unattended automated way.

Environment variables
---------------------

Let's define some useful environment variables that will describe our Invenio
instance setup:

.. glossary::

   INVENIO_WEB_HOST
     The IP address of the Web server node.

   INVENIO_WEB_INSTANCE
     The name of your Invenio instance that will be created. Usually equal to
     the name of the Python virtual environment.

   INVENIO_WEB_VENV
     The name of the Python virtual environment where Invenio will be installed.
     Usually equal to the name of the Invenio instance.

   INVENIO_USER_EMAIL
     The email address of a user account that will be created on the Invenio
     instance.

   INVENIO_USER_PASS
     The password of this Invenio user.

   INVENIO_POSTGRESQL_HOST
     The IP address of the PostgreSQL database server.

   INVENIO_POSTGRESQL_DBNAME
     The database name that will hold persistent data of our Invenio instance.

   INVENIO_POSTGRESQL_DBUSER
     The database user name used to connect to the database server.

   INVENIO_POSTGRESQL_DBPASS
     The password of this database user.

   INVENIO_REDIS_HOST
     The IP address af the Redis server.

   INVENIO_ELASTICSEARCH_HOST
     The IP address of the Elasticsearch information retrieval server.

   INVENIO_RABBITMQ_HOST
     The IP address of the RabbitMQ messaging server.

   INVENIO_WORKER_HOST
     The IP address of the Celery worker node.

Web
---

TODO: rewrite this part.

The web application node (192.168.50.10) is where the main Invenio application
will be running. We need to provision it with some system dependencies in order
to be able to install various underlying Python and JavaScript libraries.

Database
--------

TODO: rewrite this part.

The database server (192.168.50.11) will hold persistent data of our Invenio
installation, such as bibliographic records or user accounts. Invenio supports
MySQL, PostgreSQL, and SQLite databases. In this tutorial, we shall use
PostgreSQL that is the recommended database platform for Invenio.

Redis
-----

TODO: rewrite this part.

The Redis server (192.168.50.12) is used for various caching needs.

Elasticsearch
-------------

TODO: rewrite this part.

The Elasticsearch server (192.168.50.13) is used to index and search
bibliographic records, fulltext documents, and other various interesting
information managed by our Invenio digital library instance.

RabbitMQ
--------

TODO: rewrite this part.

The RabbitMQ server (192.168.50.14) is used as a messaging middleware broker.

Worker
------

TODO: rewrite this part.

The Celery worker node (192.168.50.15) is used to execute potentially long tasks
in asynchronous manner.

Invenio
-------

TODO: rewrite this part.

Now that all the prerequisites have been set up, we can proceed with the
installation of the Invenio itself. The installation is happening on the web
node (192.168.50.10).

Let’s see in detail about every Invenio installation step.

Create instance
~~~~~~~~~~~~~~~

We start by creating a fresh new Python virtual environment that will hold our
brand new Invenio v3.0 instance:

We continue by installing Invenio v3.0 Integrated Library System flavour demo
site from PyPI:

Let's briefly customise our instance with respect to the location of the
database server, the Redis server, the Elasticsearch server, and all the other
dependent services in our multi-server environment:

In the instance folder, we run Npm to install any JavaScript libraries that
Invenio needs:

We can now collect and build CSS/JS assets of our Invenio instance:

Our first new Invenio instance is created and ready for loading some example
records.

Populate instance
~~~~~~~~~~~~~~~~~

TODO: rewrite this part.

We proceed by creating a dedicated database that will hold persistent data of
our installation, such as bibliographic records or user accounts. The database
tables can be created as follows:

We continue by creating a user account:

We can now create the Elasticsearch indexes and initialise the indexing queue:

We proceed by populating our Invenio demo instance with some example demo
MARCXML records:

Start instance
~~~~~~~~~~~~~~

TODO: rewrite this part.

Let's now start the web application:

and the web server:

We should now see our demo records on the web:

.. code-block:: shell

   firefox http://${INVENIO_WEB_HOST}/records/1

and we can access them via REST API:

.. code-block:: shell

   curl -i -H "Accept: application/json" \
        http://${INVENIO_WEB_HOST}/api/records/1

We are done! Our first Invenio v3.0 demo instance is fully up and running.

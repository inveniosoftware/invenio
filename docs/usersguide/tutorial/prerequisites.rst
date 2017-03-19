.. _install_prerequisites:

Install prerequisites
=====================

Overview
--------

Invenio uses several services such as `PostgreSQL <http://www.postgresql.org/>`_
database server, `Redis <http://redis.io/>`_ for caching, `Elasticsearch
<https://www.elastic.co/products/elasticsearch>`_ for indexing and information
retrieval, `RabbitMQ <http://www.rabbitmq.com/>`_ for messaging, `Celery
<http://www.celeryproject.org/>`_ for task execution.

You can install them manually or you can use provided kickstart scripts as
mentioned in :ref:`quickstart`:

.. code-block:: bash

  vim .inveniorc
  source .inveniorc
  scripts/provision-web.sh
  scripts/provision-postgresql.sh
  scripts/provision-elasticsearch.sh
  scripts/provision-redis.sh
  scripts/provision-rabbitmq.sh
  scripts/provision-worker.sh

The next section gives a detailed walk-through of what the scripts do.

Concrete example
----------------

In this installation example, we'll create an Invenio digital library instance
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
~~~~~~~~~~~~~~~~~~~~~

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

In our example setup, we shall use:

.. include:: ../../../.inveniorc
   :start-after: # sphinxdoc-kickstart-configuration-variables-begin
   :end-before: # sphinxdoc-kickstart-configuration-variables-end
   :literal:

Let us save this configuration in a file called ``.inveniorc`` for future use.

Web
~~~

The web application node (192.168.50.10) is where the main Invenio application
will be running. We need to provision it with some system dependencies in order
to be able to install various underlying Python and JavaScript libraries.

The web application node can be set up in an automated unattended way by running
the following script:

.. code-block:: shell

   source .inveniorc
   ./scripts/provision-web.sh

Let's see in detail what the web provisioning script does.

First, let's see if using ``sudo`` will be required:

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-detect-sudo-begin
   :end-before: # sphinxdoc-install-detect-sudo-end
   :literal:

Second, some useful system tools are installed:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-useful-system-tools-ubuntu14-begin
   :end-before: # sphinxdoc-install-useful-system-tools-ubuntu14-end
   :literal:

* on CentOS 7:

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-useful-system-tools-centos7-begin
   :end-before: # sphinxdoc-install-useful-system-tools-centos7-end
   :literal:

Third, an external Node.js package repository is enabled. We'll be needing to
install and run Npm on the web node later. The Node.js repository is enabled as
follows:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-add-nodejs-external-repository-ubuntu14-begin
   :end-before: # sphinxdoc-add-nodejs-external-repository-ubuntu14-end
   :literal:

* on CentOS 7:

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-add-nodejs-external-repository-centos7-begin
   :end-before: # sphinxdoc-add-nodejs-external-repository-centos7-end
   :literal:

Fourth, all the common prerequisite software libraries and packages that Invenio
needs are installed:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-web-common-ubuntu14-begin
   :end-before: # sphinxdoc-install-web-common-ubuntu14-end
   :literal:

* on CentOS7:

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-web-common-centos7-begin
   :end-before: # sphinxdoc-install-web-common-centos7-end
   :literal:

We want to use PostgreSQL database in this installation example, so we need to
install corresponding libraries too:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-web-libpostgresql-ubuntu14-begin
   :end-before: # sphinxdoc-install-web-libpostgresql-ubuntu14-end
   :literal:

* on CentOS7:

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-web-libpostgresql-centos7-begin
   :end-before: # sphinxdoc-install-web-libpostgresql-centos7-end
   :literal:

Fifth, now that Node.js is installed, we can proceed with installing Npm and
associated CSS/JS filter tools. Let's do it globally:

* on either of the operating systems:

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-npm-and-css-js-filters-begin
   :end-before: # sphinxdoc-install-npm-and-css-js-filters-end
   :literal:

Sixth, we'll install Python virtual environment wrapper tools and activate them
in the current user shell process:

* on either of the operating systems:

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-virtualenvwrapper-begin
   :end-before: # sphinxdoc-install-virtualenvwrapper-end
   :literal:

Seventh, we install Nginx web server and configure appropriate virtual host:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-web-nginx-ubuntu14-begin
   :end-before: # sphinxdoc-install-web-nginx-ubuntu14-end
   :literal:

* on CentOS7:

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-web-nginx-centos7-begin
   :end-before: # sphinxdoc-install-web-nginx-centos7-end
   :literal:

Finally, let's clean after ourselves:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-web-cleanup-ubuntu14-begin
   :end-before: # sphinxdoc-install-web-cleanup-ubuntu14-end
   :literal:

* on CentOS7:

.. include:: ../../../scripts/provision-web.sh
   :start-after: # sphinxdoc-install-web-cleanup-centos7-begin
   :end-before: # sphinxdoc-install-web-cleanup-centos7-end
   :literal:

Database
~~~~~~~~

The database server (192.168.50.11) will hold persistent data of our Invenio
installation, such as bibliographic records or user accounts. Invenio supports
MySQL, PostgreSQL, and SQLite databases. In this tutorial, we shall use
PostgreSQL that is the recommended database platform for Invenio.

The database server node can be set up in an automated unattended way by running
the following script:

.. code-block:: shell

   source .inveniorc
   ./scripts/provision-postgresql.sh

Let's see in detail what the database provisioning script does.

First, we install and configure the database software:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-postgresql.sh
   :start-after: # sphinxdoc-install-postgresql-ubuntu14-begin
   :end-before: # sphinxdoc-install-postgresql-ubuntu14-end
   :literal:

* on CentOS 7:

.. include:: ../../../scripts/provision-postgresql.sh
   :start-after: # sphinxdoc-install-postgresql-centos7-begin
   :end-before: # sphinxdoc-install-postgresql-centos7-end
   :literal:

We can now create a new database user with the necessary access permissions on
the new database:

* on either of the operating systems:

.. include:: ../../../scripts/provision-postgresql.sh
   :start-after: # sphinxdoc-setup-postgresql-access-begin
   :end-before: # sphinxdoc-setup-postgresql-access-end
   :literal:

Finally, let's clean after ourselves:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-postgresql.sh
   :start-after: # sphinxdoc-install-postgresql-cleanup-ubuntu14-begin
   :end-before: # sphinxdoc-install-postgresql-cleanup-ubuntu14-end
   :literal:

* on CentOS7:

.. include:: ../../../scripts/provision-postgresql.sh
   :start-after: # sphinxdoc-install-postgresql-cleanup-centos7-begin
   :end-before: # sphinxdoc-install-postgresql-cleanup-centos7-end
   :literal:

Redis
~~~~~

The Redis server (192.168.50.12) is used for various caching needs.

The Redis server can be set up in an automated unattended way by running the
following script:

.. code-block:: shell

   source .inveniorc
   ./scripts/provision-redis.sh

Let's see in detail what the Redis provisioning script does.

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-redis.sh
   :start-after: # sphinxdoc-install-redis-ubuntu14-begin
   :end-before: # sphinxdoc-install-redis-ubuntu14-end
   :literal:

* on CentOS 7:

.. include:: ../../../scripts/provision-redis.sh
   :start-after: # sphinxdoc-install-redis-centos7-begin
   :end-before: # sphinxdoc-install-redis-centos7-end
   :literal:

Finally, let's clean after ourselves:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-redis.sh
   :start-after: # sphinxdoc-install-redis-cleanup-ubuntu14-begin
   :end-before: # sphinxdoc-install-redis-cleanup-ubuntu14-end
   :literal:

* on CentOS7:

.. include:: ../../../scripts/provision-redis.sh
   :start-after: # sphinxdoc-install-redis-cleanup-centos7-begin
   :end-before: # sphinxdoc-install-redis-cleanup-centos7-end
   :literal:

Elasticsearch
~~~~~~~~~~~~~

The Elasticsearch server (192.168.50.13) is used to index and search
bibliographic records, fulltext documents, and other various interesting
information managed by our Invenio digital library instance.

The Elasticsearch server can be set up in an automated unattended way by running
the following script:

.. code-block:: shell

   source .inveniorc
   ./scripts/provision-elasticsearch.sh

Let's see in detail what the Elasticsearch provisioning script does.

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-elasticsearch.sh
   :start-after: # sphinxdoc-install-elasticsearch-ubuntu14-begin
   :end-before: # sphinxdoc-install-elasticsearch-ubuntu14-end
   :literal:

* on CentOS 7:

.. include:: ../../../scripts/provision-elasticsearch.sh
   :start-after: # sphinxdoc-install-elasticsearch-centos7-begin
   :end-before: # sphinxdoc-install-elasticsearch-centos7-end
   :literal:

Some packages require extra plugins to be installed.

.. include:: ../../../scripts/provision-elasticsearch.sh
   :start-after: # sphinxdoc-install-elasticsearch-plugins-begin
   :end-before: # sphinxdoc-install-elasticsearch-plugins-end
   :literal:

Finally, let's clean after ourselves:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-elasticsearch.sh
   :start-after: # sphinxdoc-install-elasticsearch-cleanup-ubuntu14-begin
   :end-before: # sphinxdoc-install-elasticsearch-cleanup-ubuntu14-end
   :literal:

* on CentOS7:

.. include:: ../../../scripts/provision-elasticsearch.sh
   :start-after: # sphinxdoc-install-elasticsearch-cleanup-centos7-begin
   :end-before: # sphinxdoc-install-elasticsearch-cleanup-centos7-end
   :literal:

RabbitMQ
~~~~~~~~

The RabbitMQ server (192.168.50.14) is used as a messaging middleware broker.

The RabbitMQ server can be set up in an automated unattended way by running the
following script:

.. code-block:: shell

   source .inveniorc
   ./scripts/provision-rabbitmq.sh

Let's see in detail what the RabbitMQ provisioning script does.

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-rabbitmq.sh
   :start-after: # sphinxdoc-install-rabbitmq-ubuntu14-begin
   :end-before: # sphinxdoc-install-rabbitmq-ubuntu14-end
   :literal:

* on CentOS 7:

.. include:: ../../../scripts/provision-rabbitmq.sh
   :start-after: # sphinxdoc-install-rabbitmq-centos7-begin
   :end-before: # sphinxdoc-install-rabbitmq-centos7-end
   :literal:

Finally, let's clean after ourselves:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-rabbitmq.sh
   :start-after: # sphinxdoc-install-rabbitmq-cleanup-ubuntu14-begin
   :end-before: # sphinxdoc-install-rabbitmq-cleanup-ubuntu14-end
   :literal:

* on CentOS7:

.. include:: ../../../scripts/provision-rabbitmq.sh
   :start-after: # sphinxdoc-install-rabbitmq-cleanup-centos7-begin
   :end-before: # sphinxdoc-install-rabbitmq-cleanup-centos7-end
   :literal:

Worker
~~~~~~

The Celery worker node (192.168.50.15) is used to execute potentially long tasks
in asynchronous manner.

The worker node can be set up in an automated unattended way by running the
following script:

.. code-block:: shell

   source .inveniorc
   ./scripts/provision-worker.sh

Let's see in detail what the worker provisioning script does.

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-worker.sh
   :start-after: # sphinxdoc-install-worker-ubuntu14-begin
   :end-before: # sphinxdoc-install-worker-ubuntu14-end
   :literal:

* on CentOS 7:

.. include:: ../../../scripts/provision-worker.sh
   :start-after: # sphinxdoc-install-worker-centos7-begin
   :end-before: # sphinxdoc-install-worker-centos7-end
   :literal:

Finally, let's clean after ourselves:

* on Ubuntu 14.04 LTS (Trusty Tahr):

.. include:: ../../../scripts/provision-worker.sh
   :start-after: # sphinxdoc-install-worker-cleanup-ubuntu14-begin
   :end-before: # sphinxdoc-install-worker-cleanup-ubuntu14-end
   :literal:

* on CentOS7:

.. include:: ../../../scripts/provision-worker.sh
   :start-after: # sphinxdoc-install-worker-cleanup-centos7-begin
   :end-before: # sphinxdoc-install-worker-cleanup-centos7-end
   :literal:

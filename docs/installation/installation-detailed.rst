..  This file is part of Invenio
    Copyright (C) 2014, 2015 CERN.

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

Detailed installation guide
===========================

.. admonition:: CAVEAT LECTOR

   Invenio v3.0 alpha is a bleeding-edge developer preview version that is
   scheduled for public release in Q1/2016.

Prerequisites
-------------

Invenio v3.0 needs several prerequisite software packages to function, such as:

- `Elasticsearch <https://www.elastic.co/products/elasticsearch>`_
- `PostgreSQL <http://www.postgresql.org/>`_
- `RabbitMQ <http://www.rabbitmq.com/>`_
- `Redis <http://redis.io/>`_

You may install the prerequisites as follows. The instructions below are fit for
Ubuntu 14.04 LTS (Trusty Tahr) operating system. Note that for this and other
operating systems such as CentOS 7, you can run ``kickstart.sh`` script that is
coming with the Invenio tarball and that performs all the installation steps
mentioned below in an automated unattended way.

First, let's install some useful system tools:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-install-useful-system-tools-begin
   :end-before: # sphinxdoc-install-useful-system-tools-end
   :literal:

We need to add external repository for Elasticsearch:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-add-elasticsearch-external-repository-begin
   :end-before: # sphinxdoc-add-elasticsearch-external-repository-end
   :literal:

and for Node.js:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-add-nodejs-external-repository-begin
   :end-before: # sphinxdoc-add-nodejs-external-repository-end
   :literal:

Now we can install all the pre-requisite software packages:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-install-prerequisites-begin
   :end-before: # sphinxdoc-install-prerequisites-end
   :literal:

Let's install Bower and CSS/JS filters globally:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-install-bower-and-css-js-filters-begin
   :end-before: # sphinxdoc-install-bower-and-css-js-filters-end
   :literal:

Finally, we install Python virtual environment wrapper tools and activate them
in the current shell process:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-install-virtualenvwrapper-begin
   :end-before: # sphinxdoc-install-virtualenvwrapper-end
   :literal:

Installation
------------

Now that all the prerequisite software packages have been installed, we can
proceed with the installation of the Invenio itself. Let's start by creating a
fresh new Python virtual environment that will hold our Invenio v3.0 instance:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-create-virtual-environment-begin
   :end-before: # sphinxdoc-create-virtual-environment-end
   :literal:

Let's install Invenio v3.0 base package and most of its available modules (using
option ``full`` as opposed to using option ``minimal``) from PyPI:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-install-invenio-full-begin
   :end-before: # sphinxdoc-install-invenio-full-end
   :literal:

This installs Invenio base package and its modules. We proceed with the creation
of a new Invenio instance called "mysite":

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-create-instance-begin
   :end-before: # sphinxdoc-create-instance-end
   :literal:

In the instance folder, we run Bower to install any JavaScript libraries that
Invenio depends on:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-run-bower-begin
   :end-before: # sphinxdoc-run-bower-end
   :literal:

We can now collect and build CSS/JS assets for our Invenio instance:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-collect-and-build-assets-begin
   :end-before: # sphinxdoc-collect-and-build-assets-end
   :literal:

We proceed by creating a dedicated database that will hold persistent data of
our installation, such as bibliographic records or user accounts. Invenio
supports MySQL, PostgreSQL, and SQLite databases. PostgreSQL is recommended, but
SQLite is used by default. The database can be created as follows:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-create-database-begin
   :end-before: # sphinxdoc-create-database-end
   :literal:

We continue by creating a user account:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-create-user-account-begin
   :end-before: # sphinxdoc-create-user-account-end
   :literal:

Let's now start Celery worker that will execute instance tasks:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-start-celery-worker-begin
   :end-before: # sphinxdoc-start-celery-worker-end
   :literal:

Now that Celery is running, we can populate our Invenio instance with demo
records:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-populate-with-demo-records-begin
   :end-before: # sphinxdoc-populate-with-demo-records-end
   :literal:

Let's register persistent identifiers for the uploaded demo records:

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-register-pid-begin
   :end-before: # sphinxdoc-register-pid-end
   :literal:

Finally, let's start the web application (in debugging mode):

.. include:: ../../scripts/kickstart.sh
   :start-after: # sphinxdoc-start-application-begin
   :end-before: # sphinxdoc-start-application-end
   :literal:

We should now see our demo record on the web:

.. code-block:: shell

   firefox http://localhost:5000/records/1

and we can access it via REST API:

.. code-block:: shell

   curl -i -H "Accept: application/json" \
        http://localhost:5000/api/records/1

We are done! Our first Invenio v3.0 instance is fully up and running.

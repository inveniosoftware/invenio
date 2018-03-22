..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Running Invenio
===============

Understanding Invenio components
--------------------------------

Invenio dems site consists of many components. To see which ones the Invenio
demo site uses, you can do:

.. code-block:: console

   $ pip freeze | grep invenio
   invenio-access==1.0.0a11
   invenio-accounts==1.0.0b3
   invenio-admin==1.0.0b1
   invenio-app==1.0.0a1
   invenio-app-ils==1.0.0a2
   invenio-assets==1.0.0b6
   invenio-base==1.0.0a14
   invenio-celery==1.0.0b2
   invenio-config==1.0.0b3
   invenio-db==1.0.0b3
   invenio-formatter==1.0.0b1
   invenio-i18n==1.0.0b3
   invenio-indexer==1.0.0a9
   invenio-jsonschemas==1.0.0a3
   invenio-logging==1.0.0b1
   invenio-mail==1.0.0b1
   invenio-marc21==1.0.0a5
   invenio-oaiserver==1.0.0a12
   invenio-oauth2server==1.0.0a15
   invenio-oauthclient==1.0.0a12
   invenio-pidstore==1.0.0b1
   invenio-query-parser==0.6.0
   invenio-records==1.0.0b1
   invenio-records-rest==1.0.0a18
   invenio-records-ui==1.0.0a9
   invenio-rest==1.0.0a10
   invenio-search==1.0.0a9
   invenio-search-ui==1.0.0a6
   invenio-theme==1.0.0b2
   invenio-userprofiles==1.0.0a9

Starting the webserver
----------------------

The Invenio application server can be started using:

.. code-block:: bash

   invenio run -h 0.0.0.0

For debugging purposes, you can use:

.. code-block:: bash

   pip install Flask-DebugToolbar
   FLASK_DEBUG=1 invenio run --debugger -h 0.0.0.0

Starting the job queue
----------------------

Invenio uses Celery for task execution. The task queue should be started as
follows:

.. code-block:: bash

   celery worker -A invenio_app.celery

For debugging purposes, you can increse logging level:

.. code-block:: bash

   celery worker -A invenio_app.celery -l DEBUG

Using the CLI
-------------

Invenio comes with centralised command line.  Use ``--help`` to see available commands:

.. code-block:: console

   $ invenio --help
   Usage: invenio [OPTIONS] COMMAND [ARGS]...

     Command Line Interface for Invenio.

   Options:
     --version  Show the flask version
     --help     Show this message and exit.

   Commands:
     access    Account commands.
     alembic   Perform database migrations.
     assets    Web assets commands.
     collect   Collect static files.
     db        Database commands.
     demo      Demo-site commands.
     index     Management command for search indicies.
     instance  Instance commands.
     marc21    MARC21 related commands.
     npm       Generate a package.json file.
     pid       PID-Store management commands.
     records   Record management commands.
     roles     Role commands.
     run       Runs a development server.
     shell     Runs a shell in the app context.
     users     User commands.

You can use ``--help`` for each individual command, for example:

.. code-block:: console

    $ invenio marc21 import --help
    Usage: invenio marc21 import [OPTIONS] INPUT

      Import MARCXML records.

    Options:
      --bibliographic
      --authority
      --help           Show this message and exit.

Using Python shell
------------------

You can start interactive Python shell which will load the Invenio application
context so that you can work with the instance:

.. code-block:: console

   $ invenio shell
   Python 2.7.6 (default, Oct 26 2016, 20:30:19)
   [GCC 4.8.4] on linux2
   App: invenio
   Instance: /home/vagrant/.virtualenvs/invenio/var/instance
   >>> app.config['BABEL_DEFAULT_LANGUAGE']
   'en'
   >>> app.config['CELERY_BROKER_URL']  # BROKER_URL for Celery 3
   'amqp://guest:guest@192.168.50.10:5672//'

Using administrative interface
------------------------------

You can access administrative interface:

.. code-block:: console

   $ firefox http://192.168.50.10/admin

For example, let us look at the record ID 117 that we have uploaded in
:ref:`create_and_search_your_first_record`. Looking at the administrative
interface, we can see that this record has been attributed an internal UUID:

======== ===================== ========== =========== ====================================
PID_Type PID                   Status     Object Type Object UUID
======== ===================== ========== =========== ====================================
oai      oai:invenio:recid/117 REGISTERED rec         a11dad76-5bd9-471c-975a-0b2b01d74831
recid    117                   REGISTERED rec         a11dad76-5bd9-471c-975a-0b2b01d74831
======== ===================== ========== =========== ====================================

See :ref:`loading_content` for more information about object UUIDs and PIDs.

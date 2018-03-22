..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _configure_invenio:

Configure Invenio
=================

After having installed Invenio demo site in :ref:`install_invenio`, let us see
briefly the instance configuration.

Configure instance
------------------

Invenio instance can be configured by editing ``invenio.cfg`` configuration
file. Here is an example:

.. code-block:: console

   $ cdvirtualenv var/instance/
   $ cat invenio.cfg
   # Database
   SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://invenio:dbpass123@192.168.50.10:5432/invenio'

   # Statis files
   COLLECT_STORAGE='flask_collect.storage.file'

   # Redis
   CACHE_TYPE='redis'
   CACHE_REDIS_HOST='192.168.50.10'
   CACHE_REDIS_URL='redis://192.168.50.10:6379/0'
   ACCOUNTS_SESSION_REDIS_URL='redis://192.168.50.10:6379/1'

   # Celery
   BROKER_URL='amqp://guest:guest@192.168.50.10:5672//'  # Celery 3
   CELERY_BROKER_URL='amqp://guest:guest@192.168.50.10:5672//'  # Celery 4
   CELERY_RESULT_BACKEND='redis://192.168.50.10:6379/2'

   # Elasticsearch
   SEARCH_ELASTIC_HOSTS='192.168.50.10'

   # JSON Schema
   JSONSCHEMAS_ENDPOINT='/schema'
   JSONSCHEMAS_HOST='192.168.50.10'

   # OAI server
   OAISERVER_RECORD_INDEX='marc21'
   OAISERVER_ID_PREFIX='oai:invenio:recid/'

Configuration options
---------------------

Since Invenio demo site uses ILS flavour of Invenio, you can learn more about
the configuration options in `Invenio-App-ILS configuration documentation
<http://invenio-app-ils.readthedocs.io/en/latest/configuration.html>`_.

We shall see how to customise instance more deeply in :ref:`customise_invenio`.

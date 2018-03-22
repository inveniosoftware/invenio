..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Installation
============

The best way to get an Invenio demo instance up and running immediately is by
using Docker or Vagrant, for example:

.. code-block:: console

   $ docker-compose build
   $ docker-compose up -d
   $ docker-compose run --rm web ./scripts/populate-instance.sh
   $ firefox http://127.0.0.1/records/1

This will start an Invenio demo instance containing several example records and
all the needed services such as PostgreSQL, Elasticsearch, Redis, RabbitMQ.

For a detailed walk-through on how to set up your Invenio instance, please see
our `installation documentation
<http://invenio.readthedocs.io/en/latest/installation/index.html>`_.

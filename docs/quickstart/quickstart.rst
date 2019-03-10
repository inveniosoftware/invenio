..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.
    Copyright (C) 2018 Northwestern University, Feinberg School of Medicine, Galter Health Sciences Library.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _launch-instance:

Launch an Invenio instance
==========================

.. _prerequisites:

Prerequisites
-------------
To be able to develop and run Invenio you will need the following installed and
configured on your system:

- `Docker v1.18+ <https://docs.docker.com/install>`_ and `Docker Compose v1.23+ <https://docs.docker.com/compose/install/>`_
- `NodeJS v6.x+ and NPM v4.x+ <https://nodejs.org/en/download/package-manager>`_
- `Enough virtual memory <https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-cli-run-prod-mode>`_
  for Elasticsearch (when running in Docker).
- `Cookiecutter <https://cookiecutter.readthedocs.io>`_
- `Pipenv <https://pipenv.readthedocs.io>`_

Invenio uses Cookiecutter to scaffold the boilerplate for your new instance and
uses Pipenv to manage Python dependencies in a virtual environment. Above links
contain detailed installation instructions, but the impatient can use following
commands:

.. code-block:: shell

  # Install cookiecutter if it is not already installed
  $ sudo apt-get install cookiecutter
  $ sudo apt-get install pipenv
  # or e.g.
  $ pip install --upgrade cookiecutter pipenv

.. _bootstrap:

Scaffold
--------
First step is to scaffold a new instance using the `official Invenio
cookiecutter template
<https://github.com/inveniosoftware/cookiecutter-invenio-instance>`_.

.. code-block:: shell

  $ cookiecutter gh:inveniosoftware/cookiecutter-invenio-instance --checkout v3.1
  # ...fill in the fields...

Note, the cookiecutter script will ask you to resolve some TODOs. These will
be covered in the :ref:`next-steps` section of this quick start guide.

The scaffolded instance comes by default with a toy example data model to help
you get started.

Install
-------
Now that we have our instance's source code ready we can proceed with the
initial setup of the services and dependencies of the project:

First, fire up the database, Elasticsearch, Redis and RabbitMQ:

.. code-block:: shell

  $ cd my-site/
  $ docker-compose up -d
  Creating mysite_cache_1 ... done
  Creating mysite_db_1    ... done
  Creating mysite_es_1    ... done
  Creating mysite_mq_1    ... done

If the Elasticsearch service fails to start mentioning that it requires more
virtual memory, see the following
`fix <https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-cli-run-prod-mode>`_.

Next, activate the virtualenv of the new project by running:

.. code-block:: shell

  $ pipenv shell

Finally, install all dependencies, build the JS/CSS assets, create the database
tables and create the Elasticsearch indices by running the bootstrap and setup
scripts:

.. code-block:: shell

  (my-site)$ ./scripts/bootstrap
  (my-site)$ ./scripts/setup

Run
---
You can now start the development web server and the background worker for your
new Invenio instance:

.. code-block:: shell

  (my-site)$ ./scripts/server
  * Environment: development
  * Debug mode: on
  * Running on https://127.0.0.1:5000/ (Press CTRL+C to quit)

You can now visit https://127.0.0.1:5000/ !

Continue tutorial
~~~~~~~~~~~~~~~~~
:ref:`crud-operations`

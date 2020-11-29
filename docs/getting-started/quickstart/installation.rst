..
    This file is part of Invenio.
    Copyright (C) 2015-2020 CERN.
    Copyright (C) 2018 Northwestern University, Feinberg School of Medicine, Galter Health Sciences Library.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _launch-instance:

Launch an Invenio instance
==========================

.. _prerequisites:

Prerequisites
-------------
Invenio requires the following software installed in your system:

- `Docker v1.18+ <https://docs.docker.com/install>`_ and `Docker Compose v1.23+ <https://docs.docker.com/compose/install/>`_
- `NodeJS v14.x+ and NPM v6.x+ <https://nodejs.org/en/download/package-manager>`_
- `Enough virtual memory <https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#_set_vm_max_map_count_to_at_least_262144>`_
  for Elasticsearch (when running in Docker).
- The Python package `Cookiecutter <https://cookiecutter.readthedocs.io>`_
- `Pipenv <https://pipenv.readthedocs.io>`_

.. _bootstrap:

Create an Invenio instance
--------------------------
First step is to create your new Invenio instance using the `official Invenio
cookiecutter template
<https://github.com/inveniosoftware/cookiecutter-invenio-instance>`_.

.. code-block:: shell

    $ cookiecutter gh:inveniosoftware/cookiecutter-invenio-instance --checkout v3.4

The cookiecutter initialisation procedure will prompt you with a series of questions
aiming to customise your new instance, e.g. the name of your application.

.. note::
    At the end of the initialisation, you will be warned to manually change some parts
    of the generated code marked with ``TODOs``. These will be covered in the
    :ref:`final-steps` section of this quick start guide.

Install
-------
Now that your project is generated, you will have to install all needed Python dependencies
and initialise the application services such as the database and the search engine.

From now on, the quick start guide will use the name ``my-site`` to refer to your
newly created Invenio application.

Let's run the service using ``docker-compose``:

.. code-block:: console

    $ cd my-site/
    $ docker-compose up
    Creating my-site_cache_1 ... done
    Creating my-site_db_1    ... done
    Creating my-site_es_1    ... done
    Creating my-site_mq_1    ... done

If Elasticsearch service fails to start, it might be due to its requirement for
additional virtual memory than the one provided by your system defaults.
For more information, see
`Elasticsearch documentation <https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#_set_vm_max_map_count_to_at_least_262144>`_.

Let's run the installation scripts:

.. code-block:: console

    $ ./scripts/bootstrap
    $ ./scripts/setup

This will:

* install required Python packages
* build JS/CSS assets
* create and initialise the database and the search engine

Run
---
Let's run Invenio and open your browser to https://127.0.0.1:5000/:

.. code-block:: console

    $ ./scripts/server
    * Environment: development
    * Debug mode: on
    * Running on https://127.0.0.1:5000/ (Press CTRL+C to quit)

Records
-------
Learn how to create and view records: :ref:`crud-operations`.

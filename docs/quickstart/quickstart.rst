..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.
    Copyright (C) 2018 Northwestern University, Feinberg School of Medicine, Galter Health Sciences Library.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _quickstart:

Launch an Invenio instance
==========================

.. _prerequisites:

Prerequisites
-------------
To be able to develop and run Invenio you will need the following installed and
configured on your system:

- `Docker <https://docs.docker.com/install>`_ and `Docker Compose <https://docs.docker.com/compose/install/>`_
- `NodeJS v6.x+ and NPM v4.x+ <https://nodejs.org/en/download/package-manager>`_
- `Enough virtual memory <https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-cli-run-prod-mode>`_
  for Elasticsearch.

Overview
--------
Creating your own Invenio instance requires scaffolding two code repositories
using `Cookiecutter <https://cookiecutter.readthedocs.io/en/latest/installation.html>`_:

- one code repository for the main website.
- one code repository for the data model.

These code repositories will be where you customize and develop the features of
your instance.

.. _bootstrap:

Bootstrap
---------

Before we begin, you want to make sure to have Cookiecutter installed. Invenio
leverages this tool to generate the starting boilerplate for different
components, so it will be useful to have in general. We recommend you install
it as a user package or in the virtualenv we define below.

.. code-block:: shell

  # Install cookiecutter if it is not already installed
  $ sudo apt-get install cookiecutter
  # OR, once you have created a virtualenv per the steps below, install it
  (my-repository-venv)$ pip install --upgrade cookiecutter


.. note::

  If you install Cookiecutter in the virtualenv, you will need to activate the
  virtualenv to be able to use `cookiecutter` on the command-line.

We can now begin. First, let's create a `virtualenv
<https://virtualenv.pypa.io/en/stable/installation/>`_ using `virtualenvwrapper
<https://virtualenvwrapper.readthedocs.io/en/latest/install.html>`_ in order to
sandbox our Python environment for development:

.. code-block:: shell

  $ mkvirtualenv my-repository-venv

Now, let's scaffold the instance using the `official cookiecutter template
<https://github.com/inveniosoftware/cookiecutter-invenio-instance>`_.

.. code-block:: shell

  (my-repository-venv)$ cookiecutter gh:inveniosoftware/cookiecutter-invenio-instance --checkout v3.0
  # ...fill in the fields...

Now that we have our instance's source code ready we can proceed with the
initial setup of the services and dependencies of the project:

.. code-block:: shell

  # Fire up the database, Elasticsearch, Redis and RabbitMQ
  (my-repository-venv)$ cd my-site/
  (my-repository-venv)$ docker-compose up -d
  Creating network "mysite_default" with the default driver
  Creating mysite_cache_1 ... done
  Creating mysite_db_1    ... done
  Creating mysite_es_1    ... done
  Creating mysite_mq_1    ... done

If the Elasticsearch service fails to start mentioning that it requires more virtual memory,
see the following fix <https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-cli-run-prod-mode>`_.

.. _customize:

Customize
---------

This instance doesn't have a data model defined, and thus it doesn't include
any records you can search and display. To scaffold a data model for the
instance we will use the `official data model cookiecutter template
<https://github.com/inveniosoftware/cookiecutter-invenio-datamodel>`_:

.. code-block:: shell

  (my-repository-venv)$ cd ..  # switch back to the parent directory
  (my-repository-venv)$ cookiecutter gh:inveniosoftware/cookiecutter-invenio-datamodel --checkout v3.0
  # ...fill in the fields...

For the purposes of this guide, our data model folder is `my-datamodel`.

Let's also install the data model in our virtualenv:

.. code-block:: shell

  (my-repository-venv)$ pip install -e .


.. note::

   Once you publish your data model somewhere, i.e. the `Python Package Index
   <https://pypi.org/>`_, you might want to edit your instance's `setup.py` file
   to add it there as a dependence.

Now that we have a data model installed we can create database tables and
Elasticsearch indices:

.. code-block:: shell

  (my-repository-venv)$ cd my-site
  (my-repository-venv)$ ./scripts/bootstrap
  (my-repository-venv)$ ./scripts/setup

Run
---
You can now run the necessary processes for the instance:

.. code-block:: shell

  (my-repository-venv)$ ./scripts/server
  * Environment: development
  * Debug mode: on
  * Running on https://127.0.0.1:5000/ (Press CTRL+C to quit)

You can now visit https://127.0.0.1:5000/ !

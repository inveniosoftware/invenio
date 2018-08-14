..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.
    Copyright (C) 2018 Northwestern University, Feinberg School of Medicine, Galter Health Sciences Library.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _quickstart:

Quickstart
==========

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

  # Install cookiecutter locally or upgrade it if already installed
  $ pip install --user --upgrade cookiecutter
  # OR, once you have created a virtualenv per the steps below, install it
  (my-repository-venv)$ pip install --upgrade cookiecutter

.. note::

  If you install Cookiecutter in the virtualenv, you will need to activate the
  virtualenv to be able to use `cookiecutter` on the command-line.


We can now begin. First, let's create a `virtualenv <https://virtualenv.pypa.io/en/stable/installation/>`_
using `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/install.html>`_
in order to sandbox our Python environment for development:

.. code-block:: shell

  $ mkvirtualenv my-repository-venv

Now, let's scaffold the instance using the `official cookiecutter template
<https://github.com/inveniosoftware/cookiecutter-invenio-instance>`_.

.. code-block:: shell

  (my-repository-venv)$ cookiecutter gh:inveniosoftware/cookiecutter-invenio-instance --checkout v3.0
  project_name [My site]: My repository
  project_shortname [my-repository]:
  project_site [my-repository.com]:
  package_name [my_repository]:
  github_repo [my-repository/my-repository]:
  description [Invenio digital library framework.]: My repository digital library
  author_name [CERN]: Me
  author_email [info@inveniosoftware.org]: me@my-repository.com
  year [2018]:
  copyright_holder [Me]:
  transifex_project [my-repository]:
  Select database:
  1 - postgresql
  2 - mysql
  Choose from 1, 2 [1]:
  Select elasticsearch:
  1 - 6
  2 - 5
  Choose from 1, 2 [1]:
  # ... project scaffolding output ...

Now that we have our instance's source code ready we can proceed with the
initial setup of the services and dependencies of the project:

.. code-block:: shell

  # Fire up the database, Elasticsearch, Redis and RabbitMQ
  (my-repository-venv)$ cd my-repository/
  (my-repository-venv)$ docker-compose up -d
  Creating network "myrepository_default" with the default driver
  Creating myrepository_cache_1 ... done
  Creating myrepository_db_1    ... done
  Creating myrepository_es_1    ... done
  Creating myrepository_mq_1    ... done
  # Install dependencies and generate static assets
  (my-repository-venv)$ ./scripts/bootstrap

.. note::

    Make sure you have `enough virtual memory
    <https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-cli-run-prod-mode>`_
    for Elasticsearch in Docker:

    .. code-block:: shell

        # Linux
        $ sysctl -w vm.max_map_count=262144

        # macOS
        $ screen ~/Library/Containers/com.docker.docker/Data/com.docker.driver.amd64-linux/tty
        <enter>
        linut00001:~# sysctl -w vm.max_map_count=262144


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

  (my-repository-venv)$ cd my-datamodel
  (my-repository-venv)$ pip install --editable .

Now that we have a data model installed we can create database tables and
Elasticsearch indices:

.. code-block:: shell

  (my-repository-venv)$ cd ../my-repository
  (my-repository-venv)$ ./scripts/bootstrap
  (my-repository-venv)$ ./scripts/setup

Currently, the system doesn't have any users, but more important, it doesn't
have an administrator. Let's create one:

.. code-block:: shell

  (my-repository-venv)$ my-repository users create admin@my-repository.com -a --password=<secret>
  (my-repository-venv)$ my-repository roles add admin@my-repository.com admin

Run
---
You can now run the necessary processes for the instance:

.. code-block:: shell

  # ...in a new terminal, start the celery worker
  $ workon my-repository-venv
  (my-repository-venv)$ celery worker --app invenio_app.celery --loglevel INFO

  # ...in a new terminal, start the flask development server
  $ workon my-repository-venv
  (my-repository-venv)$ ./scripts/server
  * Environment: development
  * Debug mode: on
  * Running on https://127.0.0.1:5000/ (Press CTRL+C to quit)

You can now visit https://127.0.0.1:5000/ !

.. note::

    Because we are using a self-signed SSL certificate to enable HTTPS, your
    web browser will probably display a warning when you access the website.
    You can usually get around this by following the browser's instructions in
    the warning message. For CLI tools like ``curl``, you can ignore the SSL
    verification via the ``-k/--insecure`` option.

Create a record
^^^^^^^^^^^^^^^

By default, the data model has a records REST API endpoint configured, which
allows performing CRUD and search operations over records. Let's create a
simple record via ``curl``:

.. code-block:: shell

  $ curl -k --header "Content-Type: application/json" \
      --request POST \
      --data '{"title":"Some title", "contributors": [{"name": "Doe, John"}]}' \
      https://localhost:5000/api/records/?prettyprint=1

  {
    "created": "2018-05-23T13:28:19.426206+00:00",
    "id": 1,
    "links": {
      "self": "https://localhost:5000/api/records/1"
    },
    "metadata": {
      "contributors": [
        {
          "name": "Doe, John"
        }
      ],
      "id": 1,
      "title": "Some title"
    },
    "revision": 0,
    "updated": "2018-05-23T13:28:19.426213+00:00"
  }

Display a record
^^^^^^^^^^^^^^^^

You can now visit the record's page at https://localhost:5000/records/1, or
fetch it via the REST API:

.. code-block:: shell

  # You can find this URL under the "links.self" key of the previous response
  $ curl -k --header "Content-Type: application/json" \
      https://localhost:5000/api/records/1?prettyprint=1

  {
    "created": "2018-05-23T13:28:19.426206+00:00",
    "id": 1,
    "links": {
      "self": "https://localhost:5000/api/records/1"
    },
    "metadata": {
      "contributors": [
        {
          "name": "Doe, John"
        }
      ],
      "id": 1,
      "title": "Some title"
    },
    "revision": 0,
    "updated": "2018-05-23T13:28:19.426213+00:00"
  }

Search for records
^^^^^^^^^^^^^^^^^^

The record you created before, besides being inserted into the database, is
also indexed in Elasticsearch and available for searching. You can search for
it via the Search UI page at https://localhost:5000/search, or via the REST
API:

.. code-block:: shell

  $ curl -k --header "Content-Type: application/json" \
      https://localhost:5000/api/records/?prettyprint=1

  {
    "aggregations": {
      "type": {
        "buckets": [],
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0
      }
    },
    "hits": {
      "hits": [
        {
          "created": "2018-05-23T13:28:19.426206+00:00",
          "id": 1,
          "links": {
            "self": "https://localhost:5000/api/records/1"
          },
          "metadata": {
            "contributors": [
              {
                "name": "Doe, John"
              }
            ],
            "id": 1,
            "title": "Some title"
          },
          "revision": 0,
          "updated": "2018-05-23T13:28:19.426213+00:00"
        }
      ],
      "total": 1
    },
    "links": {
      "self": "https://localhost:5000/api/records/?size=10&sort=mostrecent&page=1"
    }
  }

Next steps
----------
Although we can run and interact with the instance, we're not quite there yet
in terms of having a proper Python package that's ready to be tested and
deployed to a production environment.

You may have noticed that after running the ``cookiecutter`` command for the
instance and the data model, there was a note for checking out some of the
TODOs. You can run the following command in each code repository directory
to see a summary of the TODOs again:

.. code-block:: console

  $ grep --color=always --recursive --context=3 --line-number TODO .

Let's have a look at some of them one-by-one and explain what they are for:

1. Creating a ``requirements.txt``: This file is used for pinning the Python
   dependencies of your instance to specific versions in order to achieve
   reproducible builds when deploying your instance. You can generate this file
   in the following fashion (note, this is only for the *instance* and not
   the *data model*):

   .. code-block:: console

      $ cd my-repository/
      $ workon my-repository-venv
      (my-repository-venv)$ pip install --editable .
      (my-repository-venv)$ pip install pip-tools
      (my-repository-venv)$ pip-compile

2. Python packages require a ``MANIFEST.in`` which specifies what files are
   part of the distributed package. You can update the existing file by running
   the following commands:

   .. code-block:: console

      (my-repository-venv)$ git init
      (my-repository-venv)$ git add --all
      (my-repository-venv)$ pip install --editable .[all]
      (my-repository-venv)$ check-manifest --update

3. Translations configuration (``.tx/config``): You might also want to generate
   the necessary files to allow localization of the instance in different
   languages via the `Transifex platform <https://www.transifex.com/>`_:

   .. code-block:: console

      (my-repository-venv)$ python setup.py extract_messages
      (my-repository-venv)$ python setup.py init_catalog -l en
      (my-repository-venv)$ python setup.py compile_catalog

   Ensure project has been created on Transifex under the my-repository
   organisation.

   Install the transifex-client

   .. code-block:: console

      (my-repository-venv)$ pip install transifex-client

   Push source (.pot) and translations (.po) to Transifex:

   .. code-block:: console

      (my-repository-venv)$ tx push --skip --translations

   Pull translations for a single language from Transifex

   .. code-block:: console

      (my-repository-venv)$ tx pull --language en

Testing
^^^^^^^

In order to run tests for the instance, you can run:

.. code-block:: shell

  # Install testing dependencies
  $ workon my-repository-venv
  # The following makes sure you have the tests dependencies installed
  # if you already installed the instance via .[all] you can skip this install
  (my-repository-venv)$ pip install --editable .[tests]
  (my-repository-venv)$ ./run-tests.sh  # will run all the tests...
  # ...or to run individual tests
  (my-repository-venv)$ pytest tests/ui/test_views.py::test_ping

Documentation
^^^^^^^^^^^^^

In order to build and preview the instance's documentation, you can run the
`setup.py build_sphinx` command:

.. code-block:: shell

  $ workon my-repository-venv
  # The following makes sure you have the docs dependencies installed
  # if you already installed the instance via .[all] you can skip this install
  (my-repository-venv)$ pip install --editable .[docs]
  (my-repository-venv)$ python setup.py build_sphinx

Open up ``docs/_build/html/index.html`` in your browser to see the documentation.

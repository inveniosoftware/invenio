..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

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
- `Cookiecutter <https://cookiecutter.readthedocs.io/en/latest/installation.html>`_
- `Enough virtual memory configured to run Elasticsearch
  <https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-cli-run-prod-mode>`_
- `Virtualenv <https://virtualenv.pypa.io/en/stable/installation/>`_ and `Virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/install.html>`_
- `NodeJS v6.x and NPM v4.x <https://nodejs.org/en/download/package-manager>`_

Minimal instance
----------------

To setup a minimal preview of Invenio you can run the following commands:

.. code-block:: shell

  $ cokiecutter gh:inveniosoftware/cookiecutter-invenio-instance -c v3.0
  $ cd my-site
  $ docker-compose -f docker-compose.full.yml up -d
  $ docker-compose -f docker-compose.full.yml run --rm web-ui ./scripts/setup
  $ firefox https://localhost

.. note::

    Because we are using a self-signed SSL certificate to enable HTTPS, your
    web browser will probably display a warning when you access the website.
    You can usuaslly get around this by following the browser's instructions in
    the warning message.

This instance doesn't have a data model defined, and thus it doesn't include
any records you can search and display. Creating a data model and loading
records is described in detail throughout the following sections.

Full instance
-------------

Overview
^^^^^^^^

Bootstrapping a complete Invenio instance involves two parts:

1. Creating and configuring the main instance.
2. Creating, configure the data model and integrating it into the instance.

Creating the instance
^^^^^^^^^^^^^^^^^^^^^

First, let's scaffold the instance using the `official cookiecutter template
<https://github.com/inveniosoftware/cookiecutter-invenio-instance>`_.
Cookiecutter will prompt you to fill in some information:

.. code-block:: shell

  $ cookiecutter gh:inveniosoftware/cookiecutter-invenio-instance -c v3.0
  project_name [My site]: Foo Library
  project_shortname [foo-library]: <enter>
  project_site [foo-library.com]: <enter>
  package_name [foo_library]: <enter>
  github_repo [foo-library/foo-library]: <enter>
  description [Invenio digital library framework.]: <enter>
  author_name [CERN]: Foo
  author_email [info@inveniosoftware.org]: info@foo.org
  year [2018]: <enter>
  copyright_holder [Foo]: <enter>
  transifex_project [foo-library]: <enter>
  Select database:
  1 - postgresql
  2 - mysql
  Choose from 1, 2 [1]: <enter>
  Select elasticsearch:
  1 - 6
  2 - 5
  Choose from 1, 2 [1]: <enter>
  # Some automatic setup will run now. Keep this output,
  # since it will include some TODOs for later.

The next step is to create a ``virtualenv`` in order to sandbox our Python
environment for development:

.. code-block:: shell

  $ cd foo-library
  $ mkvirtualenv foo-library

Now we can proceed with fixing the TODOs mentioned in the cookiecutter output:

requirements.txt
""""""""""""""""

This file is used for pinning the Python dependencies of your instance to
specific versions in order to achieve reproducible builds when deploying your
instance. You can generate this file in the following fashion:

.. code-block:: shell

  $ pip install -e .
  $ pip install pip-tools
  $ pip-compile

.. _manifest-in:

MANIFEST.in
"""""""""""

Python packages require a ``MANIFEST.in`` which specifies what files are part
of the distributed package. You can update the existing file by running the
following commands:

.. code-block:: shell

  $ git init
  $ git add -A
  $ pip install -e .[all]
  $ check-manifest -u

Translations configuration (.tx/config)
"""""""""""""""""""""""""""""""""""""""

You might also want to generate the necessary files to allow localization of
the instance in different languages via the `Transifex platform
<https://www.transifex.com/>`_:

.. code-block:: shell

  $ python setup.py extract_messages
  $ python setup.py init_catalog -l en
  $ python setup.py compile_catalog
  # Ensure project has been created on Transifex under the foo-library organisation
  # Install the transifex-client
  $ pip install transifex-client
  # Push source (.pot) and translations (.po) to Transifex
  $ tx push -s -t
  # Pull translations for a single language from Transifex
  $ tx pull -l en
  # Pull translations for all languages from Transifex
  $ tx pull -a

Setup and Bootstrapping
"""""""""""""""""""""""

Now that the you're done with the initial configuration of the project's source
code you can proceed with the initial setup of services and fixtures. You can
then bootstrap the instance by building the necessary static assets:

.. code-block:: shell

  # First start the services that Invenio depends on via docker-compose
  $ docker-compose up -d
  $ ./scripts/setup
  $ ./scripts/bootstrap

Running the instance
""""""""""""""""""""

You can now run the necessary processes for the instance:

.. code-block:: shell

  # ...in a new terminal, start the celery worker
  $ workon foo-library
  $ celery -A invenio_app.celery -l INFO

  # ...in a new terminal, start the flask development server
  $ workon foo-library
  $ ./scripts/server
  * Environment: development
  * Debug mode: on
  * Running on https://127.0.0.1:5000/ (Press CTRL+C to quit)

Currently the system doesn't have any users, but more important, it doesn't
have an administrator. Let's create one:

.. code-block:: shell

  $ foo-library users create admin@foo-library.com -a --password=<secret>
  $ foo-library roles add admin@foo-library.com admin

Testing
"""""""

In order to run the default test that were generated ofr the instance you can
run the following:

.. code-block:: shell

  $ pip install -e .[tests]
  $ ./run-tests.sh  # will run all the tests...
  # ...or to run individual tests
  $ py.test tests/ui/test_views.py::test_ping

Documentation
"""""""""""""

In order to build and preview the instance's documentation you can run the
following commands:

.. code-block:: shell

  $ cd docs
  $ make html
  $ firefox _build/html/index.html

Upgrading
"""""""""

If there are any new changes (e.g. new tables, indices, etc) you apply them by
running:

.. code-block:: shell

  $ ./scripts/update

Creating the data model
^^^^^^^^^^^^^^^^^^^^^^^

To scaffold a data model for the instance you can use the `official data model
cookiecutter template
<https://github.com/inveniosoftware/cookiecutter-invenio-datamodel>`_.
Cookiecutter will prompt you to fill in some information:

.. code-block:: shell

  $ cookiecutter gh:inveniosoftware/cookiecutter-invenio-datamodel -c v3.0
  project_name [My datamodel]: foo-datamodel
  project_shortname [foo-datamodel]:
  package_name [foo_datamodel]:
  github_repo [foo-datamodel/foo-datamodel]:
  description [Invenio data model.]:
  author_name [CERN]: Foo
  author_email [info@inveniosoftware.org]:
  year [2018]:
  copyright_holder [Foo]:
  extension_class [foodatamodel]:
  pid_name [id]:
  # Some automatic setup will run now. Keep this output,
  # since it will include some TODOs for later.

Let's install the datamodel as a Python package in our virtualenv:

.. code-block:: shell

  $ workon foo-library
  $ cd foo-datamodel
  $ pip install -e .

In order to continue we'll have to address some of the TODOs, as we did for the
instance. One of them is :ref:`updating MANIFEST.in <manifest-in>`. The other
one is adding the datamodel's configuration in our instance:

.. code-block:: python

  # foo_library/config.py
  ...
  from foo_datamodel.config import FOO_DATAMODEL_RECORDS_REST_ENDPOINTS
  RECORDS_REST_ENDPOINTS = {
      **FOO_DATAMODEL_RECORDS_REST_ENDPOINTS,
  }
  ...

Creating a record
"""""""""""""""""

By default the datamodel has an Invenio-Records-REST API endpoint configured,
which allows accessing a record and retrieving


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
      "title": "Some title"
    },
    "revision": 0,
    "updated": "2018-05-23T13:28:19.426213+00:00"
  }

Showing a record
""""""""""""""""

Now you can fetch a single record by accessing the "self" link from the
previous response:

.. code-block:: shell

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
      "title": "Some title"
    },
    "revision": 0,
    "updated": "2018-05-23T13:28:19.426213+00:00"
  }

You can also visit the record's page at https://localhost:5000/records/1.

Searching records
"""""""""""""""""

The record you created before, besides being inserted to the database, are also
indexed in Elasticsearch and become available for searching via the REST API:

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

You can also search via the UI page at https://localhost:5000/search.

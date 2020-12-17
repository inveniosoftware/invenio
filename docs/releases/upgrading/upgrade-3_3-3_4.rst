..
    This file is part of Invenio.
    Copyright (C) 2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _upgrade-3_3-3_4:

Upgrading from Invenio v3.3 to v3.4
===================================

If you have your instance of Invenio v3.3 already up and running and
you would like to upgrade to version v3.4 you don't need to set up your
project from scratch. The goal of this guide is to show the steps to upgrade
your project without losing any of your work.

Bootstrap 3 to Semantic UI
--------------------------

You can upgrade to Invenio v3.4 without migrating to Semantic UI. However,
Invenio v3.4 is deprecating the Bootstrap 3 templates, thus you should
already now **plan on allocating time for migrating your templates to Semantic
UI during 2021**.


Pipfile modifications
---------------------

The most important changes that you will have to make are in ``Pipfile``.

1. Change the Invenio version:

.. code::

    invenio = { version = ">=3.4.0,<3.5.0", extras = ["base", "auth", "metadata", "files", "postgresql", "elasticsearch7" ]}


2. Make sure that your database and Elasticsearch version matches your
   installation. In above example the database is ``postgresql`` and the
   Elasticsearch version is ``elasticsearch7``.

3. Add the following line to ``Pipfile`` (note that most pytest dependencies
   are now managed via ``pytest-invenio``):

.. code:: diff

     [packages]
    -Babel = ">=2.4.0"
    -Flask-BabelEx = ">=0.9.3"
    +lxml = ">=4.3.0,<5.0.0"


.. code:: diff

     [dev-packages]
    -check-manifest = ">=0.35"
    -coverage = ">=4.4.1"
    -Flask-Debugtoolbar = ">=0.10.1"
    -isort = ">=4.3"
    -mock = ">=2.0.0"
    -pydocstyle = ">=2.0.0"
    -pytest = ">=3.3.1"
    -pytest-cov = ">=2.5.1"
    -pytest-invenio = ">=1.2.1,<1.3.0"
    -pytest-mock = ">=1.6.0"
    -pytest-pep8 = ">=1.0.6"
    -pytest-random-order = ">=0.5.4"
    -pytest-runner = ">=3.0.0,<5"
    -Sphinx = ">=1.5.1"
    +pytest-invenio = ">=1.4.0,<1.5.0"
    +Sphinx = ">=3,<4"

4. Add the following line to your ``config.py`` file:

.. code:: python

    APP_THEME = ['bootstrap3']

5. Remove your ``Pipfile.lock`` file and run `./scripts/bootstrap`

Celery 5.0.x
------------

**Following is only applicable if you use Celery 5.0.x**.

1. First check which version of Celery you use by running ``pipenv run pip freeze | grep ^celery``.


2. Apply the following changes to ``scripts/server``:

.. code:: diff

    -pipenv run celery worker -A invenio_app.celery -l INFO & pid_celery=$!
    +pipenv run celery -A invenio_app.celery worker -l INFO & pid_celery=$!


2. Apply the following changes to ``docker-compose.full.yml``:

.. code:: diff

    -    command: ["celery worker -A invenio_app.celery --loglevel=INFO"]
    +    command: ["celery -A invenio_app.celery worker --loglevel=INFO"]

..
    This file is part of Invenio.
    Copyright (C) 2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _upgrade-3_1-3_2:

Upgrading from Invenio v3.2 to v3.3
===================================

If you have your instance of Invenio v3.2 already up and running and
you would like to upgrade to version v3.3 you don't need to set up your
project from scratch. The goal of this guide is to show the steps to upgrade
your project without losing any of your work.

Pipfile modifications
---------------------

The most important changes that you will have to make are in ``Pipfile``.

1. Change the Invenio version:

.. code::

    invenio = { version = ">=3.3.0,<3.4.0", extras = ["base", "auth", "metadata", "files", "postgresql", "elasticsearch7" ]}


2. Make sure that your database and Elasticsearch version matches your
   installation. In above example the database is ``postgresql`` and the
   Elasticsearch version is ``elasticsearch7``.

3. Remove the following line from Pipfile:

.. code:: diff

    - lxml = ">=3.5.0,<4.2.6"
      marshmallow = ">=3.0.0,<4.0.0"
    - SQLAlchemy-Utils = ">=0.33.1,<0.36"

4. Install the new packages in ``Pipfile`` by running the following commands:

.. code:: bash

    # Update Pipfile.lock
    pipenv lock --dev

    # Install packages specified in Pipfile.lock
    pipenv sync --dev

    # Install application code and entrypoints from 'setup.py'
    pipenv run pip install -e .

    # Build assets
    pipenv run invenio collect -v
    pipenv run invenio webpack buildall

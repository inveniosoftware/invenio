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

Pipfile modifications
---------------------

The most important changes that you will have to make are in ``Pipfile``.

1. Change the Invenio version:

.. code::

    invenio = { version = ">=3.4.0,<3.5.0", extras = ["base", "auth", "metadata", "files", "postgresql", "elasticsearch7" ]}


2. Make sure that your database and Elasticsearch version matches your
   installation. In above example the database is ``postgresql`` and the
   Elasticsearch version is ``elasticsearch7``.

3. Add the following line to ``Pipfile``:

.. code:: diff

    +lxml = ">=4.3.0,<5.0.0"
    -pytest = ">=3.3.1"
    +pytest = ">=3.3.1, <6.0.0"

4. Add the following line to your ``config.py`` file:

.. code:: diff

    APP_THEME = ['bootstrap3']

5. Then remove your ``Pipfile.lock`` file.

6. Finally run `./scripts/bootstrap`.

.. note::

    This guide is responsible to help you upgrade to Invenio 3.4 while
    keeping `Bootstrap` as your theme.
    In the near future we will add a subsequent section to help you migrate
    to `Semantic UI` as well.

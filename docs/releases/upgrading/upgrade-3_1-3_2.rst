..
    This file is part of Invenio.
    Copyright (C) 2015-2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _upgrade-3_1-3_2:

Upgrading from Invenio v3.1 to v3.2
===================================

If you have your instance of Invenio v3.1 already up and running and
you would like to upgrade to version v3.2 you don't need to set up your
project from scratch. The goal of this guide is to show the steps to upgrade
your project without losing any of your work.


Pipfile modifications
---------------------

The most important changes that you will have to make are in ``Pipfile``.

First you need to change the Invenio version:

::

    invenio = { version = "==3.2.0", extras = ["base", "auth", "metadata", "files", "postgresql", "elasticsearch7" ]}

If you want to use the new files bundle make sure you include the ``files``
bundle. Add any additional :ref:`bundles` you would like in your project in
``extras``.

Make sure that your database and Elasticsearch version matches your
installation. In above example the database is ``postgresql`` and the
Elasticsearch version is ``elasticsearch7``.

To install the new packages in ``Pipfile`` run the following commands:

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


Database tables
---------------
Changes have been made to the database from Invenio 3.1 so you will need to
upgrade the database by running the latest Alembic recipes:

.. code:: bash

    invenio alembic upgrade

Your database should now have the latest changes.


Files
-----
To integrate the files bundle with your Invenio instance, please see the guide
to configure files for Invenio 3.2.

For files to work properly ensure that the config variables
``RECORDS_FILES_REST_ENDPOINTS`` and ``FILES_REST_PERMISSION_FACTORY`` have
been configured properly.

.. note::

    If you are upgrading from a previous cookiecutter instance and you updated
    ``records/config.py``, please remember to update the changed config keys in
    ``records/ext.py``.

Uploading files
~~~~~~~~~~~~~~~
Records created after you upgraded to Invenio 3.2 will support files
out-of-the-box as long as files are configured properly.

However, if you have records created by previous versions of Invenio they will
not work with files because there is no bucket attached to the record.
To support uploading files to an old record you first need to create
a bucket for each record you want to enable files support for and update the
record's metadata.

Invenio currently doesn't provide a script for this migration. However, here a
snippet that can help with the migration:

.. code-block:: python

    from invenio_db import db
    from invenio_records_files.api import Record
    from invenio_records_files.models import RecordsBuckets

    # Get all old records as invenio_records_files.api:Record objects
    old_records = # ...
    for record in old_records:
        # Create a bucket
        if not record.bucket_id:
            bucket = Record.create_bucket(record)
            if bucket:
                # Attach bucket to the record
                Record.dump_bucket(record, bucket)
                RecordsBuckets.create(record=record.model, bucket=bucket)
                record.commit()
    db.session.commit


Elasticsearch
-------------
Invenio 3.2 comes with support for Elasticsearch 6 and 7. Support for
Elasticsearch v2 and v5 has been deprecated and will be removed in future
releases. It's recommended to upgrade your Elasticsearch version to stay
up-to-date.

.. note::

    If you're upgrading to Elasticsearch v7, don't forget to add mappings for
    v7.

There are currently two paths to upgrade to Elasticsearch v7: upgrade by
reindexing all your records or by using Elasticsearch rolling upgrades.

Upgrade to v7 by reindexing
~~~~~~~~~~~~~~~~~~~~~~~~~~~
The easiest way to upgrade to v7 is to upgrade your Invenio installation,
install Elasticsearch v7 and then reindex all your records stored in the
database with the following command:

.. code-block:: console

    $ invenio index reindex -t <pid_type>

.. warning::

    This command will destroy your indexed records with the provided
    ``pid_type`` and reindex all records.

However, this means you have to reindex everything and will require some
downtime

.. _rolling-upgrades:

Upgrade by Elasticsearch rolling upgrades
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Elasticsearch supports `rolling upgrades <https://www.elastic.co/guide/en/elasticsearch/reference/current/setup-upgrade.html>`_
which can upgrade your Elasticsearch installation between certain versions
without any interruption to your service. This will allow you to upgrade from
v5 to v6 or v6 to v7, but not from v5 to v7 due to index incompatibilities.

Upgrade by index migration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This section describes an unreleased feature.

Invenio v3.3 will add support for online index migration. This will allow you
to upgrade between Elasticsearch versions, migrate indexes between clusters as
well as upgrade Elasticsearch mappings. You can read more about this upcoming
feature on:

- `Keeping up with Elasticsearch <https://inveniosoftware.org/blog/2019-05-24-sprint-report/>`_
- `Invenio-Index-Migrator <https://github.com/inveniosoftware/invenio-index-migrator>`_

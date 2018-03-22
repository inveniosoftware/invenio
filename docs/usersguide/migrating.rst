..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Migrating to v3
===============

Dump Invenio v1.2 or v2.1 data
------------------------------

Dump CLI installation
^^^^^^^^^^^^^^^^^^^^^

There are several ways of installing ``invenio-migrator`` in your Invenio v1.2 or
v2.1 production environment, the one we recommend is using `Virtualenv
<https://virtualenv.pypa.io/en/stable/>`_ to avoid any interference with the
currently installed libraries:

.. code-block:: bash

    $ sudo pip install virtualenv virtualenvwrapper
    $ source /usr/local/bin/virtualenvwrapper.sh
    $ mkvirtualenv migration --system-site-packages
    $ workon migration
    $ pip install invenio-migrator --pre
    $ inveniomigrator dump --help

It is important to use the option ``--system-site-packages`` as Invenio-Migrator
will use Invenio legacy python APIs to perform the dump.
The package ``virtualenvwrapper`` is not required but it is quite convenient.

Dump records and files
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $ mkdir /vagrant/dump
    $ cd /vagrant/dump/
    $ inveniomigrator dump records

This will generate one or more JSON files containing 1000 records each tops, with
the following information:

* The record id.
* The record metadata, stored in the ``record`` key there is a list with one
  item for each of the revisions of the record, and each item of the list
  contains the MARC21 representation of the record plus the optional JSON.
* The files linked with the record, like for the record metadata it is a list
  with all the revisions of the files.
* Optionally it also contains the collections the record belongs to.

For more information about how to dump records and files see the `Usage section
<http://invenio-migrator.readthedocs.io/en/latest/usage.html>`_ of the
Invenio-Migrator documentation.

The file path inside the Invenio legacy installation will be included
in the dump and used as file location for the new Invenio v3 installation.
If you are able to mount the file system following the same pattern in your
Invenio v3 machines, there shouldn't be any problem, but if you can't do it,
then you need to copy over the files folder manually using your favorite method,
i.e.:

.. code-block:: bash

    $ cd /opt/invenio/var/data
    $ tar -zcvf /vagrant/dump/files.tar.gz files

**Pro-tip**: Maybe you want to have different data models in your new
installation depending on the nature of the record, i.e. bibliographic records
vs authority records. In this case one option is to dump them in different files
using the ``--query`` argument when dumping from your legacy installation:

.. code-block:: bash

   $ inveniomigrator dump records --query '-980__a:AUTHORITY' --file-prefix bib
   $ inveniomigrator dump records --query '980__a:AUTHORITY' --file-prefix auth


Things
^^^^^^

The dump command of the Invenio-Migrator works with, what we called, *things*. A
*thing* is an entity you want to dump from Invenio legacy, in the previous
example the *thing* was records.
The list of *things* Invenio-Migrator can dump by default is listed via
entry-points in the ``setup.py``, this not only help us add new dump scripts
easily, but also allows anyone to create their own from outside the
Invenio-Migrator.

You can read more about which *things* are already supported by the
`Invenio-Migrator documentation <http://invenio-migrator.readthedocs.io>`_ and
also we have section dedicated to :ref:`entrypoints` where you can learn how we
used them to extend Invenio's functionality.

Load data into Invenio v3
-------------------------

Load CLI installation
^^^^^^^^^^^^^^^^^^^^^

Invenio-Migrator can be installed in any Invenio 3 environment using PyPi and
the extra dependencies ``loader``:

.. code-block:: bash

    $ pip install invenio-migrator[loader]

Depending on what you want to load you might need to have installed other
packages, i.e. to load communities from Invenio 2.1 ``invenio-communities``
needs to be installed.

This will add to your Invenio application a new set of commands under ``dumps``:

.. code-block:: bash

   $ invenio dumps --help


Load records and files
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $ invenio dumps loadrecords /vagrant/dump/records_dump_0.json

This will generate one celery task to import each of the records inside the
dump.

**Pro-tip**: By default Invenio-Migrator uses the bibliographic MARC21 standard
to transform and load the records, we now that this might not be the case to all
Invenio v3 installation, i.e authority records. By changing
``MIGRATOR_RECORDS_DUMP_CLS`` and ``MIGRATOR_RECORDS_DUMPLOADER_CLS`` you can
customize the behavior of the loading command. There is a full chapter in the
Invenio-Migrator documentation about `customizing loading
<http://invenio-migrator.readthedocs.io/en/latest/usage.html#customizing-loading>`_
if you want more information.

Loaders
^^^^^^^

Each of the entities that can be loaded by Invenio-Migrator have a companion
command generally prefixed by *load*, i.e. ``loadrecords``.

The loaders are similar to the things we describe previously, but in this case,
instead of entry-points, if you want to extend the default list of loaders it
can be done adding a new command to ``dumps``, more information about the
loaders can be found in the `Invenio-Migrator documentation
<http://invenio-migrator.readthedocs.io>`_ and on how to add more commands in
the `click documentation <http://click.pocoo.org/5/>`_.

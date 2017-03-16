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

    sudo pip install virtualenv virtualenvwrapper
    source /usr/local/bin/virtualenvwrapper.sh
    mkvirtualenv migration --system-site-packages
    workon migration
    pip install invenio-migrator --pre
    inveniomigrator dump --help

It is important to use the option ``--system-site-packages`` as Invenio-Migrator
will use Invenio legacy python APIs to perform the dump.
The package ``virtualenvwrapper`` is not required but it is quite convenient.

Dump records and files
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    mkdir /vagrant/dump
    cd /vagrant/dump/
    inveniomigrator dump records

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

**ProTip**: The file path inside the Invenio legacy installation will be included
in the dump and used as file location for the new Invenio v3 installation.
If you are able to mount the file system following the same pattern in your
Invenio v3 machines, there shouldn't be any problem, but if you can't do it,
then you need to copy over the files folder manually using your favorite method,
i.e.:

.. code-block:: bash

    cd /opt/invenio/var/data
    tar -zcvf /vagrant/dump/files.tar.gz files

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

    pip install invenio-migrator[loader]

Depending on what you want to load you might need to have installed other
packages, i.e. to load communities from Invenio 2.1 ``invenio-communities``
needs to be installed.

Load records and files
^^^^^^^^^^^^^^^^^^^^^^



Loaders
^^^^^^^



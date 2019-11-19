..
    This file is part of Invenio.
    Copyright (C) 2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _backends:


Configure your Storage Backend
==============================

A storage backend serves as an interface for the underlying file access.

In the `config.py` file of your application, you can use the variable
`FILES_REST_STORAGE_FACTORY <https://invenio-files-rest.readthedocs.io/en/latest/configuration.html#invenio_files_rest.config.FILES_REST_STORAGE_FACTORY>`_
to provide your custom factory that will be used to create the storage
instance.

The module provides an abstract layer for storage implementation that allows
to swap storages easily. The default storage solution for saving files locally
for Invenio-Files-REST is `PyFilesystem <https://www.pyfilesystem.org/>`_,
which can be replaced according to your needs even with a cloud
storage like `Invenio-S3 <https://invenio-s3.readthedocs.io/>`_ which
offers integration with any S3 REST API compatible object storage.


Build your own Storage Backend
------------------------------

If you would like to provide your own implementation as a storage backend, it
is requires to subclass the `FileStorage <https://invenio-files-rest.readthedocs.io/en/latest/api.html#invenio_files_rest.ext.FileStorage>`_
class, and implement for some of its core methods.

The following methods are required to be implemented for the storage to work:

* :code:`initialize`
* :code:`open`
* :code:`save`
* :code:`update`
* :code:`delete`

The base class provides also some optional methods to implement to extend the
existing functionality:

* :code:`send_file`
* :code:`checksum`
* :code:`copy`
* :code:`_init_hash`
* :code:`_compute_checksum`
* :code:`_write_stream`

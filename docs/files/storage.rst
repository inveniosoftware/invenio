..
    This file is part of Invenio.
    Copyright (C) 2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _backends:


Configure your Storage Backend
==============================

In order to get started let's setup and configure a storage backend.
Storage will serve as an interface for the actual file access.

In the configuration of the application, the variable
`invenio_files_rest.config.FILES_REST_STORAGE_FACTORY <https://invenio-files-rest.readthedocs.io/en/latest/configuration.html#invenio_files_rest.config.FILES_REST_STORAGE_FACTORY>`_
defines the path of the factory that will be used to create a storage instance.

Invenio-Files-REST comes with a default storage implementation
`PyFilesystem <https://www.pyfilesystem.org/>`_ to save files locally.

The module provides an abstract layer for storage implementation that allows
to swap storages easily. For example the storage backend can be a cloud
service, such as `Invenio-S3 <https://invenio-s3.readthedocs.io/>`_ which
offers integration with any S3 REST API compatible object storage.


Build your own Storage Backend
------------------------------

Advanced topic on how to implement and connect your own storage Backend for
Invenio-Files-REST.

In order to use a different storage backend, it is required to subclass the
`invenio_files_rest.storage.FileStorage <https://invenio-files-rest.readthedocs.io/en/latest/api.html#invenio_files_rest.ext.FileStorage>`_
class, and provide implementations for some of its methods.

Mandatory methods to implement:

* :code:`initialize`
* :code:`open`
* :code:`save`
* :code:`update`
* :code:`delete`

Optional methods to implement:

* :code:`send_file`
* :code:`checksum`
* :code:`copy`
* :code:`_init_hash`
* :code:`_compute_checksum`
* :code:`_write_stream`

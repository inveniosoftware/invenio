..
    This file is part of Invenio.
    Copyright (C) 2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _integration:

Integrating Files
=================

Invenio provides a bundle of modules to accommodate all around needs about
file management. You can install all the necessary modules at once, or due to
invenio modular architecture you can hand pick only those you need.

In case you have scaffolded your invenio application with
`cookiecutter-invenio-instance <https://github.com/inveniosoftware/cookiecutter-invenio-instance>`_
files bundle is already a part of your solution, the only step you need to
take is to enable them through configuration.

In case you want all the modules automatically installed you can navigate to
your project and with your virtual environment selected you can

.. code-block:: console

   $ pip install invenio[auth]


Files bundle
------------

As mentioned before functionality for files support is broken down in different
parts to provide as much flexibility as possible.

`invenio-files-rest <https://invenio-files-rest.readthedocs.io/>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ pip install invenio-files-rest

:code:`invenio-files-rest` is the first required module for managing files
with your application, and some of its key functions is to allow you to store
and retrieve files in a similar way to Amazon S3 APIs.

- Configurable files storage
- Secure REST APIs for upload/download
- Support for large file uploads and multipart upload.
- File integrity monitoring
- Customizable access control

After you install the module on your environment you just have to register
the invenio-files-rest blueprint in the list of blueprints defined in the
:code:`entry_points` of the :code:`setup.py` of your application.

.. code-block:: python

    entry_points={
        "invenio_app.api_blueprints": [
            "invenio_files = invenio_files_rest.views:blueprint",
        ],
    }

Read more about `configuration <https://invenio-files-rest.readthedocs.io/en/latest/configuration.html>`__
and `usage <https://invenio-files-rest.readthedocs.io/en/latest/usage.html>`__
of invenio-files-rest on the module's `documentation <https://invenio-files-rest.readthedocs.io/>`__.


`invenio-records-files <https://invenio-records-files.readthedocs.io/>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ pip install invenio-records-files

:code:`invenio-records-files` is the other required module, which provides a
basic API for the seamless co-operation of `invenio-records <https://invenio-records.readthedocs.io/>`__
and `invenio-files-rest`_. The API provides functionality for

- records creation
- files creation
- accessing files
- files metadata management
- files extraction from records

After installing the module you will need to provide the relevant
configuration in the :code:`config.py` of your application, for the
endpoints you want to use, it should be in the following form

.. code-block:: python

    RECORDS_FILES_REST_ENDPOINTS = {
        '<*_REST_ENDPOINTS>': {
            '<endpoint-prefix>': '<endpoint-suffix>',
        }
    }

Read more about `configuration <https://invenio-records-files.readthedocs.io/en/latest/configuration.html>`__
and `usage <https://invenio-records-files.readthedocs.io/en/latest/usage.html>`__
of invenio-records-files on the module's `documentation <https://invenio-records-files.readthedocs.io/>`__.


`invenio-previewer <https://invenio-previewer.readthedocs.io/>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ pip install invenio-previewer

:code:`invenio-previewer` by default comes with support to a number of file
types but it also provides an extensible API to create new previewers.
By default the supported file types are: **PDF**,
**ZIP** **CSV**, **Markdown**, **XML**, **Json**, **PNG**, **JPG**, **GIF** and
**Jupyter Notebooks**.

After you install the module the only configuration you have to make to enable
it, is to define and endpoint in the :code:`RECORDS_UI_ENDPOINTS` for the
previewer.

.. code:: python

    RECORDS_UI_ENDPOINTS=dict(
        recid_preview=dict(
            pid_type='recid',
            route='/records/<pid_value>/preview/<filename>',
            view_imp='invenio_previewer.views:preview',
            record_class='invenio_records_files.api:Record',
        ),
    )

Read more about `configuration <https://invenio-previewer.readthedocs.io/en/latest/configuration.html>`__
and `usage <https://invenio-previewer.readthedocs.io/en/latest/usage.html>`__
of invenio-previewer on the module's `documentation <https://invenio-previewer.readthedocs.io/>`__.


`invenio-iiif <https://invenio-iiif.readthedocs.io/>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ pip install invenio-iiif


:code:`invenio-iiif` integrates Invenio-Records-Files with `Flask-IIIF <https://flask-iiif.readthedocs.io/en/latest/>`__
to provide support for serving images complying with the International Image
Interoperability Framework (IIIF) API standards.

Invenio-IIIF registers the REST API endpoint provided by Flask-IIIF in the
Invenio instance through entry points. On each image request, it delegates
authorization check and file retrieval to Invenio-Files-REST and it serves the
image after adaptation by Flask-IIIF. Invenio-IIIF can also be used in a
combination with Invenio-Previewer to preview images and comes with the
following features.

- Thumbnail generation and previewing of images.
- Allows to preview, resize and zoom images, by implementing the `IIF <https://iiif.io/>`__ API.
- Provide celery task to create image thumbnails.

Read more about `configuration <https://invenio-iiif.readthedocs.io/en/latest/configuration.html>`__
and `usage <https://invenio-iiif.readthedocs.io/en/latest/usage.html>`__
of invenio-iiif on the module's `documentation <https://invenio-iiif.readthedocs.io/>`__.

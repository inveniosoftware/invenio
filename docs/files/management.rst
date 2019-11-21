..
    This file is part of Invenio.
    Copyright (C) 2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _serve:

Managing files
================

In this section are explained the different operations you can do to manage
files.

Operations
----------

Serving
+++++++

To serve and allow download of files, you can perform a GET request
specifying the bucket and the filename used to upload the file.

.. code-block:: console

   $ curl -i -X GET "http://localhost:5000/api/files/$BUCKET/my_file.txt"

You can also list files or download specific versions of files. See the REST
APIs reference documentation below for more information.

Be aware that there are security implications to take into account when
serving files. See the :ref:`usage-security` for more information.

Uploading
+++++++++

You can upload, download and modify single files via REST APIs.
A file is uniquely identified within a bucket by its name and version.
Each file can have multiple versions.

Let's upload a file called :code:`my_file.txt` inside the bucket that
was just created.

.. code-block:: console

   $ BUCKET=cb8d0fa7-2349-484b-89cb-16573d57f09e

   $ echo "my file content" > my_file.txt

   $ curl -i -X PUT --data-binary @my_file.txt \
     "http://localhost:5000/api/files/$BUCKET/my_file.txt"

.. code-block:: json

    {
        "mimetype": "text/plain",
        "updated": "2019-05-16T13:10:22.621533+00:00",
        "links": {
            "self": "http://localhost:5000/api/files/
                     cb8d0fa7-2349-484b-89cb-16573d57f09e/my_file.txt",

            "version": "http://localhost:5000/api/files/
                        cb8d0fa7-2349-484b-89cb-16573d57f09e/my_file.txt?
                        versionId=7f62676d-0b8e-4d77-9687-8465dc506ca8",
            "uploads": "http://localhost:5000/api/files/
                        cb8d0fa7-2349-484b-89cb-16573d57f09e/
                        my_file.txt?uploads"
        },
        "is_head": true,
        "tags": {},
        "checksum": "md5:d7d02c7125bdcdd857eb70cb5f19aecc",
        "created": "2019-05-16T13:10:22.617714+00:00",
        "version_id": "7f62676d-0b8e-4d77-9687-8465dc506ca8",
        "delete_marker": false,
        "key": "my_file.txt",
        "size": 14
    }

If you have a new version of the file, you can upload it to the same bucket
using the same filename. In this case, a new ObjectVersion will be created.

.. code-block:: console

   $ echo "my file content version 2" > my_filev2.txt

   $ curl -i -X PUT --data-binary @my_filev2.txt \
     "http://localhost:5000/api/files/$BUCKET/my_file.txt"

.. code-block:: json

    {
        "mimetype": "text/plain",
        "updated": "2019-05-16T13:11:22.621533+00:00",
        "links": {
            "self": "http://localhost:5000/api/files/
                     cb8d0fa7-2349-484b-89cb-16573d57f09e/my_file.txt",

            "version": "http://localhost:5000/api/files/
                        cb8d0fa7-2349-484b-89cb-16573d57f09e/my_file.txt?
                        versionId=24bf075f-09f4-42f8-9fbe-3f00b8aac3e8",
            "uploads": "http://localhost:5000/api/files/
                        cb8d0fa7-2349-484b-89cb-16573d57f09e/
                        my_file.txt?uploads"
        },
        "is_head": true,
        "tags": {},
        "checksum": "md5:fe76512703258a894e56bac89d2e8dec",
        "created": "2019-05-16T13:11:22.617714+00:00",
        "version_id": "24bf075f-09f4-42f8-9fbe-3f00b8aac3e8",
        "delete_marker": false,
        "key": "my_file.txt",
        "size": 13
    }

When integrating the REST APIs to upload files via a web application, you
might use JavaScript to improve user experience. Invenio-Files-REST provides
out of the box integration with JavaScript uploaders. See the
:ref:`usage-js-uploaders` section for more information.

Invenio-Files-REST also provides different ways to upload large files. See
the :ref:`usage-multipart-upload` and :ref:`usage-large-files` sections
for more information.

Downloading
+++++++++++

Once the bucket is created and a file is uploaded, it is possible
to retrieve it with a :code:`GET` request.

By default, the latest version will be retrieved. Invenio provides also support
for file versioning. In order to retrieve a different than the default version
of the file you have to provide the :code:`versionId` as query parameter, as in
the example below:

Download the latest version of the file:

.. code-block:: console

   $ BUCKET_ID=cb8d0fa7-2349-484b-89cb-16573d57f09e
   $ curl -i http://localhost:5000/files/$BUCKET_ID/my_file.txt

Download a specific version of the file:

.. code-block:: console

   $ curl -i http://localhost:5000/files/$B/my_file.txt?versionId=<version_id>

.. note::
    By default, the file is returned with the header
    :code:`'Content-Disposition': 'inline'`, so that the browser will try to
    preview it. In case you want to trigger a download of the file, use the
    :code:`download` boolean query parameter, which will change the
    :code:`'Content-Disposition'` header to :code:`'attachment'`

.. code-block:: console

   $ curl -i http://localhost:5000/files/$B/my_file.txt?download

Stream
******
Instead of waiting for the file download to complete, invenio provides support
for streaming out of the box for the following file types:
`audio/mpeg`, `audio/ogg`, `audio/wav`, `audio/webm`, `image/gif`,
`image/jpeg`, `image/png`, `image/tiff`, `text/plain`.

You can add your custom mime types to
`MIMETYPE_WHITELIST <https://invenio-files-rest.readthedocs.io/en/latest/api.html#invenio_files_rest.helpers.MIMETYPE_WHITELIST>`_
to extend functionality according to your needs.

.. warning::

    Be extra careful when you extend the whitelisted mime types since it could
    potentially expose your server to XSS attacks


Deleting
++++++++

A delete operation can be of two types:

1. mark an object as deleted, allowing the possibility of restoring
   a deleted file (also called delete marker or soft deletion).
2. permanently remove any trace of an object and referenced file
   on disk (also called hard deletion).

Soft deletion
**************
Technically, it creates a new ObjectVersion, that becomes the new :code:`head`,
with no reference to a FileInstance. It is possible to revert it
by getting the previous version.

This operation will not access to the file on disk and it will leave it
untouched.

You can soft delete using REST APIs:

.. code-block:: console

   DELETE /files/<bucket_id>/<file_name>

Hard deletion
**************
Given a specific object version, it will delete the ObjectVersion,
the referenced FileInstance and the file on disk. If the deleted version
was the :code:`head`, it will then set the previous object
as the new head.

The deletion of files on disk will not happen immediately. This is because
it is done via an asynchronous task to ensure that the FileInstance is
safely removed from the database in case the low level operation of file
removal on disk fails for any unexpected reason.

You can hard delete a file using REST APIs:

.. code-block:: console

   DELETE /files/<bucket_id>/<file_name>?versionId=<version_id>

REST APIs do not allow to perform delete operations that can affect multiple
objects at the same time. For advanced use cases, you will to use the
Invenio-Files-REST APIs programmatically.

.. note::
    For safety reasons, the deletion will fail if the file that you want
    to delete is referenced by multiple ObjectVersions, for example
    in case of Buckets snapshots.

Security
--------

When serving files, you will have to take into account any security
implications. Here you can find some recommendations to mitigate possible
vulnerabilities, such as Cross-Site Scripting (XSS):

1. If possible, serve user uploaded files from a separate domain
   (not a subdomain).

2. By default, Invenio-Files-REST sets some response headers to prevent
   the browser from rendering and executing HTML files.
   See :py:func:`invenio_files_rest.helpers.send_stream` for more information.

3. Prefer file download instead of allowing the browser to preview any file,
   by adding the :code:`?download` URL query argument

..
    This file is part of Invenio.
    Copyright (C) 2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _serve:

Serve your files
================

Invenio provides several ways to access securely your files.


Preview or Download
-------------------
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
------
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

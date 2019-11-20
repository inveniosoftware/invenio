..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Big files upload
----------------

By default, Flask and your web server have the maximum file size limit after
which an upload is aborted and the server returns a response code
:code:`413 (Request Entity Too Large)`.

You can adjust these configurations according to your needs.

For Flask, specify :code:`MAX_CONTENT_LENGTH` config variable. Be aware that if
the request does not specify a :code:`CONTENT_LENGTH`, no data will be read.
To change the max size, you can for example:

.. console::

 $ app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

The code above will limit the maximum allowed file size to 25 megabytes.

The example below refers to :code:nginx server. In case you use another web
server consult relevant documentation on how to configure max content length.

.. code-block:: console

 http {
     ...
     client_max_body_size 25M;
 }

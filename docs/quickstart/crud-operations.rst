..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.
    Copyright (C) 2018 Northwestern University, Feinberg School of Medicine, Galter Health Sciences Library.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _crud-operations:

Create, Display, Search Records
===============================

.. _create-a-record:

Create a record
---------------
By default, the toy data model has a records REST API endpoint configured,
which allows performing CRUD and search operations over records. Let's create a
simple record via ``curl``, by sending a ``POST`` request to ``/api/records``
with some sample data:

.. code-block:: shell

  $ curl -k --header "Content-Type: application/json" \
      --request POST \
      --data '{"title":"Some title", "contributors": [{"name": "Doe, John"}]}' \
      https://localhost:5000/api/records/?prettyprint=1

When the request was successful, the server returns the details of the created
record:

.. code-block:: shell

    {
      "_bucket": "9ae1c979-9c6a-4603-afb2-38074eb48a54",
      "created": "2019-11-22T10:30:06.135431+00:00",
      "id": "1",
      "links": {
        "files": "https://localhost:5000/api/records/1/files",
        "self": "https://localhost:5000/api/records/1"
      },
      "metadata": {
        "$schema": "https://my-site.com/schemas/records/record-v1.0.0.json",
        "contributors": [
          {
            "name": "Doe, John"
          }
        ],
        "id": "1",
        "title": "Some title"
      },
      "revision": 0,
      "updated": "2019-11-22T10:30:06.135438+00:00"
    }

.. note::

    Because we are using a self-signed SSL certificate to enable HTTPS, your
    web browser will probably display a warning when you access the website.
    You can usually get around this by following the browser's instructions in
    the warning message. For CLI tools like ``curl``, you can ignore the SSL
    verification via the ``-k/--insecure`` option.

.. _display-a-record:

Display a record
----------------

You can now visit the record's page at https://localhost:5000/records/1, or
fetch it via the REST API:

.. code-block:: shell

  # You can find this URL under the "links.self" key of the previous response
  $ curl -k --header "Content-Type: application/json" \
      https://localhost:5000/api/records/1?prettyprint=1

  {
    "_bucket": "9ae1c979-9c6a-4603-afb2-38074eb48a54",
    "created": "2019-11-22T10:30:06.135431+00:00",
    "id": "1",
    "links": {
      "files": "https://localhost:5000/api/records/1/files",
      "self": "https://localhost:5000/api/records/1"
    },
    "metadata": {
      "$schema": "https://my-site.com/schemas/records/record-v1.0.0.json",
      "contributors": [
        {
          "name": "Doe, John"
        }
      ],
      "id": "1",
      "title": "Some title"
    },
    "revision": 0,
    "updated": "2019-11-22T10:30:06.135438+00:00"
  }

.. _upload-a-file:

Upload a file
-------------

You can upload a file to a record.

.. code-block:: shell

  # Create an example file

  $ echo 'example' > example.txt

  # Upload a file named example.txt to the record with pid of 1

  $ curl -k -X PUT https://localhost:5000/api/records/1/files/example.txt \
     -H "Content-Type: application/octet-stream" \
     --data-binary @example.txt

  {
    "version_id": "059a6706-632f-403a-beab-36e31e370737",
    "is_head": true,
    "mimetype": "text/plain",
    "size": 8,
    "key": "example.txt",
    "delete_marker": false,
    "links": {
      "self": "https://localhost:5000/api/records/1/files/example.txt",
      "version": "https://localhost:5000/api/records/1/files/example.txt?versionId=059a6706-632f-403a-beab-36e31e370737",
      "uploads": "https://localhost:5000/api/records/1/files/example.txt?uploads"
    },
    "checksum": "md5:ddce269a1e3d054cae349621c198dd52",
    "created": "2019-11-22T10:34:08.944425",
    "tags": {},
    "updated": "2019-11-22T10:34:08.951942"
  }

.. _list-files-of-a-record:

List files of a record
----------------------

Get the list of files for the record.

.. code-block:: shell

  $ curl -k -X GET https://localhost:5000/api/records/1/files?prettyprint=1

  {
    "contents": [
    {
      "version_id": "059a6706-632f-403a-beab-36e31e370737",
      "is_head": true,
      "mimetype": "text/plain",
      "size": 8,
      "key": "example.txt",
      "delete_marker": false,
      "links": {
        "self": "https://localhost:5000/api/records/1/files?key=example.txt",
        "version": "https://localhost:5000/api/records/1/files?key=example.txt&versionId=059a6706-632f-403a-beab-36e31e370737",
        "uploads": "https://localhost:5000/api/records/1/files?key=example.txt?uploads"
      },
      "checksum": "md5:ddce269a1e3d054cae349621c198dd52",
      "created": "2019-11-22T10:34:08.944425",
      "tags": {},
      "updated": "2019-11-22T10:34:08.951942"
    }
    ],
    "id": "9ae1c979-9c6a-4603-afb2-38074eb48a54",
    "size": 16,
    "locked": false,
    "max_file_size": null,
    "links": {
      "self": "https://localhost:5000/api/records/1/files",
      "versions": "https://localhost:5000/api/records/1/files?versions",
      "uploads": "https://localhost:5000/api/records/1/files?uploads"
    },
    "quota_size": null,
    "created": "2019-11-22T10:30:06.118477",
    "updated": "2019-11-22T10:34:08.962336"
  }

.. _download-a-file:

Download a file
---------------

Download the file named ``example.txt`` of the record.

.. code-block:: shell

  $ curl -k -X GET https://localhost:5000/api/records/1/files/example.txt -o example.txt

.. _search-for-records:

Search for records
------------------

The record you created before, besides being inserted into the database, is
also indexed in Elasticsearch and available for searching. You can search for
it via the Search UI page at https://localhost:5000/search, or via the REST
API from the ``/api/records`` endpoint:

.. code-block:: shell

  $ curl -k --header "Content-Type: application/json" \
      https://localhost:5000/api/records/?prettyprint=1

  {
    "aggregations": {
      "keywords": {
        "buckets": [],
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0
      },
      "type": {
        "buckets": [],
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0
      }
    },
    "hits": {
      "hits": [
        {
          "_bucket": "9ae1c979-9c6a-4603-afb2-38074eb48a54",
          "created": "2019-11-22T10:30:06.135431+00:00",
          "id": "1",
          "links": {
            "files": "https://localhost:5000/api/records/1/files",
            "self": "https://localhost:5000/api/records/1"
          },
          "metadata": {
            "$schema": "https://my-site.com/schemas/records/record-v1.0.0.json",
            "contributors": [
              {
                "name": "Doe, John"
              }
            ],
            "id": "1",
            "title": "Some title"
          },
          "revision": 0,
          "updated": "2019-11-22T10:30:06.135438+00:00"
        }
      ],
      "total": 1
    },
    "links": {
      "self": "https://localhost:5000/api/records/?sort=mostrecent&size=10&page=1"
    }
  }

Continue tutorial
~~~~~~~~~~~~~~~~~
:ref:`next-steps`

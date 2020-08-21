..
    This file is part of Invenio.
    Copyright (C) 2015-2019 CERN.
    Copyright (C) 2018 Northwestern University, Feinberg School of Medicine, Galter Health Sciences Library.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _crud-operations:

Create, display and search records
==================================

.. _create-a-record:

Create a record
---------------
Invenio provides REST APIs to perform operations on records, such as
create, search or retrieve.

Let's create a simple record via ``curl``, by sending a ``POST`` request to
the ``/api/records`` endpoint with some sample data:

.. code-block:: console

    $ curl -k --header "Content-Type: application/json" \
        --request POST \
        --data '{"title":"Some title", "contributors": [{"name": "Doe, John"}]}' \
        https://127.0.0.1:5000/api/records/?prettyprint=1

The response of the request contains the newly created record metadata:

.. code-block:: console

    {
      "created": "2019-11-22T10:30:06.135431+00:00",
      "id": "1",
      "links": {
        "files": "https://127.0.0.1:5000/api/records/1/files",
        "self": "https://127.0.0.1:5000/api/records/1"
      },
      "metadata": {
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

.. _display-a-record:

Display a record
----------------

You can now visit the record's page at https://127.0.0.1:5000/records/1.

.. note::
    To enable HTTPS, Invenio uses a self-signed SSL certificate.
    Your web browser should display a warning when accessing the website
    since it will consider it insecure. You can safely ignore it when
    developing locally.

You can also fetch the record via REST APIs:

.. code-block:: console

    $ curl -k --header "Content-Type: application/json" \
        https://127.0.0.1:5000/api/records/1?prettyprint=1

    {
      "created": "2019-11-22T10:30:06.135431+00:00",
      "id": "1",
      "links": {
        "files": "https://127.0.0.1:5000/api/records/1/files",
        "self": "https://127.0.0.1:5000/api/records/1"
      },
      "metadata": {
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

.. _search-for-records:

Search for records
------------------
The record that you have created is safely stored in the database but
also indexed in Elasticsearch for fast searching. You can see the list of
records and perform search queries at https://127.0.0.1:5000/search,
or via the REST API from the ``/api/records`` endpoint:

.. code-block:: console

    $ curl -k --header "Content-Type: application/json" \
        https://127.0.0.1:5000/api/records/?prettyprint=1

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
            "created": "2019-11-22T10:30:06.135431+00:00",
            "id": "1",
            "links": {
              "files": "https://127.0.0.1:5000/api/records/1/files",
              "self": "https://127.0.0.1:5000/api/records/1"
            },
            "metadata": {
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
        "self": "https://127.0.0.1:5000/api/records/?sort=mostrecent&size=10&page=1"
      }
    }

.. _upload-a-file:

Upload a file
-------------
Invenio allows you to attach files to a record. Let's upload a file
to the previously created record.

.. code-block:: console

    # create a sample file

    $ echo 'my file content' > example.txt

    # Upload the file to the record with PID 1

    $ curl -k -X PUT https://127.0.0.1:5000/api/records/1/files/example.txt \
        -H "Content-Type: application/octet-stream" \
        --data-binary @example.txt

The response of the request contains the uploaded file's metadata:

.. code-block:: console

    {
      "version_id": "059a6706-632f-403a-beab-36e31e370737",
      "is_head": true,
      "mimetype": "text/plain",
      "size": 8,
      "key": "example.txt",
      "delete_marker": false,
      "links": {
        "self": "https://127.0.0.1:5000/api/records/1/files/example.txt",
        "version": "https://127.0.0.1:5000/api/records/1/files/example.txt?versionId=059a6706-632f-403a-beab-36e31e370737",
        "uploads": "https://127.0.0.1:5000/api/records/1/files/example.txt?uploads"
      },
      "checksum": "md5:ddce269a1e3d054cae349621c198dd52",
      "created": "2019-11-22T10:34:08.944425",
      "tags": {},
      "updated": "2019-11-22T10:34:08.951942"
    }

.. _list-files-of-a-record:

List the files of a record
--------------------------
You can use REST APIs to retrieve all the files attached to a record:

.. code-block:: console

    $ curl -k -X GET https://127.0.0.1:5000/api/records/1/files?prettyprint=1

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
          "self": "https://127.0.0.1:5000/api/records/1/files?key=example.txt",
          "version": "https://127.0.0.1:5000/api/records/1/files?key=example.txt&versionId=059a6706-632f-403a-beab-36e31e370737",
          "uploads": "https://127.0.0.1:5000/api/records/1/files?key=example.txt?uploads"
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
        "self": "https://127.0.0.1:5000/api/records/1/files",
        "versions": "https://127.0.0.1:5000/api/records/1/files?versions",
        "uploads": "https://127.0.0.1:5000/api/records/1/files?uploads"
      },
      "quota_size": null,
      "created": "2019-11-22T10:30:06.118477",
      "updated": "2019-11-22T10:34:08.962336"
    }

.. _download-a-file:

Download a file
---------------
Let's download the file that we have just uploaded:

.. code-block:: console

    $ curl -k -X GET https://127.0.0.1:5000/api/records/1/files/example.txt -o example.txt

Final steps
-----------
Complete the initialisation of your Invenio application: :ref:`final-steps`.

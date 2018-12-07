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
    "created": "2018-05-23T13:28:19.426206+00:00",
    "id": 1,
    "links": {
      "self": "https://localhost:5000/api/records/1"
    },
    "metadata": {
      "contributors": [
        {
          "name": "Doe, John"
        }
      ],
      "id": 1,
      "title": "Some title"
    },
    "revision": 0,
    "updated": "2018-05-23T13:28:19.426213+00:00"
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
    "created": "2018-05-23T13:28:19.426206+00:00",
    "id": 1,
    "links": {
      "self": "https://localhost:5000/api/records/1"
    },
    "metadata": {
      "contributors": [
        {
          "name": "Doe, John"
        }
      ],
      "id": 1,
      "title": "Some title"
    },
    "revision": 0,
    "updated": "2018-05-23T13:28:19.426213+00:00"
  }

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
          "created": "2018-05-23T13:28:19.426206+00:00",
          "id": 1,
          "links": {
            "self": "https://localhost:5000/api/records/1"
          },
          "metadata": {
            "contributors": [
              {
                "name": "Doe, John"
              }
            ],
            "id": 1,
            "title": "Some title"
          },
          "revision": 0,
          "updated": "2018-05-23T13:28:19.426213+00:00"
        }
      ],
      "total": 1
    },
    "links": {
      "self": "https://localhost:5000/api/records/?size=10&sort=mostrecent&page=1"
    }
  }

Continue tutorial
~~~~~~~~~~~~~~~~~
:ref:`next-steps`

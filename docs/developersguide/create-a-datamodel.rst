..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Creating a data model
=====================

Use Cases
---------

Invenio datamodel is designed for one pattern which is common to many
different use cases: store and provide access to some **Records**, be it
*Bibliographic* publications like research papers, a list of *Grants* or some
*Authorities* like authors. Those resources are referenced
by **Persistent Identifiers** and use a specific **format** for their
**metadata**.

|
|

.. graphviz::

    digraph {
        {
        "Bibliographic" [shape ="ellipse"];
        "Authority" [shape ="ellipse"];
        "Grants" [shape ="ellipse"];
        "MARC 21" [shape="hexagon"];
        "Custom format" [shape="hexagon"];
        "Bibliographic DOI" [shape="rectangle"];
        "Grant DOI" [shape="rectangle"];
        "ORCID" [shape="rectangle"];
        }
       "Bibliographic" -> "MARC 21"[ label = "  Format"];
       "Authority" -> "MARC 21" [ label = "  Format" ];
       "Grants" -> "Custom format"[label = "  Format"];
       "Bibliographic DOI" -> "Bibliographic"[ label = "  Persistent Identifier" dir="back"];
       "Grant DOI" -> "Grants"[ label = "  Persistent Identifier" dir="back"];
       "ORCID" -> "Authority"[ label = "  Persistent Identifier" dir="back"];
    }

|

Records storage:
----------------

Invenio stores Record metadata as JSON, uses `JSON Schemas <http://json-schema.org/>`_
for the formats and it can support any type of Persistent Identifier.

|
|

.. graphviz::

    digraph {
        {
        "Record" [label="Record (JSON metadata)" shape ="ellipse"];
        "Format" [label="Format (JSON Schema)" shape="hexagon"];
        "PID" [label="Persistent Identifier (DOI, Handle...)" shape="rectangle"];
        }
       "Record" -> "Format"[ label = "  Validated by"];
       "PID" -> "Record"[ label = "  Identified by" dir="back"];
    }

|
|

The JSON Schemas enable to define complex constraints which must be satisfied
each time a record is created or modified. Invenio provides JSON Schemas for
MARC 21 but custom JSON Schemas can also be used.

The rest of this documentation will show how to store and give access to
documents having two metadata fields:

* title: the title of our document.
* description: the description of our documents.


Here is an example of such a record in the JSON format:

.. code-block:: json

    {
        "title": "CERN new accelerator",
        "description": "It now accelerates muffins."
    }

Record Storage
--------------

JSON Schemas
^^^^^^^^^^^^

The JSON Schema corresponding to our record could look like this:

.. code-block:: json

    {
        "title": "Custom record schema v1.0.0",
        "id": "http://localhost:5000/schemas/custom-record-v1.0.0.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Record title."
            },
            "description": {
                "type": "string",
                "description": "Description for record."
            },
            "custom_pid": {
                "type": "string"
            },
            "$schema": {
                "type": "string"
            }
        }
    }

This JSON Schema defines the fields and their types. Other constraints
can be added if needed.

Every record has a reference to the JSON Schema which validates it. In our
example, the :code:`$schema` field will be the URL pointing to the JSON
Schema. The *invenio-jsonschemas* module enables Invenio to serve JSON Schemas
as static files.

We will explain :ref:`in the next part<pid_minting>` why we added the
"custom_pid" field.

External access to records:
---------------------------

Persistent Identifiers and URLs:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Different things can happen to published records. For example they can be:

* **deleted**: this happens when they contain invalid or illegal data. However
  we can't just remove all information as users should be informed that the
  record existed at some point and was deleted.

* **merged**: duplicates are sometime created. It is then better to keep only
  one version. Users can be redirected from the deleted version to the one
  which was kept.

Invenio uses the concept of **Persistent Identifiers**, often abbreviated as
**PID**. Those identifiers expose records to the outside world.

They are for example used in URLs. A typical User Interface url is of the
form:

.. code-block:: html

    http://records/<PID>

Note that the *invenio-records-ui* module enables to customize the URL
(ex: :code:`http://authors/<PID>`), but it always contain the PID.

Persistent Identifiers can have different types and reflect Persistent
Identifiers existing outside of Invenio such as DOI or ORCID. They can
also be completely custom.

Many Invenio modules such as *invenio-records-ui* enable to have different
configuration for each PID type. This for example enables to have one URL for
authors and another for research papers.

.. note:: **Records can have multiple Persistent Identifiers**

    One use case for multiple PIDs per records is systems which migrate from
    Invenio version 1 where records were referenced with incremental integers
    (ex: :code:`http://records/1`). For backward compatibility reasons it is
    possible to keep internal PIDs which still use integers. The
    *invenio-pidstore* module provides everything needed for this use case. Our
    system might at the same time need to support DOI PIDs. It is then possible
    to create those PIDs without exposing them as an additional URL.

.. _pid_minting:

.. note:: **PID minting**

    Every record's JSON contains a copy of its Persistent Identifier. We say
    that they are *minted* with the PID. The "custom_pid" field which we
    saw previously in the JSON Schema would contain this PID. This field name
    can be changed. It is advised to have it defined in the JSON Schema.


REST API:
^^^^^^^^^

Invenio enables access and modification of records via a REST API. This API
is provided by the *invenio-records-rest* module, which uses Persistent
Identifiers too.

A REST API URL will often look like:

.. code-block:: html

    http://api/records/<PID>

Note that just like *invenio-records-ui*, *invenio-records-rest* enables
to customize the URLs for each PID type.

Serializers
"""""""""""

The REST API can output records in any format as long as a **serializer** is
defined. **invenio-marc21** provides serializers for MARC 21. Custom
serializers can be easily added.

Here is a simple serializer example:

.. code-block:: python

    from flask import current_app

    def plain_text_serializer(pid, record, code=200, headers=None, **kwargs):
        """Example of a custom serializer which just returns the record's title."""
        # create a response
        response = current_app.response_class()

        # set the returned data, which will just contain the title
        response.data = record['title']

        # set the return code in order to notify any error
        response.status_code = code

        # update headers
        response.headers['Content-Type'] = 'text/plain'
        if headers is not None:
            response.headers.extend(headers)
        return response

It is then possible to register this serializer for requestes of type
`text/plain`. The result would look like this:

.. code-block:: console

    $ curl -H "Accept:text/plain" -XGET 'http://myinvenio.com/api/custom_records/custom_pid_1'
    CERN new accelerator

Serializers not only enable to output records in a specific format but also
to remove fields, add fields or do any other transformation before showing
the record to the outside world.


Search:
^^^^^^^

Users need to find records easily. Often this means to type a few words
and get a list of results ordered by their relevance. Invenio uses
Elasticsearch as its search engine. It needs to be configured in order to
find the records as expected.

In this example we will focus on a very simple use case:
how to search records containing english text in its metadata. This means that
if our record contains "muffins" it should also be found when the user queries
with the word "muffin" (without 's').

We will provide an **Elasticsearch mapping** file which will define every field
and specify that it should be *analyzed* as "english".

.. code-block:: json

    {
        "mappings": {
            "custom-record-v1.0.0": {
                "_all": {
                    "analyzer": "english"
                },
                "properties": {
                    "title": {
                        "type": "string",
                        "analyzer": "english"
                    },
                    "description": {
                        "type": "string",
                        "analyzer": "english"
                    },
                    "custom_pid": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "$schema": {
                        "type": "string",
                        "index": "not_analyzed"
                    }
                }
            }
        }
    }

If you want to know more about Elasticsearch mapping you can see its
documentation.


Linking records:
----------------

Invenio provides tools to link records one to another.

We can extend our example by adding a "references" field which will contain
a list of references to other records.

When creating a record the user would give this as input:

.. code-block:: json

    {
        "title": "CERN new accelerator",
        "description": "It now accelerates muffins.",
        "references": [
            {"$ref": "http://myinvenio.com/custom_records/custom_pid_1#/title" },
            {"$ref": "http://myinvenio.com/custom_records/custom_pid_42#/title" }
        ]
    }

The pattern :code:`{"$ref": http://myinvenio.com/records/1#/title }` is called
a JSON reference. It enables to have a reference to another JSON object, or a
field in it, with a URL just like :code:`$schema`.

The corresponding JSON Schema would be:

.. code-block:: json

    {
        "title": "Custom record schema v1.0.0",
        "id": "http://localhost:5000/schemas/custom-record-v1.0.0.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Record title."
            },
            "description": {
                "type": "string",
                "description": "Description for record."
            },
            "references": { 
                "type": "array",
                "items": {
                    "type": "object"
                }
            },
            "custom_pid": {
                "type": "string"
            },
            "$schema": {
                "type": "string"
            }
        }
    }



Invenio provide tools to dereference those JSON references and replace them
with the referenced value. The output would then look like this:

.. code-block:: console

    $ curl -XGET 'http://myinvenio.com/api/custom_records/custom_pid_1'
    {
        "created": "2017-03-16T14:53:42.126710+00:00",
        "links": {
        "self": "http://192.168.50.10/api/custom_records/custom_pid_1"
    },
    "metadata": {
        "$schema": "http://myinvenio.com/schema/custom_record/custom-record-v1.0.0.json",
        "custom_pid": "custom_pid_1",
        "title": "CERN new accelerator",
        "description": "It now accelerates muffins."
        "references": [
            "This is the title of record custom_pid_1",
            "This is the title of record custom_pid_42",
        ]
    },
    "updated": "2017-03-16T14:53:42.126725+00:00"
    }

The dereferencing is done by the serializer. The database still contain
the original JSON references.


This dereferencing is also done before the record is indexed in Elasticsearch.
Thus the mapping would define the "references" field as a list of string
(titles are of type string):


.. code-block:: json

    {
        "mappings": {
            "custom-record-v1.0.0": {
                "_all": {
                    "analyzer": "english"
                },
                "properties": {
                    "title": {
                        "type": "string",
                        "analyzer": "english"
                    },
                    "description": {
                        "type": "string",
                        "analyzer": "english"
                    },
                    "references": {
                        "type": "string"
                    },
                    "custom_pid": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "$schema": {
                        "type": "string",
                        "index": "not_analyzed"
                    }
                }
            }
        }
    }


.. warning::

    The records containing the references need to be reindexed if the
    referenced records change.


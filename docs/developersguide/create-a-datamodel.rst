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
|

Records storage:
----------------

Invenio stores Records' metadata as JSON, the format as `JSON Schemas <http://json-schema.org/>`_
and can support any type of Persistent Identifier.

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
each time a record is created or modified. Invenio provide JSON Schemas for
MARC 21 but custom JSON Schemas can also be used.

The rest of this documentation will show how to store and give access to
documents having two metadata fields:

* title: the title of our document.
* description: the description of our documents.


Here is an example of such a record in the JSON format:

.. code-block:: json

    {
        "title": "CERN new accelerator",
        "description": "It now accelerates yogourts."
    }

|

Record Storage
--------------

JSON Schemas
^^^^^^^^^^^^

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
            }
        }
    }

**TODO: explain the JSON Schema.**


External access to records:
---------------------------

User Interface URLs:
^^^^^^^^^^^^^^^^^^^^

**TODO: explain how PID are used as namespaces for records.**

REST API:
^^^^^^^^^

**TODO: explain that REST API's URLs are also namespaced by PIDs**

**TODO: explain serialization**

.. code-block:: python

    def plain_text_serializer(pid, record, code=200, headers=None, **kwargs):
        """Example of a custom serializer which just returns the record's title."""
        response = current_app.response_class()

        # the returned data will just contain the title
        response.data = record['title']

        # set the return code in order to notify any error
        response.status_code = code

        # update headers
        response.headers['Content-Type'] = 'text/plain'
        if headers is not None:
            response.headers.extend(headers)
        return response

Search:
^^^^^^^

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
                    }
                }
            }
        }
    }

**TODO: explain mappings**


Linking records:
----------------

**TODO: show that references can be resolved without going into details**

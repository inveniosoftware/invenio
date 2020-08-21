..
    This file is part of Invenio.
    Copyright (C) 2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _understanding-data-models:

Understanding data models
=========================
An Invenio data model, a bit simply put, defines *a record type*. You can also
think of a data model as a supercharged database table.

In addition to storing records (aka documents or rows in a database) according
to a specific structure, a data model also deals with:

* Access to records via REST APIs and landing pages.
* Internal storage, representation and retrieval of records and
  persistent identifiers.
* Mapping external representations to/from the internal representation via
  loaders and serializers.

You can build data models that are both custom to your exact needs, or you can
build data models that follow standard metadata formats such as Dublin Core,
DataCite or MARC21. In fact, a data model does not put any restrictions on what
you can store, except that a record must be stored internally as JSON.

You can build data models for classic digital repository use cases such as
bibliographic and author records, but Invenio is in no way limited to these
classic use cases, and you could as well build your geographical research
database on top of Invenio.

First steps
-----------
First of all, make sure you have followed the :ref:`quickstart`, to ensure
you have scaffolded an initial *Invenio instance* and *a data model package*.

You should see a directory structure similar to the one below in the newly
scaffolded data model package:

.. code-block:: shell

    |-- ...
    |-- docs
    |   |-- ...
    |-- my_site
    |   |-- config.py
    |   |-- records
    |   |   |-- jsonschemas/
    |   |   |-- loaders/
    |   |   |-- mappings/
    |   |   |-- marshmallow/
    |   |   |-- serializers/
    |   |   |-- static/
    |   |   |-- templates/
    |   |   `-- ...
    |   `-- ...
    |-- setup.py
    `-- tests
        |-- ...


**Steps**

Building a data model involves the following tasks:

- Internal representation
    - :ref:`models-jsonschema` -- used to validate the internal
      structure of your record.
    - :ref:`models-mapping` --  used to specify how your
      records are indexed by the search engine.
- External representation
    - :ref:`models-serializers` -- transform an *internal* representation to an external (e.g. JSON to DataCite XML).
    - :ref:`models-loaders` -- transform and validates an *external* representation to an internal (e.g. DataCite XML to JSON).
    - :ref:`models-marshmallow` -- used to build loaders and serializers.
- Exposing records via the UI and REST API
    - :ref:`models-templates` -- used to render search results and landing pages.
    - :ref:`models-ui` -- enables HTML landing pages for your records.
    - :ref:`models-rest` -- enables the REST API for your records.

.. _models-jsonschema:

Define a JSONSchema
-------------------
Internally records are stored as JSON, and in order to validate the structure of
the stored JSON you must write a `JSONSchema <http://json-schema.org>`_.

The scaffolded data model package includes an example of a simple JSONSchema,
that you can use to get a feeling of what a JSONSchema looks like.

.. code-block:: shell

    |-- my_site
    |   |-- records
    |   |   |-- jsonschemas
    |   |   |   |-- __init__.py
    |   |   |   `-- records
    |   |   |       `-- record-v1.0.0.json


In ``record-v1.0.0.json`` you should see something like:

.. code-block:: json

    {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "id": "https://localhost/schemas/records/record-v1.0.0.json",
        "type": "object",
        "properties": {
            "title": {
            "description": "Record title.",
            "type": "string"
            },
        }
    }

**Example record**

An example record that validates against this schema could look like:

.. code-block:: json

    {
        "$schema": "https://localhost/schemas/records/record-v1.0.0.json",
        "title": "My record"
    }

Note, that the ``$schema`` key points to the JSONSchema that the record should
be validated against.

**Discovery of schemas**

Invenio is using standard Python entry points to discover your data model
package's JSONSchemas. Thus, you'll see in the ``setup.py`` an entry point
group ``invenio_jsonschemas.schemas``:

.. code-block:: python

    setup(
        # ...
        entry_points={
            'invenio_jsonschemas.schemas': [
                'my_datamodel = my_datamodel.jsonschemas'
            ],
            # ...
        },
    )

.. note::

    A typical mistake is to forget to add a blank ``__init__.py`` file inside
    the ``jsonschemas`` folder, in which case the entry point won't work.

.. _models-mapping:

Define an Elasticsearch mapping
-------------------------------
In order to make records searchable, the records need to be indexed in
Elasticsearch. Similarly to the JSONSchema that allows you to validate the
structure of the JSON, you need to define an *Elasticsearch mapping*, that
tells Elasticsearch how to index your document.

The scaffolded data model package includes an example of a simple Elasticsearch
mapping

.. code-block:: shell

    |-- my_site
    |   |-- records
    |   |   |-- mappings
    |   |   |   |-- __init__.py
    |   |   |   |-- v6
    |   |   |   |   |-- __init__.py
    |   |   |   |   `-- records
    |   |   |   |       `-- record-v1.0.0.json
    |   |   |   `-- v7
    |   |   |       |-- __init__.py
    |   |   |       `-- records
    |   |   |           `-- record-v1.0.0.json

Note, you need an Elasticsearch mapping per major version of Elasticsearch
you want to support.

In ``record-v1.0.0.json`` (for Elasticsearch 7) you should see something like:

.. code-block:: json

    {
        "mappings": {
            "date_detection": false,
            "numeric_detection": false,
            "properties": {
                "$schema": {
                    "type": "text",
                    "index": false
                },
                "title": {
                    "type": "text",
                },
                "keywords": {
                    "type": "keyword"
                },
            }
        }
    }

The above Elasticsearch mapping, similarly to the JSONSchema, defines the
structure of the JSON, but also how it should be indexed.

For instance, in the above example the ``title`` field is of type ``text``,
which applies stemming when searching, whereas the ``keywords`` field is of
type ``keyword``, which means no stemming is applied, therefore, this field
is searched based on exact match. The mapping also allows you to define e.g.
that a ``lat`` and a ``lon`` field are in fact geographical coordinates, and
enable geospatial queries over your records.

.. _naming-schemas-mappings:

Naming JSONSchemas and mappings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You may already have noticed that both JSONSchemas and Elasticsearch mappings
are using the same folder structure and naming scheme:

.. code-block:: shell

    |-- my_site
    |   |-- records
    |   |   |-- jsonschemas
    |   |   |   |-- __init__.py
    |   |   |   `-- records
    |   |   |       `-- record-v1.0.0.json
    |   |   |-- mappings
    |   |   |   |-- __init__.py
    |   |   |   `-- v7
    |   |   |       |-- __init__.py
    |   |   |       `-- records
    |   |   |           `-- record-v1.0.0.json


The naming scheme is very important for three reasons:

1. Indexing of records
2. Data model evolution
3. Discovery of mappings

**1. Indexing of records**

Invenio will determine the Elasticsearch index for a given record, based on the
record's ``$schema`` key. For instance, given the following record:

.. code-block:: json

    {
        "$schema": "https://localhost/schemas/records/record-v1.0.0.json",
        "...": "..."
    }

Invenio will send the above record to the ``records-record-v1.0.0``
Elasticsearch index. Note, it's possible to customize this behavior.

**2. Data model evolution**

Over time data models are likely to evolve. In many cases, you can simply make
backward compatible changes to the existing JSONSchema and Elasticsearch
mappings. In cases, where you change the data model in a backward incompatible
way, you create a new JSONSchema and new mappings (e.g. ``record-v1.1.0.json``)

.. code-block:: shell

    |-- my_site
    |   |-- records
    |   |   |-- jsonschemas
    |   |   |   |-- __init__.py
    |   |   |   `-- records
    |   |   |       `-- record-v1.0.0.json
    |   |   |       `-- record-v1.1.0.json
    |   |   |-- mappings
    |   |   |   |-- __init__.py
    |   |   |   `-- v7
    |   |   |       |-- __init__.py
    |   |   |       `-- records
    |   |   |           `-- record-v1.0.0.json
    |   |   |           `-- record-v1.1.0.json


This allows you to simultaneously store old and new records - i.e. you don't
have to take down your service for hours to migrate millions of records from
one version to a new one.

Now of course, old records will be sent to the ``records-record-v1.0.0`` index
and new records will be sent to the ``records-record-v1.1.0`` index. However,
a special Elasticsearch *index alias* ``records`` is also created, that allows
you to search over both old and new records, thus smoothly handling data model
evolution.

**3. Discovery of mappings**

Invenio is using standard Python entry points to discover your data model
package's Elasticsearch mappings. Thus, you'll see in the ``setup.py`` an entry
point group ``invenio_search.mappings``:

.. code-block:: python

    setup(
        # ...
        entry_points={
            'invenio_search.mappings': [
                'records = my_datamodel.mappings'
            ],
            # ...
        },
    )

Note, that the left-hand-side of the entry point,
``records = my_datamodel.mappings``, defines the folder name/index alias (i.e.
``records``) and that the right-hand-side defines the Python import path to the
``mappings`` package.

.. note::

    A typical mistake is to forget to add a blank ``__init__.py`` file inside
    the ``mappings``, ``v6`` and ``v7`` folders, in which case the entry points
    won't be correctly discovered.

.. _models-marshmallow:

Define a Marshmallow schema
---------------------------
`Marhsmallow <https://marshmallow.readthedocs.io/en/3.0/index.html>`_ is a
Python library that helps you write highly advanced
serialization/deserialization/validation rules for your input/output data.
You can think of Marshmallow schemas as akin to form validation.

Marshmallow use in Invenio is optional, but is usually very helpful when you go
beyond purely structural data validation - e.g. validating one field given the
value of another field.

In Invenio, the Marshmallow schemas are located in the ``marshmallow`` Python
module. You may have multiple Marshmallow schemas depending on your
serialization and deserialization needs.

.. code-block:: shell

    |-- my_site
    |   |-- records
    |    |   |-- marshmallow
    |    |   |   |-- __init__.py
    |    |   |   `-- json.py

Below is a simplified example of a Marshmallow schema you could use in
``json.py`` (note, the scaffolded data model package, includes a more complete
example):

.. code-block:: python

    from invenio_records_rest.schemas import StrictKeysMixin
    from marshmallow import fields

    class RecordSchemaV1(StrictKeysMixin):
        metadata = fields.Raw()
        created = fields.Str()
        revision = fields.Integer()
        updated = fields.Str()
        links = fields.Dict()
        id = fields.Str()

In Invenio the Marshmallow schemas are often used together with serializers and
loaders, so continue reading to see how the schema is used.

**What's the difference: JSONSchemas, Mappings and Marshmallow?**

It may seem a bit confusing that Invenio is dealing with three types of
schemas. There's however good reasons:

- **JSONSchema**: Deals with the internal structural validation of records
  stored in the database (much like you define the table structure in
  database).
- **Elasticsearch mappings**: Deals with how records are indexed in
  Elasticsearch which has big impact on your search results ranking.
- **Marshmallow schema**: Deals with primarily data validation and
  transformation for both serialization and deserialization (think of it as
  form validation).

.. _models-serializers:

Define serializers
------------------
Think of serializers as the definition of your output formats for records. The
serializers are responsible for transforming the internal JSON for a record
into some external representation (e.g. another JSON format or XML).

Serializers are defined in the ``serializers`` module:

.. code-block:: shell

    |-- my_site
    |   |-- records
    |   |   |-- serializers
    |   |   |   `-- __init__.py

By default, Invenio provides serializers that can help you serialize your
internal record into common formats such as JSON-LD, Dublin Core, DataCite,
MARCXML, Citation Style Language.

**Example**

In the scaffolded data model package, there's an example of a simple
serializer:

.. code-block:: python

    from invenio_records_rest.serializers.json import \
        JSONSerializer
    from invenio_records_rest.serializers.response import \
        record_responsify, search_responsify

    from ..marshmallow import RecordSchemaV1

    #: JSON serializer definition.
    json_v1 = JSONSerializer(RecordSchemaV1, replace_refs=True)

    #: Serializer for individual records.
    json_v1_response = record_responsify(json_v1, 'application/json')
    #: Serializer for search results.
    json_v1_search = search_responsify(json_v1, 'application/json')


First, we create an instance of the ``JSONSerializer`` and provide it with
our previously created Marshmallow schema. The marshmallow schema is used to
transform the internal JSON prior to that the ``JSONSerializer`` dumps the
actual JSON output. This allows you e.g. to evolve your internal data model,
without affecting your REST API.

Next, we create two different **response serializers**: ``json_v1_response``
and ``json_v1_search``. The former is responsible for producing an HTTP
response for an individual record, while the latter is responsible for
producing an HTTP response for a search result (i.e. multiple records).

The response serializer can not only output data to the HTTP response body, but
can also add HTTP headers (e.g. Link headers).

You can see examples of the output from the two response serializers in
the Quickstart section: :ref:`display-a-record` and :ref:`search-for-records`.

.. _models-loaders:

Define loaders
--------------
Think of loaders as the definition of your input formats for records. You only
need loaders if you plan to allow creation of records via the REST API.

The loaders are responsible for transforming a request payload (external
representation) into the internal JSON format.

Loaders are defined in the ``loaders`` module:

.. code-block:: shell

    |-- my_site
    |   |-- records
    |    |   |-- loaders
    |    |   |   `-- __init__.py

Loaders are defined in much the same way as serializers, and similarly you can
use the Marshmallow schemas:

.. code-block:: python

    from invenio_records_rest.loaders.marshmallow import \
        marshmallow_loader
    from ..marshmallow import MetadataSchemaV1

    json_v1 = marshmallow_loader(MetadataSchemaV1)

Note, that you are not required to use Marshmallow for deserialization, but it
allows you to use advanced data validation rules on your REST API.

.. _models-templates:

Define templates
----------------
In order to display records not only on your REST API, but also provide
search interface and landing pages for your record you need to provide
templates that render your records.

You will need two different types of templates:

- Search result template
- Landing page template

The templates are stored in two different folders (``static`` and
``templates``):

.. code-block:: shell

    |-- my_site
    |   |-- records
    |   |   |-- static
    |   |   |   `-- templates
    |   |   |       `-- my_datamodel
    |   |   |           `-- results.html
    |   |   |-- templates
    |   |   |   `-- my_datamodel
    |   |   |       `-- record.html


**Search result template**

The Invenio search interface is run by a JavaScript application, and thus the
template is rendered client side in the user's browser. The template uses data
received by the REST API and thus your REST API must be able to deliver all
information you would like to render in the template (your serializers are
responsible for this).

The search results template is by default (it's configurable) located in
``static/templates/my_datamodel/results.html`` and is using the Angular
template syntax.

**Landing page template**

The landing page for a single record is rendered on the server-side using a
Jinja template.

The landing page template is by default (it's configurable) located in
``templates/my_datamodel/record.html`` and is using the Jinja template
syntax.

.. _models-ui:

Configure the UI
----------------
Last step after having defined all the different schemas, serializers, loaders
and templates is to configure your REST API and landing pages for your records.

This is all done from the data model's ``config.py``:

.. code-block:: shell

    |-- my_site
    |   |-- records
    |   |   |-- config.py

.. note::

    Take care, not to confuse ``my_site/records/config.py`` (the data model's
    module configuration) with ``my_site/config.py`` (your application's
    configuration).

    To avoid the application configuration file from growing very big, we
    usually keep the **default** configuration for a module in a ``config.py``
    inside the module.

**Landing page**

Let's start by configuring the landing page:

.. code-block:: python

    RECORDS_UI_ENDPOINTS = {
        'recid': {
            'pid_type': 'recid',
            'route': '/records/<pid_value>',
            'template': 'my_datamodel/record.html',
        },
    }

Here an explanation of the different keys:

* ``pid_type``: Defines the persistent identifier type which the resolver
  should use to lookup records. Invenio provides an internal persistent
  identifier type called ``recid`` which is an auto-incrementing integer.
* ``route``: URL endpoint under which to expose the landing pages.
* ``template``: Template to use when rendering the landing page.
* ``recid``: Unique name of the endpoint. If this is the primary landing page,
  it must be named the same as the value of ``pid_type`` (i.e. ``recid``).

.. _models-rest:

Configure the REST API
----------------------
Configuring the REST API is done similarly to the landing pages via the
``RECORDS_REST_ENDPOINTS`` configuration variable in ``config.py``:

**Persistent identifier type**

First you provide the persistent identifier type used by the resolver. You also
need to configure a persistent identifier minter and fetcher. In the scaffolded
data model package, you are just using the already provided ``recid`` minter
and fetchers.

A `minter <https://invenio-pidstore.readthedocs.io/en/latest/usage.html#minters>`_
is responsible for generating a new persistent identifier for your
record, while a
`fetcher <https://invenio-pidstore.readthedocs.io/en/latest/usage.html#fetchers>`_
is responsible for extracting the persistent identifier from your search
results:

.. code-block:: python

    RECORDS_REST_ENDPOINTS = {
        'recid': dict(
            pid_type='recid',
            pid_minter='recid',
            pid_fetcher='recid',
            # ...
        ),
    }

**Search**

Next, you define the Elasticsearch index to use for searches. The index is
defined as ``records`` because this is the index alias which was created for
our mappings ``records/record-v1.0.0.json`` (see
:ref:`naming-schemas-mappings`).

.. code-block:: python

    RECORDS_REST_ENDPOINTS = {
        'recid': dict(
            # ...
            search_index='records',
        ),
    }

**Serializers**

Next, you define which serializers to use. Invenio is using HTTP Content
Negotiation to choose your serializer. You have to specify the serializer for
individual records in ``record_serializers`` and the serializers for search
results in ``search_serializers``:

.. code-block:: python

    RECORDS_REST_ENDPOINTS = {
        'recid': dict(
            # ...
            record_serializers={
                'application/json': (
                    'my_datamodel.serializers:json_v1_response'),
            },
            search_serializers={
                'application/json': (
                    'my_datamodel.serializers:json_v1_search'),
            },
        ),
    }


**Loaders**

Next, you define the loaders to use. Similar to the serializers the loaders are
selected based on HTTP Content Negotiation.

.. code-block:: python

    RECORDS_REST_ENDPOINTS = {
        'recid': dict(
            # ...
            record_loaders={
                'application/json': (
                    'my_datamodel.loaders:json_v1'),
            },
        ),
    }

**URL routes**

Last you define the URL routes under which to expose your records:

.. code-block:: python

    RECORDS_REST_ENDPOINTS = {
        'recid': dict(
            # ...
            list_route='/records/',
            item_route='/records/<pid(recid):pid_value>',
        ),
    }


Next steps
----------
Above is a quick walk through of the different steps to build a data model. In
order to get more details on individual topics we suggest further reading:

- `Invenio-Records-REST <http://invenio-records-rest.readthedocs.io/en/latest/>`_
- `Invenio-JSONSchemas <http://invenio-jsonschemas.readthedocs.io/en/latest/>`_
- `Invenio-PIDStore <http://invenio-pidstore.readthedocs.io/en/latest/>`_
- `Invenio-Records <http://invenio-records.readthedocs.io/en/latest/>`_
- `JSONSchema <http://json-schema.org>`_
- `Elasticsearch mappings <https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html>`_
- `Elasticsearch field types <https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html>`_
- `Marshmallow schemas <https://marshmallow.readthedocs.io/en/3.0/index.html>`_

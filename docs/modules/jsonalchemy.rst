===========
JSONAlchemy
===========

.. currentmodule:: invenio.modules.jsonalchemy

JSONAlchemy provides an abstraction layer on top of your database to work with
JSON objects, helping the administrators to define the data model of their site
independent of the master format they are working with and letting the
developers work in a controlled and uniform data environment.

.. contents::
   :local:
   :backlinks: none


Configuration
=============
TODO: talk about fields and models, how to define them (decorators and
extensions included), readers and storage engine

How it Works
============
TODO: explain how everything works together, how the magic happens. Maybe a
small example (record centric?)

Invenio Use Cases
=================
TODO: pointer to records, annotations and documents documentation (where real
'how to' stile documentation is place for each of them).

API Documentation
=================
This documentation is automatically generated from JSONAlchemy's source code.

Core
----

Bases
^^^^^
.. automodule:: invenio.modules.jsonalchemy.bases
    :members:

Errors
^^^^^^
.. automodule:: invenio.modules.jsonalchemy.errors
    :members:

Base Model and Field Parser
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: invenio.modules.jsonalchemy.parser._create_field_parser

.. autofunction:: invenio.modules.jsonalchemy.parser._create_model_parser

.. autoclass:: invenio.modules.jsonalchemy.parser.FieldParser
    :members:
.. autoclass:: invenio.modules.jsonalchemy.parser.ModelParser
    :members:

Base Reader
^^^^^^^^^^^
.. autoclass:: invenio.modules.jsonalchemy.reader.Reader
    :members:

Registries
^^^^^^^^^^
.. automodule:: invenio.modules.jsonalchemy.registry
    :members:

Storage Engine Interface
^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: invenio.modules.jsonalchemy.storage.Storage
    :members:

Default Validator
^^^^^^^^^^^^^^^^^
.. autoclass:: invenio.modules.jsonalchemy.validator.Validator
    :members:

Wrappers
^^^^^^^^
.. automodule:: invenio.modules.jsonalchemy.wrappers
    :members:

Extensions
----------

Engines
^^^^^^^
.. autoclass:: invenio.modules.jsonalchemy.jsonext.engines.cache.CacheStorage
    :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.engines.memory.MemoryStorage
    :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.engines.mongodb_pymongo.MongoDBStorage
    :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.engines.sqlalchemy.SQLAlchemyStorage
    :members:

Fields
^^^^^^
TODO

Functions
^^^^^^^^^
TODO

Models
^^^^^^^^^
TODO

Parsers
^^^^^^^^^
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.connect_parser.ConnectParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.depends_on_parser.DependsOnParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.description_parser.DescriptionParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.extension_model_parser.ExtensionModelParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.json_extra_parser.JsonExtraParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.legacy_parser.LegacyParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.memoize_parser.MemoizeParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.only_if_master_value_parser.OnlyIfMasterValueParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.only_if_parser.OnlyIfParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.parse_first_parser.ParseFirstParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.producer_parser.ProducerParser
   :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.parsers.schema_parser.SchemaParser
   :members:

Producers
^^^^^^^^^

JSON for MARC
*************

.. automodule:: invenio.modules.jsonalchemy.jsonext.producers.json_for_marc
   :members:

Readers
^^^^^^^
.. autoclass:: invenio.modules.jsonalchemy.jsonext.readers.json_reader.JsonReader
    :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.readers.marc_reader.MarcReader
    :members:


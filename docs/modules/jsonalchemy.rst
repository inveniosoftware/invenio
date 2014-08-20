..  This file is part of Invenio
    Copyright (C) 2014 CERN.

    Invenio is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

.. _jsonalchemy:

=============
 JSONAlchemy
=============

.. currentmodule:: invenio.modules.jsonalchemy

JSONAlchemy provides an abstraction layer on top of your database to work with
JSON objects, helping the administrators to define the data model of their site
independent of the master format they are working with and letting the
developers work in a controlled and uniform data environment.

.. contents::
   :local:
   :depth: 2
   :backlinks: none

.. admonition:: WIP, Finish with the empty sections:

    * Module Structure: Explain what is each folder for and maybe the
      namespaces.
    * Readers:
    * How it works: explain how everything works together, how the magic
      happens. Maybe a small example (record centric?).
    * How to Extend JSONAlchemy Behaviour
    * Invenio Use Cases: pointer to records, annotations and documents
      documentation (where real 'how to' stile documentation is place for each
      of them).

Module Structure
================

Configuration
=============

JSONAlchemy works with two different configuration files, one for the field
definitions and the second one for the models.

Field Configuration Files
-------------------------

This is an example (it might not be 100% semantically correct) of the
definition of the field 'title'::


    title:
        schema:
            {'title': {'type': 'dict', 'required': False}}
        creator:
            @legacy((("245", "245__","245__%"), ""),
                    ("245__a", "title", "title"),
                    ("245__b", "subtitle"),
                    ("245__k", "form"))
            marc, '245..', {'title': value['a'], 'subtitle': value[b]}
            dc, 'dc:title', {'title': value}
            unimarc, '200[0,1]_', {'title': value['a'], 'subtitle': value['e']}
        producer:
            json_for_marc(), {'a': 'title', 'b': 'subtitle'}
            json_for_dc(), {'dc:title': ''}
            json_for_unimarc(), {'a': 'title', 'e': 'subtitle'}


A field definition is made out several sections, each of them identified
by its indentation (like python does).

In this example we can find the three more common sections that a field can
have, ``schema``, ``creator`` and ``producer``.  There could be more sections,
we will explain the ones that *Invenio* provides but be aware that new sections
could come via extensions, actually only the ones mentioned before are inside
the core of the *JSONAlchemy* the rest are already defined as extensions.

Each of this section will add some information to the dictionary representing
the field definition, for example the dictionary generated for the field
defined above would be something like::

    {'aliases': [],
     'extend': False,
     'override': False,
     'pid': None,
     'producer': {
         'json_for_marc': [((), {'a': 'title', 'b': 'subtitle'})],
         'json_for_dc': [(), {'dc:title': ''}]
         'json_for_unimarc': [(), {'a': 'title', 'e': 'subtitle'}]}
     'rules': {
         'json': [
             {'decorators': {'after': {}, 'before': {}, 'on': {}},
             'function': <code object <module> at 0x10f173030, file "", line 1>,
             'source_format': 'json',
             'source_tags': ['title'],
             'type': 'creator'}],
         'marc': [
             {'decorators': {'after': {}, 'before': {}, 'on': {'legacy': None}},
             'function': <code object <module> at 0x10f10de30, file "", line 1>,
             'source_format': 'marc',
             'source_tags': ['245__'],
             'type': 'creator'}]}}

Here we are just showing one field but one file could contain from one up to
*n* field definitions. Check out the ``atlantis.cfg`` file from the *Invenio demo
site* to get a quick view about how your configuration file for your fields
should look like.

For the BFN lovers, this is something close to the grammar used to parse this::

    rule       ::= [pid | extend | override]
                json_id ["," aliases]":"
                    body
    json_id    ::= (letter|"_") (letter|digit|_)*
    aliases    ::= json_id ["," aliases]

    pid        ::= @persitent_identifier( level )
    extend     ::= @extend
    override   ::= @override

    body       ::=(creator* | derived | calculated) (extensions)*

    creator    ::= [decorators] format "," tag "," expr
    derived    ::= [decorators] expr
    calculated ::= [decorators] expr

Creator
^^^^^^^

This is the one of most important part of the field definition, here the
content of the field is defined depending on its origin.

The creator section is the one used to define the fields that are coming from
the input file directly and don't depend on any type of calculation from any
other source, we also call this kind of field **real fields**.

This section could be made out of several lines, one at least, where each one
represents the translation of this field from the input format to JSON.

For example::

    marc, '245..', {'title': value['a'], 'subtitle': value[b]}

Is telling us that for the master format ``marc`` we will take any field that
matches the regular expression ``245..`` (more regular expressions could be
specified space separated) and then we will apply the transformation ``{'title':
value['a'], 'subtitle': value[b]}``.

The last part of the line needs to be a valid python expression as it will be
evaluated assuming that. For this part we have available the value of the field
that we are dealing with inside ``value``, which is typically a dictionary.
This python expression could be also a function call, in this case either you
manage the import using ``__import__()`` function or if you put the function
implementation inside the ``/functions`` folder it will be imported
automatically.

For each master format that we want to deal with we need to have a ``Reader``, we
will see afterwards what it that and how to create one. A reader for JSON and
for MARC21 is provided by default with *Invenio*. See :ref:`readers` for more
information about readers and :ref:`how-to-extend-jsonalchemy-behaviour` to
learn about how to write your own reader.

Together with each creator rule there could be one or more decorators (as in
python). We will describe the default decorators that are implemented and how
to do more later in the :ref:`decorators` section.

Derived
^^^^^^^

When a field comes from other place that is not the input file and it could be
calculated only onces, meaning that it might change just a few times we call it
derived, and it is also **virtual field**.

An example of kind of field could be something like::

    number_of_authors:
        derived:
            @depends_on('authors')
            len(self['authors'])


This section is similar to the previous one, creator, but in this case each
line is just a valid python expression.

Calculated
^^^^^^^^^^

Another type of **virtual field** are the ones which values changes a lot
during time, for example the number of comments that a record inside *Invenio*
has or the number of reviews that a paper has.

In this cases we use calculated field definitions. Following the example of
the number of comments this could be its definition::

    number_of_comments:
        calculated:
            @parse_first('recid')
            @memoize(30)
            get_number_of_comments(self.get('recid'))

The way that a calculate rule is defined is the same as for the derived fields.

One important point about the calculated fields is caching, one field could be
cached always until someone (some other module) changes its name, could be
cached for a period of time (like in the example) or could be not cached at all
so its value is calculated every time. See the :ref:`decorators` for more
information about it.

Schema
^^^^^^

Here we can specify the **schema** or structure that the field should follow.
This is using `nicolaiarocci/cerberus
<http://github.com/nicolaiarocci/cerberus>`_ and you read the documentation on
how to use it in `read the docs <http://cerberus.readthedocs.org/en/latest/>`_.

*JSONAlchemy* only adds two things to the default *cerberus*:

1. ``force``, boolean value that tells if the value of the filed needs to be
   casted to ``type``.  2. ``default``, function without any parameter to call
   if the field has a default value.

An example of the schema section could be::

    schema:
        {'uuid': {'type':'uuid', 'required': True, 'default': lambda: str(__import__('uuid').uuid4())}}

Description
^^^^^^^^^^^

This is an special section as it could be used without the block::

    uuid:
        ""
        This is the main persistent identifier of a document and will be
        used
        internally as this, therefore the pid important should always
        be '0'.
        """

    recid:
        description:
            """Record main identifier. """

Both cases are the same and the syntax of is the same, triple quoted string
(like python doc string).

.. note:: The docstrings are not used anywhere else but inside the
    configuration files, for now. The plan is to use them to build the sites
    data model documentation using spinxh, therefore is quite important to
    write them and keep them updated.

JSON
^^^^

Not all the fields that we want to use have a JSON friendly representation,
think about a date, we would like to use it as a ``datetime`` object but we
still want to store as a JSON object.

To solve this issue we introduce the json section where a couple of functions
could be used to **load** the JSON representation from the database into and
object and **dumps** which does the opposite.

A clear example of that is the ``creation_date`` field::

    creation_date:
        json:
            dumps, lambda d: d.isoformat()
            loads, lambda d: __import__('dateutil').parser.parse(d)

Both functions take only one argument, which is the value of the field.

Producer
^^^^^^^^

Generating a different output from a JSON object is not always easy, there
might be implications among fields or any kind or rules. For that we introduce
the producer section, which could also be seen as a short of documentation of
how a field is exported to different formats and which are those formats.

This is an example of its use::

    title:
        creator:
            marc, "245..", { 'title':value['a'], 'subtitle': value['b']}
        producer:
            json_for_marc(), {'a': 'title', 'b': 'subtitle'}
            json_for_dc(), {'dc:title': 'title'}

Each rule inside the producer section follows the same pattern, first we
specify the function that we want to use (what we want to produce), which
should be placed inside the ``/producers`` folder. This function is not a real
function call the function, it is just a way to specify which producer we will
use an which parameter we what to use for this field. In the case of the MARC21
producer we can put ``245__`` as parameter and only if title came from a
``245__`` MARC21 field this function will generate the output. This parameter
could be used differently depending on each producer.

The second part, after the comma, is the rule that we will apply and it is
typically a dictionary. In the case of the MARC21 producer we can put full name
of the field as key, ``245__a`` or just the subfield like in the example. The
value for this keys could a function call, a subfield or empty if we want the
value of the full field.

For more information about the MARC21 producer please check
:ref:`json-for-marc` documentation.

Inside any JSONAlchemy object, like records or documents, there is a method,
``produce(producer_code, fields=None)``, that uses this and outputs a
dictionary with a certain "flavor". This new representation of the JSON object
could be used elsewhere, for example in the formatter module, to generate the
desired output in a easier way than only using the JSON object.

.. _decorators:

Decorators
^^^^^^^^^^

Like python decorators, field decorators could be used either to add extra
information to the field itself or to modify the translation process that
creates the field.

There are two different types of field decorators, one that decorates the
entire field and the other that decorates one creator/derived/calculated rule.
As well as for the sections in the field definition new decorators could be
defined to extend the current ones.

Field Decorators
""""""""""""""""

This type of decorators should be used outside of the field definition and
affects the whole field, maybe adding some information to the dictionary that
defines it.

*Invenio* provides already three different field decorators:
``@persitent_identifier(int)`` identifies a field as a *PID* with a priority,
afterwards this field could be accessed using the ``persistent_identifiers``
property; ``@override`` as it name points out allow us to override completely
the field definition; and ``@extend`` which let us extend an existing field
with, for example, new creator rules.

.. note:: For this type of decorators there are currently no extensions.
    It is in the road map to allow each *Invenio* instace to extend this
    decorators with any other that they might need.

Rule Decorators
"""""""""""""""

The other type of decorators applies to the creator/derived/calculated rules,
for example::

    authors:
    """List with all the authors, connected with main_author and rest_authors"""
    derived:
        @parse_first('_first_author', '_additional_authors')
        @connect('_first_author', sync_authors)
        @connect('_additional_authors', sync_authors)
        @only_if('_firs_author' in self or '_additional_authors' in self)
        util_merge_fields_info_list(self, ['_first_author', '_additional_authors'])

The for decorators are applied only if the derived rule of the field
``authors`` is applied.

Within the rule decorators there are three different kinds depending on when
they are evaluated: before the rule gets evaluated, during the evaluation of
the rule and after the rule evaluation.

This is the list of rule decorators available in *Invenio* and what they are
used for.

``connect(field_name, handler=None)``
    This is an after evaluation decorator that allows the connection between
    fields. This connection is bidirectional, if the connected field gets
    modify the decorated field also gets modified and vice versa.

    The optional handler function will be called whenever there is any
    modification in any of the field. The default behavior is to propagate the
    value across all the connected fields.

``depends_on(*field_names)``
    Before rule evaluation decorator that simply tells JSONAlchemy whether the
    rule will be evaluated depending on the existence of the ``field_names``
    inside the current JSON object.

    If the fields are not in the JSON object and their rules were not evaluated
    yet, then it will try to evaluate them before failing.

``legacy(master_format, legay_field, matching)``
    On evaluation decorator that add some legacy information the rule that its
    being applied.
    The master format is not important if dealing with a creator rule (it will
    be derived from the rule), otherwise it needs to specified.
    The matching argument is typically a tuple where we connect the legacy
    field with the subfields.

``memoize(life_time=0)``
    This after evaluation decorator only works with calculated fields, it
    creates a cached value of the field that is decorated for a determined
    time.

``only_if_master_value(*boolean_expresions)``
    On evaluation decorator that gives access to the current master value. It
    is typically use to evaluate one rule only if the master value matches a
    series of conditions.

    The boolean expression could be any python expression that is evaluated to
    ``True`` or ``Flase``.

``only_if(*boolean_expresions)``
    Like the previous one but in this case we don't have access to the current
    master value, only to the current JSON object.

``parse_first(*field_names)``
    It could be seen as a lighter version of ``depends_on``, in this case the
    rule will be evaluated even though the fields names are not inside the JSON
    object, it only triggers parsing the rules for the fields.

For more information about the decorators, and also about the other extensions,
check the :ref:`parsers` section.


.. note:: Be aware that right now the order of the decorators is not respected.


Model Configuration File
------------------------

.. _readers:

Readers
-------


How it Works
============


.. _how-to-extend-jsonalchemy-behaviour:

How to Extend JSONAlchemy Behaviour
===================================


Invenio Use Cases
=================


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


Functions
^^^^^^^^^

.. _parsers:

Parsers
^^^^^^^
.. automodule:: invenio.modules.jsonalchemy.jsonext.parsers

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

.. _json-for-marc:

JSON for MARC
"""""""""""""

.. automodule:: invenio.modules.jsonalchemy.jsonext.producers.json_for_marc
   :members:


Readers
^^^^^^^

.. autoclass:: invenio.modules.jsonalchemy.jsonext.readers.json_reader.JsonReader
    :members:
.. autoclass:: invenio.modules.jsonalchemy.jsonext.readers.marc_reader.MarcReader
    :members:


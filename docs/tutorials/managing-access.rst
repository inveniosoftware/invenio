..
    This file is part of Invenio.
    Copyright (C) 2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _managing-access:

Managing access to records
==========================
Invenio comes with a access control system that is very powerful and flexible
but which can also seem overwhelming at first. This guide will show you a
basic example of how to protect our REST API so only some users can see
certain records.

If you haven't already done so, make sure you've followed the :ref:`quickstart`
so you have an Invenio instance to work on.

Endpoints
---------
Your data model's REST API has two main endpoints:

    - Search endpoint (e.g. ``/api/records``)
    - Detail endpoint (e.g. ``/api/records/<id>``)

The goal is to ensure that a) only an owner of a record can retrieve their
record from the detail endpoint and b) that the search endpoint only shows
records that a given user owns.

In order to protect the two endpoints we will:

1. **Store permissions** in a record by adding a new field ``owner`` to our
   data model.
2. **Require permissions** by writing:
    - a *permission factory* to protect the detail endpoint.
    - a *search filter* to filter results in the search endpoint.
3. **Configure endpoints** to use the permission factory and search filter.

Storing permissions
-------------------
First, below is an example of how we could store an owner inside a
record by adding a new field ``owner``:

.. code-block:: json

    {
        "title": "My secret publication",
        "owner": 1
    }

In order to be able to store the ``owner`` property in our data model, you
must add this new field to the data model's:

1. **JSONSchema** (think of the JSONSchema as the database table structure that
   you add a new column to).
2. **Elasticsearch mapping** (think of the mapping as a description of how your
   data should be indexed).
3. **Marshmallow schema** (think of the Marshmallow schema as a description of
   how you would render one or more rows in a database table to an end-user).

JSONSchema
~~~~~~~~~~
In the quickstart example, our JSONSchema is located in
``.../records/jsonschemas/record-v.1.0.0.json``, and you would add something
like below to our schema:

.. code-block:: json

    {
        "owners": {
        "type": "integer"
        }
    }
    
Elasticsearch mapping
~~~~~~~~~~~~~~~~~~~~~
In the quickstart example, our Elastisearch mapping is likely located in
``.../records/mappings/v6/record-v.1.0.0.json``, and you would add something
like below to our mapping:

.. code-block:: json

    {
        "owners": {
        "type": "int"
        }
    }

Requiring permissions
---------------------
Once you have added the new field(s) to your data model, you need to make use
of the field to protect the detail endpoint and the search endpoint. You
do that by writing

    - a *permission factory* to protect the detail endpoint.
    - a *search filter* to filter results in the search endpoint.

Permission factory
~~~~~~~~~~~~~~~~~~
The purpose of the permission factory is to create a permission object from a
record which is then used by the detail endpoint to check if the current user
has permission to view the current record. Below is a simple example of a
permission factory:

.. code-block:: python

    from invenio_access import Permission
    from flask_principal import UserNeed

    def my_permission_factory(record=None):
        return Permission(UserNeed(record["owner"]))

The permission factory function takes as input a record and creates a
:py:class:`~invenio_access.permissions.Permission` object from it.

The permission, when checked, requires that the current user has the same id as
the id stored in the records ``owner`` field. This is expressed with the
``UserNeed``.

**Permissions and needs**

The concept of *needs* can be somewhat hard to grasp, but essentially it just
expresses the smallest level of access control. For instance ``UserNeed(1)``
expresses the statement "has user id 1", and ``RoleNeed('admin')`` expresses
the statement "has admin role".

A *permission* represents a set of required *needs*. For instance
``Permission(UserNeed(1), RoleNeed('admin'))`` expresses the statement "has
user id 1 or has admin role".

Thus, with a permission factory you can build arbitrarily complex permissions
from the information stored in your records.

Search filter
~~~~~~~~~~~~~
For searches over possibly millions of records we need to be able to
efficiently check permissions of all records. This is done with a search filter
which is applied when executing a query. In comparison, a permission factory
only deals with one record at a time.

Below is an example of search filter which is applied to all queries on
the search endpoint:

.. code-block:: python

    from elasticsearch_dsl import Q
    from flask_security import current_user
    from invenio_search.api import DefaultFilter, RecordsSearch

    def permission_filter():
        return [Q('match', owner=current_user.get_id())]

    class MyRecordSearch(RecordsSearch):
        class Meta:
            index = 'records'
            default_filter = DefaultFilter(permission_filter)


The method ``permission_filter`` when called, will create an Elasticsearch DSL
``Q()`` (query object) which will match all records where the property owner
equals the current user's id (``current_user`` is an object that holds the
current request's authenticated user).

The class ``MyRecordSearch``,  will be responsible for executing all queries on
the search endpoint. In above example, we set the name of the Elasticsearch
index it should used, and the search filter which it should use (in our case
the permission filter).

**Search filter vs permission factory**

There's a subtle difference between the search filter and the permission
factory which is worth noting.

The permission factory takes a record as input, while the search filter takes
the current user as input. For the permission factory, the created permission
is checked against the current user, while with the search filter the current
user is checked against the records. Hence, the permission factory and search
filter are coming from each their end when checking permissions.

It's therefore very important when writing the search filter and permission
factory, that the two are producing identical results.

Configuring endpoints
---------------------
The last part of the puzzle is to tell our detail/search endpoints to use our
newly created permission factory and search filter:

.. code-block:: python

    RECORDS_REST_ENDPOINTS = {
        'recid': dict(
            # ...
            search_class=MyRecordSearch,
            read_permission_factory_imp=my_permission_factory,
            # ...
        ),
    }

In our case we are protecting only the read operation on the view. Needless to
say, as the REST API also supports CRUD operations, you should also protect
the other operations with their a permission factory.

Complex access rights
----------------------
The toy example presented in this guide is too simple for most normal
requirements, thus in order to provide some inspiration, we here present two
more complex ways you could store access rights in records:

Computed rights
~~~~~~~~~~~~~~~
In some cases, it can be an advantage to use existing properties in your record
to manage access rights. This way, you ensure that access rights does not get
out of sync with other properties. An example of such a record could be:

.. code-block:: json

    {
        "visibility": "restricted",
        "owners": [1, 2],
        "communities": ["blr"]
    }

A permission factory could for above record then compute different permissions
objects for different types of actions.

For reading the record, the permission could be:

.. code-block:: python

    Permission(any_user)

For seeing the files in the record, the permission could be:

.. code-block:: python

    Permission(UserNeed(1), UserNeed(2), RoleNeed('blr-curators'))

For editing the record, the permission could be:

.. code-block:: python

    Permission(UserNeed(1), UserNeed(2))

Explicit rights
~~~~~~~~~~~~~~~
In some cases, it is an advantage to have explicit rights defined on your
record so that even if the code changes, it still obvious who should have
access for which actions. An example of such a record could be:

.. code-block:: json

    {
        "_access": {
            "read": {
                "systemroles": ["campus_user"]
            },
            "update": {
                "users": [1],
                "roles": ["curators"],
            }
        }
    }

This way, changes to rights can also be explicitly tracked via the records
revision history and thus be audited.

Further information
~~~~~~~~~~~~~~~~~~~
- `Invenio-Access <https://invenio-access.readthedocs.io/>`_
- `Invenio-Records-REST <https://invenio-records-rest.readthedocs.io/>`_

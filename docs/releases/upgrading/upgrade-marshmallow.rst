..
    This file is part of Invenio.
    Copyright (C) 2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _marshmallow:

Marshmallow v2/v3 compatibility
===============================

Marshmallow
-----------

Marshmallow is a package for serialization and deserialization of complex data
structures from and to Python types. You can discover its usage within
Invenio in the `documentation <https://invenio.readthedocs.io/en/latest/tutorials/understanding-data-models.html?highlight=marshmallow#define-a-marshmallow-schema>`_.


Compatibility of v2 and v3
--------------------------

If you are using or you are about to use Marshmallow in your repository
implementation, you should know that the package is about to be upgraded
to version 3.x. There have been significant changes in the code which will
influence already existing code and you should be aware of them.

.. note::

    The full guide is available in the Marshmallow `documentation <https://invenio.readthedocs.io/en/latest/tutorials/understanding-data-models.html?highlight=marshmallow#define-a-marshmallow-schema>`_.


We are upgrading the Invenio modules to be compatible with Marshmallow v3.x.
**We will provide a transition period in which modules will support both
v2.3.x and v3.x implementations of Marshmallow**.
Deprecated methods will be marked with warnings to provide you with
time to adjust your code to the latest changes.


There are two options you could follow if you are using
schemas from Marshmallow 2:

1. Stay with Marshmallow 2 for now by pinning the Marshmallow version
in your instance.

2. Upgrade to Marshmallow 3. Follow the guide below and the Marshmallow
`documentation <https://invenio.readthedocs.io/en/latest/tutorials/understanding-data-models.html?highlight=marshmallow#define-a-marshmallow-schema>`_


Guide
-----

After upgrading Marshmallow 3 in your dependencies you might find some of your
code failing. Mostly it will be connected with schema validation and the `webargs <https://webargs.readthedocs.io/en/latest/quickstart.html>`_
package. Webargs in version 5.4.0 is compatible with Marshmallow 3.x.

The biggest change is the return type of ``Schema().dump()``,
``Schema().load()``, ``Schema().dumps()`` and ``Schema().loads()``.
They do not return the ``(data, errors)`` named tuple
and the ``ValidationError`` is raised instead.
In this case if you were using ``.errors`` attribute, it will no longer work
- you need to implement your own handlers for the type
``marshmallow.ValidationError``.
Alternatively by doing ``Schema.validate()`` you can still get a list
of the errors, an example is
located in the `Marshmallow documentation <https://marshmallow.readthedocs.io/en/3.0/quickstart.html#schema-validate>`_.

Other significant changes and solutions:

- ``ValidationError`` is the Exception raised when marshmallow encounters an
   error during the validation, since the ValidationError is raised listing
   all the errors you can catch the Exception and then process them as a
   dictionary to mimic the previous behaviour.

- ``Unknown field.`` indicates that your schema is trying to validate
  data containing a field which was not defined in the schema.
  You can either add this field to the schema or use the ``unknown`` option
  of the `Schema options <https://marshmallow.readthedocs.io/en/stable/api_reference.html#marshmallow.Schema.Meta>`_
  to restore the previous, non-strict, behaviour.

- ``Not a valid type.`` indicates that the field has data of
  a different type than defined in the schema.

- ``Missing field.`` indicates that a field defined as required
  is missing from the data.
- ``JSON object has no attribute data``
  Marshmallow schema provides methods ``.dump(..)``, ``.dumps(..)``
  which no longer return namedtuple of ``(data, errors)``.
  They return json object only (formerly ``data``). All the errors
  are raised, not returned.

- If your test data is not read properly when using webargs you are probably
  using old parameters when initialising the arguments.
  You should change the ``load_from`` argument to ``data_key``.

.. code-block:: python

    # Marhsmallow 2.x
    'part_number': fields.Int(
        load_from='partNumber',
        location='query',
        required=True,
    ),

    # Marhsmallow 3.x
    'part_number': fields.Int(
        data_key='partNumber',
        location='query',
        required=True,
    ),

The full list of Marshmallow v3 changes can be found in the Marshmallow
`upgrade guide <https://marshmallow.readthedocs.io/en/stable/upgrading.html>`_.

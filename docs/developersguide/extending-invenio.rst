..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _extending-invenio:

Extending Invenio
=================

Invenio modules
---------------

Flask Extensions
----------------

.. _entrypoints:

Entry points
------------

Quick word about entry-points: it is a mechanism widely used in Invenio 3.

Invenio is built on top of Flask, so it inherits its mechanisms: it is made of modules that you can add to get new features in your base installation.

In order to extend Invenio, modules use entry-points. There are a lot of available entry-points, like:

- *bundles* (to use CSS or JavaScript bundle)
- *models* (to store data in the database)
- ...

The complete list of entry points in Invenio can be seen running ``invenio instance entrypoints``.

Depending on how your module extends Invenio, it will be registered on one or several entry points. A module can also add new entry points, thus the *bundles* entry point comes from ``invenio_assets``, and its complete name is ``invenio_assets.bundles``.

The entry-points used by your module are listed in the ``setup.py`` file.


Hooks
-----

Signals
-------

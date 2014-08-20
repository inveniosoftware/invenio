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

.. _developers-howtomodule:

How to develop a module: Part 1
===============================

This page summarizes the standard structure and naming conventions of a
module in Invenio v2.0.0. It serves as a reference point when developing
a new module, enhancing an existing one or porting a module from
older versions of Invenio.

The previous pages explained briefly what a module usually consists of, here
we will go deeper into what goes where inside the module.

Overview
--------

A simple module may have the following folder structure::

    invenio/modules/
        mymodule/
            __init__.py
            api.py
            models.py
            config.py
            views.py

These files are:

``___init__.py``
    (usually) an empty file that tells Python that this directory should be considered a Python package.
    Module level documentation are sometimes located here.

``models.py``
    contains the data model for the modules (written as SQLAlchemy models). See how (link here)

``config.py``
    contains module-wide configuration with prefix ``MYMODULE_*``. See how to import (link here)

``views.py``
    contains Flask blueprints if the module requires a web-interface. Multiple views? (link here)

``api.py``
    contains the API for other modules to access features of this module.


Additional files:

``signals.py``
    define custom signals here. See signals module.

``receivers.py``
    define your custom signal receivers here. See signals module.

``errors.py``
    contains any custom module-specific exceptions. For example::

        class MyException(Exception): pass

``user_settings.py``
    TODO

``forms.py``
    TODO

``tasks.py``
    TODO

``restful.py``
    TODO


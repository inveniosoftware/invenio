Invenio module layout
=====================

This page summarizes the standard structure and naming conventions of a
module in Invenio v2.0.0. It serves as a reference point when developing
a new module, enhancing an existing one or porting a module from
older versions of Invenio.

The previous pages explained briefly what a module usually consists of, here
we will go deeper into what goes where inside the module.

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


Module naming conventions
-------------------------

Invenio modules are standalone independent components that implement some
functionality used by the rest of the Invenio ecosystem. The modules provide API
to other modules and use API of other modules.

A module is usually called:

1. with plural noun, meaning "database (of things)", for example
   ``invenio-records``, ``invenio-tags``, ``invenio-annotations``,

2. with singular noun, meaning "worker (using things)", for example
   ``invenio-checker``, ``invenio-editor``.

A module may have split its user interface and REST API interface, for example
``invenio-records-ui`` and ``invenio-records-rest``, to clarify dependencies and
offer easy customisation.

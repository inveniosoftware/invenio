.. _developers-introduction:

Introducing Invenio for Developers
==================================

This page summarizes adoption of frameworks in used Invenio. It describes
extensions and module anatomy and concept of pluggable components across
modules.


Extensions
----------

There are many of Flask extensions that can extend the functionality of
your application in various different ways. For instance they add support
for databases, user authentication & authorization, menu & breadcrumbs and
other common tasks.

Many of Flask extensions can be found in the `Flask Extension Registry`_.
All extensions are automatically loaded from ``EXTENSIONS`` configuration
option list. If they should a function ``setup_app(app)`` or function
accepting ``app`` needs to be specified (e.g. ``foo.bar:init``,
``mymodule:setup``).

Continue with :ref:`developers-extensions`.

.. _Flask Extension Registry: http://flask.pocoo.org/extensions/


Modules
-------

Modules are application components that can be use within an application
or across aplications.  They can contains `SQLAlchemy`_ models, `Flask`_
views, `Jinja2`_ templates and other ref:`pluggable-objects`.

Discovery of modules is done based on configuration parameter called
``PACKAGES``, where expansion character `*` is supported at the end of
package path after last dot (e.g. ``foo.bar.something.*``).

Continue with :ref:`developers-modules`.

.. _Flask: http://flask.pocoo.org/
.. _Jinja2: http://jinja.pocoo.org/2/
.. _SQLAlchemy: http://www.sqlalchemy.org/

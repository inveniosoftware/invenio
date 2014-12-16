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

.. _developers-introduction:

Introducing Invenio for Developers
==================================

This page summarizes adoption of frameworks used in Invenio. It describes
the anatomy of extensions and modules and the concept of pluggable
components across modules.

Invenio development adopts the following principles:

- *Convention over Configuration* means that common building blocks
  are provided for you, so use them! If you are not sure or documentation
  of certain feature is missing, contact the developers at the
  `mailing list <http://invenio-software.org/wiki/Community/MailingLists>`_
  or `IRC <http://invenio-software.org/wiki/Community/ChatRooms>`_.


- *Don't Repeat Yourself (DRY)* to help us keep our software maintainable.
  Duplication of code fragments makes application codebase larger and
  more importantly it can become a source of many errors during future
  development (refactoring).

- *Agile Development* where each iteration should lead to working code
  in relatively short time while incremental steps are small and easy to
  understand by other developers. When you start with development take
  advantage of built-in tools provided by Python and underlying libraries::

    # Install package in editable mode
    $ pip install -e git+http://invenio-software.org/repo/invenio.git
    # Follow the instructions in src/invenio/INSTALL file.
    # Edit a file
    $ `$EDITOR` src/invenio/invenio/<module>/<file>.py
    # See that your server has been reloaded automatically.

  When you are done with editing do not forget to run our tests to make
  sure that all other modules are working fine (``python setup.py test``).

Extensions
----------

There are many Flask extensions which extend the functionality of
your application in various ways. For instance they can add support
for databases, user authentication & authorization, menu & breadcrumbs and
other common tasks.

Many Flask extensions can be found in the `Flask Extension Registry`_.
All extensions are automatically loaded from the ``EXTENSIONS`` configuration
option list. If they should a function ``setup_app(app)`` or function
accepting ``app`` needs to be specified (e.g. ``foo.bar:init``,
``mymodule:setup``).

Continue with :ref:`developers-extensions`.

.. _Flask Extension Registry: http://flask.pocoo.org/extensions/


Modules
-------

Modules are application components that can be used within an application
or across applications.  They can contain `SQLAlchemy`_ models, `Flask`_
views, `Jinja2`_ templates and other ref:`pluggable-objects`.

Discovery of modules is done based on a configuration parameter called
``PACKAGES``, where the expansion character `*` is supported at the end of
package path after the last dot (e.g. ``foo.bar.something.*``).

Continue with :ref:`developers-modules`.

.. _Flask: http://flask.pocoo.org/
.. _Jinja2: http://jinja.pocoo.org/2/
.. _SQLAlchemy: http://www.sqlalchemy.org/

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

.. _developers-modules:

Modules
=======

Modules are application components that can be used within an application or
across aplications.  They can contain :ref:`SQLAlchemy <sqlalchemy:overview>`
models, :ref:`Flask view <flask:tutorial>`, :py:class:`Jinja2 templates
<jinja:jinja2.Template>` and other :ref:`pluggable-objects`.

Discovery of modules is done based on the ``PACKAGES`` configuration parameter,
where the `*` wildcard character is supported at the end of the
package path after the last dot (e.g. ``foo.bar.something.*``).


Views
-----

Flask uses a concept of *blueprints* for making application components and
supporting common patterns within an application or across applications.
Blueprints can greatly simplify how large applications work and provide a
central means for Flask extensions to register operations on applications. A
:py:class:`~flask.Blueprint` object works similarly to a
:py:class:`~flask.Flask` application object, but it is not actually an
application.  Rather it is a *blueprint* of how to construct or extend an
application.

Blueprints in Flask are intended for these cases:

* Factor an application into a set of blueprints.  This is ideal for
  larger applications; a project could instantiate an application object,
  initialize several extensions, and register a collection of blueprints.
* Register a blueprint on an application at a URL prefix and/or subdomain.
  Parameters in the URL prefix/subdomain become common view arguments
  (with defaults) across all view functions in the blueprint.
* Register a blueprint multiple times on an application with different URL
  rules.
* Provide template filters, static files, templates, and other utilities
  through blueprints.  A blueprint does not have to implement applications
  or view functions.
* Register a blueprint on an application for any of these cases when
  initializing a Flask extension.

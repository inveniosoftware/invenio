.. _developers-modules:

Modules
=======

Modules are application components that can be use within an application
or across aplications.  They can contains `SQLAlchemy`_ models, `Flask`_
views, `Jinja2`_ templates and other ref:`pluggable-objects`.

Discovery of modules is done based on configuration parameter called
``PACKAGES``, where expansion character `*` is supported at the end of
package path after last dot (e.g. ``foo.bar.something.*``).


Views
-----

Flask uses a concept of *blueprints* for making application components and
supporting common patterns within an application or across applications.
Blueprints can greatly simplify how large applications work and provide a
central means for Flask extensions to register operations on applications.
A :class:`Blueprint` object works similarly to a :class:`Flask`
application object, but it is not actually an application.  Rather it is a
*blueprint* of how to construct or extend an application.

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

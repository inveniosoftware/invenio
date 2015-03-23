============================
 Invenio v2.0.1 is released
============================

Invenio v2.0.1 was released on March 20, 2015.

About
-----

Invenio is a digital library framework enabling you to build your own
digital library or document repository on the web.

New features
------------

+ global:

  - Deprecation policy comes with new deprecation warnings wrappers.
    (#2875)

Bug fixes
---------

+ assets:

  - Avoids bundle changes to persist between requests in DEBUG mode,
    which is not desired.  (#2777)

+ docs:

  - Adds missing `invenio.base` package to the `config.py` file for a
    custom overlay in the docs.

+ global:

  - Replaces `invenio-demo.cern.ch` by `demo.invenio-software.org`
    which is the new canonical URL of the demo site.  (#2867)

+ installation:

  - Reorders 'compile_catalog' and 'install' commands to fix
    installation process from PyPI.

  - Adds apache2 xsendfile package to installation script.  (#2857)

+ messages:

  - Defines a path for jquery.ui required by jQuery-Timepicker-Addon
    and sets an exact version for the plugin instead of latest.
    (#2910)

+ records:

  - Changes creation_date field definition in tests.  (#2214)

+ search:

  - Generates correct url for `/collection` redirect.

Installation
------------

   $ pip install invenio

Documentation
-------------

   http://invenio.readthedocs.org/en/v2.0.1

Homepage
--------

   https://github.com/inveniosoftware/invenio

Happy hacking and thanks for choosing Invenio.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: http://github.com/inveniosoftware
|   URL: http://invenio-software.org

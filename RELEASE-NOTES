============================
 Invenio v2.0.4 is released
============================

Invenio v2.0.4 was released on June 1, 2015.

About
-----

Invenio is a digital library framework enabling you to build your own
digital library or document repository on the web.

New features
------------

+ template:

  - Adds Jinja2 filter 's' to convert anything to 'str'.

Improved features
-----------------

+ BibDocFile:

  - Escapes file name special characters including accents and spaces
    in document URLs.

+ installation:

  - Adds default priviledges for database user to access from any
    host.

Bug fixes
---------

+ arxiv:

  - Adds proper quotation around OAI-PMH query to avoid a query parser
    exception due to colons in the OAI identifiers.

+ global:

  - Catches possible KeyError exceptions when using dotted notation in
    a list to allow for the case when items are missing certain keys.

+ installation:

  - Fixes syntax error in generated Apache virtual host configuration.

+ knowledge:

  - Fixes HTML character encoding in admin templates. (#3118)

+ legacy:

  - Changes the default timestamp to a valid datetime value when
    reindexing via `-R`.

+ WebSearch:

  - Removes special behaviour of the "subject" index that was hard-
    coded based on the index name.  Installations should rather
    specify wanted behaviour by means of configurable tokeniser
    instead.

Installation
------------

   $ pip install invenio

Upgrade
-------

   $ bibsched stop
   $ sudo systemctl stop apache2
   $ pip install --upgrade invenio==2.0.4
   $ inveniomanage upgrader check
   $ inveniomanage upgrader run
   $ sudo systemctl start apache2
   $ bibsched start

Documentation
-------------

   http://invenio.readthedocs.org/en/v2.0.4

Happy hacking and thanks for flying Invenio.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: http://github.com/inveniosoftware
|   URL: http://invenio-software.org

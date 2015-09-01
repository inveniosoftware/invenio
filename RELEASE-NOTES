============================
 Invenio v2.1.1 is released
============================

Invenio v2.1.1 was released on September 1, 2015.

About
-----

Invenio is a digital library framework enabling you to build your own
digital library or document repository on the web.

Security fixes
--------------

+ global

  - Fixes potential XSS issues by changing main flash messages
    template so that they are not displayed as safe HTML by default.

+ search

  - Fixes potential XSS issues by changing search flash messages
    template so that they are not displayed as safe HTML by default.

Incompatible changes
--------------------

+ access

  - Removes configuration option CFG_SUPERADMINROLE_ID.
  - Replaces all zero values with NULL in the table
    accROLE_accACTION_accARGUMENT. The usage of NULL value in
    substitution of zero value was introduced in the commit 7974188
    because Foreign Key does not support it.

Improved features
-----------------

+ I18N

  - Completes Italian translation.
  - Completes French translation.

+ accounts

  - Uses the localized site name when sending email to users. (#3273)

+ docker

  - Improves Docker documentation notably related to how to work with
    Invenio site overlays.

+ global

  - Adds super(SmartDict, self).__init__ call in the __init__ method
    in SmartDict to be able to make multiple inheritance in Record
    class in invenio-records and be able to call both parent's
    __init__.

+ jasmine

  - Allows using variables from application config for building asset
    bundles.

+ legacy

  - Improves exception handling of integrity errors raised by MySQLdb
    library.

Bug fixes
---------

+ OAIHarvest

  - Fixes the parsing of resumptiontoken in incoming OAI-PMH XML which
    could fail when the resumptiontoken was empty.

+ access

  - Sets superadmin role ID included in roles list returned from
    acc_find_possible_roles to the correct, current value. (#3390)
    (#3392)
  - Fixes the authorization delete query to consider NULL value on
    id_accARGUMENT authorization column. The usage of NULL value in
    substitution of zero value was introduced in the commit 7974188
    because Foreign Key does not support it.
  - Fixes property id_accARGUMENT of AccAuthorization model.

+ encoder

  - Corrects the `compose_file` function call in `process_batch_job`
    to produce `<directory>/content.<extension>` instead of
    `<directory>/content.content;<extension>`. (#3354)

+ global

  - Fixes the way configuration variables are parsed from ENV. It now
    uses the same method we are using in `inveniomanage config set`.
    This fixes the problem that `False` is not parsed correctly.

+ i18n

  - Updates PO message catalogues and cleans them of duplicated
    messages.  (#3455)

+ indexer

  - Adds missing `get_nearest_terms_in_idxphrase_with_collection`
    import. Fixes the name of field argument, and returns an empty
    list when no model is passed.  (#3271)

+ installation

  - Fixes database creation and upgrading by limiting Alembic version
    to <0.7.

+ legacy

  - Addresses an issue with calling six urllib.parse in a wrong way,
    making users unable to harvest manually from the command line.

+ login

  - Provides flash message to indicate that an email with password
    recovery could not be sent. (#3309)

+ search

  - Enforces query string to be unicode to overcome pypeg2 parsing
    issues.  (#3296)
  - Fixes admin interface for managing facets.  (#3333)

Notes
-----

+ global

  - Displaying HTML safe flash messages can be done by using one of
    these flash contexts: '(html_safe)', 'info(html_safe)',
    'danger(html_safe)', 'error(html_safe)', 'warning(html_safe)',
    'success(html_safe)' instead of the standard ones (which are the
    same without '(html safe)' at the end).
  - Backports Flask-IIIF extension from original commit
    213b6f1144734c9ecf425a1bc7b78e56ee5e4e3e. The extension is not
    enabled by default in order to avoid feature addition to existing
    minor release.

+ search

  - Displaying HTML safe flash messages can be done by using one of
    these flash contexts: 'search-results-after(html_safe)',
    'websearch-after-search-form(html_safe)' instead of the standard
    ones (which are the same without '(html safe)' at the end).

Installation
------------

   $ pip install invenio==2.1.1

Upgrade
-------

   $ bibsched stop
   $ sudo systemctl stop apache2
   $ pip install --upgrade invenio==2.1.1
   $ inveniomanage upgrader check
   $ inveniomanage upgrader run
   $ sudo systemctl start apache2
   $ bibsched start

Documentation
-------------

   http://invenio.readthedocs.org/en/v2.1.1

Happy hacking and thanks for flying Invenio.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: http://github.com/inveniosoftware
|   URL: http://invenio-software.org

============================
 Invenio v2.0.6 is released
============================

Invenio v2.0.6 was released on September 1, 2015.

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


Improved features
-----------------

+ I18N

  - Completes Italian translation.
  - Completes French translation.

+ global

  - Adds super(SmartDict, self).__init__ call in the __init__ method
    in SmartDict to be able to make multiple inheritance in Record
    class in invenio-records and be able to call both parent's
    __init__.


Bug fixes
---------

+ OAIHarvest

  - Fixes the parsing of resumptiontoken in incoming OAI-PMH XML which
    could fail when the resumptiontoken was empty.

+ i18n

  - Updates PO message catalogues and cleans them of duplicated
    messages.  (#3455)

+ installation

  - Fixes database creation and upgrading by limiting Alembic version
    to <0.7.

+ legacy

  - Addresses an issue with calling six urllib.parse in a wrong way,
    making users unable to harvest manually from the command line.


Notes
-----

+ global

  - Displaying HTML safe flash messages can be done by using one of
    these flash contexts: '(html_safe)', 'info(html_safe)',
    'danger(html_safe)', 'error(html_safe)', 'warning(html_safe)',
    'success(html_safe)' instead of the standard ones (which are the
    same without '(html safe)' at the end).

+ search

  - Displaying HTML safe flash messages can be done by using one of
    these flash contexts: 'search-results-after(html_safe)',
    'websearch-after-search-form(html_safe)' instead of the standard
    ones (which are the same without '(html safe)' at the end).

Installation
------------

   $ pip install invenio==2.0.6

Upgrade
-------

   $ bibsched stop
   $ sudo systemctl stop apache2
   $ pip install --upgrade invenio==2.0.6
   $ inveniomanage upgrader check
   $ inveniomanage upgrader run
   $ sudo systemctl start apache2
   $ bibsched start

Documentation
-------------

   http://invenio.readthedocs.org/en/v2.0.6

Happy hacking and thanks for flying Invenio.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: http://github.com/inveniosoftware
|   URL: http://invenio-software.org

============================
 Invenio v2.0.2 is released
============================

Invenio v2.0.2 was released on April 17, 2015.

About
-----

Invenio is a digital library framework enabling you to build your own
digital library or document repository on the web.

Security fixes
--------------

+ celery:

  - Forces Celery to only accept msgpack content when using standard
    configuration. This disallows pickle messages which can be used
    for remote code execution.  (#3003)

+ global:

  - Disables all attempts to serve directory listings for directories
    found under static root.

Incompatible changes
--------------------

+ celery:

  - If you use any Celery serializer other than msgpack, you must
    update configuration variable CELERY_ACCEPT_CONTENT to include
    that serializer.

+ pidstore:

  - Refactors DataCite provider to use the new external DataCite API
    client.

  - Removes DataCite API client from Invenio.

New features
------------

+ docs:

  - Adds "Code of Conduct" to the "Community" documentation.

  - Adds new fast track deprecation policy.

  - Documents commit message labels used by developers (such as NEW,
    SECURITY, FIX, etc.) used in automatic generation of structured
    release notes.  (#2856)

+ global:

  - Adds a `inveniomanage config locate` command to request the
    location of the instance config file.

  - Adds new configurable variable `INVENIO_APP_CONFIG_ENVS` that can
    be set both from `invenio.cfg` and OS environment. Application
    factory iterates over comma separated list of configuration
    variable names and updates application config with equivalent OS
    environment value.  (#2858)

+ template:

  - Adds 'u' filter that converts str to unicode in Jinja2 templates
    since support for str has been deprecated. Example: `{{ mystr|u
    }}`.  (#2862)

Improved features
-----------------

+ docs:

  - Adds example of how to deprecate a feature and includes
    deprecation policy in documentation.

+ global:

  - Moves datacite API wrapper to external package.

  - Escapes all unicode characters in Jinja2 templates.

+ installation:

  - Apache virtual environments are now created with appropriate
    `WSGIDaemonProcess` user value, taken from the configuration
    variable `CFG_BIBSCHED_PROCESS_USER`, provided it is set.  This
    change makes it easier to run Invenio under non-Apache user
    identity.

  - Apache virtual environments are now created with appropriate
    `WSGIPythonHome` directive so that it would be easier to run
    Invenio from within Python virtual environments.

+ jsonalchemy:

  - Introduces support for accepting MARC fields having any
    indicator. (#1722 #2075)

Bug fixes
---------

+ admin:

  - Adds `admin.js` bundle that loads `select2.js` library on `/admin`
    pages.  (#2690 #2781)

+ assets:

  - Implements `__deepcopy__` method for `webassets.filter.option` in
    order to fix unexpected behavior of the `option` class contructor.
    (#2777 #2864 #2921)

+ documents:

  - Flask-Login import in field definition.  (#2905)

  - Safer upgrade recipe for migrations from the old document storage
    model (used in v1.1) to the new document storage model (used in
    v1.2).

+ global:

  - Drops support for serving directories in Apache site configuration
    to avoid problems with loading '/admin' url without trailing slash
    that attempts to serve the static directory of the same
    name. (#2470 #2943)

+ installation:

  - Adds Babel as setup requirements for installing compile_catalog
    command.

+ jsonalchemy:

  - Fixes the definition of time_and_place_of_event_note,
    series_statement and source_of_description fields.

+ oairepository:

  - Switches keys in CFG_OAI_METADATA_FORMATS configuration mapping.
    (#2962)

  - Amends bfe_oai_marcxml element since get_preformatted_record does
    not return a tuple anymore.

+ search:

  - Fixes portalbox text overflow and and syntax error in CSS.
    (#3023)

  - Collection names containing slashes are now supported again.
    However we recommend not to use slashes in collection names; if
    slashes were wanted for aesthetic reasons, they can be added in
    visible collection translations.  (#2902)

+ sorter:

  - Comparison function of record tags uses space concatened string
    from list of all tags values.  (#2750)

Notes
-----

+ assets:

  - Adds deprecation warning when LESS_RUN_IN_DEBUG is used.  (#2923)

+ global:

  - Deprecates use of invenio.utils.datacite:DataCite (to be removed
    in Invenio 2.2).

  - External authentication methods are being deprecated. Please use
    `invenio.modules.oauthclient` or Flask-SSO instead.  (#1083)

  - Recreate Apache site configurations using new template.  Run
    following command: `inveniomanage apache create-config`.

  - Deprecates custom remote debuggers. Please use native Werkzeug
    debugger or other (*)pdb equivalents.  (#2945)

  - Adds deprecation warning for `invenio.ext.jinja2hacks` and all
    detected non-ascii strings usage in templates mainly coming from
    legacy (1.x) modules.  (#2862)

+ installation:

  - Limits version of SQLAlchemy<=1.0 and SQLAlchemy-Utils<=0.30.

+ oairepository:

  - Changes current behavior of OAI-PMH server for logged in users to
    take into account all records a user can view and not only public
    records.

Installation
------------

   $ pip install invenio

Documentation
-------------

   http://invenio.readthedocs.org/en/v2.0.2

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

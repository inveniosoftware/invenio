============================
 Invenio v2.1.0 is released
============================

Invenio v2.1.0 was released on June 16, 2015.

About
-----

Invenio is a digital library framework enabling you to build your own
digital library or document repository on the web.

Security fixes
--------------

+ docker:

  - Disables debug mode when using standard Docker image. Uses docker
    compose to set the variable instead.

Incompatible changes
--------------------

+ access:

  - Removes proprietary authentication protocol for robotlogin.
    (#2972)

  - Removes external authentication engines. Please use
    `invenio.modules.oauthclient` or Flask-SSO instead.  (#1083)

+ assets:

  - Removes support for runtime compiling of less files in debug mode
    when option LESS_RUN_IN_DEBUG is enabled. (#2923)

  - Requires update of bootstrap version of overlays.

+ collections:

  - Collection reclist is not populated anymore. Use collection phrase
    index using query matcher based on record data, hence no second
    order operator will work in collection query definition.

+ communities:

  - Removes 'communities' module that has been externalised to
    separate Python package called 'invenio_communities'.  Migration
    can be done by running `pip install invenio_communities` and
    adding 'invenio_communites' to PACKAGES.  (#3008)

+ formatter:

  - Database table 'format' and 'formatname' have been dropped and
    foreign keys in other tables has been changed to use lower case
    version of output format base filename without extension name.

  - Output formats are no longer modifiable from web interface as they
    syntax has been changed from custom "bfo" to "yml". (#2662)

  - Custom output formats from the database needs to by merged with
    `bfo` files to new `yml` files. Please follow instructions when
    running `python scripts/output_format_migration_kit.py`.

+ global:

  - Removes old URL handlers for `/search` and `/record`.  (#2958)

  - Enables 'sql_mode' as 'ansi_quotes' for quotes compatibility for
    MySQL.

  - Drops all active sessions during upgrade. Might result in log
    entries about non-restorable sessions.

  - Drops all active sessions during upgrade. Might result in log
    entries about non-restorable sessions.

  - Moves `deprecated` decorator under `invenio/utils/deprecation.py`

  - Changes url_for behaviour to return always a unicode string.
    (#2967)

  - Deprecates invenio.config hack for legacy code. (#3106)

  - Deprecates use of invenio.utils.redis in favor of
    invenio.ext.cache. (#2885)

  - Removes support for custom remote debuggers. (#2945)

+ installation:

  - Upgrades minimum SQLAlchemy version to resolve Enum life cycle
    problems on PostgreSQL. (#2351)

+ legacy:

  - Specifies deprecation warnings for all remaining legacy modules
    according to the latest Invenio 3 road map.

  - Specifies deprecation warnings for legacy modules bibcirculation,
    bibdocfile, bibedit, elmsubmit, websearch_external_collections,
    and websubmit.

  - Enables 'sql_mode' as 'ansi_quotes' for quotes compatibility for
    MySQL.

  - Removes deprecated bibknowledge module.

  - Removes deprecated `inveniocfg` command line interface.

+ multimedia:

  - Depreactes multimedia module.

+ search:

  - Removes support for legacy `perform_request_search` and
    `search_unit` API functions.

  - Removes support for specific Aleph idendifiers from search engine.

New features
------------

+ access:

  - Adds 'usedeposit' action which enables per user access
    restrictions for different deposit types.  (#2724)

  - Adds the ability to restrict access per object independently from
    the parent.

+ accounts:

  - Adds support for allowing users to update their profile (nickname,
    email, family name and given name).

  - Adds support for users to re-request an verification email to be
    sent.

  - Adds new Passlib Flask extension to support configurable password
    contexts in Invenio. (#2874)

  - Adds panel blocks to settings templates.

+ babel:

  - Adds datetime localization template filters.

+ collections:

  - Adds new calculated field '_collections' to records from which the
    'collection' index is created.  (#2638)

+ deposit:

  - Adds generic JinjaField and JinjaWidget to render templates as
    form fields. This might be used in case longer explainations are
    required for forms or to add pictures and other material that may
    increase usability.

+ global:

  - Uses Flask-IIIF extension providing various image manipulation
    capabilities.

  - Adds possibility to refer to documents and legacy BibDocFiles via
    special path such as `/api/multimedia/image/recid:{recid}` or
    `/api/multimedia/image/recid:{recid}-{filename}` or
    `/api/multimedia/image/uuid` with proper permission checking.
    (#3080) (#3084)

  - Adds general pagination macro for Flask-SQLAlchemy Pagination
    object.  (PR #3006)

  - Adds 'noscript' block to the page template to warn users with
    disabled JavaScript on their browser.  (#1039)

+ knowledge:

  - Adds manager to knowledge with a command to load mappings into an
    existing knowledge base from a file. E.g. `inveniomanage knowledge
    load kb_name /path/to/file.kb`

+ oauthclient:

  - Adds support for CERN OAuth authentication.

+ records:

  - Adds support for granting author/viewer rights to records via tags
    by specifying CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_USERIDS_IN_TAGS
    and/or CFG_ACC_GRANT_VIEWER_RIGHTS_TO_USERIDS_IN_TAGS. (#2873)

+ script:

  - Implements optional TLS encryption directly by Werkzeug. Adds many
    configuration variables (`SERVER_TLS_*`) to control the behaviour.

  - Adds support for PostgreSQL database initialization.

+ search:

  - Implements a mechanism that enhances user queries.  The enhancer
    functions are specified in the 'SEARCH_QUERY_ENHANCERS' and later
    they are applied to the query AST one after the other in the
    search method.  (#2987)

  - Adds new API for querying records.

  - Adds new configuration option SEARCH_WALKERS which specifies
    visitor classes that should be applied to a search query.

  - Adds additional search units for the auxiliary author fields
    `firstauthor`, `exactauthor`, `exactfirstauthor` and
    `authorityauthor`.

  - Adds missing operator handling of greater than (>) queries.

  - Adds new configuration varibles `SEARCH_QUERY_PARSER` and
    `SEARCH_QUERY_WALKERS` for query parser.

  - Adds new API for record matching againts given query.

+ template:

  - Adds bootstrap scrollspy to the base template so it can be used by
    all modules.

+ workflows:

  - Adds new buttons to the Holding Pen details pages to delete and
    restart current task.

Improved features
-----------------

+ accounts:

  - Improves legend alignment in login form.

+ classifier:

  - Improves the stripping of reference section when extracting text
    from PDF by using a more appropriate refextract API.

+ deposit:

  - Corrects reflow on narrow screens and removes misused classes for
    labels.

  - Adds sticky navigation item to the deposit page to simplify
    overview on larger forms. Works well with collapsed elements. On
    narrow screens the navigation gets pushed in front of all other
    form elements.

  - Improves handling of large files in deposit.

  - Fixes problem with misaligned checkbox and radio list items. They
    are produced because wtforms does not wrap input elements into
    labels as it is intended by the bootstrap framework.

+ docker:

  - Changes port number exposed by docker to non-reserved ones to
    avoid conflicts with local installations. Webport is now 28080,
    Redis 26379 and MySQL is 23306, which is a simple +20000 shift
    from the standard ports.

  - Integrates docker boot script into docker image.

  - Changes docker boot script to use `exec`. This ensure signal
    forwarding and reduces the overhead by one process. As a result
    container shutdown is faster now.

  - Changes manual master/slave configuration of Docker devboot script
    to automatic solution using file locks.

+ formatter:

  - Improves support for translated output format names on search
    results page.  (#2429)

+ global:

  - Supports database creation on PostgreSQL server.

  - Implements session signing. This avoids cache request for invalid
    sessions and reduces the DDoS attack surface.

  - Removes IP address storage+checks. This avoids data privacy issues
    and enables users with multiple connections (e.g. WIFI+LTE,
    multiple WIFI connections on trains+stations) to stay signed in.

  - Enhances `run_py_func` to be able to print both to some StringIO
    and to the terminal at the same time. This is enabled with the
    `passthrough` argument. It now also always returns stderr,
    deprecating the `capture_stderr` argument. The return value is now
    a namedtuple so that one can easily fetch the required value. Its
    arguments to a more natural order (name of the executable first
    and arguments afterwards.

  - Supports database creation on PostgreSQL server.

  - Improves compatibility of Text fields in PostrgeSQL by changing
    Text in models and removes Invenio hacks on MySQL Index and
    Primary Key creation because starting from SQLAlchemy>=1.0 it
    arises an exception if the length is specified. (#3037)

+ knowledge:

  - Relaxes constraints on dynamic search function that used to force
    us to create temporary knowledge base. (#698)

+ legacy:

  - Supports database creation on PostgreSQL server.

+ oauthclient:

  - Extra template block addition.

+ refextract:

  - Replaces usage of 'urllib' by 'requests' library and improves
    manipulation with temporary file used for extraction of
    references.

+ script:

  - Uses SQLAlchemy and SQLAlchemy-Utils to initialize the database
    instead of executing mysql in a python subshell. (#2846) (#2844)

+ search:

  - The search results pages emits proper Cache and TTL information in
    its HTTP headers, so that any eventual external cachers (such as
    varnish) could act accordingly to invalidate their caches
    automatically, without any configuration.  (#2302)

  - Collection filtering of search results no longer returns orphan
    records.

  - Improves native facet creations.

+ template:

  - Replaces Invenio PNG logo with SVG version. This works better on
    high resolution (retina) screens and it is supported by all
    browers.

+ unapi:

  - Separates UnAPI url handling to a new module.

+ upgrader:

  - Clarifies that the upgrade dependency is only a best guess.
    (#2561)

+ workflows:

  - Updates the layout of the details pages in Holding Pen to display
    at which step the object is in the workflow.

  - When rendering the task results, the Holding Pen now passes a
    dictionary instead of a list in order to allow finer grained
    control in the template.

Bug fixes
---------

+ access:

  - Sets the superadmin role ID properly when elaborating access
    authorizations. Previously it was masked behind an application
    context exception. (#3184)

+ accounts:

  - Fixes invalid HTML of the 'remember me' login form checkbox.

  - Corrects conditions on when to sent a notification email.
    (addresses zenodo/zenodo#275) (#3163)

  - Fixes issue that allowed blocked accounts to login.

+ classifier:

  - Properly handles file paths containing a colon (:), avoiding bad
    text extraction that causes (1) wrong results and (2) much slower
    execution.

  - Properly tags the execution of classifier as fast in the standard
    workflow task when applicable.

+ deposit:

  - Fixes issue with PLUpload chunking not being enabled.

  - Fixes "both collapse arrows are shown" bug in deposit frontend.

+ formatter:

  - Changes the mimetype of the `id` output format to application/json
    and properly returns a JSON formatted list of results.

+ indexer:

  - Avoids an exception from happening when passing a unicode string
    to the BibIndex engine washer. (#2981)

+ installation:

  - Fixes capitalization of package names.

+ legacy:

  - Fixes inveniogc crash when mysql is NOT used to store sessions.
    (#3205)

  - Catches also any `MySQLdb.OperationalError` coming from legacy
    MySQL queries using `run_sql()`. (#3089)

  - Fixes an issue with outputting the post-process arguments when
    adding or editing an OAI source.

+ oauthclient:

  - Marks email address of users creating their account with oauth
    process as invalid.

  - Sends a validation email when users create their account with
    oauth. (#2739)

  - Improves security by leaving users' password uninitialized when
    their account is created by the oauth module.

+ records:

  - Improves type consistency of keys and values in JSON record
    created from MARC and retrieved from storage engine.  (#2772)

  - Fixes double message flashing issues during 401 errors.

  - Fixes issue with empty records not returning an 404 error.

  - Fixes 500 error when record does not exist. (#2891)

+ search:

  - Fixes an issue of returning the wrong results when searching for
    single values in the author field (e.g. 'author:ellis').

+ submit:

  - Fixes upgrade recipe for SbmCOLLECTION_SbmCOLLECTION table
    introduced in commit @1021055. (#2954)

+ workflows:

  - Fixes an issue where the workflow engine would try to save a
    function reference in the extra_data task history, causing an
    error when serializing extra_data.

Notes
-----

+ access:

  - The default access role ID for the superadmin user is 1, but it
    can be configured via CFG_SUPERADMINROLE_ID.

  - Requires running `webaccessadmin -u admin -c -a -D` command.

+ accounts:

  - Changes user model fields family name/given names to store empty
    string as default instead of null.

  - Adds support for users to change email address/nickname. If you
    store email addresses in e.g. records or fireroles you are
    responsible for propagating the users change of email address by
    adding listeners to the 'profile-updated' signal. Alternatively
    you can migrate records (using
    CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_USERIDS_IN_TAGS and
    CFG_ACC_GRANT_VIEWER_RIGHTS_TO_USERIDS_IN_TAGS) and fireroles
    (using "allow/deny uid <uid>") to restrict access based on user id
    instead of user email address.

  - Refactors password hashing to (a) explicitly specify password salt
    instead of relying on the email address, since a change of email
    would cause the password to be invalidated (b) support multiple
    password hashing algorithms concurrently (c) automatic migration
    of deprecated hashes when users log in (d) allows overlays to
    specify their preferred hashing algorithms.

  - Deprecates legacy Invenio's hashing algorithm based on AES
    encryption of email address using the password as secret key in
    favor of SHA512 using random salt and 100000 rounds.

+ assets:

  - Updates Twitter Bootstrap to 3.3 to fix some issues, e.g. to low
    colour contrast of navbar background<->font.  Requires update of
    Twitter Bootstrap version in Invenio overlays.

+ collections:

  - The tag table now contains 'collection idetifier' with correct
    'value' and 'recjson_value' ('' and '_collections').

+ formatter:

  - Invenio 1.x BFT template language and BFE elements are being
    deprecated. Please migrate overlay output formats to use Jinja2.
    (#2662)

  - Removes fallback template rendering and puts standard exception
    logging in place.  (#2958)

+ global:

  - Removes unused legacy cascade style sheets.  (#2040)

+ indexer:

  - The lower_index_term() now returns the term as a Unicode string
    which can have an impact on custom tokenizers and regular
    indexing.

+ installation:

  - Adds missing access rights for database user accessing server from
    localhost.  (#3146)

+ records:

  - Ports basic BibDocFile serving including access right checks.
    (#3160)

+ unapi:

  - Add `invenio.modules.unapi` to PACKAGES if you would like to keep
    the `/unapi` url.

Installation
------------

   $ pip install invenio

Upgrade
-------

   $ bibsched stop
   $ sudo systemctl stop apache2
   $ pip install --upgrade invenio==2.1.0
   $ inveniomanage upgrader check
   $ inveniomanage upgrader run
   $ sudo systemctl start apache2
   $ bibsched start

Documentation
-------------

   http://invenio.readthedocs.org/en/v2.1.0

Happy hacking and thanks for flying Invenio.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: http://github.com/inveniosoftware
|   URL: http://invenio-software.org

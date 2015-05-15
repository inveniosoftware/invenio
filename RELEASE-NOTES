============================
 Invenio v2.0.3 is released
============================

Invenio v2.0.3 was released on May 15, 2015.

About
-----

Invenio is a digital library framework enabling you to build your own
digital library or document repository on the web.

Security fixes
--------------

+ script:

  - Switches from insecure standard random number generator to secure
    OS-driven entropy source (/dev/urandom on linux) for secret key
    generation.

New features
------------

+ formatter:

  - Adds html_class and link_label attributes to bfe_edit_record.
    (#3020)

+ script:

  - Adds `SERVER_BIND_ADDRESS` and `SERVER_BIND_PORT` to overwrite
    bind address and port independently from the public URL. This
    gives control over the used network interface as well as the
    ability to bind Invenio to a protected port and use a reverse
    proxy for access. Priority of the config is (1) runserver command
    arguments, (2) `SERVER_BIND_ADDRESS` and `SERVER_BIND_PORT`
    configuration, (3) data from `CFG_SITE_URL`, (4) defaults
    (`127.0.0.1:80`).

Improved features
-----------------

+ docker:

  - Slims down docker image by building on top of less bloated base
    image and only install what is really required. Also purges
    unneeded packages, flushes caches and clean temporary files. All
    these parts should not be in a production image and are also not
    required by developers. You can still install components when
    extending the Invenio base image.

+ docs:

  - Adds missing 'libffi' library and howto start redis server.
    Causing an exception when running `pip install --process-
    dependency-links -e .[development]`: 'ffi.h' file not found and
    'sudo: service: command not found' when starting redis server (OS
    X Yosemite, 10.10).

  - Adds a step describing how to install MySQL on CentOS 7 because it
    does not have 'mysql-server' package by default.

Bug fixes
---------

+ email:

  - Fixes 'send_email' to expect an 'EmailMessage' object from the
    'forge_email' method rather than a string-like object. (#3076)

  - Fixes reference to CFG_SITE_ADMIN_EMAIL (not a global).

+ legacy:

  - Makes lazy loading of `stopwords_kb` variable to avoid file
    parsing during script loading. (#1462)

+ logging:

  - Fixes Sentry proxy definition pointing to a wrong application
    attribute.

+ matcher:

  - Fixes Unicode conversion required to use the levenshtein_distance
    function. (#3047)

Installation
------------

   $ pip install invenio

Documentation
-------------

   http://invenio.readthedocs.org/en/v2.0.3

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

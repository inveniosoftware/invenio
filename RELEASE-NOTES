============================
 Invenio v2.0.5 is released
============================

Invenio v2.0.5 was released on July 17, 2015.

About
-----

Invenio is a digital library framework enabling you to build your own
digital library or document repository on the web.

Security fixes
--------------

+ docker:

  - Disables debug mode when using standard Docker image. Uses docker
    compose to set the variable instead.

Improved features
-----------------

+ deposit:

  - Improves handling of large files in deposit.

+ docker:

  - Improves Docker documentation notably related to how to work with
    Invenio site overlays.

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

+ jasmine:

  - Allows using variables from application config for building asset
    bundles.

Bug fixes
---------

+ deposit:

  - Fixes issue with PLUpload chunking not being enabled.

+ encoder:

  - Corrects the `compose_file` function call in `process_batch_job`
    to produce `<directory>/content.<extension>` instead of
    `<directory>/content.content;<extension>`. (#3354)

+ global:

  - Fixes the way configuration variables are parsed from ENV. It now
    uses the same method we are using in `inveniomanage config set`.
    This fixes the problem that `False` is not parsed correctly.

+ installation:

  - Fixes capitalization of package names.

+ legacy:

  - Fixes inveniogc crash when mysql is NOT used to store sessions.
    (#3205)

+ login:

  - Provides flash message to indicate that an email with password
    recovery could not be sent. (#3309)

Notes
-----

+ global:

  - Backports Flask-IIIF extension from original commit
    213b6f1144734c9ecf425a1bc7b78e56ee5e4e3e. The extension is not
    enabled by default in order to avoid feature addition to existing
    minor release.

Installation
------------

   $ pip install invenio==2.0.5

Upgrade
-------

   $ bibsched stop
   $ sudo systemctl stop apache2
   $ pip install --upgrade invenio==2.0.5
   $ inveniomanage upgrader check
   $ inveniomanage upgrader run
   $ sudo systemctl start apache2
   $ bibsched start

Documentation
-------------

   http://invenio.readthedocs.org/en/v2.0.5

Happy hacking and thanks for flying Invenio.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: http://github.com/inveniosoftware
|   URL: http://invenio-software.org

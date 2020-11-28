Base bundle
-----------
The base bundle contains all modules related to the generic web application.
This includes the Flask/Celery application factories, configuration management,
I18N, logging, database management, assets/theme management, mail handling and
administration interface.

Included modules:

- `invenio-admin <https://invenio-admin.readthedocs.io>`_
    - Administration interface for Invenio based on Flask-Admin.
- `invenio-app <https://invenio-app.readthedocs.io>`_
    - Flask, WSGI, Celery and CLI applications for Invenio including
      security-related headers and rate limiting.
- `invenio-assets <https://invenio-assets.readthedocs.io>`_
    - Static files management and Webpack integration for Invenio.
- `invenio-base <https://invenio-base.readthedocs.io>`_
    - Flask application factories implementing the application loading patterns
      with entry points in Invenio.
- `invenio-cache <https://invenio-cache.readthedocs.io>`_
    - Caching module for Invenio, supporting Redis and Memcached as backends.
- `invenio-celery <https://invenio-celery.readthedocs.io>`_
    - Task discovery and default configuration of Celery for Invenio.
- `invenio-config <https://invenio-config.readthedocs.io>`_
    - Configuration loading pattern responsible for loading configuration from
      Python modules, instance folder and environment variables.
- `invenio-db <https://invenio-db.readthedocs.io>`_
    - Database connection management for Invenio.
- `invenio-formatter <https://invenio-formatter.readthedocs.io>`_
    - Jinja template engine utilities for Invenio.
- `invenio-i18n <https://invenio-i18n.readthedocs.io>`_
    - I18N utilities like user locale detection, message catalog merging and
      views for language change.
- `invenio-logging <https://invenio-logging.readthedocs.io>`_
    - Configuration of logging to both console, files and log aggregation
      engines like `sentry.io <https://sentry.io/>`_
- `invenio-mail <https://invenio-mail.readthedocs.io>`_
    - Mail sending for Invenio using Flask-Mail.
- `invenio-rest <https://invenio-rest.readthedocs.io>`_
    - REST API utilities including Cross Origin Resource Sharing (CORS) and
      Content Negotiation versioning support.
- `invenio-theme <https://invenio-theme.readthedocs.io>`_
    - Jinja templates implementing a basic theme for Invenio as well as menus
      and breadcrumbs support.
- `docker-invenio <https://docker-invenio.readthedocs.io>`_
    - Docker base images based on CentOS 7 for Invenio.
- `pytest-invenio <https://pytest-invenio.readthedocs.io>`_
    - Testing utilities for Invenio modules and applications.

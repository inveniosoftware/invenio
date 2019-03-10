..
    This file is part of Invenio.
    Copyright (C) 2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _build-repository:

Build a repository
==================

Now that you have generated the skeleton of your repository via cookiecutter,
bootstrapped your instance, run it and created a record, let's have a deep dive
at the various files and folders that were generated and what they do.

The generated skeleton is our default recommendation, however you are
completely free to adapt it as your see fit.

Management scripts
------------------

.. code-block:: shell

    ...
    ├── scripts
    │   ├── bootstrap
    │   ├── console
    │   ├── server
    │   ├── setup
    │   └── update
    ...

In your root folder, you will find the ``scripts`` directory which contains
executable bash scripts that will assist you with developing and managing your
Invenio instance:

**scripts/bootstrap**

  Installs all of the Python dependencies, your application's code, and
  collects and builds the static files required for the instance to run. We'll
  talk more about how we manage `dependencies`_ in the relevant section below.

**scripts/setup**

  (Re)initializes data needed for services that hold application state, i.e.:

  - Database tables
  - Elasticsearch indices and templates
  - RabbitMQ queues
  - Redis databases

  This script is also useful when you're doing local development and want to
  start from a clean state.

  .. warning::

      This scripts performs destructive and non-reversible operations. Only run
      this when you initialize your instance the first time. Running this in
      e.g. a production or testing environment will remove all existing data.

**scripts/server**

  Fires up a development HTTPS-enabled flask web server at https://localhost
  for your application and a Celery worker. As you make HTTP requests to the
  web application or run any tasks you will see information, warnings and
  errors being logged in the terminal. Interrupting this script will
  automatically stop both services.

**scripts/console**

  This will spawn an interactive IPython shell with your application fully
  loaded. You can use it to run arbitrary Python commands while having access
  to your application's database models for queries. This is a great tool for
  testing functionality during development, troubleshooting and fixing problems
  on a live instance

**scripts/update**

  This will repeat all of the steps of the ``bootstrap`` script, but will also
  additionally apply any new Alembic recipes for the database and Elasticsearch
  index changes.

.. _dependencies:

Python dependencies and packaging
---------------------------------

.. code-block:: shell

    ...
    ├── Pipfile
    ├── Pipfile.lock
    ├── setup.py
    ├── MANIFEST.in
    ...

To manage our Python dependencies we have chosen to use `pipenv
<https://pipenv.readthedocs.io>`_. Pipenv does the following:

- Tracks your *loose* Python dependencies inside ``Pipfile``.
- Pins specific versions (and hashes) of your Python depedendencies inside
  ``Pipfile.lock``. The existence of this file is essential to make sure that
  when you deploy your instance on a production environment, you can reproduce
  the exact same environment that you used when you developed and tested your
  application.
- Automatically creates a Python virtualenv with the correct Python version
  under the path defined in the ``WORKON_HOME`` environment variable (commonly
  used by ``virtualenvwrapper``). If not set, new virtualenvs will be placed
  under ``$HOME/.local/share/virtualenvs/``.

We still need a ``setup.py`` file though, not for tracking any dependencies,
but for specifiyng the entrypoints that various Invenio packages rely on to
automatically detect and register Flask blueprints, Celery tasks and other
features.

Docker and Docker-Compose
-------------------------

.. code-block:: shell

    ...
    ├── docker
    │   ├── postgres
    │   │   ├── ...
    │   ├── uwsgi
    │   │   ├── ...
    │   ├── nginx
    │   │   ├── ...
    │   ├── haproxy
    │   │   ├── ...
    ├── docker-services.yml
    ├── docker-compose.yml
    ├── docker-compose.full.yml
    ├── Dockerfile.base
    ├── Dockerfile
    ...

The instance requires some services in order to run, like a database,
Elasticsearch, Redis and RabbitMQ. To provide a cross-platform and convenient
way of running these services, we are using Docker and Docker Compose, by
configuring the following files:

**docker-services.yml**

  This file contains basic definitions for the Docker containers for the
  services the instance uses. Configuration options such as the database
  credentials, exposed ports, and other service-specific options can be
  modified in here. This file's containers are used as a common base and are
  extended by other ``docker-compose.*.yml`` files to build up a specific
  configuration for an infrastructure.

**docker-compose.yml**

  This file contains and exposes locally the minimal set of service containers
  needed for developing the instance locally:

  - ``db``: The database, PostgreSQL or MySQL, exposing the 5432 or 3306 ports.
  - ``es``: Elasticsearch version 5 or 6, exposing the 9200 and 9300 ports.
  - ``mq``: RabbitMQ, exposing port 5672 for the service and port 15672 for a
    management web server (accessible via the default username/password
    ``guest:guest``).
  - ``cache``: Redis exposing port 6379.

  When developing and running your instance locally these services can be
  accessed by your application.

**docker-compose.full.yml**

  This file contains a full-fledged definition of a production-like application
  infrastructure. It has all of the ``docker-compose.yml`` file's containers
  defined, and additionally:

  - ``lb``: HAProxy, publicly exposing ports 80 and 443 for accessing the web
    application and 8080 for accessing statistics.
  - ``frontend``: Nginx, exposing ports 80 and 443 and acting as a reverse
    proxy for your application containers and serving static files.
  - ``web-ui``/``web-api``: Two separate web application containers running
    uWSGI for the Invenio UI and REST API applications and exposing port 5000
  - ``worker``: The Celery worker of your application.
  - ``flower``: Monitoring web application for Celery, publicly exposing port
    5555.
  - ``kibana``: Monitoring web application for Elasticsearch, publicly exposing
    port 5601.

  The ``web-ui``, ``web-api`` and ``worker`` containers are using Docker images
  that are built from the ``Dockerfile.base`` and ``Dockerfile`` files
  described below.

  .. warning::

      While one might be tempted to deploy this as a fully functional Invenio
      instance, it is not meant to be a turn-key solution, since it hasn't been
      tested for this purpose. This is rather meant to be an inspiration (in
      terms of configuration, networking and general principles) for
      configuring your own setup either by replacing the container services
      with actual nodes/machines or configuring a production-level container
      orchestration system like Kubernetes, OpenShift, etc.

**Dockerfile.base**

  This Dockerfile helps you build a Python dependencies-only base image from
  where your application can be built quickly.

**Dockerfile**

  This Dockerfile builds a fully functional image of your application with all
  of the static assets it requires.

**docker/postgres**

  Contains a Dockerfile and script that will setup the necessary users/roles
  for the database.

**docker/uwsgi**

  Contains a the ``uwsgi_ui.ini`` and ``uwsgi_api.ini`` uWSGI configruation
  files used for running the Invenio UI and REST API web applications.

**docker/nginx**

  Contains a Dockerfile, nginx configurations (``nginx.conf`` and
  ``conf.d/default.conf``) and a self-signed generated SSL certificate
  (``test.crt`` and ``test.key``). You can look into these files if you are
  interested in how to confiugre nginx to proxy requests to one or multiple
  uWSGI web application.

**docker/haproxy**

  Contains a Dockerfile, HAProxy configuration (``haproxy.cfg``) and a
  self-signed generated SSL certificate (``haproxy_cert.pem``).

Configuration
-------------

.. code-block:: shell

    ...
    ├── my_site
    │   ├── config.py
    ...

**my_site/config.py**

  The instance's basic configuration variables are defined inside this file.
  You should go through all of these variables to understand what kind of
  things can be customized for your instance, like e.g. what should be the
  "From" email address for your automatically sent emails.

The configuration used by the Invenio applications is dynamically loaded from
multiple sources. You can read more about this in `Invenio-Config documentation
<https://invenio-config.readthedocs.io>`_. Probably the most important part of
this, is the order in which the various configuration sources are loaded, which
allows you to effectively override any config variable. The following list
describes this order (every item overrides the one above it):

- Configuation modules defined in ``invenio_config.module`` entrypoints.
  ``my_site.config`` is actually one of them. You can add as many as you want
  and they will be applied in alphabetical order of the entrypoint name.
- Configuration in the ``<app.instance_path>/invenio.cfg``. For local
  development this is usually ``${VIRUAL_ENV}/var/instance/invenio.cfg``.
- ``INVENIO_XYZ`` environment variables. If for example you want to override
  the ``SECRET_KEY``, you would have to do ``export
  INVENIO_SECRET_KEY="my-secret"``.

Tests
-----

.. code-block:: shell

    ...
    ├── tests
    │   ├── api
    │   │   ├── conftest.py
    │   │   └── test_api_simple_flow.py
    │   ├── e2e
    │   │   ├── conftest.py
    │   │   └── test_front_page.py
    │   ├── ui
    │   │   └── conftest.py
    │   ├── conftest.py
    │   └── test_version.py
    ├── pytest.ini
    ├── run-tests.sh
    ...

In Invenio we're using the Python `pytest <https://pytest.org/>`_ library for
testing. All of the instance's tests are placed in the ``tests/`` directory.

**tests/ui/**

  Includes tests that use the UI application views.

**tests/api/**

  Includes tests that use the REST API application views.

**tests/e2e/**

  Includes Selenium-based end-to-end tests which access both the UI and REST
  API applications.

**pytest.ini**

  Used to configure ``pytest`` and its various plugins.

**run-tests.sh**

  You can run this script locally or in your CI/CD pipeline and it will check:

  - Your Python dependencies for security vulnerabilities using
    `pyup.io's "safety" library <https://github.com/pyupio/safety>`_.
  - Your docs styling based on `PEP 257
    <https://www.python.org/dev/peps/pep-0257/>`_.
  - Your Python import for the correct sorting order using `isort
    <https://readthedocs.org/projects/isort/>`_.
  - Your ``MANIFEST.in`` for any missing entries.
  - Your docs are building without errors.
  - That your tests are passing.

Documentation
-------------

.. code-block:: shell

    ...
    ├── docs
    │   ├── api.rst
    │   ├── authors.rst
    │   ├── changes.rst
    │   ├── configuration.rst
    │   ├── conf.py
    │   ├── contributing.rst
    │   ├── index.rst
    │   ├── installation.rst
    │   ├── license.rst
    │   ├── make.bat
    │   ├── Makefile
    │   ├── requirements.txt
    │   └── usage.rst
    ├── AUTHORS.rst
    ├── CHANGES.rst
    ├── CONTRIBUTING.rst
    ├── INSTALL.rst
    ├── README.rst
    ...

To build the instance's documentation we're using `Sphinx docs
<https://www.sphinx-doc.org>`_ and `reStructuredText
<http://docutils.sourceforge.net/rst.html>`_ as a markup language.

**docs/*.rst**

  The various ``.rst`` files are placed in the root of your repository and in
  the ``docs/`` directory, and will be used to build your instance's
  documentation, via running ``pipenv run build_sphinx``.

**docs/conf.py**

  This is the place where various documentation configuration variables can be
  set. You can have a look at it and tweak things based `Sphinx docs' extensive
  section on its configuration
  <http://www.sphinx-doc.org/en/master/usage/configuration.html>`

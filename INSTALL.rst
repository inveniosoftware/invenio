..
    This file is part of Invenio.
    Copyright (C) 2015-2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Installation
============

Please see our quick start guide on
https://invenio.readthedocs.io/en/latest/quickstart/index.html

1. Scaffold
-----------

.. code-block:: console

    # prerequisites: cookiecutter and pipenv
    # scaffold my-site instance
    $ cookiecutter gh:inveniosoftware/cookiecutter-invenio-instance \
        --checkout v3.2

2. Install
----------

.. code-block:: console

    $ cd my-site/
    # start services (db, es, mq, cache)
    $ docker-compose up
    # build and install my-site instance
    $ ./scripts/bootstrap

3. Run
------

.. code-block:: console

    # setup database and indexes
    $ ./scripts/setup
    # start webserver and task queue
    $ ./scripts/server
    # your site is running!
    $ firefox https://127.0.0.1:5000/

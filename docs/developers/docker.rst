..  This file is part of Invenio
    Copyright (C) 2015 CERN.

    Invenio is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

.. _developers-docker:

Docker
======

This page describes how to set up Docker containers for development purposes.

Setup
-----

Install Docker_ and `Docker Compose`_. Now run::

    docker-compose -f docker-compose-dev.yml build
    docker-compose -f docker-compose-dev.yml up

This builds and runs the docker containers. You can now connect to `localhost:5000` to see your Invenio installation. The `admin` user does not have any password.

Should you require a fresh installation and therefore wipe all your instance data, run::

    docker-compose -f docker-compose-dev.yml rm -f

Code changes and live reloading
-------------------------------

As long as you do not add new requirements (python and bower) and only change files inside the `invenio` package, it is not required to rebuild the docker images. Code changes are mirrored to the containers. If Flask supports it on your system it will automatically reload the application when changes are detected. This sometimes might lead to timeouts in your browser session. Do not worry about this, but be aware to only save files when you are ready for reloading.

As of this writing changing template files do not lead to application reloading and do not purge caches. As a workaround you can simple alter one of the python files, e.g. by using `touch`.

Building documentation
----------------------

You can also use the Docker container to build the documentation. This can be done either by attaching to running container::

    docker exec -it invenio_web_1 sphinx-build -nW docs docs/_build/html

or, in case you do not want to fire up the entire docker compose setup, by running the sphinx commands in a new container::

    docker run --rm -it -v $(pwd)/docs/_build/html:/code/docs/_build/html invenio_web:latest sphinx-build -nW docs docs/_build/html

Running tests
-------------

You can also run tests using the Docker containers. Wait until the containers finished setup and the webservice is running. Then use::

    docker exec -it invenio_web_1 python setup.py test

.. WARNING::
    Currently the tests do **not** succeed when using this method.

.. _Docker: https://www.docker.com/
.. _Docker Compose: https://docs.docker.com/compose/

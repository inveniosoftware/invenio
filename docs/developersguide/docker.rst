..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _developers-docker:

Docker
======

This page describes how to set up Docker containers for development purposes.

.. image:: /_static/docker-compose-setup.svg

Setup
-----

Install Docker_ and `Docker Compose`_. Now run:

.. code-block:: shell

   docker-compose -f docker-compose-dev.yml build
   docker-compose -f docker-compose-dev.yml up

This builds and runs the docker containers. You can now connect to
`localhost:28080` to see your Invenio installation. The `admin` user does not
have any password.

.. caution::
    This will mirror the current source code directory into the Docker
    container, so make sure to delete all `*.pyc`-files before. They might
    not be compatible with the Python version and libraries of Docker image.

.. note::
    If you are using `boot2docker`_ you need to set up port forwarding by
    running the following command in a new terminal:

    .. code-block:: shell

        boot2docker ssh -vnNT \
            -Llocalhost:29200:localhost:29200 \
            -Llocalhost:28080:localhost:28080 \
            -Llocalhost:26379:localhost:26379 \
            -Llocalhost:25673:localhost:25673 \
            -Llocalhost:25672:localhost:25672 \
            -Llocalhost:23306:localhost:23306

    You have to run this after Invenio booted up. Do **not** stop it while you
    are working with Invenio. Otherwise the port forwarding gets stopped. You
    have to restart the forwarding when your restart the Docker containers. The
    process can be stopped using `CTRL-C`.

Should you require a fresh installation and therefore wipe all your instance
data, run:

.. code-block:: shell

    docker-compose -f docker-compose-dev.yml rm -f

Interactive sessions
--------------------

For interactive sessions inside the container simply attach a shell to the
running instance:

.. code-block:: shell

    docker exec -it invenio_web_1 bash

.. note::
    Some tools (mostly ncurses-based ones) require the ability to detect the
    used terminal. To enable this, set the `TERM` environment variable to the
    correct value as a first command inside the container, e.g. by running:

    .. code-block:: shell

        export TERM=xterm

.. note::
    Do not forget to run `bibsched` to schedule the processing of uploaded
    records. You can put it into automatic mode if you like.

Debugging
---------

The `docker-compose-dev.yml` enables Werkzeug_, a debugger that
automatically kicks in whenever an error occurs. Stacktraces and
debugger terminal are available via web interface.

You can also insert a tracepoint into the code to start an interactive debugger
session:

.. code-block:: python

    import ipdb; ipdb.set_tracepoint()

Furthermore you can debug MySQL at `localhost:23306`, Elasticsearch at
`localhost:29200`, RabbitMQ via `localhost:25672` (webinterface at
`localhost:25673`) and Redis at `localhost:26379`. You might want to use
flower_ for celery debugging and analysis as well. Just run the following
command to open the webinterface at port `5555`:

.. code-block:: shell

    celery flower --broker=amqp://guest:guest@localhost:25672//

Should you require additional information about the behaviour of the different
containers as well as the contained processes and their interaction with the
system and other processes, the usage of classical Linux tools like Wireshark_
and sysdig_ might be helpful.

Code changes and live reloading
-------------------------------

.. note::
    This section does not apply to OS X, Windows and boot2docker as these
    systems are not properly supported by the used watchdog mechanism. When
    you are using one of these setups, you have to restart the Docker
    containers to reload the code and templates.

As long as you do not add new requirements (python and npm) and only change
files inside the `invenio` package, it is not required to rebuild the docker
images. Code changes are mirrored to the containers. If Flask supports it, on
your system it will automatically reload the application when changes are
detected. This sometimes might lead to timeouts in your browser session. Do not
worry about this, but be aware to only save files when you are ready for
reloading.

As of this writing changing template files do not lead to application reloading
and do not purge caches. As a workaround you can simple alter one of the python
files, e.g. by using `touch`.

.. note::
    Changing the Python source files will invalidate stored bytecode files. For
    security reasons, these bytecode files can only be recreated by the root
    user. This can be done via:

    .. code-block:: shell

        docker exec -it -u root invenio_web_1 python -O -m compileall .

Building documentation
----------------------

You can also use the Docker container to build the documentation. This can be
done by attaching to running container:

.. code-block:: shell

    docker exec -it invenio_web_1 sphinx-build -nW docs docs/_build/html

.. note::
    This needs do be done in a running or initialized container because it
    requires that Invenio is set up correctly. Otherwise, the script will break
    because of missing access rights.

Running tests
-------------

You can also run tests using the Docker containers. Wait until the containers
finished setup and the webservice is running. Then use:

.. code-block:: shell

    docker exec -it invenio_web_1 python setup.py test

.. note:: Running the test requires the deactivation of redirection
    debugging. You can achieve this by setting the configuration
    variable `DEBUG_TB_INTERCEPT_REDIRECTS = False`.  (Done for you by
    default if you use ``docker-compose``.)

Overlays
--------

You might want to use build distribute overlays using Docker. Instead of
creating an entire new image and rewrite everything from scratch, you can the
Invenio Docker image. Start by building the image from a branch or release of
your choice:

.. code-block:: shell

    cd src/invenio
    docker build -t invenio:2.0 .

Now go to your overlay and create a Dockerfile that suits your needs, e.g:

.. code-block:: docker

   # based on the right Invenio base image
   FROM invenio:2.0

   # get root rights again
   USER root

   # optional:
   # add new packages
   # (update apt caches, because it was cleaned from the base image)
   #   RUN apt-get update && \
   #       apt-get -qy install whatever_you_need

   # optional:
   # add new packages from pip
   #   RUN pip install what_suits_you

   # optional:
   # add new packages from npm
   #   RUN npm update && \
   #       npm install fun

   # optional:
   # make even more modifications

   # add content
   ADD . /code-overlay
   WORKDIR /code-overlay

   # fix requirements.txt and install additional dependencies
   RUN sed -i '/inveniosoftware\/invenio[@#]/d' requirements.txt && \
       pip install -r requirements.txt --exists-action i

   # build
   RUN python setup.py compile_catalog

   # optional:
   # do some cleanup

   # step back
   # in general code should not be writeable, especially because we are using
   # `pip install -e`
   RUN mkdir -p /code-overlay/src && \
       chown -R invenio:invenio /code-overlay && \
       chown -R root:root /code-overlay/invenio_demosite && \
       chown -R root:root /code-overlay/scripts && \
       chown -R root:root /code-overlay/setup.* && \
       chown -R root:root /code-overlay/src

   # finally step back again
   USER invenio

Notice that this Dockerfile must be located in the directory of your
overlay.  For a full working example, please see `invenio-demosite
<https://github.com/inveniosoftware/invenio-demosite/tree/maint-2.0>`_.
Here is how to build the demo site:

.. code-block:: shell

   cd ~/private/src/invenio
   git checkout maint-2.0
   docker build -t invenio:2.0 .
   cd ~/private/src/invenio-demosite
   git checkout maint-2.0
   docker-compose -f docker-compose-dev.yml build
   docker-compose -f docker-compose-dev.yml up

After all the daemons are up and running, you can populate the demo
site with demo records:

.. code-block:: shell

   docker exec -i -t -u invenio inveniodemosite_web_1 \
          inveniomanage demosite populate \
          --packages=invenio_demosite.base --yes-i-know

Done.  Your Invenio overlay installation is now up and running.

.. _boot2docker: http://boot2docker.io/
.. _Docker: https://www.docker.com/
.. _Docker Compose: https://docs.docker.com/compose/
.. _flower: https://flower.readthedocs.io/
.. _sysdig: http://www.sysdig.org/
.. _Werkzeug: http://werkzeug.pocoo.org/
.. _Wireshark: https://www.wireshark.org/

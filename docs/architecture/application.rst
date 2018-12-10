..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Application architecture
========================
Invenio is at the core an application built on-top of the Flask web
development framework, and fully understanding Invenio's architectual design
requires you to understand core concepts from Flask which will briefly be
covered here.

The Flask application is exposed via different *application interfaces*
depending on if the application is running in a webserver, CLI or job queue.

Invenio adds a powerful *application factory* on top of Flask, which takes
care of dynamically assembling an Invenio application from the many individual
modules that makes up Invenio, and which also allow you to easily extend
Invenio with your own modules.

Core concepts
-------------
We will explain the core Flask concepts using simple Flask application:

.. code-block:: python

    from flask import Blueprint, Flask, request

    # Blueprint
    bp = Blueprint('bp', __name__)

    @bp.route('/')
    def my_user_agent():
        # Executing inside request context
        return request.headers['User-Agent']

    # Extension
    class MyExtension(object):
        def __init__(self, app=None):
            if app:
                self.init_app(app)

        def init_app(self, app):
            app.config.setdefault('MYCONF', True)

    # Application
    app = Flask(__name__)
    ext = MyExtension(app)
    app.register_blueprint(bp)


You can save above code in a file ``app.py`` and run the application:

.. code-block:: console

    $ pip install Flask
    $ export FLASK_APP=app.py flask run

.. rubric:: Application and blueprint

Invenio is a large application built up of many smaller individual modules. The
way Flask allows you to build modular applications is via *blueprints*.
In above example we have a small blueprint which just have one *view*
(``my_user_agent``), which returns the browser's user agent sting.

This blueprint is *registered* on the *Flask application*. This allow you
to possible reuse the blueprint in another Flask application.

.. rubric:: Flask extensions

Like blueprints allow you to modularise your Flask application's views, then
Flask extensions allow you to modularise non-view specific initialization of
your application (e.g. providing database connectivity).

Flask extensions are just objects like the one in the example below, which has
``init_app`` method.

.. rubric:: Application and request context

Code in a Flask application can be executed in two "states":

- *Application context*: when the application is e.g. being used via a CLI
  or running in a job queue (i.e. not handling requests).
- *Request context*: when the application is handling a request from a user.

In above example e.g. the  code inside the view ``my_user_agent`` is executed
during a request, and thus you can have access to the browser's user agent
string. On the other hand, if you tried to access ``request.headers`` outside
the view, the application would fail as no request is being processed.

The ``request`` object is a proxy object which points to the current request
being processed. There is some magic happening behind the scenes in order to
make this thread safe.


Interfaces: WSGI, CLI and Celery
--------------------------------
Overall the Flask application is running via three different applications
interfaces:

- **WSGI:** The frontend webservers interfaces with Flask via Flask's WSGI
  application.
- **CLI:** The command-line interface is made using Click and takes care of
  executing commands inside the Flask application.
- **Celery:** The disitrbuted job queue is made using Celery and takes care of
  executing jobs inside the Flask application.

Application assembly
--------------------
In each of the above interfaces, a Flask application needs to be created.
A common pattern for large Flask applications is to move the application
creation into a factory function, named an **application factory**.

Invenio provides a powerful application factory for Flask which is capable of
dynamically assembling an application. In order to illustrate the basics of
what the Invenio application factory does, have a look at the following
example:

.. code-block:: python

    from flask import Flask, Blueprint

    # Module 1
    bp1 = Blueprint(__name__, 'bp1')
    @bp1.route('/')
    def hello():
        return 'Hello'

    # Module 2
    bp2 = Blueprint(__name__, 'bp1')
    @bp2.route('/')
    def world():
        return 'World'

    # Application factory
    def create_app():
        app = Flask(__name__)
        app.register_blueprint(bp1)
        app.register_blueprint(bp2)
        return app

The example illustrates two blueprints, which are statically registered on the
Flask application blueprint inside the application factory. It is essentially
this part that the Invenio application factory takes care of for you. Invenio
will automatically discover all your installed Invenio modules and register
them on your application.

Assembly phases
---------------
The Invenio application factory assembles your application in five phases:

1. **Application creation**: Besides creating the Flask application object,
   this phase will also ensure your instance folder exists, as well as route
   Python warnings through the Flask application logger.
2. **Configuration loading**: In this phase your application will load your
   instance configuration. Your instance configuration is essentially all the
   configuration variables where you don't want to use the default values, e.g.
   the database host configuration.
3. **URL converter loading**: In this phase, the application will load any of
   your URL converts. This phase is usually only needed for some few specific
   cases.
4. **Flask extensions loading**: In this phase all the Invenio modules which
   provides Flask extensions will initialize the extension. Usually the
   extensions will provide default configuration values they need, unless the
   user already set them.
5. **Blueprints loading**: After all extensions have been loaded, the factory
   will end with registering all the blueprints provided by the Invenio modules
   on the application.

Understanding above application assembly phases, what they do, and how you
can plug into them is essential for fully mastering Invenio development.

.. note::

    **No loading order within a phase**

    It's very important to know, that within each phase, there is **no order**
    in how the Invenio modules are loaded. Say, with in the Flask extensions
    loading phase, there's no way to specify that one extension has to be
    loaded before another extension.

    You only have the order of the phases to work, so e.g. Flask extensions are
    loaded before any blueprints are loaded.

Module discovery
----------------
In each of the application assembly phases, the Invneio factory automatically
discover your installed Invenio modules. The way this works, is via Python
**entry points**. When you install the Python package for an Invenio module,
the package describes via entry points which Flask extensions, blueprints etc.
that this module provides.

WSGI: UI and REST
-----------------
Each of the application interfaces (WSGI, CLI, Celery) may need slightly
different Flask applications. The Invenio application factory is in charge
of assembling these applications, which is done through the five assembly
phases.

The WSGI application is however also split up into two Flask applications:

- **UI:** Flask application responsible for processing all user facing views.
- **REST:** Flask application responsible for processing all REST API requests.

The reason to split the frontend part of Invenio into two separate applications
is partly

- to be able to run the REST API in one domain (``api.example.org``) and the
  UI app on another domain (``www.example.org``)
- because UI and REST API applications usually have vastly different
  requirements.

As an example, a ``404 Not found`` HTTP error, usually needs to render a
template in the UI application, but return a JSON response in the REST API
application.

Implementation
--------------
The following Invenio modules are each responsible for implementing parts of
above application architecture, and it is highly advisable to dig deeper into
these modules if you want a better understanding of the Invenio application
architecture:

- `Invenio-Base <https://invenio-base.readthedocs.io>`_: Implements the Invenio
  application factory.
- `Invenio-Config <https://invenio-config.readthedocs.io>`_: Implements the
  configuration loading phase.
- `Invenio-App <https://invenio-app.readthedocs.io>`_: Implements default
  applications for WSGI, CLI and Celery.

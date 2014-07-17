.. _overlay:

==================================
 How to create an Invenio overlay
==================================

What is an overlay
==================

Invenio is a library that enable the creation of an digital library but it
has to be coupled with an overlay. The overlay will contain your configuration
options, your desired look and feel, the extra invenio modules you've developed
and are using.


Creating your first Invenio overlay
===================================

If you've already setup the :ref:`developer's environement invenio
<first-steps>` itself, it will feel familiar. We are reproducing here the
steps for Ubuntu LTS. Other distributions may be found in the previous link.


The global setup
----------------

Some softwares and libraries are required to work on your overlay. It's mostly
Python, MySQL, Redis as well as XML, XSLT and graphical libraries. Node.js is
solely required for development purposes.

.. code-block:: console

    $ python --version
    Python 2.7.5+
    $ sudo apt-get update
    $ sudo apt-get install build-essential redis-server \
                           libmysqlclient-dev libxml2-dev libxslt-dev \
                           libjpeg-dev libfreetype6-dev libtiff-dev \
                           software-properties-common python-dev \
                           virtualenvwrapper
    $ sudo pip install -U virtualenvwrapper pip
    $ source .bashrc

    # Install MySQL server, and keep the root password somewhere safe.
    $ sudo apt-get install mysql-server

    # Install Node.js
    $ sudo add-apt-repository ppa:chris-lea/node.js
    $ sudo apt-get update
    $ sudo apt-get install nodejs

The virtual environment
-----------------------

Python development usually recommends to work within a ``virtualenv``, which
creates an isolated environment where the libraries required by one will not
intervene with the system ones or the ones of another system. We are using
``virtualenvwrapper`` but nothing prevents your from directly using
``virtualenv`` you are familiar with it.

.. code-block:: console

    $ mkvirtualenv myoverlay
    (myoverlay)$ # we are in your overlay environment now and
    (myoverlay)$ # can leave it using the deactivate command.
    (myoverlay)$ deactivate
    $ # Now join it back, recreating it would fail.
    $ workon myoverlay
    (myoverlay)$ # That's all there is to know about it.

The base of the overlay
-----------------------

Let's dive in.

.. code-block:: console

    $ workon myoverlay
    (myoverlay)$ cdvirtualenv
    (myoverlay)$ mkdir -p src/myoverlay
    (myoverlay)$ cd src/myoverlay
    (myoverlay)$ edit setup.py

The ``setup.py`` file contains the definition of a python package. Having one
means you can rely on existing tools like ``pip`` to package, install, deploy
it later on. Here is its minimal content.

.. code-block:: python

    from setuptools import setup

    setup(
        name="My Overlay",
        version="0.1dev0",
        url="http://invenio-software.org/",
        author="Invenio Software",
        author_email="invenio@invenio-software.org",
        description="My first overlay",
        install_requires=[
            "Invenio>=2"
        ],
        entry_points={
            "invenio.config": ["myoverlay = myoverlay.config"]
        }
    )

Now we can install it in editable mode (``-e``) meaning you don't have to
reinstall it after each change

.. code-block:: console

    (myoverlay)$ pip install -e .

This way will use the latest invenio version published on PyPI, as a developer,
you may want to use the development version of Invenio. To do so, create a file
called ``requirements.txt``.

.. code-block:: text

    git://github.com/inveniosoftware/invenio@pu#egg=Invenio-dev
    -e .

The installation process changes a little bit. It still contains the ``-e .``
command we used before but specify the github version of Invenio instead of the
PyPI one.

.. code-block:: console

    (myoverlay)$ pip install -r requirements.txt

Configuration
=============

As you've seen above, we defined an entry_point for ``myoverlay.config``. It
points to a module that will contain our configuration. So create your
application.

.. code-block:: text

    src/
     │
     ├ myoverlay/
     │  │
     │  ├ base/
     │  │  │
     │  │  └ __init__.py
     │  │
     │  ├ __init__.py
     │  └ config.py
     │
     ├ requirements.txt
     └ setup.py

Put the required configuration into ``config.py``.

.. code-block:: python

    from myoverlay.instance_config import *

    CFG_SITE_LANGS = ["en"]

    CFG_SITE_NAME = "My Overlay"
    CFG_SITE_NAME_INTL = {
        "en": CFG_SITE_NAME
    }

    PACKAGES = [
        "myoverlay.base",
        "invenio.modules.*",
    ]

Sensitive configuration
-----------------------

Other configuration elements like database username and password or the website
url should not be put here as this file is not specific to the installation and
may be put under a version control system such as Git or Subversion.

The configuration can be handled via the `inveniomanage` command line interface
(or by editing the `invenio.cfg` file in the instance folder and reloading
the application).

.. code-block:: console

    (myoverlay)$ inveniomanage config set create secret-key
    # MySQL configuration
    (myoverlay)$ inveniomanage config set CFG_DATABASE_NAME mysql-database
    (myoverlay)$ inveniomanage config set CFG_DATABASE_USER mysql-user
    # HOST configuration (for redirects, etc.)
    (myoverlay)$ inveniomanage config set CFG_SITE_URL http://0.0.0.0:4000
    (myoverlay)$ inveniomanage config set CFG_SITE_SECURE_URL https://0.0.0.0:4000
    (myoverlay)$ inveniomanage config set DEBUG True
    (myoverlay)$ inveniomanage config set ASSETS_DEBUG True
    (myoverlay)$ inveniomanage config set LESS_RUN_IN_DEBUG False


Database setup
--------------

.. code-block:: console

    (invenio)$ inveniomanage database init --user=root --password=$MYSQL_ROOT --yes-i-know
    ...
    >>> Database has been installed.
    (invenio)$ inveniomanage database create
    ...
    >>> Tables filled successfully.


Assets
------

Most of the JavaScript and CSS libraries used are not bundles with invenio
itself and needs to be downloaded via `bower <http://bower.io/>`_. Bower is
configured using two files:

- `.bowerrc`: tells where the assets are downloaded
- `bower.json`: lists the dependencies to be downloaded

.. code-block:: json

    {
        "directory": "myoverlay/base/static/vendors"
    }

The ``bower.json`` can be automagically generated.

.. code-block:: console

    $ sudo su -c "npm install -g bower less clean-css requirejs uglify-js"
    (myoverlay)$ inveniomanage bower > bower.json
    (myoverlay)$ bower install

For invenio to see the static files from the ``myoverlay.base`` module, it
needs to declare a Flask blueprint. Create the following file:
``myoverlay/base/views.py``.

.. code-block:: python

    from flask import Blueprint

    blueprint = Blueprint(
        "myoverlay",
        __name__
        url_prefix="/",
        template_folder="templates",  # where your custom templates will go
        static_folder="static"        # where the assets go
    )

The assets will now be collected into the instance static folder from your
overlay, invenio itself and every libraries it uses.

.. code-block:: console

    (myoverlay)$ inveniomanage collect


**TODO**

- celery/redis/honcho/flower
- translations
- populate the data

Running
=======

.. code-block:: console

    (myoverlay)$ inveniomanage runserver

**TODO**

- Details
- Procfile

Deployment
==========

**TODO**

- sdist
- Fabric

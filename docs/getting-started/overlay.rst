..  This file is part of Invenio
    Copyright (C) 2014 CERN.

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

.. _overlay:

==================================
 How to create an Invenio overlay
==================================

.. admonition:: TODO

    The following items are still missing from this document, feel free to
    contribute to it.

    - celery/redis/honcho/flower
    - populate the data

    Thanks


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
    $ sudo apt-get install build-essential git redis-server \
                           libmysqlclient-dev libxml2-dev libxslt-dev \
                           libjpeg-dev libfreetype6-dev libtiff-dev \
                           libffi-dev libssl-dev \
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
    from setuptools import setup, find_packages
    packages = find_packages()

    setup(
        name="My Overlay",
        version="0.1.dev0",
        url="http://invenio-software.org/",
        author="Invenio Software",
        author_email="invenio@invenio-software.org",
        description="My first overlay",
        packages=packages,
        install_requires=[
            "Invenio>=2"
        ],
        entry_points={
            "invenio.config": ["myoverlay = myoverlay.config"]
        }
    )

Now we can install it in editable mode (``-e``), meaning you don't have to
reinstall it after each change

.. code-block:: console

    (myoverlay)$ pip install -e .

This will fetch the latest Invenio version published on PyPI. As a developer,
you may instead want to use the development version of Invenio from GitHub. To
do so, create a file called ``requirements.txt`` with the following content:

.. code-block:: text

    git+git://github.com/inveniosoftware/invenio@pu#egg=Invenio-dev
    -e .

and install using:

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

    CFG_SITE_LANGS = ["en"]

    CFG_SITE_NAME = "My Overlay"
    CFG_SITE_NAME_INTL = {
        "en": CFG_SITE_NAME
    }

    PACKAGES = [
        "myoverlay.base",
        "invenio.modules.*",
        "invenio.base",
    ]

    try:
        from myoverlay.instance_config import *
    except ImportError:
        pass


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
    (myoverlay)$ inveniomanage config set CFG_SITE_URL http://invenio.example.com
    (myoverlay)$ inveniomanage config set CFG_SITE_SECURE_URL https://invenio.example.com
    (myoverlay)$ inveniomanage config set DEBUG True
    (myoverlay)$ inveniomanage config set ASSETS_DEBUG True


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

Most of the JavaScript and CSS libraries used are not bundled with invenio
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
        __name__,
        url_prefix="/",
        template_folder="templates",  # where your custom templates will go
        static_folder="static"        # where the assets go
    )

The assets will now be collected into the instance static folder from your
overlay, invenio itself and every libraries it uses.

.. code-block:: console

    (myoverlay)$ inveniomanage collect

Running
=======

.. code-block:: console

    (myoverlay)$ inveniomanage runserver



Translations
============

Invenio comes with full internationalization and localization support
based on `Babel <http://babel.pocoo.org/>`_ library and `Flask-Babel
<https://pythonhosted.org/Flask-Babel/>`_.  All strings you want to
translate in your overlay have to be marked with ``_()``.

When you have all strings properly marked, it is time to prepare
catalog that contains all these strings for tranlations to desired
languages.


Configuration
-------------

First of all, you have to get into the source folder of your overlay and
create a configuration file for *Babel*.

.. code-block:: ini

    [python: **.py]
    encoding = utf-8

    [jinja2: **/templates/**]
    encoding = utf-8
    extensions = jinja2.ext.autoescape.jinja2.ext.with_


Save it as ``babel.cfg`` next to your ``setup.py``. Before we run the
extraction tool we need to add section to configure translation directory
to ``setup.cfg``.

.. code-block:: ini

    [compile_catalog]
    directory = myoverlay/base/translations/

    [extract_messages]
    output-file = myoverlay/base/translations/myoverlay.pot

    [init_catalog]
    input-file = myoverlay/base/translations/myoverlay.pot
    output-dir = myoverlay/base/translations/

    [update_catalog]
    input-file = myoverlay/base/translations/myoverlay.pot
    output-dir = myoverlay/base/translations/

Message Extraction
------------------

Then it’s time to run the Babel string extraction with given
configuration:

.. code-block:: console

    (myoverlay)$ python setup.py extract_messages


Create Catalog for New Language
-------------------------------

Once all translatable strings are extracted, one need to prepare catalogs
for new languages. Following example shows how to prepare new catalog for
French in PO (Portable Object) format.


.. code-block:: console

    (myoverlay)$ python setup.py init_catalog -l fr


Now edit the ``myoverlay/base/translations/fr/LC_MESSAGES/messages.po``
file as needed.


Compiling Catalog
-----------------

Next step is to prepare MO (Machine Object) files in the format which is
defined by the GNU `gettext <http://www.gnu.org/software/gettext/>`_ tools
and the GNU `translation project
<http://sourceforge.net/projects/translation>`_.

To compile the translations for use, pybabel integration with distutils
helps again:

.. code-block:: console

    (myoverlay)$ python setup.py compile_catalog

If you install Invenio in development mode you must compile catalog also
from the Invenio directory project.

.. note::

    You should tell git to ignore your compliled translation by running:

    .. code-block:: console

        $ echo \*.mo >> .gitignore


Updating Strings
----------------

It is pretty common that your strings in the code will change over the
time. Pybabel provides support for updating the translation catalog with
new strings or changing existing ones. What do you have to do? Create a
new ``myoverlay.pot`` like above and then let pybabel merge the changes:

.. code-block:: console

    $ python setup.py update_catalog


Deployment
==========

Deploying Invenio is almost a piece of cake using `Fabric
<http://www.fabfile.org/>`_. The following step are inspired by the Flask
documentation: `Deploying with Fabric
<http://flask.pocoo.org/docs/patterns/fabric/>`_

Prerequisites
-------------

First, you need a server with remote access (SSH), where you've installed all
the python dependencies (e.g. ``build-essentials``, ``python-dev``,
``libmysqlclient-dev``, etc.).

Install `fabric` locally,

.. code-block:: console

    $ pip install fabric

and create a boilerplate ``fabfile.py``:

.. code-block:: python

    import json

    from fabric.api import *
    from fabric.utils import error
    from fabric.contrib.files import exists


    env.user = 'invenio'  # remote username
    env.directory = '/home/invenio/www'  # remote directory
    env.hosts = ['yourserver']  # list of servers


Preparing the tarball
---------------------

Before deploying anything, we need to locally prepare the python package to be
installed. Thanks to our ``setup.py`` file, it's very simple.

Beforehand, we have to generate the static assets into our static folder. By
doing so, it's not required to install anything related to node.js on your
server (no ``bower``, ``less``, ``uglifyjs``, etc.).

.. code-block:: python

    @task
    def pack():
        """Create a new source distribution as tarball."""
        with open(".bowerrc") as fp:
            bower = json.load(fp)

        local("inveniomanage assets build --directory {directory}/gen"
              .format(**bower))
        return local("python setup.py sdist --formats=gztar", capture=False) \
            .succeeded

Try it:

.. code-block:: console

    $ fab pack
    ...
    Done
    $ ls dist/
    My-Overlay-0.1.dev0.tar.gz

This is the package that will be installed on your server.

Creating the virtual environement
---------------------------------

We love virtual environments. We recommend you to install each version into its
own virtual env enabling quick rollbacks.

.. code-block:: python

    @task
    def create_virtualenv():
        """Create the virtualenv."""
        package = local("python setup.py --fullname", capture=True).strip()
        venv = "{0}/{1}".format(env.directory, package)

        with cd(env.directory):
            if exists(package):
                return error("This version {0} is already installed."
                             .format(package))

            return run("virtualenv {0}".format(package)).succeeded


Installing the package
----------------------

We can now upload the local tarball into the virtualenv, and install everything
there.

.. code-block:: python

    @task
    def install():
        """Install package."""
        package = local("python setup.py --fullname", capture=True).strip()
        venv = "{0}/{1}".format(env.directory, package)

        if not exists(venv):
            return error("Meh? I need a virtualenv first.")

        # Upload the package and put it into our virtualenv.
        put("dist/{0}.tar.gz".format(package), "/tmp/app.tgz")
        run("mkdir -p {0}/src".format(venv))
        with cd("{0}/src".format(venv)):
            run("tar xzf /tmp/app.tgz")
            run("rm -rf /tmp/app.tgz")

        # Jump into the virtualenv and install stuff
        with cd("{0}/src/{1}".format(venv, package)):
            success = run("{0}/bin/python setup.py install".format(venv)

            if success:
                # post install
                run("{0}/bin/inveniomanage collect".format(venv))
        return success

Combining all the three steps:

.. code-block:: console

    $ fab pack virtualenv install


Configuration
-------------

The setup doesn't have the ``invenio.cfg`` file that is generated via
``inveniomanage config``. You should do so manually.


Running the server
------------------

uWSGI is super simple and neat, all you need is two files. In the example
below, we've installed two versions of our overlay and a symbolic link is
pointing to the one we want to run.

.. code-block:: console

    $ ls www/
    current -> My-Overlay-0.1
    My-Overlay-0.1.dev1
    My-Overlay-0.1.dev2
    My-Overlay-0.1
    wsgi.py
    uwsgi.ini

Let's create the ``wsgi.py`` file.

.. code-block:: python

    from invenio.base.factory import create_wsgi_app

    application = create_wsgi_app()

And the µWSGI configuration:

.. code-block:: python

    [uwsgi]
    http = 0.0.0.0:4000
    master = true

    processes = 4
    die-on-term = true
    vaccum = true

    chdir = %d
    virtualenv = %d/current/
    module = wsgi:application
    touch-reload = %d/wsgi.py

Let's run it.

.. code-block:: console

    $ pip install uwsgi

    $ uwsgi --ini uwsgi.ini
    # or in daemon mode
    $ uwsgi -d uwsgi.log --ini uwsgi.ini

If the new version causes troubles, going back to the old one is as fast as
changing the symbolic link and restarting the WSGI server.

.. code-block:: console

    $ rm current
    $ ln -s My-Overlay-0.1.dev1 current
    $ touch wsgi.py

Dealing with versions
---------------------

One good idea is to use symlink to point to your current virtualenv and run
your overlay from there. Doing that via Fabric is left as an exercise to the
reader.

When installing a new version, copying the ``invenio.cfg`` file over is the
only requirements. Restarting the WSGI server is usually done by ``touch``-ing
the ``wsgi.py`` file.

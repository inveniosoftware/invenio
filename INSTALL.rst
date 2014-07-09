Invenio installation
====================

1. About
--------

This document specifies how to quickly install Invenio v2.0.0 for the first
time. See RELEASE-NOTES if you are upgrading from a previous Invenio release.

2. Prerequisites
----------------

Here is the software you need to have around before you start installing
Invenio for development.

Unix-like operating system.  The main development and production platforms for
Invenio at CERN are GNU/Linux distributions Debian, Gentoo, Scientific Linux
(RHEL-based), Ubuntu, but we also develop on Mac OS X.  Basically any Unix
system supporting the software listed below should do.

2.1. Debian / Ubuntu LTS
~~~~~~~~~~~~~~~~~~~~~~~~

If you are using Ubuntu 13.10 or later, then you can install Invenio by
following this tutorial. **Note:** the recommended Python version is 2.7.5+

.. code-block:: console

    $ python --version
    Python 2.7.5+
    $ sudo apt-get update
    $ sudo apt-get install build-essential git redis-server \
                           libmysqlclient-dev libxml2-dev libxslt-dev \
                           libjpeg-dev libfreetype6-dev libtiff-dev \
                           software-properties-common python-dev \
                           virtualenvwrapper
    $ sudo pip install -U virtualenvwrapper pip
    $ source .bashrc

2.1.1. MySQL
++++++++++++

MySQL Server will ask you for a password, you will need it later and we will
refer to it as ``$MYSQL_ROOT``.

.. code-block:: console

    $ sudo apt-get install mysql-server

2.1.2. Node.js
++++++++++++++

`node.js <http://nodejs.org/>`_ and `npm <https://www.npmjs.org/>`_ from Ubuntu
are troublesome so we recommend you to install them from Chris Lea's PPA.

.. code-block:: console

    $ sudo add-apt-repository ppa:chris-lea/node.js
    $ sudo apt-get update
    $ sudo apt-get install nodejs

2.2. Centos / RHEL
~~~~~~~~~~~~~~~~~~

If you are using Redhat, Centos or Scientific Linux this will setup everything
you need. We are assuming that sudo has been installed and configured nicely.

.. code-block:: console

    $ python --version
    2.6.6
    $ sudo yum update
    $ sudo rpm -Uvh http://mirror.switch.ch/ftp/mirror/epel/6/i386/epel-release-6-8.noarch.rpm
    $ sudo yum -q -y groupinstall "Development Tools"
    $ sudo yum install git wget redis python-devel \
                       mysql-devel libxml2-devel libxslt-devel \
                       python-pip python-virtualenvwrapper
    $ sudo service redis start
    $ sudo pip install -U virtualenvwrapper pip
    $ source /usr/bin/virtualenvwrapper.sh

2.2.1. MySQL
++++++++++++

Setting up MySQL Server requires you to give some credentials for the root
user. You will need the root password later on and we will refer to it as
``$MYSQL_ROOT``.

.. code-block:: console

    $ sudo yum install mysql-server
    $ sudo service msyqld status
    mysqld is stopped
    $ sudo service mysqld start
    $ sudo mysql_secure_installation
    # follow the instructions

2.2.2. Node.js
++++++++++++++

Node.js requires a bit more manual work to install it from the sources. We are
following the tutorial: `digital ocean: tutorial on how to install node.js on
centor
<https://www.digitalocean.com/community/tutorials/how-to-install-and-run-a-node-js-app-on-centos-6-4-64bit>`_

.. code-block:: console

    $ mkdir opt
    $ cd opt
    $ wget http://nodejs.org/dist/v0.10.29/node-v0.10.29.tar.gz
    $ tar xvf node-v0.10.29.tar.gz
    $ cd node-v0.10.29
    $ ./configure
    $ make
    $ sudo make install
    $ node --version
    v0.10.29
    $ npm --version
    1.4.14


2.3. Extra tools
~~~~~~~~~~~~~~~~

2.3.1. Bower and Grunt
++++++++++++++++++++++

Bower and Grunt as used to manage the static assets such as JavaScript
libraries (e.g., jQuery) and CSS stylesheets (e.g., Bootstrap), it's much
easier to install them globally.

.. code-block:: console

    $ sudo su -c "npm install -g bower grunt-cli"


2.3.2 ``git-new-workdir``
++++++++++++++++++++++++++

For the rest of the tutorial you will need to check that you have ``git-new-workdir``.

.. code-block:: console

    $ mkdir -p $HOME/bin
    $ which git-new-workdir || { \
         wget https://raw.github.com/git/git/master/contrib/workdir/git-new-workdir \
         -O $HOME/bin/git-new-workdir; chmod +x $HOME/bin/git-new-workdir; }

**NOTE:** Check that ``~/bin`` is in your ``$PATH``.

.. code-block:: console

    $ export PATH+=:$HOME/bin


3. Quick instructions for the impatient Invenio admin
------------------------------------------------------

3.1. Installation
~~~~~~~~~~~~~~~~~

The first step of the installation is to download the development version of
Invenio. This development is done in the ``pu`` branch.

.. code-block:: console

    $ cd $HOME/src/
    $ export BRANCH=pu
    $ git clone --branch $BRANCH git://github.com/inveniosoftware/invenio.git

We recommend to work using
`virtual environments <http://www.virtualenv.org/>`_ so packages are installed
locally and it will make your live easier. ``(invenio)$`` tells your that the
*invenio* environment is the active one.

.. code-block:: console

    $ mkvirtualenv invenio
    (invenio)$ # we are in the invenio environment now and
    (invenio)$ # can leave it using the deactivate command.
    (invenio)$ deactivate
    $ # Now join it back, recreating it would fail.
    $ workon invenio
    (invenio)$ # That's all there is to know about it.

Let's install Invenio in the environment just created.

.. code-block:: console

    (invenio)$ cdvirtualenv
    (invenio)$ mkdir src; cd src
    (invenio)$ git-new-workdir $HOME/src/invenio/ invenio $BRANCH
    (invenio)$ cd invenio

Installing Invenio.

.. code-block:: console

    (invenio)$ pip install -r requirements.txt

Some modules may require specific dependencies listed as ``extras``. Pick the
ones you need. E.g. to add images support, we can do as follow:

.. code-block:: console

    (invenio)$ pip install -e .[img]

Compiling the translations.

.. code-block:: console

    (invenio)$ pybabel compile -fd invenio/base/translations/

Installing the npm dependencies and the external JavaScript and CSS libraries.

..  FIXME
    bower / grunt / inveniomanage collect should be run after the demosite has
    been installed and only there.

.. code-block:: console

    (invenio)$ npm install
    (invenio)$ bower install

``grunt`` and ``inveniomanage collect`` will create the static folder with all
the required assets (JavaScript, CSS and images) from each module static folder
and bower.

.. code-block:: console

    (invenio)$ grunt
    (invenio)$ inveniomanage collect


3.2. Configuration
~~~~~~~~~~~~~~~~~~

Generate the secret key for your installation.

.. code-block:: console

    (invenio)$ inveniomanage config create secret-key

If you are planning to develop locally in multiple environments please run
the following commands.

.. code-block:: console

    (invenio)$ inveniomanage config set CFG_EMAIL_BACKEND flask.ext.email.backends.console.Mail
    (invenio)$ inveniomanage config set CFG_BIBSCHED_PROCESS_USER $USER
    (invenio)$ inveniomanage config set CFG_DATABASE_NAME $BRANCH
    (invenio)$ inveniomanage config set CFG_DATABASE_USER $BRANCH
    (invenio)$ inveniomanage config set CFG_SITE_URL http://0.0.0.0:4000
    (invenio)$ inveniomanage config set CFG_SITE_SECURE_URL http://0.0.0.0:4000

Assets in non-development mode may be combined and minified using various
filters (see :ref:`ext_assets`). We need to set the path to the binaries if
they are not in the environment ``$PATH`` already.

.. code-block:: console

    # Global installation
    $ sudo su -c "npm install -g less clean-css requirejs uglify-js"

    or
    # Local installation
    (invenio)$ inveniomanage config set LESS_BIN `find $PWD/node_modules -iname lessc | head -1`
    (invenio)$ inveniomanage config set CLEANCSS_BIN `find $PWD/node_modules -iname cleancss | head -1`
    (invenio)$ inveniomanage config set REQUIREJS_BIN `find $PWD/node_modules -iname r.js | head -1`
    (invenio)$ inveniomanage config set UGLIFYJS_BIN `find $PWD/node_modules -iname uglifyjs | head -1`

Invenio comes with default demo site configuration examples that you can use
for quick start.

.. code-block:: console

    (invenio)$ cd $HOME/src/
    (invenio)$ git clone --branch $BRANCH git://github.com/inveniosoftware/invenio-demosite.git
    (invenio)$ cdvirtualenv src
    (invenio)$ git-new-workdir ~/src/invenio-demosite/ invenio-demosite $BRANCH
    (invenio)$ cd invenio-demosite
    (invenio)$ pip install -r requirements.txt --exists-action i


3.3. Development
~~~~~~~~~~~~~~~~

Once you have everything installed you can create database and populate it
with demo records.

.. code-block:: console

    (invenio)$ inveniomanage database init --user=root --password=$MYSQL_ROOT --yes-i-know
    (invenio)$ inveniomanage database create
    (invenio)$ inveniomanage demosite create --packages=invenio_demosite.base

Now you should be able to run the development server. Invenio uses
`Celery <http://www.celeryproject.org/>`_ and `Redis <http://redis.io/>`_
which must be running alongside with the web server.

.. code-block:: console

    $ # make sure that redis is running
    $ sudo service redis-server status
    redis-server is running
    $ # or start it with start
    $ sudo service redis-start start

    $ # launch celery
    $ workon invenio
    (invenio)$ celeryd -E -A invenio.celery.celery --workdir=$VIRTUAL_ENV

    $ # in a new terminal
    $ workon invenio
    (invenio)$ inveniomanage runserver
     * Running on http://0.0.0.0:4000/
     * Restarting with reloader


**Troubleshooting:** As a developer, you may want to use the provided
``Procfile`` with `honcho <https://pypi.python.org/pypi/honcho>`_. It
starts all the services at once with nice colors. Be default, it also runs
`flower <https://pypi.python.org/pypi/flower>`_ which offers a web interface
to monitor the *Celery* tasks.

.. code-block:: console

    (invenio)$ pip install flower

When you have the servers running, it is possible to upload the demo records.

.. code-block:: console

    $ # in a new terminal
    $ workon invenio
    (invenio)$ inveniomanage demosite populate --packages=invenio_demosite.base

And you may now open your favourite web browser on
`http://0.0.0.0:4000/ <http://0.0.0.0:4000/>`_

Optionally, if you are using Bash shell completion, then you may want to
register python argcomplete for inveniomanage.

.. code-block:: bash

    eval "$(register-python-argcomplete inveniomanage)"

4. Final words
--------------

Good luck, and thanks for choosing Invenio.

       - Invenio Development Team
         <info@invenio-software.org>
         <http://invenio-software.org/>

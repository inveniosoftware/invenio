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
                           libffi-dev libssl-dev \
                           software-properties-common python-dev \
                           virtualenvwrapper subversion
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

If you are on CentOS 7, the mysql-server package is not available in the
default repository. First we need to add the official YUM repository provided
by Oracle. The YUM repository configuration can be downloaded from the `MySQL
website <http://dev.mysql.com/downloads/repo/yum/>`_. Choose the desired
distribution (Red Hat Enterprise Linux 7 / Oracle Linux 7 for CentOS 7) and
click Download.
The download link can be retrieved without registering for an Oracle account.
Locate the "No thanks, just start my download" link and pass the link URL as a
parameter to rpm.

.. code-block:: console

    # only needed with CentOS version >= 7
    $ sudo rpm -Uvh http://dev.mysql.com/get/mysql-community-release...

    # for every CentOS version
    $ sudo yum install mysql-server
    $ sudo service mysqld status
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


.. _OS X:


2.3. OS X
~~~~~~~~~~

The steps below can be used to install Invenio on a machine running OS X 10.9 or later.

First, we need to install the `Homebrew <http://brew.sh/>`_ package manager.
Follow the installation procedure by running following command:

.. code-block:: console

    $ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

You need to check that ``/usr/local/bin`` occurs before the ``/usr/bin``, otherwise you can
try following commands:

.. code-block:: console

    $ echo export PATH="/usr/local/bin:$PATH" >> ~/.bash_profile
    $ source ~/.bash_profile (to reload the profile)

Next, you should check if everything is up-to-date!

.. code-block:: console

    $ brew update
    $ brew doctor
    $ brew upgrade

Now, it is time to start installing the prerequisites.

.. code-block:: console

    $ brew install python --framework -- universal
    $ sudo pip install virtualenv
    $ sudo pip install virtualenvwrapper
    # edit the Bash profile
    $ $EDITOR ~/.bash_profile

Add the following to the file you have opened and paste the following lines.

.. code-block:: text

    export WORKON_HOME=~/.virtualenvs
    source /usr/local/bin/virtualenvwrapper.sh

Save the file and reload it by typing:

.. code-block:: console

    $ source ~/.bash_profile

and continue with the installation of prerequisite packages:

.. code-block:: console

    $ brew install redis
    $ brew install mongodb


.. note::

    See `MySQL on OS X`_ for installing ``mysql``.

In order to install ``libxml2`` and ``libxslt`` packages run:

.. code-block:: console

    $ brew install automake autoconf libtool libxml2 libxslt
    $ brew link --force libxml2 libxslt

The following might not be necessary but is good to have for completeness.

.. code-block:: console

    $ brew install libjpeg libtiff freetype libffi xz
    $ pip install -I pillow

Install ``node`` by following `Node on OS X`_

For ``bower``, type:

.. code-block:: console

    $ npm install -g bower

After the configuration section install the following(required for the assets):

.. code-block:: console

    $ npm install -g less clean-css requirejs uglify-js

See the following sections `Installation`_ , `Configuration`_ and `Development`_
The commands for ``OS X`` are the same as in ``Linux``.

.. note::

    When initializing the database, type:

    .. code-block:: console

        $ inveniomanage database init --user=root --yes-i-know (because we have no root password)

.. note::

    For developers, honcho is recommended and will make your life
    easier because it launches all the servers together as it finds the ``Procfile``.

.. _MySQL on OS X:

2.3.1. MySQL
++++++++++++

We will install MySQL but without a root password.
It should be easy to set the root password once you are connected in MySQL.

.. code-block:: console

    $ brew install mysql
    $ unset TMPDIR
    $ mysql_install_db --verbose --user=`whoami` \
     --basedir="$(brew --prefix mysql)" \
     --datadir=/usr/local/var/mysql \
     --tmpdir=/tmp

You can start, stop, or restart MySQL server by typing:

.. code-block:: console

    $ mysql.server (start | stop | restart)


.. _Node on OS X:

2.3.2. Node.js
++++++++++++++

Install ``node`` by typing:

.. code-block:: console

    $ brew install node


2.4. Extra tools
~~~~~~~~~~~~~~~~

2.4.1. Bower
++++++++++++

Bower is used to manage the static assets such as JavaScript libraries (e.g.,
jQuery) and CSS stylesheets (e.g., Bootstrap). It's much easier to install them
globally (``-g``) but you're free to choose your preferred way.

.. code-block:: console

    # global installation
    $ sudo su -c "npm install -g bower"
    # user installation
    $ npm install bower


2.4.2 ``git-new-workdir`` (optional)
++++++++++++++++++++++++++++++++++++

For the rest of the tutorial you may want to use ``git-new-workdir``. It's a
tool that will let you working on the same repository from different locations.
Just like you would do with subversion branches.

.. code-block:: console

    $ mkdir -p $HOME/bin
    $ which git-new-workdir || { \
         wget https://raw.github.com/git/git/master/contrib/workdir/git-new-workdir \
         -O $HOME/bin/git-new-workdir; chmod +x $HOME/bin/git-new-workdir; }

**NOTE:** Check that ``~/bin`` is in your ``$PATH``.

.. code-block:: console

    $ export PATH+=:$HOME/bin


3. Quick instructions for the impatient Invenio developer
---------------------------------------------------------

This installation process is tailored for running the development version of
Invenio, check out the :py:ref:`overlay` documentation for the production
setup.


.. _Installation:

3.1. Installation
~~~~~~~~~~~~~~~~~

The first step of the installation is to download the development version of
Invenio and the Invenio Demosite. This development is done in the ``master``
branch.

.. code-block:: console

    $ mkdir -p $HOME/src
    $ cd $HOME/src/
    $ export BRANCH=master
    $ git clone --branch $BRANCH git://github.com/inveniosoftware/invenio.git
    $ git clone --branch $BRANCH git://github.com/inveniosoftware/invenio-demosite.git

We recommend to work using
`virtual environments <http://www.virtualenv.org/>`_ so packages are installed
locally and it will make your life easier. ``(invenio)$`` tells your that the
*invenio* environment is the active one.

.. code-block:: console

    $ mkvirtualenv invenio
    (invenio)$ # we are in the invenio environment now and
    (invenio)$ # can leave it using the deactivate command.
    (invenio)$ deactivate
    $ # Now join it back, recreating it would fail.
    $ workon invenio
    (invenio)$ # That's all there is to know about it.

Let's put Invenio and the Invenio Demosite in the environment just created.

.. code-block:: console

    (invenio)$ cdvirtualenv
    (invenio)$ mkdir src
    (invenio)$ cd src
    (invenio)$ git-new-workdir $HOME/src/invenio/ invenio $BRANCH
    (invenio)$ git-new-workdir $HOME/src/invenio-demosite/ invenio-demosite $BRANCH

If you don't want to use the ``git-new-workdir`` way, you can either:

- create a symbolic link,
- or clone the repository directly into the virtualenv.


Installing Invenio.

.. code-block:: console

    (invenio)$ cdvirtualenv src/invenio
    (invenio)$ pip install --process-dependency-links -e .[development]

Some modules may require specific dependencies listed as ``extras``. Pick the
ones you need. E.g. to add `images` support, we can do as follow:

.. code-block:: console

    (invenio)$ pip install -e .[img]

If the Invenio is installed in development mode, you will need to compile the
translations manually.

.. code-block:: console

    (invenio)$ python setup.py compile_catalog

.. note:: Translation catalog is compiled automatically if you install
    using `python setup.py install`.

Installing Invenio Demosite. ``exists-action i`` stands for `ignore`, it means
that it'll will skip any previous installation found. Because the Invenio
Demosite depends on Invenio, it would have tried to reinstall it without this
option. If you omit it, ``pip`` will ask you what action you want to take.

.. code-block:: console

    (invenio)$ cdvirtualenv src/invenio-demosite
    (invenio)$ pip install -r requirements.txt --exists-action i

Installing the required assets (JavaScript, CSS, etc.) via bower. The file
``.bowerrc`` is configuring where bower will download the files and
``bower.json`` what libraries to download.

.. code-block:: console

    (invenio)$ inveniomanage bower -i bower-base.json > bower.json
    Generates or update bower.json for you.
    (invenio)$ cat .bowerrc
    {
        "directory": "invenio_demosite/base/static/vendors"
    }
    (invenio)$ bower install
    (invenio)$ ls invenio_demosite/base/static/vendors
    bootstrap
    ckeditor
    hogan
    jquery
    jquery-tokeninput
    jquery-ui
    plupload
    ...


We recommend you to only alter ``bower-base.json`` and regenerate
``bower.json`` with it as needed. The
:py:class:`invenio.ext.assets.commands.BowerCommand` is aggregating all the
dependencies defined by each bundle.

The last step, which is very important will be to collect all the assets, but
it will be done after the configuration step.


.. _Configuration:

3.2. Configuration
~~~~~~~~~~~~~~~~~~

Generate the secret key for your installation.

.. code-block:: console

    (invenio)$ inveniomanage config create secret-key

If you are planning to develop locally in multiple environments please run
the following commands.

.. code-block:: console

    (invenio)$ inveniomanage config set CFG_EMAIL_BACKEND flask_email.backends.console.Mail
    (invenio)$ inveniomanage config set CFG_BIBSCHED_PROCESS_USER $USER
    (invenio)$ inveniomanage config set CFG_DATABASE_NAME $BRANCH
    (invenio)$ inveniomanage config set CFG_DATABASE_USER $BRANCH
    (invenio)$ inveniomanage config set CFG_SITE_URL http://localhost:4000
    (invenio)$ inveniomanage config set CFG_SITE_SECURE_URL http://localhost:4000

Assets in non-development mode may be combined and minified using various
filters (see :ref:`ext_assets`). We need to set the path to the binaries if
they are not in the environment ``$PATH`` already.

.. code-block:: console

    # Local installation (using package.json)
    (invenio)$ cdvirtualenv src/invenio
    (invenio)$ npm install
    (invenio)$ inveniomanage config set LESS_BIN `find $PWD/node_modules -iname lessc | head -1`
    (invenio)$ inveniomanage config set CLEANCSS_BIN `find $PWD/node_modules -iname cleancss | head -1`
    (invenio)$ inveniomanage config set REQUIREJS_BIN `find $PWD/node_modules -iname r.js | head -1`
    (invenio)$ inveniomanage config set UGLIFYJS_BIN `find $PWD/node_modules -iname uglifyjs | head -1`

All the assets that are spread among every invenio module or external libraries
will be collected into the instance directory. By default, it create copies of
the original files. As a developer you may want to have symbolic links instead.

.. code-block:: console

    # Developer only
    (invenio)$ inveniomanage config set COLLECT_STORAGE flask_collect.storage.link


    (invenio)$ inveniomanage collect
    ...
    Done collecting.
    (invenio)$ cdvirtualenv var/invenio.base-instance/static
    (invenio)$ ls -l
    css
    js
    vendors
    ...


.. _Development:

3.3. Development
~~~~~~~~~~~~~~~~

Once you have everything installed, you can create the database and populate it
with demo records.

.. code-block:: console

    (invenio)$ inveniomanage database init --user=root --password=$MYSQL_ROOT --yes-i-know
    (invenio)$ inveniomanage database create

Now you should be able to run the development server. Invenio uses
`Celery <http://www.celeryproject.org/>`_ and `Redis <http://redis.io/>`_
which must be running alongside with the web server.

.. code-block:: console

    # make sure that redis is running
    $ sudo service redis-server status
    redis-server is running
    # or start it with start
    $ sudo service redis-server start

    # launch celery
    $ workon invenio
    (invenio)$ celery worker -E -A invenio.celery.celery --workdir=$VIRTUAL_ENV

    # in a new terminal
    $ workon invenio
    (invenio)$ inveniomanage runserver
     * Running on http://0.0.0.0:4000/
     * Restarting with reloader

.. note::

    On OS X, the command ``service`` might not be found when starting the redis
    server. To run redis, just type:

    .. code-block:: console

        $ redis-server

**Troubleshooting:** As a developer, you may want to use the provided
``Procfile`` with `honcho <https://pypi.python.org/pypi/honcho>`_. It
starts all the services at once with nice colors. By default, it also runs
`flower <https://pypi.python.org/pypi/flower>`_ which offers a web interface
to monitor the *Celery* tasks.

.. code-block:: console

    (invenio)$ pip install honcho flower
    (invenio)$ cdvirtualenv src/invenio
    (invenio)$ honcho start

When all the servers are running, it is possible to upload the demo records.

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

Happy hacking and thanks for flying Invenio.

       - Invenio Development Team
         <info@invenio-software.org>
         <http://invenio-software.org/>

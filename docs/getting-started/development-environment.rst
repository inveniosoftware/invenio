..
    This file is part of Invenio.
    Copyright (C) 2017-2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _setting-up-your-environment:

Setting up your system
======================

The following is a guide to help you prepare your system for developing with
Invenio. A proper development environment setup can save a lot of time and
frustrations. Note that the following guide, is not meant as a guide for
setting up servers.

System setup
------------
We support development on macOS and Linux-based systems (development on Windows
is not supported).

macOS
~~~~~
We recommend that you install libraries and tools using the
`Homebrew <https://brew.sh>`_ package manager. Homebrew allows you to install
two types of packages - cask and normal.

**Cask packages**

Cask packages are usually UI applications that end up in your Applications
folder. You can install cask packages using the command:

.. code-block:: console

    $ brew cask install <packages>

Here are some recommended cask packages (only ``docker`` is required):

.. code-block:: console

    db-browser-for-sqlite # UI for SQLite
    discord               # app that we use for chat among developers
    docker                # docker setup for macOS
    google-chrome         # needed for some end-to-end tests
    iterm2                # a better terminal than Terminal.app
    postico               # UI for PostgreSQL
    spectacle             # organise windows with keyboard shortcuts
    visual-studio-code    # a text editor used by many Invenio developers

**Normal packages**

Normal packages are usually command line tools/libraries that end up in
/usr/local and that you use from the CLI. You can install normal packages
using the command:

.. code-block:: console

    $ brew install <packages>

The following packages are libraries that are likely to be needed during
Invenio development in order to install certain Python packages:

.. code-block:: console

    cairo
    freetype
    geoip
    gettext
    glib
    imagemagick
    jpeg
    libffi
    libmemcached
    libpng
    libtiff
    libxml2
    libxslt
    readline
    xz
    zlib

Following are CLI tools that are useful during development:

.. code-block:: console

    cookiecutter # tool to bootstrap new modules from templates
    chromedriver # selenium driver for chrome (used for end-to-end testing)
    gh           # GitHub CLI client (useful e.g for checking out PRs)
    gifify       # make short screen recordings for bug reports
    git          # our version control system
    hub          # extends git with github features

General CLI tools:

.. code-block:: console

    htop            # a better top
    tree            # pretty print a directory structure
    wget            # http client
    zsh-completion  # if you use zsh as shell
    base-completion # if you use bash as shell

CERN specific tools:

.. code-block:: console

    openshift-cli # if you deploy on openshift
    xrootd        # library for accessing EOS storage cluster
    sshuttle      # tunnel into CERN

**Python**

Invenio is developed using Python and JavaScript. We highly recommend that
install ``pyenv`` and ``nvm`` - both tools manage version of python and node
respectively. Install the following packages:

.. code-block:: console

    nvm
    pyenv
    pyenv-virtualenv
    pyenv-virtualenvwrapper


Once you have installed above packages, you can proceed with installing Python
versions. The following will install Python 3.6, 3.7 and 3.8 and set the
default Python installation to Python 3.8 (node you can always install the
latest patch-level release):

.. code-block:: console

    $ pyenv install 3.6.9
    $ pyenv install 3.7.8
    $ pyenv install 3.8.5
    $ pyenv global 3.8.5

You should edit your `.bashrc` or `.zshrc` file to initialise pyenv:

.. code-block:: sh

    # nvm setup
    export NVM_DIR="$HOME/.nvm"
    [ -s "/usr/local/opt/nvm/nvm.sh" ] && . "/usr/local/opt/nvm/nvm.sh"

    # pyenv
    eval "$(pyenv init -)"

    # pyenv-virtualenv
    eval "$(pyenv virtualenv-init -)"

    # pyenv-virtualenvwrapper
    pyenv virtualenvwrapper

Now, you can create e.g. Python virtual environments using the following
commands:

.. code-block:: console

    $ mkvirtualenv <name>
    $ mkvirtualenv -p python3.7 <name>
    $ workon <name>


**Fonts**

In order to create e.g. DOI badges you need the DejaVu Sans font installed.
Go to https://dejavu-fonts.github.io/ and follow the instructions.

**Docker Desktop for Mac**

You may need to increase the resources assigned to Docker Desktop for Mac
See https://docs.docker.com/docker-for-mac/#resources.

A typical sign of needed more resources, is that services are not running or
images are having problems building.

Linux
~~~~~

Want to write it? Contact us on the chat!

Editor
------
You can use any code editor of your choice. Here we give a brief overview of
some of the editors our existing developers are using. For all editors, the
most important is support for `EditorConfig <https://editorconfig.org>`_

EditorConfig
~~~~~~~~~~~~
All repositories have a ``.editorconfig`` file which defines indention style,
text encoding, newlines etc. Many editors either come with built-in support
or plugins that reads the ``.editorconfig`` file and configures your editor
accordingly.

Visit `EditorConfig <https://editorconfig.org>`_ to see the list of supported
editors.

Editors
~~~~~~~
Following editors are used by our existing developers. Don't hesitate to reach
out on our Discord server, to ask for help for useful plugins:

- `Emacs <https://www.gnu.org/software/emacs/>`_
- `PyCharm <https://www.jetbrains.com/pycharm/>`_
- `Sublime <https://www.sublimetext.com>`_
- `VIM <https://www.vim.org>`_
- `Visual Studio Code <https://code.visualstudio.com>`_

Plugins for editors
~~~~~~~~~~~~~~~~~~~
The key plugins you should look for in your editor of choice are:

- Python / JavaScript environment
- PEP8 / PEP257 style checking
- `Isort <https://isort.readthedocs.io/en/latest/>`_ plugin.

Working with Git and GitHub
---------------------------
There are a couple of utilities that allow you to work more efficiently with
Git and GitHub.

CLI tools
~~~~~~~~~

- `GitHub CLI <https://cli.github.com/>`_: command-line tool to interact with
  GitHub. Note that this tool is independent from the git CLI.
- `Hub <https://hub.github.com>`_: command-line wrapper around git that makes
  it easier to work with GitHub by adding new commands.

Git aliases
~~~~~~~~~~~

Use `aliases <https://git-scm.com/book/en/v2/Git-Basics-Git-Aliases>`_ to type
frequent commands more efficiently. Note that your shell might offer more git
aliases too, for example `Oh My Zsh <https://ohmyz.sh/>`_ has the
`git plugin <https://github.com/ohmyzsh/ohmyzsh/blob/master/plugins/git/git.plugin.zsh>`_
which among other things it will come with a few pre-configured aliases.

Debugging
---------

There are several tools for debugging, we will list here the ones which are
editor agnostic:

- `pytest <https://docs.pytest.org/en/2.8.7/contents.html>`_: comes with
  builtin support for dropping into pdb.
- `ipdb <https://github.com/gotcha/ipdb>`_: this is a terminal debugger with
  features tab completion, syntax highlighting among others. Note that the
  debugging session is opened as the output of the running program.
- `wdb <https://github.com/Kozea/wdb>`_: web debugger with a client server
  architecture. The debugging session is opened in a web browser. Suitable for
  remote debugging and programs which do not allow to open an interactive shell
  session (i.e. Celery).

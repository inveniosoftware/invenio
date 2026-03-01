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
frustrations. Note that the following is not meant as a guide for
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
:code:`/usr/local` and that you use from the CLI. You can install normal packages
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
    hub          # alternative GitHub CLI client

General CLI tools:

.. code-block:: console

    htop            # a better top
    tree            # pretty print a directory structure
    wget            # http client
    zsh-completion  # if you use zsh as shell
    bash-completion # if you use bash as shell

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
default Python installation to Python 3.8.

.. code-block:: console

    $ pyenv install 3.6.9
    $ pyenv install 3.7.8
    $ pyenv install 3.8.5
    $ pyenv global 3.8.5

Install the latest patch-level release for node.

.. code-block:: console

    $ nvm install --lts

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

Now, you can create Python virtual environments using the following
commands:

.. code-block:: console

    $ mkvirtualenv <name>
    $ mkvirtualenv -p python3.7 <name>
    $ workon <name>


**Fonts**

In order to create DOI badges you need the DejaVu Sans font installed.
Go to https://dejavu-fonts.github.io/ and follow the instructions.

**Docker Desktop for Mac**

You may need to increase the resources assigned to Docker Desktop for Mac
See https://docs.docker.com/docker-for-mac/#resources.

Typically this is necessary if services are not running or
images are having problems building.

Linux
~~~~~

This section covers setting up a Linux system for Invenio development.
Instructions are provided for Debian/Ubuntu, NixOS, Alpine Linux, and
Arch Linux. Install the system packages for your distribution, then follow
the `Shared setup (all distributions)`_ section.

Debian / Ubuntu
^^^^^^^^^^^^^^^

Tested on Debian 12 (Bookworm) and Ubuntu 22.04+.

**System libraries**

These are needed to compile the Python packages that Invenio depends on:

.. code-block:: console

    $ sudo apt-get update
    $ sudo apt-get install -y \
        build-essential python3-dev libssl-dev \
        libcairo2-dev libfreetype-dev libgeoip-dev gettext libglib2.0-dev \
        imagemagick libmagickwand-dev \
        libjpeg-dev libpng-dev libtiff-dev \
        libffi-dev libmemcached-dev \
        libxml2-dev libxslt1-dev \
        libreadline-dev xz-utils zlib1g-dev \
        libbz2-dev libsqlite3-dev libncurses-dev tk-dev liblzma-dev

.. note::

    **Debian 11 (Bullseye) or older:** replace ``libfreetype-dev`` with
    ``libfreetype6-dev`` and ``libncurses-dev`` with
    ``libncurses5-dev libncursesw5-dev``.

**CLI development tools**

.. code-block:: console

    $ sudo apt-get install -y git wget curl htop tree

GitHub CLI:

.. code-block:: console

    $ curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    $ echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
        https://cli.github.com/packages stable main" \
        | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    $ sudo apt-get update && sudo apt-get install -y gh

Chromedriver (for end-to-end tests):

.. code-block:: console

    $ sudo apt-get install -y chromium-driver   # Debian
    $ sudo apt-get install -y chromium-chromedriver   # Ubuntu

**Docker**

Install Docker Engine from the
`official repository <https://docs.docker.com/engine/install/debian/>`_:

.. code-block:: console

    $ sudo apt-get install -y ca-certificates gnupg
    $ sudo install -m 0755 -d /etc/apt/keyrings
    $ curl -fsSL https://download.docker.com/linux/debian/gpg \
        | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    $ echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    $ sudo apt-get update
    $ sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

.. note::

    For **Ubuntu**, replace ``download.docker.com/linux/debian`` with
    ``download.docker.com/linux/ubuntu`` in the commands above.

See `Docker post-install`_ below.

**Fonts**

.. code-block:: console

    $ sudo apt-get install -y fonts-dejavu

NixOS
^^^^^

NixOS is different from traditional distributions. The idiomatic approach is
to use a ``shell.nix`` (or ``flake.nix``) for project-local dev environments
and ``configuration.nix`` for system-wide tools like Docker and fonts.

**Project dev shell (shell.nix)**

Create a ``shell.nix`` at the root of your Invenio project:

.. code-block:: nix

    { pkgs ? import <nixpkgs> {} }:

    pkgs.mkShell {
      buildInputs = with pkgs; [
        # Build toolchain
        gcc gnumake pkg-config openssl

        # System libraries for Python packages
        cairo freetype geoip gettext glib imagemagick
        libjpeg libffi libmemcached libpng libtiff
        libxml2 libxslt readline xz zlib

        # pyenv build dependencies
        bzip2 sqlite ncurses tcl tk

        # CLI tools
        git gh chromedriver nodejs wget curl htop tree

        # Python version management
        pyenv
      ];

      shellHook = ''
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
      '';
    }

Enter the dev shell:

.. code-block:: console

    $ nix-shell

Or with flakes:

.. code-block:: console

    $ nix develop

**System configuration (configuration.nix)**

Add system-wide packages in ``/etc/nixos/configuration.nix``:

.. code-block:: nix

    {
      # Docker
      virtualisation.docker.enable = true;
      users.users.<your-user>.extraGroups = [ "docker" ];

      # Fonts
      fonts.packages = with pkgs; [ dejavu_fonts ];

      # System-wide CLI tools (optional)
      environment.systemPackages = with pkgs; [
        git gh docker-compose htop tree
      ];
    }

Rebuild:

.. code-block:: console

    $ sudo nixos-rebuild switch

.. note::

    **nvm** is not packaged in nixpkgs. Use ``nodejs`` from nixpkgs
    directly (pinned via ``shell.nix``), or install nvm via the upstream
    script as described in `Node.js via nvm`_.

Alpine Linux
^^^^^^^^^^^^

Alpine uses **musl libc** instead of glibc. Most Python packages build fine,
but some pre-built binary wheels may not be available -- pip will compile
them from source, which is why the ``-dev`` packages below are essential.

**Enable the community repository**

Several packages (imagemagick, docker, gh, npm) live in the community
repository:

.. code-block:: console

    $ setup-apkrepos -cf
    $ apk update

**System libraries**

.. code-block:: console

    $ apk add \
        build-base python3-dev openssl-dev linux-headers \
        cairo-dev freetype-dev geoip-dev gettext-dev glib-dev \
        imagemagick-dev \
        libjpeg-turbo-dev libpng-dev tiff-dev \
        libffi-dev libmemcached-dev \
        libxml2-dev libxslt-dev \
        readline-dev xz-dev zlib-dev \
        bzip2-dev sqlite-dev ncurses-dev tk-dev

**CLI development tools**

.. code-block:: console

    $ apk add git github-cli wget curl htop tree bash

Chromedriver:

.. code-block:: console

    $ apk add chromium-chromedriver

**Docker**

.. code-block:: console

    $ apk add docker docker-cli-compose
    $ rc-update add docker default
    $ service docker start

See `Docker post-install`_ below.

**Node.js**

.. code-block:: console

    $ apk add nodejs npm

**Fonts**

.. code-block:: console

    $ apk add ttf-dejavu

.. note::

    If a Python package fails to install with wheel errors, ensure you have
    all the ``-dev`` headers above. Packages that ship only ``manylinux``
    wheels must be built from source on Alpine.

Arch Linux
^^^^^^^^^^

**System libraries**

.. code-block:: console

    $ sudo pacman -S --needed \
        base-devel python openssl \
        cairo freetype2 geoip gettext glib2 \
        imagemagick \
        libjpeg-turbo libpng libtiff \
        libffi libmemcached-awesome \
        libxml2 libxslt \
        readline xz zlib \
        bzip2 sqlite ncurses tk

.. note::

    ``libmemcached-awesome`` is the maintained replacement for the legacy
    ``libmemcached`` package.

**CLI development tools**

.. code-block:: console

    $ sudo pacman -S --needed git github-cli wget curl htop tree

Chromedriver (AUR):

.. code-block:: console

    $ yay -S chromedriver   # or: paru -S chromedriver

**Docker**

.. code-block:: console

    $ sudo pacman -S --needed docker docker-compose
    $ sudo systemctl enable --now docker.service

See `Docker post-install`_ below.

**Python & Node.js version managers**

Both ``pyenv`` and ``nvm`` are available in the official repos:

.. code-block:: console

    $ sudo pacman -S --needed pyenv nvm nodejs npm

**Fonts**

.. code-block:: console

    $ sudo pacman -S --needed ttf-dejavu

Shared setup (all distributions)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The steps below are the same regardless of which Linux distribution you use.

.. _pyenv-setup:

**Python via pyenv**

If you did not install pyenv from your package manager (Arch and NixOS
provide it), install it from source:

.. code-block:: console

    $ curl https://pyenv.run | bash

Add the following to your ``~/.bashrc`` or ``~/.zshrc``:

.. code-block:: sh

    # pyenv
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"

Reload your shell, then install Python versions:

.. code-block:: console

    $ pyenv install 3.6.15
    $ pyenv install 3.7.17
    $ pyenv install 3.8.20
    $ pyenv global 3.8.20

Create virtual environments:

.. code-block:: console

    $ pyenv virtualenv 3.8.20 my-invenio-env
    $ pyenv activate my-invenio-env

Or, if you prefer **pyenv-virtualenvwrapper**:

.. code-block:: console

    $ pip install virtualenvwrapper
    $ pyenv virtualenvwrapper
    $ mkvirtualenv my-invenio-env
    $ workon my-invenio-env

To deactivate the virtual environment:

.. code-block:: console

    $ deactivate

.. _nvm-setup:

**Node.js via nvm**

Install nvm:

.. code-block:: console

    $ curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash

Add to your ``~/.bashrc`` or ``~/.zshrc`` (the installer usually does this
automatically):

.. code-block:: sh

    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

Install Node.js:

.. code-block:: console

    $ nvm install 14
    $ nvm use 14

.. _docker-post-install:

**Docker post-install**

Add your user to the ``docker`` group so you can run Docker without ``sudo``:

.. code-block:: console

    $ sudo usermod -aG docker $USER

Log out and back in (or run ``newgrp docker``) for the group change to take
effect. Verify:

.. code-block:: console

    $ docker run hello-world

**Elasticsearch vm.max_map_count**

Elasticsearch requires a higher virtual memory map limit than most Linux
defaults. Set it persistently:

.. code-block:: console

    $ sudo sysctl -w vm.max_map_count=262144

To make it permanent across reboots:

.. code-block:: console

    $ echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.d/99-elasticsearch.conf
    $ sudo sysctl --system

.. note::

    On **NixOS**, add to ``configuration.nix`` instead:

    .. code-block:: nix

        boot.kernel.sysctl."vm.max_map_count" = 262144;

**Fonts**

All distributions above include a step to install DejaVu Sans. If you
skipped it, install the ``dejavu`` font package for your distro (needed for
generating DOI badges).

**cookiecutter**

Tool to bootstrap new modules from templates:

.. code-block:: console

    $ pip install cookiecutter

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
out on our Discord server to ask for help for useful plugins:

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

..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _setting-up-your-environment:

Developer environment guide
===========================
You can save a lot of time and frustrations by spending some time setting up
your development environment. We have primarily adopted existing community
style guides, and in most cases the formatting and checking can be fully
automated by your editor.

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

See `EditorConfig <https://editorconfig.org>`_ for list of supported editors.

Editors
~~~~~~~
Following editors (listed alphabetically) are used by our existing developers.
Don't hesitate to reach out on our Gitter channel, to ask for help for useful
plugins:

- `Atom <https://atom.io>`_
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

.. todo: docker, git, cli tools (hub), git aliases, getting pull-requests,
   virtualenv, virtualenv-wrapper, debugging pdb/ipdb, homebrew


Working with Git and GitHub
---------------------------
There are a couple of utilities that allow you to work more efficiently with
Git and GitHub.

Hub
~~~
`Hub <https://hub.github.com>`_ is a command-line wrapper for git that makes it
easier to work with GitHub. See the
`installation instructions <https://hub.github.com>`_ for how install Hub.

Here is a short overview of possibilities:

```console
# Clone one of your personal repositories from GitHub
$ git clone invenio-app
# Fetch the upstream inveniosoftware/invenio-app
$ git fetch inveniosoftware
```

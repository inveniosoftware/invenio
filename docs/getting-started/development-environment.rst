..
    This file is part of Invenio.
    Copyright (C) 2017-2020 CERN.

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

Visit `EditorConfig <https://editorconfig.org>`_ to see the list of supported editors.

Editors
~~~~~~~
Following editors (listed alphabetically) are used by our existing developers.
Don't hesitate to reach out on our Discord server, to ask for help for useful
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

Working with Git and GitHub
---------------------------
There are a couple of utilities that allow you to work more efficiently with
Git and GitHub.

CLI tools
~~~~~~~~~

- `GitHub CLI <https://cli.github.com/>`_: command-line tool to interact with GitHub. Note that this tool is independent from the git CLI.
- `Hub <https://hub.github.com>`_: command-line wrapper around git that makes it easier to work with GitHub by adding new commands.

Git aliases
~~~~~~~~~~~

Use `aliases <https://git-scm.com/book/en/v2/Git-Basics-Git-Aliases>`_ to type frequent
commands more efficiently. Note that your shell might offer more git aliases too, for
example `Oh My Zsh <https://ohmyz.sh/>`_ has the `git plugin <https://github.com/ohmyzsh/ohmyzsh/blob/master/plugins/git/git.plugin.zsh>`_
which among other things it will come with a few pre-configured aliases.

Debugging
---------

There are several tools for debugging, we will list here the ones which are editor agnostic:

- `ipdb <https://github.com/gotcha/ipdb>`_: this is a terminal debugger with features tab completion, syntax highlighting among others. Note that the debugging session is opened as the output of the running program.
- `wdb <https://github.com/Kozea/wdb>`_: web debugger with a client server architecture. The debugging session is opened in a web browser. Suitable for remote debugging and programs which do not allow to open an interactive shell session (i.e. Celery).

Python
------

- Manage versions: you can manage serveral Python versions installed locally using `pyenv <https://github.com/pyenv/pyenv>`_.
- Manage virtual environments: you can manage virtual environments using `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_.

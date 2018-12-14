..
    This file is part of Invenio.
    Copyright (C) 2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _build-a-module:

Build a module
==============

Invenio modules are independent, interchangeable components that add functionality.
A full invenio application consists of a set of modules, and can be customized easily by adding or
removing specific modules.
All modules have the same structure, which is defined in the
`cookiecutter-invenio-module <https://github.com/inveniosoftware/cookiecutter-invenio-module>`_
template.

Invenio module layout
---------------------

A simple module may have the following folder structure::

    invenio-foo/
        docs/
        examples/
        invenio_foo/
            templates/invenio_foo/
            __init__.py
            config.py
            ext.py
            version.py
            views.py
        tests/
        *.rst
        run-tests.sh
        setup.py

These files are described in the sections below.

\*.rst files
++++++++++++

All these files are used by people who want to know more about your module (mainly developers).

- ``README.rst`` is used to describe your module. You can see the short
  description written in the Cookiecutter here. You should update it with
  more details.
- ``AUTHORS.rst`` should list all contributors to this module.
- ``CHANGES.rst`` should be updated at every release and store the list of
  versions with the list of changes (changelog).
- ``CONTRIBUTING.rst`` presents the rules to contribute to your module.
- ``INSTALL.rst`` describes how to install your module.

setup.py
++++++++

First, there is the ``setup.py`` file, one of the most important: this file is
executed when you install your module with *pip*. If you open it, you can see
several parts.

On the top, the list of the requirements:

- For normal use.
- For development.
- For tests.

Depending on your needs, you can install only part of the requirements, or
everything (``pip install invenio-foo[all]``).

Then, in the ``setup()`` function, you can find the description of your module with
the values entered in cookiecutter. At the end, you can find the
``entrypoints`` section.

run-tests.sh
++++++++++++
This is used to run a list of tests locally, to make sure that your module works
as intended. It will generate the documentation, run *pytest* and any remaining
checks.

docs folder
+++++++++++
This folder contains the settings to generate documentation for your module,
along with files where you can write the documentation. When you run the
``run-tests.sh`` script, it will create the documentation in HTML files in a
sub-folder.

examples folder
+++++++++++++++
Here you can find a small example of how to use your module. You can test it,
follow the steps described in the :ref:`run-the-example-app` section.

tests folder
++++++++++++
Here are all the tests for your application, that will be run when
you execute the ``run-tests.sh`` script. If all these tests pass, you can
safely commit your work.

See `pytest-invenio <https://pytest-invenio.readthedocs.io/en/latest/>`_ for
how to structure your tests.

invenio_foo folder
++++++++++++++++++
This folder has the name of your module, in lower case with the dash changed
to an underscore. It contains the code of your module. You can add any code files
here, organized as you wish.

The files that already exist are standard, and are covered 
in the following sections. A rule of thumb is that if you need multiple
files for one action (for instance, 2 ``views``: one for the API and a standard
one), create a folder having the name of the file you want to split (here, a
``views`` folder with ``ui.py`` and ``api.py`` inside).

MANIFEST.in
>>>>>>>>>>>
This file lists all the files included in the sub-folders. It should
be updated before the first commit.

config.py
>>>>>>>>>
All configuration variables should be declared in this file.

ext.py
>>>>>>
This file contains a class that extends the Invenio application
with your module. It registers the module during the initialization of the application
and loads the default configuration from ``config.py``. 

version.py
>>>>>>>>>>
File containing the version of your module.

views.py
>>>>>>>>
Here you declare the views or endpoints you want to expose. By default, it creates a
simple view on the root end point that renders a template.

templates
>>>>>>>>>
All your Jinja templates should be stored in this folder. A Jinja template is an HTML file that can be modified according to some parameters.

static
>>>>>>
If your module contains JavaScript or CSS files, they should go in a folder called ``static``. Also, if you want to group them in bundles,
you should add a ``bundles.py`` file next to the ``static`` folder.

Module naming conventions
-------------------------

Invenio modules are standalone independent components that implement some
functionality used by the rest of the Invenio ecosystem. Modules provide API
to other modules and use API of other modules.

A module is usually called:

1. with plural noun, meaning "database (of things)", for example
   ``invenio-records``, ``invenio-tags``, ``invenio-annotations``,

2. with singular noun, meaning "worker (using things)", for example
   ``invenio-checker``, ``invenio-editor``.

A module may have split its user interface and REST API interface, for example
``invenio-records-ui`` and ``invenio-records-rest``, to clarify dependencies and
offer easy customisation.

To create a new module, make sure to have
`cookiecutter <https://cookiecutter.readthedocs.io/en/latest/installation.html>`_
installed and run:

.. code-block:: console

    $ cookiecutter gh:inveniosoftware/cookiecutter-invenio-module
    project_name [Invenio-FunGenerator]: Invenio-Foo
    project_shortname [invenio-foo]:
    package_name [invenio_foo]:
    github_repo [inveniosoftware/invenio-foo]:
    description [Invenio module that adds more fun to the platform.]:
    author_name [CERN]:
    author_email [info@inveniosoftware.org]:
    year [2018]:
    copyright_holder [CERN]:
    copyright_by_intergovernmental [True]:
    superproject [Invenio]:
    transifex_project [invenio-foo]:
    extension_class [InvenioFoo]:
    config_prefix [FOO]:

Integrating a new module to a full Invenio application
comes down to adding it as a dependency in the central ``setup.py``, an example of which can be
seen in `Invenio-App-ILS <https://github.com/inveniosoftware/invenio-app-ils/blob/master/setup.py>`_.

Next steps
----------

To learn more about the development process in Invenio, follow the next guide :ref:`developing-with-invenio`.
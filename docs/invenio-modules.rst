..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _invenio-module-layout:

Invenio module layout
=====================

This page summarizes the standard structure and naming conventions of a
module in Invenio v3.0. It serves as a reference point when developing
a new module or enhancing an existing one.

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
different parts.

On the top, the list of the requirements:

- for normal use
- for development
- for tests

Depending on your needs, you can install only part of the requirements, or
everything (``pip install invenio-foo[all]``).

Then, in the ``setup()`` function, you have the description of your module with
the values entered in the Cookiecutter. At the end, you can find the
``entrypoints`` section. For the moment, there is only the registration in the
Invenio application, and the translations.

MANIFEST.in
+++++++++++
This file lists all the files included in the sub-folders. This file should
be updated before the first commit. See the :ref:`install-run-and-test`
section.

run-tests.sh
++++++++++++
This is used to run a list of tests locally, to make sure that your module works
as intended. It will generate the documentation, run *pytest* and do other
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
follow the steps described in the :ref:`run-the-example-app` section

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
into an underscore. Here is the code of your module. You can add any code files
here, organized as you wish.

The files that already exist are kind of a standard, we are going through them
in the following sections. A rule of thumb is that if you need multiple
files for one action (for instance, 2 ``views``: one for the API and a standard
one), create a folder having the name of the file you want to split (here, a
``views`` folder with ``ui.py`` and ``api.py`` inside).

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
Here you declare the views or end points you want to expose. By default, it creates a
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
functionality used by the rest of the Invenio ecosystem. The modules provide API
to other modules and use API of other modules.

A module is usually called:

1. with plural noun, meaning "database (of things)", for example
   ``invenio-records``, ``invenio-tags``, ``invenio-annotations``,

2. with singular noun, meaning "worker (using things)", for example
   ``invenio-checker``, ``invenio-editor``.

A module may have split its user interface and REST API interface, for example
``invenio-records-ui`` and ``invenio-records-rest``, to clarify dependencies and
offer easy customisation.

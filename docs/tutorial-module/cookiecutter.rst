..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Scaffold new module
===================
The easiest way to create a new Invenio module is to use our provided
cookiecutter template to scaffold the new module.

First, you need to install Cookiecutter, which is available on PyPI (the
``-U`` option will upgrade it if it is already installed):

.. code-block:: console

    $ pip install -U cookiecutter

Now we will create the files for the module. A module is basically a folder
gathering all the files needed for its installation and execution. So, go where
you want the directory to be created, and run the command:

.. code-block:: console

    $ cookiecutter https://github.com/inveniosoftware/cookiecutter-invenio-module.git


This will first clone the template from git to your current directory. Then,
Cookiecutter will ask you questions about the module you want to create:

.. code-block:: console

    project_name [Invenio-FunGenerator]: Invenio-Unicorn
    project_shortname [invenio-unicorn]:
    package_name [invenio_unicorn]:
    github_repo [inveniosoftware/invenio-unicorn]:
    description [Invenio module that adds more fun to the platform.]:
    author_name [CERN]: Nice Unicorn
    author_email [info@inveniosoftware.org]: nice@unicorn.com
    year [2017]:
    copyright_holder [Nice Unicorn]:
    copyright_by_intergovernmental [True]: False
    superproject [Invenio]:
    transifex_project [invenio-unicorn]:
    extension_class [InvenioUnicorn]:
    config_prefix [UNICORN]:

A folder ``invenio-unicorn`` has been created, you can go inside and have a
look at all the generated files. Don't be scared about the number of files -
a lot of the files are standard files that follow best practices for any Python
package.

If you want further information about the created files, you can read the
:ref:`invenio-module-layout` section.

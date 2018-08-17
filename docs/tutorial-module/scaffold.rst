..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Scaffold new module
===================
The easiest way to create a new Invenio module is to use our provided
`Cookiecutter <https://cookiecutter.readthedocs.io/en/latest/installation.html>`_
template to scaffold the new module.

First, make sure you have Cookiecutter installed as per :ref:`bootstrap`.

Now we will create the files for the module. A module is basically a folder
gathering all the files needed for its installation and execution. So, go where
you want the directory to be created, and run the command:

.. code-block:: console

    $ cookiecutter gh:inveniosoftware/cookiecutter-invenio-module


This will first clone the template from git to your current directory. Then,
Cookiecutter will ask you questions about the module you want to create:

.. code-block:: console

    project_name [Invenio-FunGenerator]: Invenio-Unicorn
    project_shortname [invenio-unicorn]:
    package_name [invenio_unicorn]:
    github_repo [inveniosoftware/invenio-unicorn]:
    description [Invenio module that adds more fun to the platform.]:
    author_name [Nice Unicorn]:
    author_email [info@inveniosoftware.org]: nice@unicorn.com
    year [2017]:
    copyright_holder [Nice Unicorn]:
    copyright_by_intergovernmental [True]:
    superproject [Invenio]:
    transifex_project [invenio-unicorn]:
    extension_class [InvenioUnicorn]:
    config_prefix [UNICORN]:


The directory ``invenio-unicorn`` has been created containing the generated files.
All modules follow the same layout which
is described in the :ref:`invenio-module-layout` section.

Once you have a grasp on the module layout, you can continue to the
:ref:`install-run-and-test` section, to learn how to install your new module.

..
    This file is part of Invenio.
    Copyright (C) 2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _build-a-module:

Build a module
==============

Invenio modules are independent, interchangeable components that add functionalities.
Each module exposes its own APIs and uses APIs of other modules.
A full invenio application consists of a set of modules, and can be easily customized by adding or
removing specific modules.


A module is usually called:

1. with plural noun, meaning "database (of things)", for example
   ``invenio-records``, ``invenio-tags``, ``invenio-annotations``,

2. with singular noun, meaning "worker (using things)", for example
   ``invenio-checker``, ``invenio-editor``.

The user interface and the REST API interface of a module may be split into separate modules,
for example ``invenio-records-ui`` and ``invenio-records-rest``, to clarify dependencies and
offer an easier customization.


All modules have the same structure, which is defined in the
`cookiecutter-invenio-module <https://github.com/inveniosoftware/cookiecutter-invenio-module>`_
template.

First steps
-----------

To create a new module, make sure you have
`cookiecutter <https://cookiecutter.readthedocs.io/en/latest/installation.html>`_
installed and run the following command:

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


The newly scaffolded module will have the following folder structure::

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
Here you can find a small example of how to use your module. You can test it
following the steps described in the :ref:`run-the-example-app` section.

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

.. _install-module:

Install a module
----------------

First of all, create a virtualenv for the module:

.. code-block:: console

    $ mkvirtualenv my_venv

Installing the module is very easy, you just need to go to its root directory
and `pip install` it:

.. code-block:: console

    (my_venv)$ cd invenio-foo/
    (my_venv)$ pip install --editable .[all]

Some explanations about the command:

- The ``--editable`` option is used for development. It means that if you change the
  files in the module, you won't have to reinstall it to see the changes. In a
  production environment, this option shouldn't be used.
- The ``.`` is in fact the path to your module. As we are in the root folder of
  the module, we can just say *here*, which is what the dot means.
- The ``[all]`` after the dot means we want to install all dependencies, which
  is common when developing. Depending on your use of the module, you can
  install only parts of it:

    - The default (nothing after the dot) installs the minimum to make the
      module run.
    - ``[tests]`` installs the requirements to test the module.
    - ``[docs]`` installs the requirements to build the documentation.
    - Some modules have extra options.

If you need multiple options, you can chain them: ``[tests,docs]``.


.. _run-the-tests:

Run the tests
-------------
In order to run the tests, you need to have a valid git repository. The
following steps need to be run only once. Go into the root folder of the module:

.. code-block:: console

    (my_venv)$ git init
    (my_venv)$ git add --all
    (my_venv)$ check-manifest --update

What we have done:

- Change the folder into a git repository, so it can record the changes made to
  the files.
- Add all the files to this repository.
- Update the file ``MANIFEST.in`` (this file controls which files are included
  in your Python package when it is created and installed).

Now, we are able to run the tests:

.. code-block:: console

    (my_venv)$ ./run-tests.sh


Build the documentation
-----------------------
The documentation can be built with the ``run-tests.sh`` script, but you need
to have the package installed with its *tests* requirements. If you just want
to build the documentation, you will only need the *docs* requirements (see
the :ref:`install-module` section above). Make sure you are at the root directory
of the module and run:

.. code-block:: console

    (my_venv)$ python setup.py build_sphinx

Open ``docs/_build/html/index.html`` in the browser and voilà, the documentation is
there.

.. _run-the-example-app:

Run the example application
---------------------------
The example application is a minimal application that presents the features of your
module. The example application is useful during development for testing.
By default, it simply prints a welcome page.
To try it, go into the ``examples`` folder and run:

.. code-block:: console

    (my_venv)$ ./app-setup.sh
    (my_venv)$ ./app-fixtures.sh
    (my_venv)$ export FLASK_APP=app.py FLASK_DEBUG=1
    (my_venv)$ flask run

You can now open a browser and go to the URL http://localhost:5000/ where you
should be able to see a welcome page.

To clean the server, run the ``./app-teardown.sh`` script after stopping the
server.

Publishing on GitHub
--------------------
Before going further in the tutorial, we can publish your repository to GitHub.
This allows to integrate a continuous integration system such as TravisCI and allows an
easy publishing of your module to PyPI afterwards.

First, create an empty repository in your GitHub account. Be sure not to
generate any *.gitignore* or *README* files, as our code already has them. If
you don't have a GitHub account, you can skip this step, it is only necessary
if you plan to publish your module on PyPI.

Now, go into the root directory of your module, and run:

.. code-block:: console

    $ git remote add origin URL-OF-YOUR-GITHUB-REPO

We can commit and push the generated files:

.. code-block:: console

    $ git commit -am "Initial module structure"
    $ git push --set-upstream origin master

Finally, we create a new branch to develop on it.

.. code-block:: console

    $ git checkout -b dev

Use the module in your application
----------------------------------

Integrating a new module to a full Invenio application comes down to adding it as a dependency
in the central ``Pipfile``. In order to do that, you should have published your module on GitHub and
run the following command from the root folder of your Invenio application:

.. code-block:: console

    $ pipenv install URL-OF-YOUR-GITHUB-REPO

``pipenv`` will update the ``Pipfile`` and install your module in the virtual enviroment of your application.

If your module has been released on PyPI, you can install it in your application by running the following
command:

.. code-block:: console

    $ pipenv install invenio-foo

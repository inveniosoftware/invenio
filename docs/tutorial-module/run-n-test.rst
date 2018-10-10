..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _install-run-and-test:

Install, run, test, document and publish
========================================
In this section, we are going to see how to install the module we just
scaffolded, run the tests, run the example application and build the
documentation.

Before that, we need to **stop** any running Invenio instance.

Install the module
------------------
First, create a virtualenv for the module:

.. code-block:: bash

    $ mkvirtualenv my-module-venv

Installing the module is very easy, you just need to go to its root directory
and `pip install` it:

.. code-block:: bash

    (my-module-venv)$ cd invenio-unicorn/
    (my-module-venv)$ pip install --editable .[all]

Some explanations about the command:

- the ``--editable`` option is used for development. It means that if you change the
  files in the module, you won't have to reinstall it to see the changes. In a
  production environment, this option shouldn't be used.
- the ``.`` is in fact the path to your module. As we are in the root folder of
  the module, we can just say *here*, which is what the dot means.
- the ``[all]`` after the dot means we want to install all dependencies, which
  is common when developing. Depending on your use of the module, you can
  install only parts of it:

    - the default (nothing after the dot) installs the minimum to make the
      module run.
    - ``[tests]`` installs the requirements to test the module.
    - ``[docs]`` installs the requirements to build the documentation.
    - some modules have extra options.

You can chain them: ``[tests,docs]``.

.. _run-the-tests:

Run the tests
-------------
In order to run the tests, you need to have a valid git repository. The
following step needs to be run only once. Go in the root folder of the module:

.. code-block:: bash

    (my-module-venv)$ git init
    (my-module-venv)$ git add --all
    (my-module-venv)$ check-manifest --update

What we have done:

- change the folder into a git repository, so it can record the changes made to
  the files.
- add all the files to this repository.
- update the file ``MANIFEST.in`` (this file controls which files are included
  in your Python package when it is created and installed).

Now, we are able to run the tests:

.. code-block:: bash

    (my-module-venv)$ ./run-tests.sh

Everything should pass as we didn't change any files yet.

.. _run-the-example-app:

Run the example application
---------------------------
The example application is a small app that presents the features of your
module. The example application is useful during e.g. development to have a
minimal application to test your module with. By default, it simply prints a
welcome page. To try it, go into the ``examples`` folder and run:

.. code-block:: console

    (my-module-venv)$ ./app-setup.sh
    (my-module-venv)$ ./app-fixtures.sh
    (my-module-venv)$ export FLASK_APP=app.py FLASK_DEBUG=1
    (my-module-venv)$ flask run

You can now open a browser and go to the URL http://localhost:5000/ where you
should be able to see a welcome page.

To clean the server, run the ``./app-teardown.sh`` script after killing the
server.

Build the documentation
-----------------------
The documentation can be built with the ``run-tests.sh`` script, but you need
to have installed *tests* requirements, and to run the tests. If you just want to build the
documentation, you will only need the *docs* requirements (see the install
section above). Make sure you are back at the root directory
of the module and run:

.. code-block:: console

    (my-module-venv)$ python setup.py build_sphinx

Open ``docs/_build/html/index.html`` in browser and voilà, the documentation is
there.

Publishing on GitHub
--------------------
Before going further in the tutorial, we can publish your repository to GitHub.
This allows to integrate e.g. TravisCI continuous integration system and have
easy publishing of your module to PyPI afterwards.

First, create an empty repository in your GitHub account. Be sure to not
generate any *.gitignore* or *README* files, as our code already has them. If
you don't have a GitHub account, you can skip this step, it is only necessary
if you plan to publish your module on PyPI.

Now, go into the root directory of your module, and run

.. code-block:: bash

    (my-module-venv)$ git remote add origin URL-OF-YOUR-GITHUB-REPO

Now, we can commit and push the generated files:

.. code-block:: bash

    (my-module-venv)$ git commit -am "Initial module structure"
    (my-module-venv)$ git push --set-upstream origin master

Finally, we create a new branch to develop on it

.. code-block:: bash

    (my-module-venv)$ git checkout -b dev

Next Step
---------
In the above steps we have seen how to do the basic operations with our module.
To add some more functionality to it, the following guide shows the steps to create
a view that will create records given some data: :ref:`develop`.

..
    This file is part of Invenio.
    Copyright (C) 2015-2019 CERN.
    Copyright (C) 2018 Northwestern University, Feinberg School of Medicine, Galter Health Sciences Library.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _final-steps:

Final steps
===========

You can now address the warnings displayed after completing the
``cookiecutter`` initialisation procedure. You can run the following
command to find all the ``TODO``:

.. code-block:: console

    $ cd my-site/
    $ grep --color=always --recursive --context=3 --line-number TODO .

Let's address them one by one:

1. Python packages require a ``MANIFEST.in`` which specifies what files are
   part of your application package. You can update the existing file by running
   the following commands in your site directory:

   .. code-block:: console

        $ git init
        $ git add --all
        $ pipenv run check-manifest --update

2. Translations configuration (``.tx/config``). You can generate
   the necessary files to allow localization of the instance in different
   languages via the `Transifex platform <https://www.transifex.com/>`_:

   .. code-block:: console

        # if you have activated the virtual environment skip `pipenv shell`
        $ pipenv shell
        (my-site)$ python setup.py extract_messages
        (my-site)$ python setup.py init_catalog -l en
        (my-site)$ python setup.py compile_catalog

   **Transifex**

   Make sure you edit ``.tx/config`` and sign-up for Transifex before trying
   below steps.

   Install the transifex-client

   .. code-block:: console

        $ pipenv install transifex-client

   Push source (.pot) and translations (.po) to Transifex:

   .. code-block:: console

        $ pipenv run tx push --skip --translations

   Pull translations for a single language from Transifex

   .. code-block:: console

        $ pipenv run tx pull --language en

REST APIs permissions
^^^^^^^^^^^^^^^^^^^^^
By default, a new Invenio instance has no permissions configured. This means that
any user can perform operations to records such as read, update, create and delete.
You can check the :ref:`managing-access` documentation to learn how to configure
permissions in Invenio.

Testing
^^^^^^^
Tests are available in the `tests` folder. You can add your own tests and then run
run linting checks and tests using the script ``run-tests.sh``:

.. code-block:: console

    $ ./run-tests.sh
    # ...or to run individual tests
    $ pipenv run pytest tests/test_version.py

Documentation
^^^^^^^^^^^^^
A basic documentation structure and configuration using ``Sphinx`` is available
in the ``docs`` folder. You build it to generate the final ``HTML`` files by running:

.. code-block:: console

    $ pipenv run python setup.py build_sphinx

Then, open the file ``docs/_build/html/index.html`` in your browser to see the generated
documentation.

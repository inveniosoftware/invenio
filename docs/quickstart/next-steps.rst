..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.
    Copyright (C) 2018 Northwestern University, Feinberg School of Medicine, Galter Health Sciences Library.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _next-steps:

Next Steps
==========

Although we can run and interact with the instance, we're not quite there yet
in terms of having a proper Python package that's ready to be tested and
deployed to a production environment.

You may have noticed that after running the ``cookiecutter`` command for the
instance and the data model, there was a note for checking out some of the
TODOs. You can run the following command in the code repository directory
to see a summary of the TODOs again:

.. code-block:: console

  $ grep --color=always --recursive --context=3 --line-number TODO .

Let's have a look at some of them one-by-one and explain what they are for:

1. Python packages require a ``MANIFEST.in`` which specifies what files are
   part of the distributed package. You can update the existing file by running
   the following commands in your site directory:

   .. code-block:: console

      (my-site)$ git init
      (my-site)$ git add --all
      (my-site)$ check-manifest --update

2. Translations configuration (``.tx/config``): You might also want to generate
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

      (my-site)$ pipenv install transifex-client

   Push source (.pot) and translations (.po) to Transifex:

   .. code-block:: console

      (my-site)$ tx push --skip --translations

   Pull translations for a single language from Transifex

   .. code-block:: console

      (my-site)$ tx pull --language en

3. REST API permissions: By default your Invenio instance have no permissions
   enabled, which means that any user will be allowed to perform any operation
   (read, update, create and delete) over the records. Check
   :ref:`managing-access` for information on how to adapt the permissions to
   your needs.

Testing
^^^^^^^
In order to run tests for the instance, you can run:

.. code-block:: shell

  # run all the tests...
  (my-site)$ ./run-tests.sh
  # ...or to run individual tests
  (my-site)$ pytest tests/test_version.py

Documentation
^^^^^^^^^^^^^

In order to build and preview the instance's documentation, you can run the
`python setup.py build_sphinx` command:

.. code-block:: shell

  (my-site)$ python setup.py build_sphinx

Open up ``docs/_build/html/index.html`` in your browser to see the
documentation.

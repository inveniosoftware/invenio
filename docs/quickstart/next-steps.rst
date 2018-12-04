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
TODOs. You can run the following command in each code repository directory
to see a summary of the TODOs again:

.. code-block:: console

  $ grep --color=always --recursive --context=3 --line-number TODO .

Let's have a look at some of them one-by-one and explain what they are for:

# we may not need 1. if we use pipenv

2. Python packages require a ``MANIFEST.in`` which specifies what files are
   part of the distributed package. You can update the existing file by running
   the following commands:

   .. code-block:: console

      $ git init
      $ git add --all
      $ pipenv install --editable .[all]
      $ pipenv shell  # activate the virtual environment
      (my-site-<random-hash>)$ check-manifest --update

3. Translations configuration (``.tx/config``): You might also want to generate
   the necessary files to allow localization of the instance in different
   languages via the `Transifex platform <https://www.transifex.com/>`_:

   .. code-block:: console

      # if you have activated the virtual environment skip `pipenv shell`
      $ pipenv shell
      (my-site-<random-hash>)$ python setup.py extract_messages
      (my-site-<random-hash>)$ python setup.py init_catalog -l en
      (my-site-<random-hash>)$ python setup.py compile_catalog

   Ensure project has been created on Transifex under the my-repository
   organisation.

   Install the transifex-client

   .. code-block:: console

      (my-site-<random-hash>)$ pipenv install transifex-client

   Push source (.pot) and translations (.po) to Transifex:

   .. code-block:: console

      # getting: tx ERROR: not enough values to unpack (expected 2, got 1)
      (my-site-<random-hash>)$ tx push --skip --translations

   Pull translations for a single language from Transifex

   .. code-block:: console

      # same error here
      (my-site-<random-hash>)$ tx pull --language en

Testing
^^^^^^^

In order to run tests for the instance, you can run:

.. code-block:: shell

  # Install testing dependencies
  # The following makes sure you have the tests dependencies installed
  # if you already installed the instance via .[all] you can skip this install
  $ pipenv install --editable .[tests]
  # if you have activated the virtual environment skip `pipenv shell`
  $ pipenv shell
  (my-site-<random-hash>)$ ./run-tests.sh  # will run all the tests...
  # ...or to run individual tests
  # ERROR: not found: /home/dinos/invenio/my-site/tests/ui/test_views.py::test_ping
  (my-site-<random-hash>)$ pytest tests/ui/test_views.py

Documentation
^^^^^^^^^^^^^

In order to build and preview the instance's documentation, you can run the
`setup.py build_sphinx` command:

.. code-block:: shell

  # The following makes sure you have the docs dependencies installed
  # if you already installed the instance via .[all] you can skip this install
  $ pipenv install --editable .[docs]
  # if you have activated the virtual environment skip `pipenv shell`
  $ pipenv shell
  (my-site-<random-hash>)$ python setup.py build_sphinx

Open up ``docs/_build/html/index.html`` in your browser to see the documentation.

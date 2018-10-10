..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Publish on GitHub
=================

Now that we finished the development, we want to push the changes to GitHub.

Commit the code
---------------
To do so, we will first list our changes and add them to our local git repository:

.. code-block:: console

    (my-module-venv)$ git status
    # shows all the files that have been modified
    (my-module-venv)$ git add .
    # adds all the modifications

Let's test our changes before we publish them. See :ref:`run-the-tests` for
more information.

.. code-block:: console

    (my-module-venv)$ ./run-tests.sh

If it complains about the manifest, it is because we added new files, but we
didn't register them into the ``MANIFEST.in`` file, so let's do so:

.. code-block:: console

    (my-module-venv)$ check-manifest -u

Push the code
-------------
Once all the tests are passing, we can push our code. As we were developing on
a branch created locally, we need to push the branch on GitHub:

.. code-block:: console

    (my-module-venv)$ git commit -am "New form, views and templates"
    (my-module-venv)$ git push --set-upstream origin dev

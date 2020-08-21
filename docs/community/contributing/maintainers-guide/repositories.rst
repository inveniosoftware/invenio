..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Setting up a repository
=======================

First, reach out to the Invenio architects and agree on scope and name of
the new repository. The architects are their to help you and to ensure that
the module fits into the larger Invenio ecosystem.

New repositories can be created in either the
`inveniosoftware <https://github.com/inveniosoftware>`_ or the
`inveniosoftware-contrib <https://github.com/inveniosoftware-contrib>`_  GitHub
organisations. Repositories in inveniosoftware must be managed according to the
contributor, style and maintainers guides. Repositories in
inveniosoftware-contrib are free to apply any rules they like.

GitHub
------
Once scope and name has been agreed upon, the product manager will create the
repository which will be setup in the following manner:

* **Settings**: The repository settings must be set in the following manner:
    - Description and homepage (link to readthedocs.io) *must* be set.
    - Issues *must* be enabled.
    - Wiki *should* be disabled (except in rare circumstances such as the main
      Invenio repository).
    - Merge button: *must* disallow merge commits, allow squash and allow
      rebase merging.
* **Teams**: A team named ``<repository-name>-maintainers`` *must* exists with
  all repository maintainers as members and with ``push`` permission on the
  repository.
* **Branch protection**: The default branch, all maintenance branches and
  optionally some feature branches must have branch protection enabled in the
  following manner:

  * Pull requests reviews *must not* be required. Enabling this feature
    prevents maintainers from merging their own PRs without approval from
    another reviewer. This is not a carte blanche for maintainers to merge
    their own PRs without reviews, but empowers them to get the job done
    when really need!
  * Status checks for TravisCI *must* be required. Status checks for
    Coveralls, QuantifiedCode and other status checks *must not* be
    required. The maintainer is responsible for manually verifing these
    checks.
  * Branches *must* be up to date before merging.
  * Push access *must* be restricted to the repository maintainers team.

* **Repository files**: A ``MAINTAINERS`` file with list of GitHub usernames
  *must* be present in the repository.

The repository setup and manage is fully automated via the
`MetaInvenio <https://github.com/inveniosoftware/metainvenio>`_ scripts.

Other services
--------------
We use the following other external services:

- `TravisCI <http://travis-ci.org>`_ for continues integration testing.
- `Coveralls <https://coveralls.io>`_ to test coverage tracking.
- `QuantifiedCode <https://www.quantifiedcode.com>`_ for Python static
  analysis.
- `Python Package Index <https://pypi.org>`_ for releasing Python packages.
- `NPM <https://npmjs.com>`_ for releasing JavaScript packags.
- `ReadTheDocs <https://readthedocs.org>`_ for hosting documentation.
- `Transifex <https://www.transifex.com>`_ for translating Invenio.

Bootstrapping
-------------
New repositories should in most cases be bootstrapped using one of our
templates. These templates encodes many best practices, setups above external
services correctly and ensure a coherent package structure throughout the
Invenio project.

Python
~~~~~~
Python-based repositories must be bootstraped using the
`cookiecutter-invenio-module
<https://github.com/inveniosoftware/cookiecutter-invenio-module>`_.

JavaScript
~~~~~~~~~~
JavaScript-based repositories must be boostraped using the
`generator-invenio-js-module
<https://github.com/inveniosoftware/generator-invenio-js-module/>`_.

..
    This file is part of Invenio.
    Copyright (C) 2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Releasing
=========

The most common releases are:

- **Major/Minor-level release** - Often these releases add significant new
  features and need to go through extensive testing.
- **Patch-level release** - Often these releases fix security issues or
  important bugs.

For major/minor-level releases, you'll mostly be working only with the
``master``-branch and only make a single PyPI release. For patch-level
releases you'll often be working with multiple maintenance branches and make
several PyPI releases for all currently maintained versions of Invenio.

Depending on the package that you are releasing, you will have to follow
a different procedure. You might have to release:

- One of the Python (e.g. `Invenio-DB <https://pypi.org/project/invenio-db/>`_)
  or JavaScript/React (e.g. `React-SearchKit <https://www.npmjs.com/package/react-searchkit>`_)
  modules (happening rather often).
- The Invenio framework, the `invenio <https://pypi.org/project/invenio/>`_ package (happening less often).

Before you start
----------------
Prior to preparing a new Invenio release, please ensure you have the latest
changes in your local environment for the maintenance branches and ``master``:

1. Check that all relevant PRs have been merged. For the ``invenio`` package,
   check that all relevant Invenio modules have been released.
2. Fetch latest changes:

   - ``git fetch inveniosoftware``

3. Checkout maintenance or master branch:

   - ``git checkout maint-<major>.<minor>``

4. Merge or reset to latest changes:

   - ``git merge --ff-only inveniosoftware/maint-<major>.<minor>``
   - *or* use git reset (**warning** use with caution) ``git reset --hard inveniosoftware/maint-<major>.<minor>``

While above is not strictly necessary, it avoids situations where you local
and GitHub branches have diverged.

Patch-level release
-------------------
Most of the time, patch-level releases are not necessary for the main
``invenio`` package, since by patch-level releases of the underlying
modules are automatically picked up: the dependencies upper bounds are
normally allowing the installation of patch-level releases.
For example:

.. code-block:: python

    'invenio-records-rest>=1.7.1,<1.8.0',
    'invenio-records-ui>=1.2.0a1,<1.3.0',

Most of the Invenio modules have maintenance branches for previous
major/minor releases. They are normally named ``maint-<version>``,
e.g. `Invenio-Records-Rest maint-1.6 <https://github.com/inveniosoftware/invenio-records-rest/tree/maint-1.6>`_.

With patch-level releases, you'll often make multiple releases and work with
multiple maintenance branches. For instance, you might have to merge a
bug fix to ``master``, but also to ``maint-3.1`` and to ``maint-3.2``.

Major/minor-level release
-------------------------
When releasing a major/minor version, you will have to take extra care to the
compatibility with the current released ``invenio`` version, by checking
the upper bounds defined for this module in the ``invenio`` releases.

The most probable scenario is that for a given ``invenio`` release,
e.g. ``3.3``, the upper bound for an Invenio module ``foo``
(with current latest release ``1.2.6``) is set to ``invenio-foo<1.3.0``.
A new minor release ``1.3.0`` of this module will not affect
``invenio 3.3``.

.. warning::
    If this is not the case, you will have to make sure that the new release
    of the module ``foo`` will not introduce backward incompatible changes,
    because it will be installed by ``invenio 3.3``, potentially breaking
    existing Invenio installations.

Module release
--------------

How to release an Invenio module.

**Python module**

1. Make sure that all relevant PRs have been merged to ``master``.
2. Make sure that the build on ``master`` branch is passing.
3. Prepare release notes in

   - Update the ``CHANGE.rst`` file, making sure that you describe changes,
     highlighting backward incompatible ones, and that the release date
     is correct. Pay attention how you write, keep consistency with previous
     sentences forms.

4. Bump version in ``version.py`` (follow semantic versioning).
5. If the module is changing from alpha/beta to official release remember to
   modify the classifiers in the setup.py according to `PyPi classifiers <https://pypi.org/classifiers/>`_.
6. Create a release commit (message pattern:
   ``release: v<major>.<minor>.<patch>``).
7. Create tag and push release:

   - ``git tag v<major>.<minor>.<patch>``
   - ``git push inveniosoftware master v<major>.<minor>.<patch>``

8. Regularly check ``Travis`` and ``PyPI`` to ensure the release went through.

**JavaScript/React module**

1. Make sure that all relevant PRs have been merged to ``master``.
2. Make sure that the build on ``master`` branch is passing.
3. Prepare release notes in

   - Update the ``CHANGE.md`` file, making sure that you describe changes,
     highlighting backward incompatible ones, and that the release date
     is correct. Pay attention how you write, keep consistency with previous
     sentences forms.

4. Bump version in ``package.json`` (follow semantic versioning).
5. Regenerate the ``package-lock.json``:

   - ``rm package-lock.json``
   - ``npm install``

6. Create a release commit (message pattern:
   ``release: v<major>.<minor>.<patch>``).
7. Create tag and push release:

   - ``git tag v<major>.<minor>.<patch>``
   - ``git push inveniosoftware master v<major>.<minor>.<patch>``

8. Regularly check ``Travis`` and ``NpmJS`` to ensure the release went through.

**Patch-level releases on multiple branches**

When you need to create new releases in multiple branches, for example
several ``maint`` releases (e.g. a bugfix affecting multiple releases),
you will have to do the extra step of "copying" the changes and applying
them to multiple branches to make a release.

After the procedure described above for the ``master`` branch, below
the procedure for a ``maint`` branch:

1. Checkout the ``maint`` branch and create a new release branch:

   - ``git checkout maint-<major>.<minor>``
   - ``git checkout -b rel-v<major>.<minor>.<patch>``

2. Cherry-pick (yes, cherry-pick :)) the commits that you need and resolve any conflict:

   - ``git cherry-pick <commit id>``

3. Run tests.
4. Create a new commit with updated ``changes`` file and bumped version,
   as described above in step 3 of Python or JavaScript module release.
5. Issue a pull request against the **maintenance branch** (
   ``maint-<major>.<minor>``).
6. If Travis fails:

   - Fix issue and **ensure head commit is the release commit** (i.e. rebase if
     necessary).

7. Merge, tag and push release:

   - ``git checkout maint-<major>.<minor>``
   - ``git merge --ff-only rel-v<major>.<minor>.<patch>``
   - ``git tag v<major>.<minor>.<patch>``
   - ``git push inveniosoftware maint-<major>.<minor> v<major>.<minor>.<patch>``

Invenio release
---------------

The pre-requirement necessary to release Invenio is that all the features in
the various Invenio modules needed for the release have been merged and
released. Then:

1. Update the ``setup.py``:

   - Review all modules lower and upper bounds and adjust them as needed.

2. Documentation:

   - Review documentation and make sure new features or breaking changes are
     documented, to help users when upgrading.

3. Prepare release notes (`see example <https://github.com/inveniosoftware/invenio/commit/f4d0aa5ac78d76228fe86754eeb3bbfe81a1854f>`_):

   - In ``docs/releases/``, copy an existing patch-level or minor
     release notes (e.g. ``docs/releases/v3.1.2.rst``).
   - Edit release notes.
   - Include the new release notes into ``docs/releases/index.rst``.
   - Check the "Maintenance policy", e.g. is the version correct?
     (`example <https://github.com/inveniosoftware/invenio/commit/edb863d2f5228fb158c090a69c2db7c3385b6ba3>`_).

4. Create a release commit (message pattern:
   ``release: v<major>.<minor>.<patch>``).
5. Create tag and push release:

   - ``git tag v<major>.<minor>.<patch>``
   - ``git push inveniosoftware master v<major>.<minor>.<patch>``

6. Regularly check ``Travis`` and ``PyPI`` to ensure the release went through.

Manual releases
---------------

When the process of releasing fails for some reasons, you might want to
manually publish the new version of a package.

**PyPI**

You can manually reproduce the publishing process done by ``Travis`` by doing:

1. Activate your virtualenv for the package that you want to release.
2. Generate the different distributions:

   - ``python setup.py compile_catalog sdist bdist_wheel``

   .. note::
       ``compile_catalog`` is an optional argument, only valid if your module include translation files.
3. Install the tool to upload releases to PyPI:

   - ``pip install twine wheel``

4. Publish:

   - ``twine upload dist/*``. The command will ask for username and password. `Invenio architects <https://github.com/orgs/inveniosoftware/teams/architects>`_ should have the credentials.

   .. warning::
       The wildcard will upload any file that are present in the folder. Make sure you build the package from a clean state
       to avoid old build's files appearing in the released package. E.g. ``rm -rf compile_catalog sdist bdist_wheel``
       before building the package.

   .. note::
       If it is your first time releasing in PyPI, or you are not sure if the release is correct, you can test it in https://test.pypi.org/. See related `documentation
       <https://twine.readthedocs.io/en/latest/#using-twine>`_.

**NpmJS**

Manual release on ``NpmJS`` is not only needed in case of failure, but also
when creating a totally new package, never released yet.

1. Make sure that you have an updated version of the
   `npm <https://www.npmjs.com/get-npm>`_ client installed in your machine.
2. Login on ``NpmJS``:

   - ``npm login``: you will need ``inveniosoftware`` username and password.
     `Invenio architects <https://github.com/orgs/inveniosoftware/teams/architects>`_ should have the credentials.

3. Optionally, verify the package before releasing:

   - ``npm pack``: this will create the final archive that will be
     published on ``NpmJS`` in case you want to check its content.

4. Understand if the package that you are publising is
   ``scoped`` (``@inveniosoftware``) or not. For example, ``react-searchkit``
   is not scoped, but ``@inveniosoftware/react-invenio-app-ils`` is scoped.
5. Publish:

   - `not scoped`: ``npm publish --dry-run`` to double check that everything
     is ok, then ``npm publish``.
   - `scoped`: you need to add the ``access`` param to publish it as public,
     otherwise by default, it will be ``restricted``.
     Run ``npm publish --access public --dry-run`` to double check that
     everything is ok, then ``npm publish --access public``.

Announcing release
==================

You should announce a new Invenio release in the following channels:

- `Invenio-Talk Announcement <https://invenio-talk.web.cern.ch/t/invenio-v3-2-released/62/3>`_
- Chatroom
- `Blog post <https://inveniosoftware.org/blog/invenio-v33-released/>`_

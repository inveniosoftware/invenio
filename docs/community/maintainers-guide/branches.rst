..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Understanding branches
======================

Master branch
-------------
The ``master`` branch is the default branch in all repositories and the
branches where all new features are being developed. The code in ``master`` is
reviewed and verified, so that it should  be possible to make a new release out
of this branch almost at any given point  in time.

We strive to always make backward compatible changes. When this is not possible
features should be deprecated (see :ref:`deprecating`).

Only architects and maintainers can merge code into the master branch.

Tags
----
Each release of a new version of a package is tagged according to the pattern
``v<major>.<minor>.<patch>``.

Maintenance branches
--------------------
Maintenance branches are created when we need to release a bug or security fix
and we cannot use the master branch because as it would break backward
compatibility of the package.

The maintenance branches are named according to the pattern
``maint-<major.minor>`` (e.g. ``maint-1.2``). The branch is forked from latest
tag in that specific version series. After fixes are merged into the
maintenance branch, the maintenance branches are merged upwards through newer
maintenance branches and finally into master.

Bug and security fixes should be applied to the earliest supported Invenio
version. Like the master branch, only architects and maintainers can merge
code into the maintenance branches.

Feature branches
----------------
Feature branches can be created by any developer/contributor and are useful
to collaborate on larger chunks of work and to expose your work early on.

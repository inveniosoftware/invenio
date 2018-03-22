..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Making releases
===============

.. _cross-check-ci-green-lights:

1. **Cross-check CI green lights.** Are all Travis builds green? Is nightly
   Jenkins build green?

.. _cross-check-read-the-docs-documentation-builds:

2. **Cross-check Read The Docs documentation builds.** Are docs building fine?
   Is this check done as part of the continuous integration? If not, add it.

.. _cross-check-demo-site-builds:

3. **Cross-check demo site builds.** Is demo site working?

.. _check-author-list:

5. **Check author list.** Are all committers listed in AUTHORS file? Use
   ``kwalitee check authors``. Add newcomers. Is this check done as part of the
   continuous integration? If not, add it.

.. _update-i18n-message-catalogs:

6. **Update I18N message catalogs.**

.. _update_version_number:

7. **Update version number.** Stick to `semantic versioning
   <http://semver.org/>`_.

.. _generate-release-notes:

8. **Generate release notes.** Use `kwalitee prepare release v1.1.0..` to
   generate release notes. Use empty commits with "AMENDS" to amend wrong past
   messages before releasing.

.. _tag-it-push-it-:

10. **Tag it. Push it.** Sign the tag with your GnuPG key. Push it to PyPI. Is
    the PyPI deployment done automatically as part of the continuous
    integration? If not, add it.

.. _bump-it:

11. **Bump it.** Don't forget the issue the pull request with a post-release
    version bump. Use ``.devYYYYMMDD`` suffix.

.. This file is part of Invenio
   Copyright (C) 2015, 2016 CERN.

   Invenio is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   Invenio is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with Invenio; if not, write to the Free Software Foundation, Inc.,
   59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

===========
 Releasing
===========

::

    The old repository
    A tag jumps in
    Plop
       —-after Matsuo Basho (1644-1694)

Releasing principles
====================

.. _cross-check-ci-green-lights:

1. **Cross-check CI green lights.** Are all Travis builds green? Is nightly
   Jenkins build green?

.. _cross-check-read-the-docs-documentation-builds:

2. **Cross-check Read The Docs documentation builds.** Are docs building fine?
   Is this check done as part of the continuous integration? If not, add it.

.. _cross-check-demo-site-builds:

3. **Cross-check demo site builds.** Is demo site working?

.. _check-manifest:

4. **check-manifest** Are all files included in the release? Is this check done
   as part of the continuous integration? If not, add it.

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

.. _push-pre-release-to-testpypi:

9. **Push a pre-release to testpypi.** Try a test install from there.

.. _tag-it-push-it-:

10. **Tag it. Push it.** Sign the tag with your GnuPG key. Push it to PyPI. Is
    the PyPI deployment done automatically as part of the continuous
    integration? If not, add it.

.. _bump-it:

11. **Bump it.** Don't forget the issue the pull request with a post-release
    version bump. Use ``.devYYYYMMDD`` suffix.

.. _add-release-notes-on-github-tweet-it-post-it:

12. **Add release notes on GitHub. Tweet it. Post it.** Make publicity for
    production-ready releases. This is not automated yet.

.. _structured-release-notes:

Structured release notes
========================

The release notes are prepared from the commit log messages that should include
the following labels:

+--------------+--------------------------+
| commit label | release notes section    |
+==============+==========================+
| SECURITY     | Security fixes           |
+--------------+--------------------------+
| INCOMPATIBLE | Incompatible changes     |
+--------------+--------------------------+
| NEW          | New features             |
+--------------+--------------------------+
| BETTER       | Improved features        |
+--------------+--------------------------+
| FIX          | Bug fixes                |
+--------------+--------------------------+
| NOTE         | Notes                    |
+--------------+--------------------------+
| (AMENDS)     | (amending past messages) |
+--------------+--------------------------+
| (missing)    | (developers only)        |
+--------------+--------------------------+

For more, see `kwalitee <http://kwalitee.readthedocs.io/>`_.

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

1. **Cross-check CI green lights.** Are all Travis builds green? Is nightly
   Jenkins build green?

2. **Cross-check Read The Docs documentation builds.** Are docs building fine?

3. **Cross-check demo site builds.** Is demo site working?

4. **check-manifest** Are all files included in the release?

5. **Check author list.** Are all committers listed in AUTHORS file? Use
   ``kwalitee check authors``. Add newcomers.

6. **Update I18N message catalogs.**

7. **Update version number. Generate release notes.** Use `kwalitee prepare
   release v1.1.0..` to generate release notes.

8. **Push a pre-release to testpypi.** Try a test install from there.

9. **Tag it. Push it. Bump it.** Sign the tag with your GnuPG key. Don't forget
   the post-release version bump.

10. **Add release notes on GitHub. Tweet it. Post it.** Make publicity for
    production-ready releases. This is not automated yet.

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

For more, see kwalitee.

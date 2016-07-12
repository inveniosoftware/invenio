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

=============
 Integrating
=============

::

    Covered with tests
    Instantly I’d like to merge
    In this dream of ours!
       -—after Ochi Etsujin (1656?-1739?)

Integrating principles
======================

.. _check-it-from-the-helicopter:

1. **Check it from the helicopter.** If it ain’t green, it ain’t finished. If it
   ain’t understandable, it ain’t documented.

.. _beware-of-inter-module-relations:

2. **Beware of inter-module relations.** Changing API? Perhaps this pull request
   may break other modules. Check outside usage. Check the presence of
   ``versionadded``, ``versionmodified``, ``deprecated`` docstring directives.

.. _beware-of-inter-service-relations:

3. **Beware of inter-service relations.** Changing pre-existing tests? Perhaps
   this pull request does not fit the needs of other Invenio services.

.. _check-the-signature-karma:

4. **Check the signature karma.** If it ain’t signed, it ain’t finished.

.. _check-the-counter-signature-karma:

5. **Check the counter-signature karma.** If it ain’t counter-signed, it ain’t
   finished. Check for "Reviewed-by" commit signatures. Check for "LGTM" or
   ":shipit:" pull request signatures.

.. _avoid-self-merges:

6. **Avoid self merges.** Each pull request should be seen by another pair of
   eyes. Was it authored and reviewed by two different persons? Good. Were the
   two different persons coming from two different service teams? Better.

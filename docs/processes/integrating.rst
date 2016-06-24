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

1. **Beware of inter-module relations.** Changing API? Perhaps this pull request
   may break other modules.

2. **Beware of inter-service relations.** Seems service specific? Perhaps this
   pull request does not fit the needs of other Invenio services.

3. **Check the signature karma.** If it ain’t signed, it ain’t finished.

4. **Check the counter-signature karma.** If it ain’t counter-signed, it ain’t
   finished. (i) "Reviewed-by" commit signatures. (ii) ":shipit:" PR signatures.
   (iii) Cross-team signatures.

5. **Check it from the helicopter.** If it ain’t green, it ain’t finished. If it
   ain’t understandable, it ain’t documented.

6. **Check its neighbourhoods.** If it changes pre-existing tests, beware of
   compatibility. If it removes API-like functions, check outside usage.

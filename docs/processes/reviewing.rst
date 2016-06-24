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
 Reviewing
===========

::

    Ecce pull request!
    Undocumented features
    Still shivering
       —-after Akutagawa Ryunosuke (1892-1927)

Reviewing principles
====================

1. **Every PR should preserve or increase code coverage.** If it ain’t green, it
   ain’t finished.

2. **Check it as a black box. Input, magic, output.** If it ain’t documented, it
   ain’t finished.

3. **Check it as a white box. Implementation details.** If it ain’t styled, it
   ain’t finished.

4. **Check it as a release news. Commit messages.** If it does not announce
   anything, it may not be finished.

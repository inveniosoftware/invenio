..  This file is part of Invenio
    Copyright (C) 2014, 2015 CERN.

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

.. _git-workflow:

W6. Rebasing against latest git/master
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At this step the new-feature-b code is working both for Atlantis
and for CDS contexts.  You should now check the official repo for any
updates to catch any changes that may have been committed to
origin/master in the meantime.

.. code-block:: console

    $ git checkout master
    $ git pull


You can then **rebase** your new-feature-b branch against recent master.

.. code-block:: console

    $ git checkout new-feature-b
    $ git rebase master


In case of conflicts during the rebase, say in file foo.py, you should
resolve them.

.. code-block:: console

    $ vim foo.py
    $ git add foo.py
    $ git rebase --continue


or you can stop the rebase for good.

.. code-block:: console

    $ git rebase --abort


You may prefer rebasing of your local commits rather than merging, so
that the project log looks nice.  (No ugly empty merge commits, no
unnecessary temporary versions.)

While rebasing, you may want to squash your commits together, to keep
the git repo history clean.  See section R4 below for more details.

You should test your code once more to verify that it was not broken by
the updates.

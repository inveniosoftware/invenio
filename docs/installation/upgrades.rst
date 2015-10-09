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

========
Upgrades
========

Invenio community is working hard on new features and fixing bugs that
were found after release. While the upgrade can be a complex process at
times, running the latest Invenio version has several benefits:

- Bugs are fixed.

- New features and improvements are added.

- Upgrading soon after a new Invenio release is available makes all future
  upgrades less painful by keeping your code base always up to date.

The upgrades are fully automatised so that it is usually sufficient to do::

  inveniomanage upgrader show pending
  inveniomanage upgrader check
  inveniomanage upgrader run

This will show the upgrade recipes which are to be run, check whether everything
is alright, and perform the upgrade operations themselves. Note that the upgrade
recipes may warn you about any further action that are necessary to execute
manually.

Please refer to the `invenio-upgrader
<http://pythonhosted.org/invenio-upgrader>`_ module documentation for more
details.



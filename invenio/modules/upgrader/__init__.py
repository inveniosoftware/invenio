# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


"""
Usage (via ``inveniomanage``).

.. code-block:: console

    $ inveniomanage upgrader create recipe -p invenio.modules.search
    $ inveniomanage upgrader create release -r invenio -p invenio.base
    $ inveniomanage upgrader show applied
    $ inveniomanage upgrader show pending
    $ inveniomanage upgrader check
    $ inveniomanage upgrader run

Recommendations for writing upgrades
------------------------------------

 * An upgrade must be self-contained. **DO NOT IMPORT ANYTHING** from Invenio
   unless absolutely necessary. Reasons: 1) If a it depends on other Invenio
   modules, then their API must be very stable and backwards-compatible.
   Otherwise when an upgrade is applied two years later, the Invenio function
   might have evolved and the upgrade will fail.
 * Once an upgrade have been committed, no fiddling is allowed afterwards (i.e.
   no semantic changes). If you want to correct a mistake, make an new upgrade
   instead.
 * All upgrades must depend on a previous upgrade (except for your first
   upgrade).
 * For every software release, make a ``<repository>_release_<x>_<y>_<z>.py``
   that depends on all upgrades between the previous release and the new, so
   future upgrades can depend on this upgrade. The command
   ``inveniomanage upgrader create release`` can help you with this.
 * Upgrades may query for user input, but must be able to run in unattended
   mode when ``--yes-i-know option`` is being used, thus good defaults/guessing
   should be used.

Upgrade modules
---------------
Upgrades are implemented as normal Python modules. They must implement the
methods ``do_upgrade()`` and ``info()`` and contain a list variable
``depends_on``. Optionally they may implement the methods ``estimate()``,
``pre_upgrade()``, ``post_upgrade()``.

The upgrade engine will search for upgrades in all packages listed in
``current_app.config['PACKAGES']``.

Upgrade dependency graph
------------------------
The upgrades form a *dependency graph* that must be without cycles (i.e.
a DAG). The upgrade engine supports having several independent graphs (normally
one per module). The graphs are defined using via a filename prefix using the
pattern (``<module name>_<date>_<name>.py``).

The upgrade engine will run upgrades in topological order (i.e upgrades
will be run respecting the dependency graph). The engine will detect cycles in
the graph and will refuse to run any upgrades until the cycles have been
broken.
"""


def populate_existing_upgrades(sender, yes_i_know=False, drop=True, **kwargs):
    """Populate existing upgrades."""
    from .engine import InvenioUpgrader
    iu = InvenioUpgrader()
    map(iu.register_success, iu.get_upgrades())

from invenio.base import signals
from invenio.base.scripts.database import create, recreate
signals.post_command.connect(populate_existing_upgrades, sender=create)
signals.post_command.connect(populate_existing_upgrades, sender=recreate)

..  This file is part of Invenio
    Copyright (C) 2014 CERN.

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

.. _developers-howtomodulepart2:

How to develop a module: Part 2
===============================

In part 2 of this guide, we will go into more advanced module structures
and usage.


Multiple views
--------------

If your module has several web interface entry points, such as an admin area and a user area.
``views`` are defined inside their own folder::

    invenio/modules/
        mymodule/
            views/
                __init__.py
                admin.py
                user.py

The ``__init__.py`` file then contains special code to include the views::

    from .user import blueprint as user_blueprint
    from .admin import blueprint as admin_blueprint

    blueprints = [user_blueprint, admin_blueprint]


Module-wide configuration
-------------------------

TODO.

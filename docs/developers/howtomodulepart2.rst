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

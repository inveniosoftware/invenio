# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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
Additional extensions and functions for the `flask_assets` module.

.. py:data:: command

    Flask-Script command that deals with assets.

    Documentation is on: `webassets` :ref:`webassets:script-commands`

    .. code-block:: python

        # How to install it
        from flask_script import Manager
        manager = Manager()
        manager.add_command("assets", command)

.. py:data:: registry

    Flask-Registry registry that handles the bundles. Use it directly as it's
    lazy loaded.
"""

from .commands import AssetsCommand, BowerCommand
from .extensions import BundleExtension
from .registry import bundles
from .wrappers import Bundle, RequireJSFilter, CleanCSSFilter


__all__ = ("bower", "bundles", "command", "setup_app", "Bundle",
           "RequireJSFilter", "CleanCSSFilter")

command = AssetsCommand()
bower = BowerCommand()


def setup_app(app):
    """Initialize Assets extension.

    Use the ``ASSETS_BUNDLES_DIR`` option to change the name of the directory
    where the assets are generated (by default ``gen``).

    :param app: Flask application
    """
    app.config.setdefault("ASSETS_BUNDLES_DIR", "gen")

    BundleExtension.install(app)

    return app

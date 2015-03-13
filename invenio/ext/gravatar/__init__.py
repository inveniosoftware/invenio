# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2015 CERN.
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
    invenio.ext.gravatar
    --------------------

    This module provides initialization and configuration for
    `flask_gravatar` module.
"""


def setup_app(app):
    """Initialize Gravatar extension."""
    from flask_gravatar import Gravatar
    gravatar = Gravatar(app,
                        size=app.config.get('GRAVATAR_SIZE', 100),
                        rating=app.config.get('GRAVATAR_RATING', 'g'),
                        default=app.config.get('GRAVATAR_DEFAULT', 'retro'),
                        force_default=False,
                        force_lower=False)
    del gravatar
    return app

# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""Initialize session interface and default config variables."""

from .interface import SessionInterface

ONE_DAY = 86400


def setup_app(app):
    """Create custom session interface."""
    app.config.setdefault('SESSION_COOKIE_NAME', 'INVENIOSESSION')
    app.config.setdefault(
        'PERMANENT_SESSION_LIFETIME',
        app.config.get('CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER') * ONE_DAY)
    # Attach legacy session handling.
    app.session_interface = SessionInterface()
    return app

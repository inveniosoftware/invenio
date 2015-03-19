# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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
    invenio.ext.sslify
    ------------------
     This module provides initialization and configuration for
     `flask_sslify` module.
"""

from flask import session, request, current_app
from .wrappers import SSLify
from .decorators import ssl_required


def setup_app(app):
    CFG_SITE_SECURE_URL = app.config.get('CFG_SITE_SECURE_URL')
    CFG_SITE_URL = app.config.get('CFG_SITE_URL')
    app.config['CFG_HAS_HTTPS_SUPPORT'] = CFG_HAS_HTTPS_SUPPORT = \
        CFG_SITE_SECURE_URL.startswith("https://")
    app.config['CFG_FULL_HTTPS'] = CFG_FULL_HTTPS = \
        CFG_SITE_URL.lower().startswith("https://")

    if CFG_HAS_HTTPS_SUPPORT:
        # Makes request always run over HTTPS.
        _sslify = SSLify(app)

        if not CFG_FULL_HTTPS:
            @_sslify.criteria_handler
            def criteria():
                """Extends criteria when to stay on HTTP site."""
                _force_https = False
                if request.blueprint in current_app.blueprints:
                    blueprint =  current_app.blueprints[request.blueprint]
                    _force_https = getattr(blueprint, '_force_https', False)

                view_func = current_app.view_functions.get(request.endpoint)
                if view_func is not None and hasattr(view_func, '_force_https'):
                    _force_https = view_func._force_https

                return not (_force_https or session.need_https())

    return app

__all__ = ['setup_app', 'ssl_required']

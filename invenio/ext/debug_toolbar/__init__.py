# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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
Debug Toolbar Extension.

Configuration
-------------
The toolbar supports several configuration options:

====================================  =====================================   ==========================
Name                                  Description                             Default
====================================  =====================================   ==========================
``DEBUG_TB_ENABLED``                  Enable the toolbar?                     ``app.debug``
``DEBUG_TB_HOSTS``                    Whitelist of hosts to display toolbar   any host
``DEBUG_TB_INTERCEPT_REDIRECTS``      Should intercept redirects?             ``True``
``DEBUG_TB_PANELS``                   List of module/class names of panels    enable all built-in panels
``DEBUG_TB_PROFILER_ENABLED``         Enable the profiler on all requests     ``False``, user-enabled
``DEBUG_TB_TEMPLATE_EDITOR_ENABLED``  Enable the template editor              ``False``
====================================  =====================================   ==========================

For more information see http://flask-debugtoolbar.readthedocs.org/en/latest/
"""


def setup_app(app):
    """Setup Flask with the DebugToolbar application."""
    # Enable Flask Debug Toolbar early to also catch HTTPS redirects
    if app.debug and app.config.get('DEBUG_TB_ENABLED', app.debug):
        try:
            from flask_debugtoolbar import module, DebugToolbarExtension
            module.static_folder = 'static'
            DebugToolbarExtension(app)
        except ImportError:
            app.logger.exception("Flask-DebugToolbar is missing")

    return app

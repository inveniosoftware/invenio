# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
    Debug toolbar Invenio extension
"""

from flask import session


def setup_app(app):
    # Enable Flask Debug Toolbar early to also catch HTTPS redirects
    if 'debug-toolbar' in app.config['CFG_DEVEL_TOOLS']:
        app.config["DEBUG_TB_ENABLED"] = True
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = \
            'intercept-redirects' in getattr(app.config, 'CFG_DEVEL_TOOLS', [])
        from flask_debugtoolbar import DebugToolbarExtension

        class InvenioDebugToolbarExtension(DebugToolbarExtension):
            def _show_toolbar(self):
                from invenio.ext.login.legacy_user import UserInfo
                user_info = UserInfo(session.get('user_id'))
                # the debug toolbar will be enabled iff it is added in
                # CFG_DEVEL_TOOLS and CFG_DEVEL_SITE == 9 (shown to ALL users)
                # or the user is super admin (regardless of CFG_DEVEL_SITE)
                if app.config["CFG_DEVEL_SITE"] != 9 and \
                        not user_info.is_super_admin:
                    return False
                return super(InvenioDebugToolbarExtension, self)._show_toolbar()

        InvenioDebugToolbarExtension(app)

    return app

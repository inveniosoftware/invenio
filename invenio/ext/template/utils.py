# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Utils related to Jinja templates."""

from flask import current_app


def render_macro_from_template(name, template, app=None, ctx=None):
    """Render macro with the given context.

    :param name: macro name.
    :type name: string.
    :param template: template name.
    :type template: string.
    :param app: Flask app.
    :type app: object.
    :param ctx: parameters of the macro.
    :type ctx: dict.
    :return: unicode string with rendered macro.
    """
    ctx = ctx or {}
    app = app or current_app
    tpl = app.jinja_env.get_template(template)
    macro = getattr(tpl.make_module(), name)
    return unicode(macro(**ctx))

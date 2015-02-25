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

"""Markdown rendering using mistune library."""

from __future__ import absolute_import

import mistune

from flask import render_template, request

from invenio.ext.cache import cache


@cache.memoize(timeout=2*86400)
def render(f):
    """Render HTML from Markdown file content."""
    with open(f.fullpath, 'rU') as mdfile:
        return mistune.markdown(mdfile.read())


def can_preview(f):
    """Determine if file can be previewed."""
    return f.superformat.lower() == '.md'


def preview(f):
    """Render Markdown."""
    return render_template("previewer/mistune.html", f=f,
                           content=render(f),
                           embed=request.args.get('embed', type=bool))

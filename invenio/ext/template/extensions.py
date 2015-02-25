# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
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

"""Custom `Jinja2` extensions."""

from jinja2 import nodes
from jinja2.ext import Extension
from flask import g


class LangExtension(Extension):

    """Ease transition from legacy templates using ``<lang>...</lang>``."""

    tags = set(['lang'])

    def parse(self, parser):
        """Parse the template."""
        lineno = parser.stream.next().lineno

        body = parser.parse_statements(['name:endlang'], drop_needle=True)

        return nodes.CallBlock(self.call_method('_lang'),
                               [], [], body).set_lineno(lineno)

    @staticmethod
    def _lang(caller):
        """Return current language string using `filter_languages`."""
        from invenio.modules.formatter.engine import filter_languages
        return filter_languages('<lang>' + caller() + '</lang>', g.ln)

# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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
    invenio.ext.legacy.request_class
    --------------------------------

     This module provides Flask Request wrapper.
"""

from flask import Request


class LegacyRequest(Request):
    """
    Flask Request wrapper which adds support for converting the request into
    legacy request (SimulatedModPythonRequest). This is primarily useful
    when Flaskifying modules, that still depends on old code.
    """
    def dummy_start_response(self, *args, **kwargs):
        """Dummy function for simulating response begining."""
        pass

    def get_legacy_request(self):
        """Returns an instance of SimulatedModPythonRequest."""
        from invenio.legacy.wsgi import SimulatedModPythonRequest
        return SimulatedModPythonRequest(self.environ,
                                         self.dummy_start_response)

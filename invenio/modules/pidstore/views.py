# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Persistent identifier store views."""

from __future__ import absolute_import, unicode_literals

from flask import Blueprint

from .models import PersistentIdentifier


blueprint = Blueprint(
    'pidstore',
    __name__,
)


#
# Template filters
#
@blueprint.app_template_filter('pid_exists')
def pid_exists(value, pidtype="doi"):
    """Check if a persistent identifier exists."""
    return PersistentIdentifier.get(pidtype, value) is not None


@blueprint.app_template_filter('doi_link')
def doi_link(value):
    """Convert DOI to a link."""
    return """<a href="http://dx.doi.org/%(doi)s">%(doi)s</a>""" % dict(
        doi=value
    )

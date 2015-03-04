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

"""Relationship API."""

import importlib

from .config import RELATIONSHIP_ENGINE, RELATIONSHIP_NODE

# FIXME: The code is currently working around the fact that Flask-registry
# is run before the application context is ready, therefore one can't use
# the LocalProxy defined in invenio.base.globals. For more details see: 
# https://github.com/inveniosoftware/invenio/pull/2719/files#r25151156
try:
    __engine = __import__('flask').current_app.config['RELATIONSHIP_ENGINE']
except RuntimeError:
    __engine = RELATIONSHIP_ENGINE

try:
    __node = __import__('flask').current_app.config['RELATIONSHIP_NODE']
except RuntimeError:
    __node = RELATIONSHIP_NODE

Node = getattr(importlib.import_module(__node[0]), __node[1])
Relationship = getattr(importlib.import_module(__engine[0]), __engine[1])

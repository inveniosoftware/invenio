# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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
"""BibFormat element - Prints record OAI identifier
"""
import cgi
from invenio.config import CFG_OAI_ID_FIELD

def format_element(bfo, instance_prefix="", separator=", ", instance_suffix=""):
    """
    Prints the record OAI identifier(s).

    @param instance_prefix: some value printed before each identifier. Must be already escaped
    @param separator: some value printed between each identifier. Must be already escaped
    @param instance_suffix: some value printed after each identifier. Must be already escaped
    """
    return separator.join([instance_prefix + cgi.escape(value) + instance_suffix \
                           for value in bfo.fields(CFG_OAI_ID_FIELD) if value])

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

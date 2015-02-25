# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011, 2014 CERN.
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
"""BibFormat element - Prints brief HTML picture and links to resources
"""
__revision__ = "$Id$"

def format_element(bfo):
    """
    Prints html image and link to photo resources.
    """
    from invenio.config import CFG_BASE_URL, CFG_SITE_RECORD

    resources = bfo.fields("8564_")
    out = ""
    for resource in resources:

        if resource.get("x", "") == "icon":
            out += '<a class="thumbnail" href="'+CFG_BASE_URL+'/'+ CFG_SITE_RECORD +'/'+bfo.control_field("001")+ \
                   '?ln='+ bfo.lang + '"><img src="' + resource.get("u", "").replace(" ","") \
                   + '" alt="" border="0" style="max-width: 80px;"/></a>'

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

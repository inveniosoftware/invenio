# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints aprents of a current HEPData dataset
"""
__revision__ = "$Id$"

from invenio.search_engine import get_record
from invenio.bibrecord import record_get_field, field_get_subfield_values
from invenio.config import CFG_BASE_URL

def format_element(bfo):
    """
    Prints HEPData table encoded in the record
    """
    parent_recids = bfo.fields("786__w")
    results = []
    a = results.append

    a("<h3>This dataset has been included in the following publications: </h3>")

    for recid in parent_recids:
        try:
            rec = get_record(str(recid))
            field = record_get_field(rec , "245", field_position_local=0)

            publication_title = field_get_subfield_values(field , "a")[0]
        except:
            publication_title = ""

        a("<a href=\"%s/record/%s\"><b>%s</b></a>" % (CFG_BASE_URL, str(recid), publication_title))

    return "\n".join(results)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

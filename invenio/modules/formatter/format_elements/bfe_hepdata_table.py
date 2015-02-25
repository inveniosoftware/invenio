# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints HEP Data table encoded by a record
"""
__revision__ = "$Id$"

from invenio.utils.hepdata import display as hepdatadisplayutils
from invenio.utils import hepdata as hepdatautils
def format_element(bfo):
    """
    Prints HEPData table encoded in the record
    """
    publisher = bfo.fields("520__9")[0]
    if publisher == "HEPDATA":
        recid = bfo.recID
        parent_recid = int(bfo.fields("786__w")[0])
        seq = int(bfo.fields("786__q")[0])
        dataset = hepdatautils.get_hepdata_by_recid(parent_recid, recid)
        return hepdatadisplayutils.render_hepdata_dataset_html(dataset, parent_recid, seq, display_link = False)
    elif publisher == "Dataverse":
        return hepdatadisplayutils.render_dataverse_dataset_html(bfo.recID, display_link = False)
    elif publisher == "INSPIRE":
        return hepdatadisplayutils.render_inspire_dataset_html(bfo.recID, display_link = False)
    else:
        return hepdatadisplayutils.render_other_dataset_html(bfo.recID, display_link = False)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

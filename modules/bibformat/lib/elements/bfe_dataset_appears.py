# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
"""BibFormat element - Prints the list of papers containing the dataset
"""
__revision__ = "$Id$"


def format_element(bfo):
    """
    Prints the list of papers containing the dataset by title.
    """

    from invenio.bibformat_engine import BibFormatObject
    from invenio.config import CFG_BASE_URL, CFG_SITE_RECORD

    parent_recid = int(bfo.field("786__w"))
    bfo_parent = BibFormatObject(parent_recid)

    title = bfo_parent.field("245__a")
    url = CFG_BASE_URL + '/' + CFG_SITE_RECORD + '/' + str(bfo_parent.recID)

    out = "This dataset complements the following publication: <br />"
    out += "<a href=\"" + url + "\">" + title + "</a>"

    return out


def escape_values(bfo):  # pylint: disable=W0613
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

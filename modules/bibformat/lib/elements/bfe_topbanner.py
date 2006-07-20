# -*- coding: utf-8 -*-
## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

def format(bfo):
    """
    HTML top page banner containing category, rep. number, etc
    """
    collection_indicator = bfo.kb("dbcollid2coll", bfo.field("980$a"))
    subject = bfo.field("65017$a") 
    subject_2 = bfo.field("65027$a")

    additional_report_numbers = bfo.fields("088$a")
    source_of_aquisition = bfo.field("037$a")

    out = '<table border="0" width="100%"><tr class="blocknote">'
    out += '''<td valign="left">
    %s
    <small>'''%collection_indicator

    if subject != "XX":
        out += " / "+ subject

    out += subject_2
    out += "</small></td>"

    for report_number in additional_report_numbers:
        out += "<td><small><strong>" +report_number +" </strong></small></td>"

    if len(source_of_aquisition) > 0:
        out += '<td align="right"><strong>'+ source_of_aquisition + "</strong></td>"

    out += "</tr></table><br>"

    return out

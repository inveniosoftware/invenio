# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""BibFormat element - Prints a custom field
"""
__revision__ = "$Id$"

from invenio.bibformat_utils import parse_tag

def format(bfo, tag, limit, instances_separator=" ", subfields_separator=" "):
    """
    Prints the given field of a record.
    If tag is in range [001, 010], this element assumes
    that it accesses a control field. Else it considers it
    accesses a data field.

    @param tag the tag code of the field that is to be printed
    @param instances_separator a separator between instances of field
    @param subfields_separator a separator between subfields of an instance
    @param limit the maximum number of values to display.
    """
    # check if data or control field
    p_tag = parse_tag(tag)
    if p_tag[0].isdigit() and int(p_tag[0]) in range(0, 11):
        return  bfo.control_field(tag)
    elif p_tag[0].isdigit():
        values = bfo.fields(tag)
    else:
        return ''
    
    out = ""
    
    if limit == "" or (not limit.isdigit()) or limit > len(values):
        limit = len(values)

    if len(values) > 0 and isinstance(values[0], dict):
        x = 0
        for value in values:
            x += 1
            out += subfields_separator.join(value.values())
            if x >= limit:
                break
            
            # Print separator between instances
            if x < len(values):
                out += instances_separator

    else:
        out += subfields_separator.join(values[:int(limit)])
    
    return out

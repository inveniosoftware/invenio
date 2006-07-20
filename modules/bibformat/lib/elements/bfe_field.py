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

def format(bfo, tag, limit, separator=" "):
    """
    Prints the given field of a record.

    @param tag the tag code of the field that is to be printed
    @param separator a separator between values of the field.
    @param limit the maximum number of values to display.
    """
    values = bfo.fields(tag)
    out = ""
    if limit == "" or (not limit.isdigit()) or limit > len(values):
        limit = len(values)


    if len(values)>0 and isinstance(values[0], dict):
        x = 0
        for value in values:
            x += 1
            out += separator.join(value.values())
            if x >= limit:
                break

    else:
        out += separator.join(values[:int(limit)])

    return out

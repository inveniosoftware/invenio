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
    Prints html image and link to photo resources.
    """

    resources = bfo.fields("8564_")
    out = ""
    for resource in resources:

        if resource.get("x", "") == "icon" and resource.get("u", "") == "": 
            out += '<br/><br/><img src="' + resource.get("q", "").replace(" ","") + '" alt=""/>' 

        if resource.get("x", "") == "1":
            out += '<br/>High resolution: <a href="'+resource.get("q", "") +'">'+ resource.get("q", "") +"</a>"

    out += "<br/><font size=-2><b>© CERN Geneva</b></font>" 
    out += '<br/> <a href="'+bfo.field("8564_.u")+'">'+ bfo.field("8564_.z") + "</a>" 
    return out

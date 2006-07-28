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


def format(bfo, reference_prefix, reference_suffix):
    """
    Prints the references of this record
    
    @param reference_prefix a prefix displayed before each reference
    @param reference_suffix a suffix displayed after each reference
    """
    from invenio.config import weburl
    
    references = bfo.fields("999C5")
    out = ""
    
    for reference in references:

        if reference.has_key('o'):
            out += "<li><small>"+ reference['o']+ "</small> "

        if reference.has_key('m'):
            out += "<small>"+ reference['m']+ "</small> "

        if reference.has_key('r'):
            out += '<small> [<a href="'+weburl+'/search.py?f=reportnumber&amp;p='+ reference['r']+ '">'+ reference['r']+ "</a>] </small> <br/>"

        if reference.has_key('t'):
            ejournal = bfo.kb("ejournals", reference.get('t', ""))
            if ejournal != "":
                out += ' <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication='\
                      + reference['t'].replace(" ", "+") \
                +"&amp;volume="+reference.get('v', "")+"&amp;year="+reference.get('y', "")+"&amp;page="+reference.get('p',"").split("-")[0]+'">'
                out += reference['t']+": "+reference.get('v', "")+" ("+reference.get('y', "")+") "
                out += reference.get('p', "")+"</a> </small> <br/>"
            else:
                out += " <small> "+reference['t']+ reference.get('v', "")+ reference.get('y',"")+ reference.get('p',"")+ " </small> <br/>"

    return out

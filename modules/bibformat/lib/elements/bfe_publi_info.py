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

__revision__ = "$Id$"

def format(bfo):
    """
    Displays inline publication information with html link to ejournal
    (when available).
    """
    from urllib import quote
    
    out = ''
    
    publication_info = bfo.field('909C4')
    if publication_info == "":
        return ""

    journal = bfo.kb('ejournals', publication_info.get('p'))
    volume = publication_info.get('v')
    year = publication_info.get('y')
    number = publication_info.get('n')
    pages = publication_info.get('c')

    if journal != '' and volume != None:
        out += '<a href="http://weblib.cern.ch/cgi-bin/ejournals?publication='
        out += quote(publication_info.get('p'))
        out += '&amp;volume=' + volume
        out += '&amp;year=' + year
        out += '&amp;page='
        page = pages.split('-')# get first page from range
        if len(page) > 0:
            out += page[0]
        out += '">%(journal)s :%(volume)s %(year)s %(page)s</a>'%{'journal': journal,
                                                                  'volume': volume,
                                                                  'year': year,
                                                                  'page': pages}
    else:
        out += publication_info.get('p') + ': '
        if volume != None:
            out +=  volume 
        if year != None:
            out += ' (' + year + ') '
        if number != None:
            out += 'no. ' + number + ', '
        if pages != None:
            out += 'pp. ' + pages
         
    return out
      






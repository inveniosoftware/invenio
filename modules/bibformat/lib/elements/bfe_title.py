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

def format(bfo, separator=" ", highlight='no'):
    """
    Prints the titles of a record.

    @param separator separator between the different titles
    @param highlight highlights the words corresponding to search query if set to 'yes'
    """
    titles = []
   
    title = bfo.field('245.a')
    title_remainder = bfo.field('245.b')

    titles.append( title + title_remainder )

    title = bfo.field('0248_a')
    if len(title) > 0:
        titles.append( title )

    title = bfo.field('246.a')
    if len(title) > 0:
        titles.append( title )

    title = bfo.field('246_1.a')
    if len(title) > 0:
        titles.append( title )

    if highlight == 'yes':
        from invenio import bibformat_utils
        titles = [bibformat_utils.highlight(x, bfo.search_pattern) for x in titles]
        
    return separator.join(titles)









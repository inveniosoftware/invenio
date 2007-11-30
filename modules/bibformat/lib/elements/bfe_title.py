# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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
"""BibFormat element - Prints titles
"""
__revision__ = "$Id$"

import cgi
from urllib import quote
from invenio.config import weburl
import re

def format(bfo, separator=" ", highlight='no'):
    """
    Prints the titles of a record.

    @param separator separator between the different titles
    @param highlight highlights the words corresponding to search query if set to 'yes'
    """
    titles = []

    title = bfo.field('245__a')
    title_remainder = bfo.field('245__b')

    if len(title) > 0:
        if title_remainder:
            titles.append( title + ': ' + title_remainder )
        else:
            titles.append( title )

    title = bfo.field('0248_a')
    if len(title) > 0:
        titles.append( title )

    title = bfo.field('246__a')
    if len(title) > 0:
        titles.append( title )

    title = bfo.field('246__b')
    if len(title) > 0:
        titles.append( title )

    title = bfo.field('246_1a')
    if len(title) > 0:
        titles.append( title )

    if len(titles) > 0:
        #Display 'Conference' title only if other titles were not found
        title = bfo.field('111__a')
        if len(title) > 0:
            titles.append( title )

    titles = [cgi.escape(x) for x in titles]

    if highlight == 'yes':
        from invenio import bibformat_utils
        titles = [bibformat_utils.highlight(x, bfo.search_pattern) for x in titles]

    return separator.join(titles)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0







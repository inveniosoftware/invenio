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
"""BibFormat element - Prints keywords
"""
__revision__ = "$Id$"

import cgi
from urllib import quote
from invenio.config import weburl

def format(bfo, keyword_prefix, keyword_suffix, separator=' ; ', link='yes'):
    """
    Display keywords of the record.
    
    @param keyword_prefix a prefix before each keyword
    @param keyword_suffix a suffix after each keyword
    @param separator a separator between keywords
    @param link links the keywords if 'yes' (HTML links)
    """
    
    keywords = bfo.fields('6531_a')
    
    if len(keywords) > 0:
        if link == 'yes':
            keywords = ['<a href="' + weburl + '/search?f=keyword&p='+ \
                        quote(keyword) + \
                        '&amp;ln='+ bfo.lang+ \
                        '">' + cgi.escape(keyword) + '</a>'
                        for keyword in keywords]
        else:
            keywords = [cgi.escape(keyword)
                        for keyword in keywords]
            
        keywords = [keyword_prefix + keyword + keyword_suffix
                    for keyword in keywords]
        return separator.join(keywords)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

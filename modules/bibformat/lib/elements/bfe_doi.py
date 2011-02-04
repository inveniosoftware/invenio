# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
"""BibFormat element - Prints authors
"""

from cgi import escape

def format_element(bfo, tag="0247_"):
    """
    Return an HTML link to the DOI.
    """
    fields = bfo.fields(tag)
    doi = ''
    for field in fields:
        if field.get('2', 'DOI') == 'DOI' and 'a' in field:
            doi = field['a']
    if doi:
        return """<a href="http://dx.doi.org/%s" title="DOI" target="_blank">%s</a>""" % (escape(doi, True), escape(doi))
    else:
        return ""

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

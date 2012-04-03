# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
"""BibFormat element - Prints DOIs
"""

from invenio.search_engine import get_field_tags
from cgi import escape

def format_element(bfo, tag="909C4", label="", separator="<br/> ", description_location=""):
    """
    Return an HTML link to the DOI.

    @param tag: field (tag + indicators) where the DOI can be found, if not specified, we take the tags asociated to the 'doi' logical field
    @param separator: the separator between multiple tags
    @param description_location: where should the description be added: if empty, the description is not printed; possible values: 'front', 'label', 'end'
    @param label: label to use for the DOI link. If not specified, use the DOI number as label for the link.
    """
    fields = []
    doi_tags = get_field_tags('doi') #first check the tags table
    for doi_tag in doi_tags:
        fields = bfo.fields(doi_tag[:5]) #we want only the tag, without the subfields
        if fields:
            break
    if not fields:
        fields = bfo.fields(tag)
    doi_list = [] 
    for field in fields:
        if field.get('2', 'DOI') == 'DOI' and 'a' in field:
            desc = field.get('y', '')
            front = end = ''
            if desc:
                if description_location == 'front':
                    front = desc + ': '
                elif description_location == 'label':
                    label = desc
                elif description_location == 'end':
                    end = ' (' + desc + ')'
                else:
                    front = end = ''
            doi_list.append((field['a'], front, end, label))

    if doi_list:
        doi_link = """%s<a href="http://dx.doi.org/%s" title="DOI" target="_blank">%s</a>%s"""
        return separator.join([doi_link % (escape(front), escape(doi, True), label and escape(label) or escape(doi), end) for (doi, front, end, label) in doi_list])
    else:
        return ""

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

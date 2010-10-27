# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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
"""BibFormat element -

"""
__revision__ = "$Id$"

from invenio.bibformat_utils import parse_tag
from invenio.bibformat_elements.bfe_field import format as field_format
from invenio.htmlutils import create_html_tag
from invenio.bibindex_engine import get_field_tags

def format(bfo, name, tag_name='', tag = '', escape=4):
    """Prints a custom field in a way suitable to be used in HTML META
    tags.  In particular conforms to Google Scholar harvesting protocol as
    defined http://scholar.google.com/intl/en/scholar/inclusion.html


    @param tag_name: the name, from tag table, of the field to be exported
    looks initially for names prefixed by "meta-"<tagname>
    then looks for exact name, then falls through to "tag"
    @param tag: the MARC tag to be exported (only if not defined by tag_name)
    @param name: name to be displayed in the meta headers, labelling this value

    """
    tags = []
    if len(tag_name) > 0:
        # First check for special meta named tags
        tags = get_field_tags("meta-" + tag_name)
        if len(tags) == 0:
            #then check for regular tags
            tags = get_field_tags(tag_name)
    if (len(tags) == 0 and len(tag)) > 0:
        # fall back to explicit marc tag
        tags = [tag]
    if len(tags) == 0:
        return ''
    out = []
    values = [bfo.fields(marctag,escape=escape) for marctag in tags]
    for value in values:
        if isinstance(value, list):
            out += value
        elif isinstance(value, dict):
            out += value.values()
        else:
            out.append(value)

    return '\n'.join([create_html_tag('meta', name=name, content=value) for value in out])

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

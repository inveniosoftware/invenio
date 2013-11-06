# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2013 CERN.
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

"""BibFormat element - meta"""

__revision__ = "$Id$"

import cgi
from invenio.modules.formatter.format_elements.bfe_server_info import format_element as server_info
from invenio.modules.formatter.format_elements.bfe_client_info import format_element as client_info
from invenio.htmlutils import create_tag
from invenio.bibindex_engine_utils import get_field_tags
from invenio.config import CFG_WEBSEARCH_ENABLE_GOOGLESCHOLAR, CFG_WEBSEARCH_ENABLE_OPENGRAPH

def format_element(bfo, name, tag_name='', tag='', kb='', kb_default_output='', var='', protocol='googlescholar'):
    """Prints a custom field in a way suitable to be used in HTML META
    tags.  In particular conforms to Google Scholar harvesting protocol as
    defined http://scholar.google.com/intl/en/scholar/inclusion.html and
    Open Graph http://ogp.me/

    @param tag_name: the name, from tag table, of the field to be exported
    looks initially for names prefixed by "meta-"<tag_name>
    then looks for exact name, then falls through to "tag"
    @param tag: the MARC tag to be exported (only if not defined by tag_name)
    @param name: name to be displayed in the meta headers, labelling this value.
    @param kb: a knowledge base through which to process the retrieved value if necessary.
    @param kb: when a '<code>kb</code>' is specified and no match for value is found, what shall we
               return? Either return the given parameter or specify "{value}" to return the retrieved
               value before processing though kb.
    @param var: the name of a variable to output instead of field from metadata.
                Allowed values are those supported by bfe_server_info and
                bfe_client_info. Overrides <code>name</code> and <code>tag_name</code>
    @param protocol: the protocol this tag is aimed at. Can be used to switch on/off support for a given "protocol". Can take values among 'googlescholar', 'opengraph'
    @see: bfe_server_info.py, bfe_client_info.py
    """
    if protocol == 'googlescholar' and not CFG_WEBSEARCH_ENABLE_GOOGLESCHOLAR:
        return ""
    elif protocol == 'opengraph' and not CFG_WEBSEARCH_ENABLE_OPENGRAPH:
        return ""

    tags = []
    if var:
        # delegate to bfe_server_info or bfe_client_info:
        value = server_info(bfo, var)
        if value.startswith("Unknown variable: "):
            # Oops variable was not defined there
            value = client_info(bfo, var)
        return not value.startswith("Unknown variable: ") and \
               create_metatag(name=name, content=cgi.escape(value, True)) \
               or ""
    elif tag_name:
        # First check for special meta named tags
        tags = get_field_tags("meta-" + tag_name)
        if not tags:
            # then check for regular tags
            tags = get_field_tags(tag_name)
    if not tags and tag:
        # fall back to explicit marc tag
        tags = [tag]
    if not tags:
        return ''
    out = []
    values = [bfo.fields(marctag, escape=9) for marctag in tags]
    for value in values:
        if isinstance(value, list):
            for val in value:
                if isinstance(val, dict):
                    out.extend(val.values())
                else:
                    out.append(val)
        elif isinstance(value, dict):
            out.extend(value.values())
        else:
            out.append(value)
    out = dict(zip(out, len(out)*[''])).keys() # Remove duplicates
    if name == 'citation_date':
        for idx in range(len(out)):
            out[idx] = out[idx].replace('-', '/')

    if kb:
        if kb_default_output == "{value}":
            out = [bfo.kb(kb, value, value) for value in out]
        else:
            out = [bfo.kb(kb, value, kb_default_output) for value in out]
    return '\n'.join([create_metatag(name=name, content=value) for value in out])

def create_metatag(name, content):
    """
    Wraps create_tag
    """
    if name.startswith("og:"):
        return create_tag('meta', property=name, content=content)
    else:
        return create_tag('meta', name=name, content=content)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

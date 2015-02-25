# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibFormat element - return the files of a record"""

from invenio.config import CFG_WEBSEARCH_ENABLE_GOOGLESCHOLAR
from invenio.modules.formatter.format_elements.bfe_fulltext import get_files
from invenio.legacy.bibdocfile.api import BibRecDocs, decompose_bibdocfile_url

def format_element(bfo, file_format='pdf'):
    """Return the files attached to this record, in order to be
    embedded as a Google Scholar tag.

    @param file_format: the format to include in this output
    """
    if not CFG_WEBSEARCH_ENABLE_GOOGLESCHOLAR:
        return ""

    bibarchive = BibRecDocs(bfo.recID)

    (files, old_versions_p, additionals_p) = get_files(bfo)
    filtered_files = []

    if files.has_key('main_urls') and \
           files['main_urls'].has_key('Main'):
        filtered_files = [f[0] for f in files['main_urls']['Main'] if f[2] == file_format and \
                          not url_is_hidden(f[0], bibarchive)]
    if not filtered_files:
        # Fall back to other doctypes
        if files.has_key('main_urls'):
            for doctype, list_of_files in files['main_urls'].iteritems():
                filtered_files.extend([f[0] for f in list_of_files if f[2] == file_format and \
                                       not url_is_hidden(f[0], bibarchive)])
    if not filtered_files:
        # Fall back to external urls
        if files.has_key('others_urls'):
            filtered_files.extend([file_url for file_url, file_name in files['others_urls'] \
                                   if file_url.endswith('.' + file_format)])

    tags = ['<meta name="citation_pdf_url" content="%s" />' % url for url in filtered_files]

    return "\n".join(tags)


def url_is_hidden(url, bibarchive):
    """
    Return True if the given URL should be hidden according to given
    BibRecDocs structure.
    """
    try:
        (recid, docname, docformat) = decompose_bibdocfile_url(url)
        return bibarchive.get_bibdoc(docname).hidden_p(docformat)
    except:
        return False
    return False

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

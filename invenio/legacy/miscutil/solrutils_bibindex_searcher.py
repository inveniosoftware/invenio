# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

"""
Solr utilities.
"""

import urllib2
import urllib
import mimetools
import intbitset
from invenio.utils.url import make_invenio_opener
from invenio.utils.json import json
from invenio.config import CFG_SOLR_URL, \
                           CFG_WEBSEARCH_FULLTEXT_SNIPPETS, \
                           CFG_WEBSEARCH_FULLTEXT_SNIPPETS_CHARS


if CFG_SOLR_URL:
    import solr
    SOLR_CONNECTION = solr.SolrConnection(CFG_SOLR_URL) # pylint: disable=E1101


SOLRUTILS_OPENER = make_invenio_opener('solrutils')

def solr_get_facets(bitset, solr_url):
    facet_query_url = "%s/invenio_facets" % solr_url
    # now use the bitset to fetch the facet data
    r = urllib2.Request(facet_query_url)
    data = bitset.fastdump()
    boundary = mimetools.choose_boundary()

    # fool solr into thinking we're uploading a file so it will read our data as a stream
    contents = '--%s\r\n' % boundary
    contents += 'Content-Disposition: form-data; name="bitset"; filename="bitset"\r\n'
    contents += 'Content-Type: application/octet-stream\r\n'
    contents += '\r\n' + data + '\r\n'
    contents += '--%s--\r\n\r\n' % boundary
    r.add_data(contents)

    contenttype = 'multipart/form-data; boundary=%s' % boundary
    r.add_unredirected_header('Content-Type', contenttype)

    # post the request and get back the facets as json
    u = SOLRUTILS_OPENER.open(r)
    return json.load(u)


def solr_get_bitset(index, query):
    """
    Queries an index and returns the ids as intbitset. Expects the Solr extension classes to be enabled
    to retrieve and intbitset result directly.
    """
    invenio_query_url = "%s/select?qt=invenio_query&q=%s:%s" % (CFG_SOLR_URL, index, urllib.quote(query))

    # query to get a bitset
    bitset = intbitset.intbitset()
    u = SOLRUTILS_OPENER.open(invenio_query_url)
    data = u.read()
    bitset.fastload(data)
    return bitset


def solr_get_snippet(keywords, recid, nb_chars, max_snippets, field='fulltext',
                     prefix_tag='<strong>', suffix_tag='</strong>'):
    query_parts = []
    for keyword in keywords:
        # Treads phrases properly
        if ' ' in keyword:
            query_parts.append('"%s"' % keyword)
        else:
            query_parts.append(keyword)

    res = SOLR_CONNECTION.query(q=' '.join(query_parts), fq='id:(%s)' % recid, fields=['fulltext'],
                                          highlight=True, hl_fragsize=nb_chars, hl_snippets=max_snippets,
                                          # backward-compatible to simple highlighter
                                          hl_simple_pre=prefix_tag, hl_simple_post=suffix_tag,
                                          # faster highlighter
                                          hl_tag_pre=prefix_tag, hl_tag_post=suffix_tag,
                                          hl_mergeContiguous='true',
                                          hl_useFastVectorHighlighter='true')

    out = ''
    try:
        for snippet in res.highlighting[str(recid)][field]:
            if out:
                out += " ... "
            out += snippet
    except KeyError:
        pass
    return out.replace('\n', ' ').encode('utf-8')

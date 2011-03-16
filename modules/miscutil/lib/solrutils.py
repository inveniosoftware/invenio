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

"""
Solr utilities.
"""

import sys
import time
import urllib2
import urllib
from invenio import intbitset
import mimetools

if sys.hexversion < 0x2060000:
    try:
        import simplejson as json
        simplejson_available = True
    except ImportError:
        # Okay, no Ajax app will be possible, but continue anyway,
        # since this package is only recommended, not mandatory.
        simplejson_available = False
else:
    import json
    simplejson_available = True

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
    u = urllib2.urlopen(r)
    return json.load(u)

def solr_get_bitset(query, solr_url):
    invenio_query_url = "%s/select?qt=invenio_query&q=fulltext:%s" % (solr_url, urllib.quote(query))

    # query to get a bitset
    bitset = intbitset.intbitset()
    u = urllib2.urlopen(invenio_query_url)
    data = u.read()
    bitset.fastload(data)
    return bitset

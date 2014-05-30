# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
API to get metadata in JSON format from http://export.arxiv.org using ArXiv ID
"""

import requests
from lxml.etree import fromstring

from invenio.utils.xmlhelpers import etree_to_dict


def get_arxiv_content(arxiv_id):
    """Get ArXiv ID content from the http://export.arxiv.org page."""
    # Clean the ArXiv ID
    search_query = 'all:' + arxiv_id.strip()

    # Getting the data from external source
    response = requests.get("http://export.arxiv.org/api/query",
                            params=dict(search_query=search_query,
                                        max_results=1))

    return response


def get_json_for_arxiv(arxiv_id):
    """Get ArXiv json data."""
    response = get_arxiv_content(arxiv_id)

    data = etree_to_dict(fromstring(response.content))
    query = {}

    for d in data['feed']:
        query.update(dict(d.items()))
    del data['feed']

    # Check if totalResults == 0 - this means the ArXiv ID was not found
    if query['totalResults'] == '0':
        query = {}
        query['status'] = 'notfound'
    else:
        for d in query['entry']:
            query.update(dict(d.items()))
        del query['entry']
        query['status'] = 'success'

    data['source'] = 'arxiv'
    data['query'] = query

    return data

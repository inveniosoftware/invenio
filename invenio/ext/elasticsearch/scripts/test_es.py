#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
# -*- coding: utf-8 -*-

"""Bad test script."""

#---------------------------- Modules -----------------------------------------

# import of standard modules
from __future__ import print_function
from optparse import OptionParser

# third party modules


#---------------------------- Main Part ---------------------------------------

if __name__ == '__main__':

    usage = "usage: %prog [options]"

    parser = OptionParser(usage)

    parser.set_description("""
    This script is done to test elasticserarch for Invenio.
    It should be replaced by unittests.
    Bascally it create a new index, index 100 records and perform a search
    query.
    """)

    (options, args) = parser.parse_args()
    from invenio.base.factory import create_app
    current_app = create_app()

    with current_app.test_request_context():
        print ("-- Connect to the ES server --")
        es = current_app.extensions.get("elasticsearch")

        print("-- Delete old index --")
        es.delete_index()

        print("-- Create the index --")
        es.create_index()

        print("-- Index records --")
        es.index_records(range(1, 100), bulk_size=10)

        print("-- Index documents --")
        es.index_documents(range(1, 100), bulk_size=10)

        print("-- Index collections --")
        es.index_collections(range(1, 100), bulk_size=1000)

        print("-- Perform search --")
        #res = es.search(query="fulltext:test")
        res = es.search(query="title:Sneutrinos",
                        facet_filters=[("facet_authors", "Schael, S"),
                                       ("facet_authors", "Bruneliere, R")])

        print("Hits:")
        print ([hit for hit in res.hits])

        import json
        print("Facets:")
        print(json.dumps(res.facets.data, indent=2))

        print("Highlights:")
        print(json.dumps(res.highlights.data, indent=2))

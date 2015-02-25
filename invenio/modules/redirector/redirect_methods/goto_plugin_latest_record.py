# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
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
Demostrative PURL.

Demostrative PURL implementing a redirection to the very last record
(of a collection).
"""

from invenio.config import CFG_SITE_NAME, CFG_SITE_RECORD
from invenio.legacy.search_engine import perform_request_search
from invenio.legacy.bibdocfile.api import BibRecDocs, InvenioBibDocFileError


def goto(cc=CFG_SITE_NAME, p='', f='', sf='date', so='d',
         docname='', format=''):
    """
    Redirect the user to the latest record in the given collection.

    Redirect the user to the latest record in the given collection,
    optionally within the specified pattern and field. If docname
    and format are specified, redirect the user to the corresponding
    docname and format. If docname it is not specified, but there is
    only a single bibdoc attached to the record will redirect to that
    one.
    """
    recids = perform_request_search(cc=cc, p=p, f=f, sf=sf, so=so)
    if recids:
        # The first is the most recent because they are sorted by date
        # descending.
        recid = recids[0]
        url = '/%s/%s' % (CFG_SITE_RECORD, recid)
        if format:
            bibrecdocs = BibRecDocs(recid)
            if not docname:
                if len(bibrecdocs.get_bibdoc_names()) == 1:
                    docname = bibrecdocs.get_bibdoc_names()[0]
                else:
                    return url
            try:
                bibdoc = BibRecDocs(recid).get_bibdoc(docname)
            except InvenioBibDocFileError:
                return url
            try:
                bibdocfile = bibdoc.get_file(format=format)
                return bibdocfile.get_url()
            except InvenioBibDocFileError:
                return url
        return url

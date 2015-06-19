# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Record utility functions."""

from __future__ import absolute_import

import errno
import os
import six

from flask import g, request
from werkzeug.utils import cached_property, import_string

from invenio.base.globals import cfg
from invenio.config import (CFG_CERN_SITE, CFG_INSPIRE_SITE,
                            CFG_BIBRANK_SHOW_CITATION_LINKS)
from invenio.ext.cache import cache

from .api import get_record


def get_unique_record_json(param):
    """API to query records from the database."""
    from invenio.modules.search.api import Query
    data, query = {}, {}
    data['status'] = 'notfound'
    recid = Query(param).search()
    if len(recid) == 1:
        query = get_record(recid[0]).dumps(clean=True)
        data['status'] = 'success'
    elif len(recid) > 1:
        data['status'] = 'multiplefound'

    data['source'] = 'database'
    data['query'] = query

    return data


def default_name_generator(document):
    """Return default name of record document with storage path.

    The path is generated from the uuid using two folder level, being the first
    two characters the name of the first folder and the second two the name of
    the second folder.

    It avoids creating the directories twice but if any of them is not a
    directory it will raise an OSError exception.

    :param document: The document to be stored.
    :returns: Path based on the `_id` of the document.

    """
    uuid = document['_id']
    directory = os.path.join(cfg.get('CFG_BIBDOCFILE_FILEDIR'),
                             uuid[0:2], uuid[2:4])
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(directory):
            pass
        else:
            raise
    return os.path.join(directory, uuid[4:])


class NameGenerator(object):

    """Record documents name generator."""

    @cached_property
    def generator(self):
        """Load function from configuration ``CFG_BIBDOCFILE_FILEDIR``."""
        func = cfg.get(
            'RECORD_DOCUMENT_NAME_GENERATOR', default_name_generator)
        if isinstance(func, six.string_types):
            func = import_string(func)
        return func

    def __call__(self, *args, **kwargs):
        """Execute name generator function."""
        return self.generator(*args, **kwargs)

name_generator = NameGenerator()


def references_nb_counts():
    """Get number of references for the record `recid`."""
    recid = request.view_args.get('recid')
    if recid is None:
        return

    from invenio.legacy.bibrecord import record_get_field_instances
    from invenio.modules.search.models import Field
    from invenio.modules.records.api import get_record

    if not CFG_CERN_SITE:
        reftag = ""
        reftags = list(Field.get_field_tags("reference"))
        if reftags:
            reftag = reftags[0]
        tmprec = get_record(recid)
        if reftag and len(reftag) > 4:
            return len(record_get_field_instances(tmprec, reftag[0:3],
                       reftag[3], reftag[4]))
    return 0


def citations_nb_counts():
    """Get number of citations for the record `recid`."""
    recid = request.view_args.get('recid')
    if recid is None:
        return

    from intbitset import intbitset
    from invenio.legacy.bibrank.citation_searcher import (get_cited_by,
                                                          get_cited_by_count)

    if CFG_BIBRANK_SHOW_CITATION_LINKS:
        if CFG_INSPIRE_SITE:
            from invenio.legacy.search_engine import search_unit
            citers_recids = intbitset(get_cited_by(recid))
            citeable_recids = search_unit(p='citeable', f='collection')
            return len(citers_recids & citeable_recids)
        else:
            return get_cited_by_count(recid)
    return 0


def visible_collection_tabs(endpoint):
    """Define if a collection tab is visible."""
    def visible_when():
        if hasattr(g, 'collection') and \
                len(g.collection.collectiondetailedrecordpagetabs):
            key = g.collection.name+'_'+endpoint

            @cache.memoize()
            def is_visible_tab(key):
                for visible_tabs in \
                        g.collection.collectiondetailedrecordpagetabs:
                    if endpoint in set(visible_tabs.tabs.split(';')):
                        return True
                # collection hasn't been found in the preference list
                return False
            return is_visible_tab(key)
        else:
            # no preference set for this collection.
            # assume all tabs are displayed
            return True
    return visible_when

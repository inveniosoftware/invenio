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

"""Record utility functions."""

from __future__ import absolute_import

import os
import six

from werkzeug.utils import cached_property, import_string

from invenio.base.globals import cfg
from invenio.modules.records.api import get_record
from invenio.legacy.search_engine import perform_request_search


def get_unique_record_json(param):
    """API to query records from the database."""
    data = {}
    query = {}
    query['status'] = 'notfound'

    recid = perform_request_search(p=param)
    if len(recid) == 1:
        query = dict(get_record(recid))
        query['status'] = 'success'
    elif len(recid) > 1:
        query['status'] = 'multiplefound'

    data['source'] = 'database'
    data['query'] = query

    return data


def default_name_generator(document):
    """Return default name of record document with storage path.

    :document:
    :returns: Path based on the `_id` of the document.

    """
    uuid = document['_id']
    directory = os.path.join(cfg.get('CFG_BIBDOCFILE_FILEDIR'),
                             uuid[0:2], uuid[2:4])
    os.makedirs(directory)
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

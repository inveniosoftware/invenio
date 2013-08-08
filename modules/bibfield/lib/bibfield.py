# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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
BibField engine
"""

__revision__ = "$Id$"

import os

try:
    import cPickle as pickle
except:
    import pickle

from pprint import pformat
from werkzeug import import_string

from invenio.config import CFG_PYLIBDIR, CFG_LOGDIR
from invenio.datastructures import LaziestDict
from invenio.dbquery import run_sql
from invenio.errorlib import register_exception
from invenio.signalutils import record_after_update

from invenio.bibfield_jsonreader import JsonReader
from invenio.bibfield_utils import BlobWrapper

# Lazy loader of bibfield readers

def reader_discover(key):
    try:
        candidate = import_string('invenio.bibfield_%sreader:readers' % (key, ))
        if issubclass(candidate, JsonReader):
            return candidate
    except:
        register_exception()
    raise KeyError(key)

CFG_BIBFIELD_READERS = LaziestDict(reader_discover)


@record_after_update.connect
def delete_record_cache(sender, recid=None, **kwargs):
    get_record(recid, reset_cache=True)


def create_record(blob, master_format='marc', verbose=0, **aditional_info):
    """
    Creates a record object from the blob description using the apropiate reader
    for it.

    @return Record object
    """
    blob_wrapper = BlobWrapper(blob=blob, master_format=master_format, **aditional_info)

    return CFG_BIBFIELD_READERS[master_format](blob_wrapper)


def create_records(blob, master_format='marc', verbose=0, **aditional_info):
    """
    Creates a list of records from the blod descriptions using the split_records
    function to divide then.

    @see create_record()

    @return List of record objects initiated by the functions create_record()
    """
    record_blods = CFG_BIBFIELD_READERS[master_format].split_blob(blob)

    return [create_record(record_blob, master_format, verbose=verbose, **aditional_info) for record_blob in record_blods]


def get_record(recid, reset_cache=False):
    """
    Record factory, it retrieves the record from bibfmt table if it is there,
    if not, or reset_cache is set to True, it searches for the appropriate
    reader to create the representation of the record.

    @return: Bibfield object representing the record or None if the recid is not
    present in the system
    """
    #Search for recjson
    if not reset_cache:
        res = run_sql("SELECT value FROM bibfmt WHERE id_bibrec=%s AND format='recjson'",
                      (recid,))
        if res:
            return JsonReader(BlobWrapper(pickle.loads(res[0][0])))

    #There is no version cached or we want to renew it
    #Then retrieve information and blob

    blob_wrapper = _build_wrapper(recid)
    if not blob_wrapper:
        return None
    record = CFG_BIBFIELD_READERS[blob_wrapper.master_format](blob_wrapper)

    #Update bibfmt for future uses
    run_sql("REPLACE INTO bibfmt(id_bibrec, format, last_updated, value) VALUES (%s, 'recjson', NOW(), %s)",
            (recid, pickle.dumps((record.rec_json))))

    return record


def _build_wrapper(recid):
    #TODO: update to look inside mongoDB for the parameters and the blob
    # Now is just working for marc and recstruct
    try:
        master_format = run_sql("SELECT master_format FROM bibrec WHERE id=%s", (recid,))[0][0]
    except:
        return None

    schema = 'recstruct'

    if master_format == 'marc':
        from invenio.search_engine import get_record as se_get_record
        blob = se_get_record(recid)
    else:
        return None

    return BlobWrapper(blob, master_format=master_format, schema=schema)

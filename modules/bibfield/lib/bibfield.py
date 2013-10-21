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

from invenio.config import CFG_PYLIBDIR
from invenio.dbquery import run_sql
from invenio.pluginutils import PluginContainer

from invenio.bibfield_jsonreader import JsonReader
from invenio.bibfield_utils import BlobWrapper

# Plug-in utils


def plugin_builder(plugin_name, plugin_code):
    if 'readers' in dir(plugin_code):
        candidate = getattr(plugin_code, 'readers')
        try:
            if issubclass(candidate, JsonReader):
                return candidate
        except:
            pass
    raise ValueError('%s is not a valid external authentication plugin' % plugin_name)

CFG_BIBFIELD_READERS = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio',
                                                    'bibfield_*reader.py'),
                                       plugin_builder=plugin_builder)

# end Plug-in utils


def create_record(blob, master_format='marc', verbose=0, **additional_info):
    """
    Creates a record object from the blob description using the apropiate reader
    for it.

    @return Record object
    """
    blob_wrapper = BlobWrapper(blob=blob, master_format=master_format, **additional_info)

    return CFG_BIBFIELD_READERS['bibfield_%sreader.py' % (master_format,)](blob_wrapper, check=True)


def create_records(blob, master_format='marc', verbose=0, **additional_info):
    """
    Creates a list of records from the blod descriptions using the split_records
    function to divide then.

    @see create_record()

    @return List of record objects initiated by the functions create_record()
    """
    record_blods = CFG_BIBFIELD_READERS['bibfield_%sreader.py' % (master_format,)].split_blob(blob)

    return [create_record(record_blob, master_format, verbose=verbose, **additional_info) for record_blob in record_blods]


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
    record = \
        CFG_BIBFIELD_READERS['bibfield_%sreader.py' % (blob_wrapper.master_format,)](blob_wrapper)

    #Update bibfmt for future uses
    run_sql("REPLACE INTO bibfmt(id_bibrec, format, last_updated, value) VALUES (%s, 'recjson', NOW(), %s)",
            (recid, pickle.dumps((record.rec_json))))

    return record


def guess_legacy_field_names(fields, master_format='marc'):
    """
    Using the legacy rules written in the config file (@legacy) tries to find
    the equivalent json field for one or more legacy fields.

    >>> guess_legacy_fields(('100__a', '245'), 'marc')
    {'100__a':['authors[0].full_name'], '245':['title']}
    """
    from invenio.bibfield_config import legacy_rules

    res = {}
    if isinstance(fields, basestring):
        fields = (fields, )
    for field in fields:
        try:
            res[field] = legacy_rules[master_format].get(field, [])
        except:
            res[field] = []
    return res


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

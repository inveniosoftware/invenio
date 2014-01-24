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
import msgpack

from invenio.config import CFG_PYLIBDIR
from invenio.dbquery import run_sql
from invenio.pluginutils import PluginContainer
from invenio.containerutils import SmartDict

from invenio.bibfield_reader import Reader
from invenio.bibfield_utils import SmartJson

class Record(SmartJson):
    """
    Default/Base record class
    """

# Plug-in utils


def plugin_builder(plugin_name, plugin_code):
    if 'reader' in dir(plugin_code):
        candidate = getattr(plugin_code, 'reader')
        try:
            if issubclass(candidate, Reader):
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

    reader = CFG_BIBFIELD_READERS['bibfield_%sreader.py' % (master_format,)](blob, **additional_info)

    return Record(reader.translate())


def create_records(blob, master_format='marc', verbose=0, **additional_info):
    """
    Creates a list of records from the blod descriptions using the split_records
    function to divide then.

    @see create_record()

    @return List of record objects initiated by the functions create_record()
    """
    record_blods = CFG_BIBFIELD_READERS['bibfield_%sreader.py' % (master_format,)].split_blob(blob, additional_info.get('schema', None))

    return [create_record(record_blob, master_format, verbose=verbose, **additional_info) for record_blob in record_blods]


def get_record(recid, reset_cache=False, fields=()):
    """
    Record factory, it retrieves the record from bibfmt table if it is there,
    if not, or reset_cache is set to True, it searches for the appropriate
    reader to create the representation of the record.

    @return: Bibfield object representing the record or None if the recid is not
    present in the system
    """
    record = None
    #Search for recjson
    if not reset_cache:
        res = run_sql("SELECT value FROM bibfmt WHERE id_bibrec=%s AND format='recjson'",
                      (recid,))
        if res:
            try:
                record = Record(msgpack.loads(res[0][0]))
            except:
                #Maybe the cached version is broken
                record = None

    #There is no version cached or we want to renew it
    #Then retrieve information and blob
    if not record or reset_cache:
        try:
            master_format = run_sql("SELECT master_format FROM bibrec WHERE id=%s", (recid,))[0][0]
        except:
            return None
        schema = 'xml'
        master_format = 'marc'
        try:
            from invenio.search_engine import print_record
            blob = print_record(recid, format='xm')
        except:
            return None

        reader = CFG_BIBFIELD_READERS['bibfield_%sreader.py' % (master_format,)](blob, schema=schema)
        record = Record(reader.translate())
        #Update bibfmt for future uses
        run_sql("REPLACE INTO bibfmt(id_bibrec, format, last_updated, value) VALUES (%s, 'recjson', NOW(), %s)",
                (recid, msgpack.dumps(record.dumps())))

    if fields:
        chunk = SmartDict()
        for key in fields:
            chunk[key] = record.get(key)
        record = chunk
    return record

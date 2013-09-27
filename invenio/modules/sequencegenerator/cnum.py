# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

from invenio.sequtils import SequenceGenerator

from invenio.bibedit_utils import get_bibrecord
from invenio.legacy.bibrecord import record_get_field_value, create_record
from invenio.search_engine import perform_request_search

from invenio.dbquery import run_sql

class ConferenceNoStartDateError(Exception):
    pass


class CnumSeq(SequenceGenerator):
    """
    cnum sequence generator
    """
    seq_name = 'cnum'

    def _get_record_cnums(self, value):
        """
        Get all the values that start with the base cnum

        @param value: base cnum
        @type value: string

        @return: values starting by the base cnum
        @rtype: tuple
        """
        return run_sql("""SELECT seq_value FROM seqSTORE WHERE seq_value
                          LIKE %s AND seq_name=%s""",
                          (value + "%", self.seq_name))

    def _next_value(self, recid=None, xml_record=None):
        """
        Returns the next cnum for the given recid

        @param recid: id of the record where the cnum will be generated
        @type recid: int

        @param xml_record: record in xml format
        @type xml_record: string

        @return: next cnum for the given recid. Format is Cyy-mm-dd.[.1n]
        @rtype: string

        @raises ConferenceNoStartDateError: No date information found in the
        given recid
        """
        if recid is None and xml_record is not None:
            bibrecord = create_record(xml_record)[0]
        else:
            bibrecord = get_bibrecord(recid)

        start_date = record_get_field_value(bibrecord,
                                            tag="111",
                                            ind1="",
                                            ind2="",
                                            code="x")
        if not start_date:
            raise ConferenceNoStartDateError

        base_cnum = "C" + start_date[2:]

        record_cnums = self._get_record_cnums(base_cnum)
        if not record_cnums:
            new_cnum = base_cnum
        elif len(record_cnums) == 1:
            new_cnum = base_cnum + '.' + '1'
        else:
            # Get the max current revision, cnums are in format Cyy-mm-dd,
            # Cyy-mm-dd.1, Cyy-mm-dd.2
            highest_revision = max([int(rev[0].split('.')[1]) for rev in record_cnums[1:]])
            new_cnum = base_cnum + '.' + str(highest_revision + 1)

        return new_cnum


# Helper functions to populate cnums from existing database records

def _cnum_exists(cnum):
    """
    Checks existance of a given cnum in seqSTORE table
    """
    return run_sql("""select seq_value from seqSTORE where seq_value=%s and seq_name='cnum'""", (cnum, ))


def _insert_cnum(cnum):
    """
    Inserts a new cnum in table seqSTORE
    """
    return run_sql("INSERT INTO seqSTORE (seq_name, seq_value) VALUES (%s, %s)", ("cnum", cnum))


def populate_cnums():
    """
    Populates table seqSTORE with the cnums present in CONFERENCE records
    """
    # First get all records from conference collection
    conf_records = perform_request_search(cc="Conferences", p="111__g:C*", rg=0)

    for recid in conf_records:
        cnum = record_get_field_value(get_bibrecord(recid), tag="111", ind1="", ind2="", code="g")
        if cnum:
            if not _cnum_exists(cnum):
                _insert_cnum(cnum)
                print "cnum %s from record %s inserted" % (cnum, recid)

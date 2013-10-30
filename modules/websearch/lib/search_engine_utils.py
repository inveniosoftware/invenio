# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

# pylint: disable=C0301

"""Invenio search engine utilities."""

from invenio.config import (CFG_BIBFORMAT_HIDDEN_TAGS,
                            CFG_CERN_SITE)
from invenio.dbquery import run_sql
from invenio.intbitset import intbitset

def get_fieldvalues(recIDs, tag, repetitive_values=True, sort=True, split_by=0):
    """
    Return list of field values for field TAG for the given record ID
    or list of record IDs.  (RECIDS can be both an integer or a list
    of integers.)

    If REPETITIVE_VALUES is set to True, then return all values even
    if they are doubled.  If set to False, then return unique values
    only.
    """
    out = []
    try:
        recIDs = int(recIDs)
    except (ValueError, TypeError):
        pass
    if isinstance(recIDs, (int, long)):
        recIDs = [recIDs, ]
    if not isinstance(recIDs, (list, tuple, intbitset)):
        return []
    if len(recIDs) == 0:
        return []
    if tag == "001___":
        # We have asked for tag 001 (=recID) that is not stored in bibXXx
        # tables.
        out = [str(recID) for recID in recIDs]
    else:
        # we are going to look inside bibXXx tables
        digits = tag[0:2]
        try:
            intdigits = int(digits)
            if intdigits < 0 or intdigits > 99:
                raise ValueError
        except ValueError:
            # invalid tag value asked for
            return []
        bx = "bib%sx" % digits
        bibx = "bibrec_bib%sx" % digits
        if not repetitive_values:
            queryselect = "DISTINCT(bx.value)"
        else:
            queryselect = "bx.value"

        if sort:
            sort_sql = "ORDER BY bibx.field_number, bx.tag ASC"
        else:
            sort_sql = ""

        def get_res(recIDs):
            query = "SELECT %s FROM %s AS bx, %s AS bibx " \
                    "WHERE bibx.id_bibrec IN (%s) AND bx.id=bibx.id_bibxxx AND " \
                    "bx.tag LIKE %%s %s" % \
                    (queryselect, bx, bibx, ("%s,"*len(recIDs))[:-1], sort_sql)
            return [i[0] for i in run_sql(query, tuple(recIDs) + (tag,))]

        #print not sort and split_by>0 and len(recIDs)>split_by
        if sort or split_by<=0 or len(recIDs)<=split_by:
            return get_res(recIDs)
        else:
            return [i for res in map(get_res, zip(*[iter(recIDs)]*split_by)) for i in res]

    return out


def get_fieldvalues_alephseq_like(recID, tags_in, can_see_hidden=False):
    """Return buffer of ALEPH sequential-like textual format with fields found
       in the list TAGS_IN for record RECID.

       If can_see_hidden is True, just print everything.  Otherwise hide fields
       from CFG_BIBFORMAT_HIDDEN_TAGS.
    """

    out = ""
    if type(tags_in) is not list:
        tags_in = [tags_in, ]
    if len(tags_in) == 1 and len(tags_in[0]) == 6:
        ## case A: one concrete subfield asked, so print its value if found
        ##         (use with care: can mislead if field has multiple occurrences)
        out += "\n".join(get_fieldvalues(recID, tags_in[0]))
    else:
        ## case B: print our "text MARC" format; works safely all the time
        # find out which tags to output:
        dict_of_tags_out = {}
        if not tags_in:
            for i in range(0, 10):
                for j in range(0, 10):
                    dict_of_tags_out["%d%d%%" % (i, j)] = 1
        else:
            for tag in tags_in:
                if len(tag) == 0:
                    for i in range(0, 10):
                        for j in range(0, 10):
                            dict_of_tags_out["%d%d%%" % (i, j)] = 1
                elif len(tag) == 1:
                    for j in range(0, 10):
                        dict_of_tags_out["%s%d%%" % (tag, j)] = 1
                elif len(tag) < 5:
                    dict_of_tags_out["%s%%" % tag] = 1
                elif tag >= 6:
                    dict_of_tags_out[tag[0:5]] = 1
        tags_out = dict_of_tags_out.keys()
        tags_out.sort()
        # search all bibXXx tables as needed:
        for tag in tags_out:
            digits = tag[0:2]
            try:
                intdigits = int(digits)
                if intdigits < 0 or intdigits > 99:
                    raise ValueError
            except ValueError:
                # invalid tag value asked for
                continue
            if tag.startswith("001") or tag.startswith("00%"):
                if out:
                    out += "\n"
                out += "%09d %s %d" % (recID, "001__", recID)
            bx = "bib%sx" % digits
            bibx = "bibrec_bib%sx" % digits
            query = "SELECT b.tag,b.value,bb.field_number FROM %s AS b, %s AS bb "\
                    "WHERE bb.id_bibrec=%%s AND b.id=bb.id_bibxxx AND b.tag LIKE %%s"\
                    "ORDER BY bb.field_number, b.tag ASC" % (bx, bibx)
            res = run_sql(query, (recID, str(tag)+'%'))
            # go through fields:
            field_number_old = -999
            field_old = ""
            for row in res:
                field, value, field_number = row[0], row[1], row[2]
                ind1, ind2 = field[3], field[4]
                printme = True
                #check the stuff in hiddenfields
                if not can_see_hidden:
                    for htag in CFG_BIBFORMAT_HIDDEN_TAGS:
                        ltag = len(htag)
                        samelenfield = field[0:ltag]
                        if samelenfield == htag:
                            printme = False
                if ind1 == "_":
                    ind1 = ""
                if ind2 == "_":
                    ind2 = ""
                # print field tag
                if printme:
                    if field_number != field_number_old or field[:-1] != field_old[:-1]:
                        if out:
                            out += "\n"
                        out += "%09d %s " % (recID, field[:5])
                        field_number_old = field_number
                        field_old = field
                    # print subfield value
                    if field[0:2] == "00" and field[-1:] == "_":
                        out += value
                    else:
                        out += "$$%s%s" % (field[-1:], value)
    return out


def record_exists(recID):
    """Return 1 if record RECID exists.
       Return 0 if it doesn't exist.
       Return -1 if it exists but is marked as deleted.
    """
    try: # if recid is '123foo', mysql will return id=123, and we don't want that
        recID = int(recID)
    except (ValueError, TypeError):
        return 0

    out = 0
    res = run_sql("SELECT id FROM bibrec WHERE id=%s", (recID,), 1)
    if res:
        # record exists; now check whether it isn't marked as deleted:
        dbcollids = get_fieldvalues(recID, "980__%")
        if ("DELETED" in dbcollids) or (CFG_CERN_SITE and "DUMMY" in dbcollids):
            out = -1 # exists, but marked as deleted
        else:
            out = 1 # exists fine
    return out

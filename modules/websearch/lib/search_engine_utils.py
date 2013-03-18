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
    except:
        pass
    if isinstance(recIDs, (int, long)):
        recIDs = [recIDs,]
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

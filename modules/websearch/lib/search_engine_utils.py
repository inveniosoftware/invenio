# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

def get_fieldvalues(recIDs, tag, repetitive_values=True, sort=True):
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
    if not isinstance(recIDs, (list, tuple)):
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
        queryparam = []
        for recID in recIDs:
            queryparam.append(recID)
        if not repetitive_values:
            queryselect = "DISTINCT(bx.value)"
        else:
            queryselect = "bx.value"

        if sort:
            sort_sql = "ORDER BY bibx.field_number, bx.tag ASC"
        else:
            sort_sql = ""

        query = "SELECT %s FROM %s AS bx, %s AS bibx " \
                "WHERE bibx.id_bibrec IN (%s) AND bx.id=bibx.id_bibxxx AND " \
                "bx.tag LIKE %%s %s" % \
                (queryselect, bx, bibx, ("%s,"*len(queryparam))[:-1], sort_sql)
        res = run_sql(query, tuple(queryparam) + (tag,))
        for row in res:
            out.append(row[0])
    return out

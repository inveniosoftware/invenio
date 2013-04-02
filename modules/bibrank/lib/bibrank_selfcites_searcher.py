# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
"""Self-citations searcher

"""
from invenio.dbquery import run_sql
from invenio.intbitset import intbitset


def get_self_cited_by(recid):
    sql = "SELECT citer FROM rnkSELFCITEDICT WHERE citee = %s"
    return intbitset(run_sql(sql, [recid]))


def get_self_cited_by_list(recids):
    in_sql = ','.join('%s' for dummy in recids)
    sql = "SELECT citee, citer FROM rnkSELFCITEDICT WHERE citee IN (%s)"
    cites = {}
    for citee, citer in run_sql(sql % in_sql, recids):
        cites.setdefault(citee, set()).add(citer)
    return [(recid, cites.get(recid, set())) for recid in recids]


def get_self_refers_to(recid):
    sql = "SELECT citee FROM rnkSELFCITEDICT WHERE citer = %s"
    return intbitset(run_sql(sql, [recid]))


def get_self_refers_to_list(recids):
    in_sql = ','.join('%s' for dummy in recids)
    sql = "SELECT citer, citee FROM rnkSELFCITEDICT WHERE citer IN (%s)"
    refs = {}
    for citer, citee in run_sql(sql % in_sql, recids):
        refs.setdefault(citer, set()).add(citee)
    return [(recid, refs.get(recid, set())) for recid in recids]

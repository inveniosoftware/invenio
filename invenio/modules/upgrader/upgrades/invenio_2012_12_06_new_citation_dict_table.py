# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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

import marshal
import time
from zlib import decompress

from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']


def info():
    return "Moves citation dictionary to the database"


def get_dict():
    ret = run_sql("""SELECT object_value
                     FROM rnkCITATIONDATA
                     WHERE object_name = 'citationdict'""")

    dic = None
    try:
        serialized = ret[0][0]
    except IndexError:
        pass
    else:
        if serialized:
            dic = marshal.loads(decompress(serialized))

    return dic


def do_upgrade():
    if not run_sql("SHOW TABLES LIKE 'rnkCITATIONDICT'"):
        run_sql("""
CREATE TABLE IF NOT EXISTS rnkCITATIONDICT (
  citee int(10) unsigned NOT NULL,
  citer int(10) unsigned NOT NULL,
  last_updated datetime NOT NULL,
  PRIMARY KEY id (citee, citer),
  KEY reverse (citer, citee)
) ENGINE=MyISAM;
""")
        dic = get_dict()
        if dic:
            for recid, cites in dic.iteritems():
                store_cites(recid, cites)
        run_sql("DROP TABLE IF EXISTS rnkCITATIONDATA")


def estimate():
    dic = get_dict()
    if dic:
        return sum(len(cites) for cites in dic.itervalues()) / 40
    else:
        return 1


def store_cites(recid, new_cites):
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    for cite in new_cites:
        run_sql("""INSERT INTO rnkCITATIONDICT (citee, citer, last_updated)
                   VALUES (%s, %s, %s)""", (recid, cite, now))

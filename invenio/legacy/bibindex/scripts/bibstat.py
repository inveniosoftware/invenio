# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2014,
#               2015 CERN.
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

from __future__ import print_function

"""
BibStat reports some interesting numbers on the bibliographic record set.
"""

__revision__ = "$Id$"

import getopt
import sys
import time

from invenio.base.factory import with_app_context


def report_table_status(tablename):
    """Report stats for the table TABLENAME.  If TABLENAME does not
       exists, return empty string.
    """
    from invenio.legacy.dbquery import get_table_status_info
    out = ""
    table_info = get_table_status_info(tablename)
    if table_info:
        out =  "%14s %17d %17d %17d" % (table_info['Name'],
                                        table_info['Rows'],
                                        table_info['Data_length'],
                                        table_info['Max_data_length']
                                        )
    return out


def report_definitions_of_physical_tags():
    """
    Report definitions of physical MARC tags.
    """
    from invenio.legacy.dbquery import run_sql
    print("### 1 - PHYSICAL TAG DEFINITIONS")
    print()
    print("# MARC tag ... description")
    res = run_sql('SELECT id,value,name FROM tag ORDER BY value')
    for row in res:
        (dummytagid, tagvalue, tagname) = row
        print("%s ... %s" % (tagvalue, tagname,))


def report_definitions_of_logical_fields():
    """
    Report definitions of logical fields.
    """
    from invenio.legacy.dbquery import run_sql
    print()
    print("### 2 - LOGICAL FIELD DEFINITIONS")
    print()
    print("# logical field: associated physical tags", end=' ')
    res = run_sql('SELECT id,name,code FROM field ORDER BY code')
    for row in res:
        (fieldid, dummyfieldname, fieldcode) = row
        print()
        print("%s:" % (fieldcode,), end=' ')
        res2 = run_sql("""SELECT value FROM tag, field_tag
                           WHERE id_field=%s AND id_tag=id
                       """, (fieldid,))
        for row2 in res2:
            tag = row2[0]
            print(tag, end=' ')
    print()


def report_definitions_of_indexes():
    """
    Report definitions of indexes.
    """
    from invenio.legacy.dbquery import run_sql
    print()
    print("### 3 - INDEX DEFINITIONS")
    print()
    print("# index (stemming): associated logical fields", end=' ')
    res = run_sql("""SELECT id,name,stemming_language FROM "idxINDEX"
                     ORDER BY name""")
    for row in res:
        (indexid, indexname, indexstem) = row
        if indexstem:
            indexname += ' (%s)' % indexstem
        print()
        print("%s:" % (indexname,), end=' ')
        res2 = run_sql("""SELECT code FROM field, "idxINDEX_field"
                           WHERE "id_idxINDEX"=%s AND id_field=id
                       """, (indexid,))
        for row2 in res2:
            code = row2[0]
            print(code, end=' ')
    print()


def report_on_all_bibliographic_tables():
    """Report stats for all the interesting bibliographic tables."""
    print()
    print("### 4 -  TABLE SPACE AND SIZE INFO")
    print('')
    print("# %12s %17s %17s %17s" % ("TABLE", "ROWS", "DATA SIZE", "INDEX SIZE"))
    for i in range(0, 10):
        for j in range(0, 10):
            print(report_table_status("bib%1d%1dx" % (i, j)))
            print(report_table_status("bibrec_bib%1d%1dx" % (i, j)))
    for i in range(0, 11):
        print(report_table_status("idxWORD%02dF" % i))
        print(report_table_status("idxWORD%02dR" % i))
    for i in range(0, 11):
        print(report_table_status("idxPHRASE%02dF" % i))
        print(report_table_status("idxPHRASE%02dR" % i))
    return


def report_tag_usage():
    """Analyze bibxxx tables and report info on usage of various tags."""
    print('')
    print("### 5 -  TAG USAGE INFO")
    print('')
    print("# TAG     NB_RECORDS\t# recID1 recID2 ... recID9 (example records)")
    from invenio.legacy.dbquery import run_sql
    for i in range(0, 10):
        for j in range(0, 10):
            bibxxx = "bib%1d%1dx" % (i, j)
            bibrec_bibxxx = 'bibrec_' + bibxxx
            # detect all the various tags in use:
            res = run_sql("SELECT DISTINCT(tag) FROM %s" % (bibxxx,))
            for row in res:
                tag = row[0]
                # detect how many records have this tag in use:
                res_usage = run_sql("""SELECT DISTINCT(b.id) FROM bibrec AS b,
                                                           %s AS bb, %s AS bx
                                            WHERE b.id=bb.id_bibrec
                                              AND bb.id_bibxxx=bx.id
                                              AND bx.tag=%%s
                                        """ % (bibrec_bibxxx, bibxxx),
                                    (tag,))
                # print results
                print(tag, (8-len(tag))*' ', len(res_usage), \
                      '\t\t', '#', " ".join([str(row[0]) for row in
                                             res_usage[:9]]))


def report_header():
    """
    Start reporting.
    """
    from invenio.config import CFG_DATABASE_HOST, \
        CFG_DATABASE_PORT, CFG_DATABASE_NAME
    print('### BIBSTAT REPORT FOR DB %s:%s.%s RUN AT %s' % (CFG_DATABASE_HOST,
                                                         CFG_DATABASE_PORT,
                                                         CFG_DATABASE_NAME,
                                                         time.asctime()))
    print('')


def report_footer():
    """
    Stop reporting.
    """
    print()
    print()
    print('### END OF BIBSTAT REPORT')


def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s [options]\n" % sys.argv[0])
    sys.stderr.write("General options:\n")
    sys.stderr.write("  -h, --help      \t\t Print this help.\n")
    sys.stderr.write("  -V, --version   \t\t Print version information.\n")
    sys.exit(exitcode)


@with_app_context()
def main():
    """Report stats on the Invenio bibliographic tables."""
    try:
        opts, dummyargs = getopt.getopt(sys.argv[1:], "hV", ["help", "version"])
    except getopt.GetoptError as err:
        usage(1, err)
    if opts:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage(0)
            elif opt[0] in ["-V", "--version"]:
                print(__revision__)
                sys.exit(0)
            else:
                usage(1)
    else:
        report_header()
        report_definitions_of_physical_tags()
        report_definitions_of_logical_fields()
        report_definitions_of_indexes()
        report_on_all_bibliographic_tables()
        report_tag_usage()
        report_footer()

# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibEdit CLI tool.

Usage: bibedit [options]

General options:
   -h, --help                          print this help
   -V, --version                       print version number

Options to inspect record history:
   --list-revisions [recid]            list all revisions of a record
   --get-revision [recid.revdate]      print MARCXML of given record revision
   --diff-revisions [recidA.revdateB]  print MARCXML difference between record A
                    [recidC.revdateD]   dated B and record C dated D
"""

__revision__ = "$Id$"

import re
import sys
import zlib
import difflib

_RE_RECORD_REVISION_FORMAT = re.compile(r'^(\d+)\.(\d{14})$')

from invenio.dbquery import run_sql

def print_usage():
    """Print help."""
    print __doc__

def print_version():
    """Print version information."""
    print __revision__

def list_record_revisions(recid):
    """
    Return list of all known MARCXML revisions for record RECID.
    """
    out = []
    res =  run_sql("""SELECT DATE_FORMAT(job_date, '%%Y%%m%%d%%H%%i%%s')
                       FROM hstRECORD WHERE id_bibrec=%s""",
                   (recid,))
    for row in res:
        out.append(recid + '.' + row[0])
    return out

def revision_valid_p(revid):
    """
    Predicate to test validity of revision ID.
    """
    if _RE_RECORD_REVISION_FORMAT.match(revid):
        return True
    return False

def get_marcxml_of_record_revision(revid):
    """
    Return MARCXML string with corresponding to revision REVID of a
    record.  Return empty string if revision does not exist.  REVID is
    assumed to be washed already.
    """
    out = ""
    match = _RE_RECORD_REVISION_FORMAT.match(revid)
    recid = match.group(1)
    revdate = match.group(2)
    job_date = "%s-%s-%s %s:%s:%s" % (revdate[0:4], revdate[4:6],
                                      revdate[6:8], revdate[8:10],
                                      revdate[10:12], revdate[12:14],)
    res =  run_sql("""SELECT marcxml FROM hstRECORD
                       WHERE id_bibrec=%s AND job_date=%s""",
                   (recid, job_date))
    if res:
        for row in res:
            out += zlib.decompress(row[0]) + "\n"
    return out

def cli_list_revisions(recid):
    """
    Print list of all known MARCXML revisions for record RECID.
    """
    print "\n".join(list_record_revisions(recid))

def cli_get_revision(revid):
    """
    Return MARCXML revision REVID (=RECID.REVDATE) of a record.
    Exit if things went wrong.
    """
    if not revision_valid_p(revid):
        print "ERROR: revision %s is invalid; " \
              "must be NNN.YYYYMMDDhhmmss." % revid
        sys.exit(1)
    out =  get_marcxml_of_record_revision(revid)
    if out:
        print out
    else:
        print "ERROR: Revision %s not found." % revid

def cli_diff_revisions(revid1, revid2):
    """
    Return diffs of MARCXML record revisions REVID1, REVID2.
    Exit if things went wrong.
    """
    for revid in [revid1, revid2]:
        if not revision_valid_p(revid):
            print "ERROR: revision %s is invalid; " \
                  "must be NNN.YYYYMMDDhhmmss." % revid
            sys.exit(1)
    xml1 = get_marcxml_of_record_revision(revid1)
    xml2 = get_marcxml_of_record_revision(revid2)
    print "".join(difflib.unified_diff(xml1.splitlines(1),
                                       xml2.splitlines(1),
                                       revid1,
                                       revid2,))

def main():
    """Main entry point."""
    if '--help' in sys.argv or \
       '-h' in sys.argv:
        print_usage()
    elif '--version' in sys.argv or \
         '-V' in sys.argv:
        print_version()
    else:
        try:
            cmd = sys.argv[1]
            opts = sys.argv[2:]
            if not opts:
                raise IndexError
        except IndexError:
            print_usage()
            sys.exit(1)
        if cmd == '--list-revisions':
            try:
                recid = opts[0]
            except IndexError:
                print_usage()
                sys.exit(1)
            cli_list_revisions(recid)
        elif cmd == '--get-revision':
            try:
                revid = opts[0]
            except IndexError:
                print_usage()
                sys.exit(1)
            cli_get_revision(revid)
        elif cmd == '--diff-revisions':
            try:
                revid1 = opts[0]
                revid2 = opts[1]
            except IndexError:
                print_usage()
                sys.exit(1)
            cli_diff_revisions(revid1, revid2)
        else:
            print """ERROR: Please specify a command.  Please see '--help'."""
            sys.exit(1)

if __name__ == '__main__':
    main()

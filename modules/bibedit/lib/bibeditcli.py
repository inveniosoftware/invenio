## -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011 CERN.
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

# pylint: disable=C0103
"""
BibEdit CLI tool.

Usage: bibedit [options]

General options::
     -h, --help                     print this help
     -V, --version                  print version number

Options to inspect record history::
    --list-revisions [recid]              list all revisions of a record
    --list-revisions-details [recid]      list detailed revisions of a record
    --get-revision [recid.revdate]        print MARCXML of given record revision
    --diff-revisions [recidA.revdateB]    print MARCXML difference between
    [recidC.revdateD]    record A dated B and record C dated D
    --revert-to-revision [recid.revdate]  submit given record revision to
    become current revision

"""

__revision__ = "$Id$"

import sys

from invenio.bibedit_utils import get_marcxml_of_revision_id, \
    get_record_revision_ids, get_xml_comparison, record_locked_by_other_user, \
    record_locked_by_queue, revision_format_valid_p, save_xml_record, \
    split_revid, get_info_of_revision_id

def print_usage():
    """Print help."""
    print __doc__

def print_version():
    """Print version information."""
    print __revision__

def cli_list_revisions(recid, details=False):
    """Print list of all known record revisions (=RECID.REVDATE) for record
    RECID.
    """
    try:
        recid = int(recid)
    except ValueError:
        print 'ERROR: record ID must be integer, not %s.' % recid
        sys.exit(1)
    record_rev_list = get_record_revision_ids(recid)
    if not details:
        out = '\n'.join(record_rev_list)
    else:
        out = "%s %s %s %s\n" % ("# Revision".ljust(22), "# Task ID".ljust(15),
                              "# Author".ljust(15), "# Job Details")
        out += '\n'.join([get_info_of_revision_id(revid) for revid in record_rev_list])
    if out:
        print out
    else:
        print 'ERROR: Record %s not found.' % recid

def cli_get_revision(revid):
    """Return MARCXML for record revision REVID (=RECID.REVDATE) of a record."""
    if not revision_format_valid_p(revid):
        print 'ERROR: revision %s is invalid; ' \
              'must be NNN.YYYYMMDDhhmmss.' % revid
        sys.exit(1)
    out =  get_marcxml_of_revision_id(revid)
    if out:
        print out
    else:
        print 'ERROR: Revision %s not found.' % revid

def cli_diff_revisions(revid1, revid2):
    """Return diffs of MARCXML for record revisions REVID1, REVID2."""
    for revid in [revid1, revid2]:
        if not revision_format_valid_p(revid):
            print 'ERROR: revision %s is invalid; ' \
                  'must be NNN.YYYYMMDDhhmmss.' % revid
            sys.exit(1)
    xml1 = get_marcxml_of_revision_id(revid1)
    if not xml1:
        print 'ERROR: Revision %s not found. ' % revid1
        sys.exit(1)
    xml2 = get_marcxml_of_revision_id(revid2)
    if not xml2:
        print 'ERROR: Revision %s not found. ' % revid2
        sys.exit(1)
    print get_xml_comparison(revid1, revid2, xml1, xml2)

def cli_revert_to_revision(revid):
    """Submit specified record revision REVID upload, to replace current
    version.

    """
    if not revision_format_valid_p(revid):
        print 'ERROR: revision %s is invalid; ' \
              'must be NNN.YYYYMMDDhhmmss.' % revid
        sys.exit(1)

    xml_record = get_marcxml_of_revision_id(revid)
    if xml_record == '':
        print 'ERROR: Revision %s does not exist. ' % revid
        sys.exit(1)

    recid = split_revid(revid)[0]

    if record_locked_by_other_user(recid, -1):
        print 'The record is currently being edited. ' \
            'Please try again in a few minutes.'
        sys.exit(1)

    if record_locked_by_queue(recid):
        print 'The record is locked because of unfinished upload tasks. ' \
            'Please try again in a few minutes.'
        sys.exit(1)

    save_xml_record(recid, 0, xml_record)
    print 'Your modifications have now been submitted. They will be ' \
        'processed as soon as the task queue is empty.'

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
            cli_list_revisions(recid, details=False)
        elif cmd == '--list-revisions-details':
            try:
                recid = opts[0]
            except IndexError:
                print_usage()
                sys.exit(1)
            cli_list_revisions(recid, details=True)
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
        elif cmd == '--revert-to-revision':
            try:
                revid = opts[0]
            except IndexError:
                print_usage()
                sys.exit(1)
            cli_revert_to_revision(revid)
        else:
            print "ERROR: Please specify a command.  Please see '--help'."
            sys.exit(1)

if __name__ == '__main__':
    main()

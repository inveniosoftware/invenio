# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013, 2015 CERN.
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
    --diff-revisions [recidA.revdateB] [recidC.revdateD] print MARCXML difference between
                                          record A dated B and record C dated D
    --revert-to-revision [recid.revdate]  submit given record revision to
                                          become current revision
    --check-revisions [recid]             check if revisions are not corrupted
                                          (* stands for all records)
    --fix-revisions [recid]               fix revisions that are corrupted
                                          (* stands for all records)
    --clean-revisions [recid]             clean duplicate revisions
                                          (* stands for all records)

"""

__revision__ = "$Id$"

import sys
import zlib
from invenio.legacy.dbquery import run_sql
from intbitset import intbitset
from invenio.legacy.bibedit.utils import get_marcxml_of_revision_id, \
    get_record_revision_ids, get_xml_comparison, record_locked_by_other_user, \
    record_locked_by_queue, revision_format_valid_p, save_xml_record, \
    split_revid, get_info_of_revision_id, get_record_revisions
from invenio.legacy.bibrecord import create_record, records_identical

def print_usage():
    """Print help."""
    print(__doc__)

def print_version():
    """Print version information."""
    print(__revision__)

def cli_clean_revisions(recid, dry_run=True, verbose=True):
    """Clean revisions of the given recid, by removing duplicate revisions
    that do not change the content of the record."""
    if recid == '*':
        recids = intbitset(run_sql("SELECT DISTINCT id_bibrec FROM hstRECORD"))
    else:
        try:
            recids = [int(recid)]
        except ValueError:
            print('ERROR: record ID must be integer, not %s.' % recid)
            sys.exit(1)
    for recid in recids:
        all_revisions = run_sql("SELECT marcxml, job_id, job_name, job_person, job_date FROM hstRECORD WHERE id_bibrec=%s ORDER BY job_date ASC", (recid,))
        previous_rec = {}
        deleted_revisions = 0
        for marcxml, job_id, job_name, job_person, job_date in all_revisions:
            try:
                current_rec = create_record(zlib.decompress(marcxml))[0]
            except Exception:
                print("ERROR: corrupted revisions found. Please run %s --fix-revisions '*'" % sys.argv[0], file=sys.stderr)
                sys.exit(1)
            if records_identical(current_rec, previous_rec):
                deleted_revisions += 1
                if not dry_run:
                    run_sql("DELETE FROM hstRECORD WHERE id_bibrec=%s AND job_id=%s AND job_name=%s AND job_person=%s AND job_date=%s", (recid, job_id, job_name, job_person, job_date))
            previous_rec = current_rec
        if verbose and deleted_revisions:
            print("record %s: deleted %s duplicate revisions out of %s" % (recid, deleted_revisions, len(all_revisions)))
    if verbose:
        print("DONE")

def cli_list_revisions(recid, details=False):
    """Print list of all known record revisions (=RECID.REVDATE) for record
    RECID.
    """
    try:
        recid = int(recid)
    except ValueError:
        print('ERROR: record ID must be integer, not %s.' % recid)
        sys.exit(1)
    record_rev_list = get_record_revision_ids(recid)
    if not details:
        out = '\n'.join(record_rev_list)
    else:
        out = "%s %s %s %s\n" % ("# Revision".ljust(22), "# Task ID".ljust(15),
                              "# Author".ljust(15), "# Job Details")
        out += '\n'.join([get_info_of_revision_id(revid) for revid in record_rev_list])
    if out:
        print(out)
    else:
        print('ERROR: Record %s not found.' % recid)

def cli_get_revision(revid):
    """Return MARCXML for record revision REVID (=RECID.REVDATE) of a record."""
    if not revision_format_valid_p(revid):
        print('ERROR: revision %s is invalid; ' \
              'must be NNN.YYYYMMDDhhmmss.' % revid)
        sys.exit(1)
    out = get_marcxml_of_revision_id(revid)
    if out:
        print(out)
    else:
        print('ERROR: Revision %s not found.' % revid)

def cli_diff_revisions(revid1, revid2):
    """Return diffs of MARCXML for record revisions REVID1, REVID2."""
    for revid in [revid1, revid2]:
        if not revision_format_valid_p(revid):
            print('ERROR: revision %s is invalid; ' \
                  'must be NNN.YYYYMMDDhhmmss.' % revid)
            sys.exit(1)
    xml1 = get_marcxml_of_revision_id(revid1)
    if not xml1:
        print('ERROR: Revision %s not found. ' % revid1)
        sys.exit(1)
    xml2 = get_marcxml_of_revision_id(revid2)
    if not xml2:
        print('ERROR: Revision %s not found. ' % revid2)
        sys.exit(1)
    print(get_xml_comparison(revid1, revid2, xml1, xml2))

def cli_revert_to_revision(revid):
    """Submit specified record revision REVID upload, to replace current
    version.

    """
    if not revision_format_valid_p(revid):
        print('ERROR: revision %s is invalid; ' \
              'must be NNN.YYYYMMDDhhmmss.' % revid)
        sys.exit(1)

    xml_record = get_marcxml_of_revision_id(revid)
    if xml_record == '':
        print('ERROR: Revision %s does not exist. ' % revid)
        sys.exit(1)

    recid = split_revid(revid)[0]

    if record_locked_by_other_user(recid, -1):
        print('The record is currently being edited. ' \
            'Please try again in a few minutes.')
        sys.exit(1)

    if record_locked_by_queue(recid):
        print('The record is locked because of unfinished upload tasks. ' \
            'Please try again in a few minutes.')
        sys.exit(1)

    save_xml_record(recid, 0, xml_record)
    print('Your modifications have now been submitted. They will be ' \
        'processed as soon as the task queue is empty.')


def check_rev(recid, verbose=True, fix=False):
    revisions = get_record_revisions(recid)
    for recid, job_date in revisions:
        rev = '%s.%s' % (recid, job_date)
        try:
            get_marcxml_of_revision_id(rev)
            if verbose:
                print('%s: ok' % rev)
        except zlib.error:
            print('%s: invalid' % rev)
            if fix:
                fix_rev(recid, job_date, verbose)


def fix_rev(recid, job_date, verbose=True):
    sql = """DELETE FROM hstRECORD WHERE id_bibrec = %s AND job_date = '%s' """
    run_sql(sql, (recid, job_date))


def cli_check_revisions(recid):
    if recid == '*':
        print('Checking all records')
        recids = intbitset(run_sql("SELECT id FROM bibrec ORDER BY id"))
        for index, rec in enumerate(recids):
            if index % 1000 == 0 and index:
                print(index, 'records processed')
            check_rev(rec, verbose=False)
    else:
        check_rev(recid)


def cli_fix_revisions(recid):
    if recid == '*':
        print('Fixing all records')
        recids = intbitset(run_sql("SELECT id FROM bibrec ORDER BY id"))
        for index, rec in enumerate(recids):
            if index % 1000 == 0 and index:
                print(index, 'records processed')
            check_rev(rec, verbose=False, fix=True)
    else:
        check_rev(recid, fix=True)


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
        elif cmd == '--check-revisions':
            try:
                recid = opts[0]
            except IndexError:
                recid = '*'
            cli_check_revisions(recid)
        elif cmd == '--fix-revisions':
            try:
                recid = opts[0]
            except IndexError:
                recid = '*'
            cli_fix_revisions(recid)
        elif cmd == '--clean-revisions':
            try:
                recid = opts[0]
            except IndexError:
                recid = '*'
            cli_clean_revisions(recid, dry_run=False)
        else:
            print("ERROR: Please specify a command.  Please see '--help'.")
            sys.exit(1)

if __name__ == '__main__':
    main()

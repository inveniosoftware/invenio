# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2015 CERN.
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
"""
WebSubmitAdmin CLI tool.

from __future__ import print_function

Usage websubmitadmin [options]

Options:
  -v, --verbose                Verbose level (0=min, 2=default, 3=max).
  -h, --help                   Prints this help
  -d, --dump=DOCTYPE           Dump given DOCTYPE from database
  -c, --clean={y|n}            Create dump that includes lines to remove
                               submission from database before
                               insertion (`y', default) or not (`n'). Default 'y'
  -n, --no-fail-insert         Create dump that does not fail when inserting
                               duplicate rows
  -f, --diff=DOCTYPE           Diff given DOCTYPE from database with standard input
  -i, --ignore={d|o|p}         Ignore some differences (d=date, o=order, p=page). Use with --diff
  -m, --method=METHOD          Type of dumps: NAMES (default) or RELATIONS:
                               - NAMES: includes functions and elements (including
                                        definitions) with a name starting with doctype,
                                        even if not used by the submission. Might then miss
                                        functions and elements (mostly ``generic'' ones) and
                                        add some unwanted elements.
                               - RELATIONS: include all functions and elements used
                                            by the submission. Might leave aside
                                            elements that are defined, but not
                                            used.

Dump submission:
Eg: websubmitadmin --dump=DEMOART > DEMOART_db_dump.sql

Dump submission including all used functions and elements definitions:
Eg: websubmitadmin --dump=DEMOART -m relations > DEMOART_db_dump.sql

Diff submission with given dump:
Eg: websubmitadmin --diff=DEMOART < DEMOART_db_dump.sql

Diff between latest version in 'master' branch of your Git repo, with
version in database:
Eg: git show master:websubmit/DEMOART_db_dump.sql | ../websubmitadmin --diff=DEMOART  | less -S

Diff between CVS version and submission in database, ignoring dates
and ordering of submission fields on the page:
Eg: cvs update -p DEMOART_db_dump.sql | ./websubmitadmin -i d,o --diff=DEMOART | less -S
"""

__revision__ = "$Id$"

import os
import sys
import getopt
import difflib
import re
import time
import tempfile
from MySQLdb.converters import conversions
from MySQLdb import escape, escape_string
from invenio.config import CFG_TMPDIR
from invenio.legacy.dbquery import run_sql
from invenio.utils.shell import run_shell_command

CFG_WEBSUBMIT_DUMPER_DEFAULT_METHOD = "NAMES"
CFG_WEBSUBMIT_DUMPER_DB_SCHEMA_VERSION = 1

def dump_submission(doctype, method=None, include_cleaning=True,
                    ignore_duplicate_insert=False):
    """Returns a .sql dump of submission with given doctype"""

    def build_table_dump(table_name, rows_with_desc, ignore_duplicate_insert):
        "Build a dump-like output from the given table and rows"
        table_dump = ''
        for row in rows_with_desc[0]:
            table_dump += 'INSERT%s INTO %s VALUES (%s);\n' % \
                          (ignore_duplicate_insert and ' IGNORE' or '',
                           table_name,
                           ','.join([escape(column, conversions) for column in row]))
        return table_dump

    if not method:
        method = CFG_WEBSUBMIT_DUMPER_DEFAULT_METHOD

    dump_header = "-- %s dump %s v%i\n" % (doctype,
                                           time.strftime("%Y-%m-%d %H:%M:%S"),
                                           CFG_WEBSUBMIT_DUMPER_DB_SCHEMA_VERSION)
    if method == "NAMES":
        dump_header += "-- Extra:NAMES (the following dump contains rows in sbmALLFUNCDESCR, sbmFUNDESC, sbmFIELD and sbmFIELDDESC tables which are not specific to this submission, but that include keyword %s)\n" % doctype
    elif method == "RELATIONS":
        dump_header += "-- Extra:RELATIONS (the following dump contains rows in sbmALLFUNCDESCR, sbmFUNDESC, sbmFIELD and sbmFIELDDESC tables that are not specific to doctype %s\n" % doctype
    else:
        dump_header += "-- Extra:None (the following dump only has rows specific to submission %s i.e. does not contains rows from sbmALLFUNCDESCR, sbmFUNDESC, sbmFIELD and sbmFIELDDESC tables\n" % doctype

    if include_cleaning:
        if method == 'NAMES':
            dump_header += """
DELETE FROM sbmFUNDESC WHERE function LIKE '%(doctype)s%%';
DELETE FROM sbmFIELD WHERE subname LIKE '%%%(doctype)s';
DELETE FROM sbmFIELDDESC WHERE name LIKE '%(doctype)s%%';
DELETE FROM sbmALLFUNCDESCR WHERE function LIKE '%(doctype)s%%';
""" % {'doctype': escape_string(doctype)}
        elif method == "RELATIONS":
            dump_header += """
DELETE sbmALLFUNCDESCR.* FROM sbmALLFUNCDESCR, sbmFUNCTIONS WHERE sbmALLFUNCDESCR.function=sbmFUNCTIONS.function and sbmFUNCTIONS.doctype='%(doctype)s';
DELETE sbmFUNDESC.* FROM sbmFUNDESC, sbmFUNCTIONS WHERE sbmFUNDESC.function=sbmFUNCTIONS.function and sbmFUNCTIONS.doctype='%(doctype)s';
DELETE sbmFIELDDESC.* FROM sbmFIELDDESC, sbmFIELD, sbmIMPLEMENT WHERE sbmFIELD.fidesc=sbmFIELDDESC.name AND sbmFIELD.subname=sbmIMPLEMENT.subname AND sbmIMPLEMENT.docname='%(doctype)s';
DELETE sbmFIELD.* FROM sbmFIELD, sbmIMPLEMENT WHERE sbmFIELD.subname=sbmIMPLEMENT.subname AND sbmIMPLEMENT.docname='%(doctype)s';
""" % {'doctype': escape_string(doctype)}

        dump_header += """DELETE FROM sbmDOCTYPE WHERE sdocname='%(doctype)s';
DELETE FROM sbmCATEGORIES WHERE doctype ='%(doctype)s';
DELETE FROM sbmFUNCTIONS WHERE doctype='%(doctype)s';
DELETE FROM sbmIMPLEMENT WHERE docname='%(doctype)s';
DELETE FROM sbmPARAMETERS WHERE doctype='%(doctype)s';
""" % {'doctype': escape_string(doctype)}

    dump_output = ''
    res = run_sql('SELECT * FROM sbmDOCTYPE WHERE sdocname=%s', (doctype,), with_desc=1)
    dump_output += build_table_dump('sbmDOCTYPE', res, ignore_duplicate_insert)
    res = run_sql('SELECT * FROM sbmCATEGORIES WHERE doctype=%s', (doctype,), with_desc=1)
    dump_output += build_table_dump('sbmCATEGORIES', res, ignore_duplicate_insert)
#    res = run_sql("SELECT * FROM sbmFIELD WHERE subname like '%%%s'" % (escape_string(doctype),), with_desc=1)
#    dump_output += build_table_dump('sbmFIELD', res)
#    res = run_sql("SELECT * FROM sbmFIELDDESC WHERE  name like '%s%%'" % (escape_string(doctype),), with_desc=1)
#    dump_output += build_table_dump('sbmFIELDDESC', res)
    res = run_sql('SELECT * FROM sbmFUNCTIONS WHERE doctype=%s', (doctype,), with_desc=1)
    dump_output += build_table_dump('sbmFUNCTIONS', res, ignore_duplicate_insert)
    res = run_sql('SELECT * FROM sbmIMPLEMENT WHERE docname=%s', (doctype,), with_desc=1)
    dump_output += build_table_dump('sbmIMPLEMENT', res, ignore_duplicate_insert)
    res = run_sql('SELECT * FROM sbmPARAMETERS WHERE doctype=%s', (doctype,), with_desc=1)
    dump_output += build_table_dump('sbmPARAMETERS', res, ignore_duplicate_insert)

    if method == "NAMES":
        res = run_sql("SELECT * FROM sbmALLFUNCDESCR WHERE function LIKE '%s%%'" % (escape_string(doctype),), with_desc=1)
        dump_output += build_table_dump('sbmALLFUNCDESCR', res, ignore_duplicate_insert)
        res = run_sql("SELECT * FROM sbmFUNDESC WHERE function LIKE '%s%%'" % (escape_string(doctype),), with_desc=1)
        dump_output += build_table_dump('sbmFUNDESC', res, ignore_duplicate_insert)
        res = run_sql("SELECT * FROM sbmFIELD WHERE subname LIKE '%%%s'" % (escape_string(doctype),), with_desc=1)
        dump_output += build_table_dump('sbmFIELD', res, ignore_duplicate_insert)
        res = run_sql("SELECT * FROM sbmFIELDDESC WHERE name LIKE '%s%%'" % (escape_string(doctype),), with_desc=1)
        dump_output += build_table_dump('sbmFIELDDESC', res, ignore_duplicate_insert)
    elif method == "RELATIONS":
        res = run_sql("SELECT DISTINCT sbmALLFUNCDESCR.* FROM sbmALLFUNCDESCR, sbmFUNCTIONS WHERE sbmALLFUNCDESCR.function=sbmFUNCTIONS.function and sbmFUNCTIONS.doctype=%s",  \
                      (doctype,), with_desc=1)
        dump_output += build_table_dump('sbmALLFUNCDESCR', res, ignore_duplicate_insert)
        res = run_sql("SELECT DISTINCT sbmFUNDESC.* FROM sbmFUNDESC, sbmFUNCTIONS WHERE sbmFUNDESC.function=sbmFUNCTIONS.function and sbmFUNCTIONS.doctype=%s",  \
                                            (doctype,), with_desc=1)
        dump_output += build_table_dump('sbmFUNDESC', res, ignore_duplicate_insert)

        res = run_sql("SELECT DISTINCT sbmFIELD.* FROM sbmFIELD, sbmIMPLEMENT WHERE sbmFIELD.subname=sbmIMPLEMENT.subname AND sbmIMPLEMENT.docname=%s",  \
                      (doctype,), with_desc=1)
        dump_output += build_table_dump('sbmFIELD', res, ignore_duplicate_insert)
        # check:
        res = run_sql("SELECT DISTINCT sbmFIELDDESC.* FROM sbmFIELDDESC, sbmFIELD, sbmIMPLEMENT WHERE sbmFIELD.fidesc=sbmFIELDDESC.name AND sbmFIELD.subname=sbmIMPLEMENT.subname AND sbmIMPLEMENT.docname=%s",  \
                      (doctype,), with_desc=1)
        #res = run_sql("SELECT DISTINCT sbmFIELDDESC.* FROM sbmFIELDDESC, sbmFIELD, sbmIMPLEMENT WHERE sbmFIELD.fidesc=sbmFIELDDESC.name AND sbmFIELDDESC.name=sbmIMPLEMENT.subname AND sbmIMPLEMENT.docname=%s",  \
        #              (doctype,), with_desc=1)
        dump_output += build_table_dump('sbmFIELDDESC', res, ignore_duplicate_insert)

    # Sort
    dump_output_lines = dump_output.splitlines()
    dump_output_lines.sort()

    return dump_header + '\n'.join(dump_output_lines)

def remove_submission(doctype, method=CFG_WEBSUBMIT_DUMPER_DEFAULT_METHOD):
    "Remove submission from database"
    # NOT TESTED
    if method == "NAMES":
        run_sql("DELETE FROM sbmFUNDESC WHERE function LIKE '%s%%'" % (doctype,))
        run_sql("DELETE FROM sbmFIELD WHERE subname LIKE '%%%s'" % (doctype,))
        run_sql("DELETE FROM sbmFIELDDESC WHERE  name LIKE '%s%%'" % (doctype,))
        run_sql("DELETE FROM sbmALLFUNCDESCR WHERE function LIKE '%s%%'" % (doctype,))
    elif method == "RELATIONS":
        run_sql("DELETE sbmALLFUNCDESCR.* FROM sbmALLFUNCDESCR, sbmFUNCTIONS WHERE sbmALLFUNCDESCR.function=sbmFUNCTIONS.function and sbmFUNCTIONS.doctype=%s", (doctype,))
        run_sql("DELETE sbmFUNDESC.* FROM sbmFUNDESC, sbmFUNCTIONS WHERE sbmFUNDESC.function=sbmFUNCTIONS.function and sbmFUNCTIONS.doctype=%s", (doctype,))
        run_sql("DELETE sbmFIELDDESC.* FROM sbmFIELDDESC, sbmFIELD, sbmIMPLEMENT WHERE sbmFIELD.fidesc=sbmFIELDDESC.name AND sbmFIELD.subname=sbmIMPLEMENT.subname AND sbmIMPLEMENT.docname=%s", (doctype,))
        run_sql("DELETE sbmFIELD.* FROM sbmFIELD, sbmIMPLEMENT WHERE sbmFIELD.subname=sbmIMPLEMENT.subname AND sbmIMPLEMENT.docname=%s", (doctype,))

    run_sql("DELETE FROM sbmDOCTYPE WHERE sdocname=%s", (doctype,))
    run_sql("DELETE FROM sbmCATEGORIES WHERE doctype=%s", (doctype,))
    run_sql("DELETE FROM sbmFUNCTIONS WHERE doctype=%s", (doctype,))
    run_sql("DELETE FROM sbmIMPLEMENT WHERE docname=%s", (doctype,))
    run_sql("DELETE FROM sbmPARAMETERS WHERE doctype=%s", (doctype,))

re_method_pattern = re.compile("-- Extra:(?P<method>\S*)\s")
def load_submission(doctype, dump, method=None):
    "Insert submission into database. Return tuple(error code, msg)"
    # NOT TESTED
    messages = []
    def guess_dump_method(dump):
        """Guess which method was used to dump this file (i.e. if it contains all the submission rows or not)"""
        match_obj = re_method_pattern.search(dump)
        if match_obj:
            return match_obj.group('method')
        else:
            return None

    def guess_dump_has_delete_statements(dump):
        """Guess if given submission dump already contain delete statements"""
        return "DELETE FROM sbmDOCTYPE WHERE sdocname".lower() in dump.lower()

    if not method:
        method = guess_dump_method(dump)
        if method is None:
            method = CFG_WEBSUBMIT_DUMPER_DEFAULT_METHOD
            messages.append("WARNING: method could not be guessed. Using method %s" % method)
        else:
            messages.append("Used method %s to load data" % method)

    (dump_code, dump_path) = tempfile.mkstemp(prefix=doctype, dir=CFG_TMPDIR)
    dump_fd = open(dump_path, 'w')
    dump_fd.write(dump)
    dump_fd.close()

    # We need to remove the submission. But let's create a backup first.
    submission_backup = dump_submission(doctype, method)
    submission_backup_path = "%s_db_dump%s.sql" % (doctype, time.strftime("%Y%m%d_%H%M%S"))
    fd = file(os.path.join(CFG_TMPDIR, submission_backup_path), "w")
    fd.write(submission_backup)
    fd.close()
    if not guess_dump_has_delete_statements(dump):
        remove_submission(doctype, method)

    # Load the dump
    (exit_code, out_msg, err_msg) = run_shell_command("dbexec < %s", (os.path.abspath(dump_path)))
    if exit_code:
        messages.append("ERROR: failed to load submission:" + err_msg)
        return (1, messages)

    messages.append("Submission loaded. Previous submission saved to %s" % os.path.join(CFG_TMPDIR, submission_backup_path))
    return (0, messages)

def diff_submission(submission1_dump, submission2_dump, verbose=2,
                    ignore_dates=False, ignore_positions=False, ignore_pages=False):
    "Output diff between submissions"

    def clean_line(line, ignore_dates, ignore_positions, ignore_pages):
        "Clean one line of the submission"
        updated_line = line
        if ignore_dates:
            if line.startswith('INSERT INTO sbmFIELD VALUES'):
                args = updated_line.split(",")
                args[-3] = ''
                args[-4] = ''
                updated_line = ','.join(args)
            elif line.startswith('INSERT INTO sbmFIELDDESC VALUES'):
                args = updated_line.split(",")
                args[-4] = ''
                args[-5] = ''
                updated_line = ','.join(args)
            elif line.startswith('INSERT INTO sbmIMPLEMENT VALUES '):
                args = updated_line.split(",")
                args[-6] = ''
                args[-7] = ''
                updated_line = ','.join(args)

        if ignore_positions:
            if line.startswith('INSERT INTO sbmFIELD VALUES'):
                args = updated_line.split(",")
                args[2] = ''
                updated_line = ','.join(args)

        if ignore_pages:
            if line.startswith('INSERT INTO sbmFIELD VALUES'):
                args = updated_line.split(",")
                args[1] = ''
                updated_line = ','.join(args)
            if line.startswith('INSERT INTO sbmIMPLEMENT VALUES '):
                args = updated_line.split(",")
                args[4] = ''
                updated_line = ','.join(args)

        return updated_line

    file1 = [line.strip() for line in submission1_dump.splitlines() if line]
    file2 = [line.strip() for line in submission2_dump.splitlines() if line]

    file1 = [clean_line(line, ignore_dates, ignore_positions, ignore_pages) for line in file1]
    file2 = [clean_line(line, ignore_dates, ignore_positions, ignore_pages) for line in file2]

    file1.sort()
    file2.sort()

    d = difflib.Differ()
    result = d.compare(file2, file1)
    result = [line for line in result if not line.startswith('  ')]
    if verbose > 1:
        result = [line.rstrip().replace('? ', '  ', 1) for line in result]
    else:
        result = [line for line in result if not line.startswith('? ')]
    return '\n'.join(result)

def usage(exitcode=1, msg=""):
    "Print usage"
    print(__doc__)
    print(msg)
    sys.exit(exitcode)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv:i:d:l:f:r:m:c:n",
                                   ["help",
                                    "verbose=",
                                    "ignore=",
                                    "dump=",
                                    "load=",
                                    "diff=",
                                    "remove=",
                                    "method=",
                                    "clean=",
                                    "no-fail-insert",
                                    "yes-i-know"])
    except getopt.GetoptError as err:
        print(err)
        usage(1)

    _ignore_date = False
    _ignore_position = False
    _ignore_page = False
    _doctype = None
    _verbose = 2
    _action = None
    _method = None
    _clean = True
    _no_fail_insert = False
    _yes_i_know = False

    try:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage()
            elif opt[0] in ["-v", "--verbose"]:
                _verbose = opt[1]
            elif opt[0] in ["-m", "--method"]:
                _method = opt[1].upper()
                if not _method in ["NAMES", "RELATIONS"]:
                    usage("Parameter --method must be 'NAMES' or 'RELATIONS'")
            elif opt[0] in ["-c", "--clean"]:
                _clean = opt[1].lower()
                if not _clean in ["y", "n"]:
                    usage("Parameter --clean must be 'y' or 'n'")
                _clean = _clean == 'y' and True or False
            elif opt[0] in ["-n", "--no-fail-insert"]:
                _no_fail_insert = True
            elif opt[0] in ["--yes-i-know"]:
                _yes_i_know = True
            elif opt[0] in ["-i", "--ignore"]:
                ignore = opt[1].split(',')
                if 'd' in ignore:
                    _ignore_date = True
                if 'p' in ignore:
                    _ignore_page = True
                if 'o' in ignore:
                    _ignore_position = True
            elif opt[0] in ["-d", "--dump"]:
                if _action:
                    usage("Choose only one action among --dump, --load, --diff and --remove")
                _action = 'dump'
                _doctype = opt[1]
            elif opt[0] in ["-l", "--load"]:
                if _action:
                    usage("Choose only one action among --dump, --load, --diff and --remove")
                _action = 'load'
                _doctype = opt[1]
            elif opt[0] in ["-f", "--diff"]:
                if _action:
                    usage("Choose only one action among --dump, --load, --diff and --remove")
                _action = 'diff'
                _doctype = opt[1]
            elif opt[0] in ["-r", "--remove"]:
                if _action:
                    usage("Choose only one action among --dump, --load, --diff and --remove")
                _action = 'remove'
                _doctype = opt[1]
    except StandardError as _exception:
        print(_exception)
        usage(1)

    if not _action:
        usage(1, 'You must specify an action among --dump, --load, --diff and --remove')
    if not _doctype:
        usage(1, 'You must specify a doctype')

    if _action == 'dump':
        print(dump_submission(doctype=_doctype,
                              method=_method,
                              include_cleaning=_clean,
                              ignore_duplicate_insert=_no_fail_insert))
    elif _action == 'load':
        if _yes_i_know:
            input_stream = sys.stdin.read()
            (code, messages) = load_submission(doctype=_doctype, dump=input_stream, method=_method)
            print('\n'.join(messages))
            sys.exit(code)
        else:
            print("Loading submission dumps using this tool is experimental. Please use 'dbexec' instead, or run with '--yes-i-know' if you really want to proceed.")
            sys.exit(1)
    elif _action == 'diff':
        if not sys.stdin.isatty():
            input_stream = sys.stdin.read()
            dump1 = dump_submission(doctype=_doctype,
                                    method=_method,
                                    include_cleaning=_clean,
                                    ignore_duplicate_insert=_no_fail_insert)
            print(diff_submission(dump1, input_stream, _verbose, _ignore_date, _ignore_position, _ignore_page))
    elif _action == 'remove':
        if not _method:
            usage(1, 'You must specify option --method')
        if _yes_i_know:
            remove_submission(doctype=_doctype, method=_method)
        else:
            print("Removing submissions using this tool is experimental. Run with '--yes-i-know' if you really want to proceed.")
            sys.exit(1)

if __name__ == '__main__':
    main()

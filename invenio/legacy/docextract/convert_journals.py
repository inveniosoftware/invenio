# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

import optparse
import sys

from invenio.legacy.docextract.record import create_records, print_records
from invenio.legacy.refextract.kbs import get_kbs

from invenio.legacy.docextract.text import re_group_captured_multiple_space
from invenio.legacy.refextract.regexs import re_punctuation


DESCRIPTION = """Utility to convert journal names from abbreviations
or full names to their short form"""

HELP_MESSAGE = """
  -o, --out            Write the extracted references, in xml form, to a file
                       rather than standard output.
"""

USAGE_MESSAGE = """Usage: convert_journals [options] file1 [file2 ...]
Command options: %s
Examples:
    convert_journals -o /home/chayward/thesis-out.xml /home/chayward/thesis.xml
""" % HELP_MESSAGE


def mangle_value(kb, value):
    value = re_punctuation.sub(u' ', value.upper())
    value = re_group_captured_multiple_space.sub(u' ', value)
    value = value.strip()

    standardized_titles = kb[1]
    if value in standardized_titles:
        value = standardized_titles[value]

    return value


def mangle(kb, value):
    try:
        title, volume, page = value.split(',')
    except ValueError:
        pass
    else:
        value = '%s,%s,%s' % (mangle_value(kb, title), volume, page)
    return value

def convert_journals(kb, record):
    for subfield in record.find_subfields('999C5s'):
        subfield.value = mangle(kb, subfield.value)
    for subfield in record.find_subfields('773__p'):
        subfield.value = mangle_value(kb, subfield.value)
    return record


def convert_journals_list(kb, records):
    return [convert_journals(kb, record) for record in records]


def write_records(config, records):
    """Write marcxml to file

    * Output xml header
    * Output collection opening tag
    * Output xml for each record
    * Output collection closing tag
    """
    if config.xmlfile:
        out = open(config.xmlfile, 'w')
    else:
        out = sys.stdout

    xml = print_records(records)

    try:
        print >>out, xml
        out.flush()
    finally:
        if config.xmlfile:
            out.close()


def usage(wmsg=None, err_code=0):
    """Display a usage message for refextract on the standard error stream and
       then exit.
       @param wmsg: (string) some kind of brief warning message for the user.
       @param err_code: (integer) an error code to be passed to halt,
        which is called after the usage message has been printed.
       @return: None.
    """
    # Display the help information and the warning in the stderr stream
    # 'help_message' is global
    if wmsg:
        print >> sys.stderr, wmsg
    print >> sys.stderr, USAGE_MESSAGE
    sys.exit(err_code)


def cli_main(options, args):
    if options.help or not args:
        usage()
        return

    if options.kb_journals:
        kbs_files = {'journals': options.kb_journals}
    else:
        kbs_files = {}

    kb = get_kbs(custom_kbs_files=kbs_files)['journals']

    out_records = []
    for path in args:
        f = open(path)
        try:
            xml = f.read()
        finally:
            f.close()

        out_records += convert_journals_list(kb, create_records(xml))

    write_records(options, out_records)


def get_cli_options():
    """Get the various arguments and options from the command line and populate
       a dictionary of cli_options.
       @return: (tuple) of 2 elements. First element is a dictionary of cli
        options and flags, set as appropriate; Second element is a list of cli
        arguments.
    """
    parser = optparse.OptionParser(description=DESCRIPTION,
                                   usage=USAGE_MESSAGE,
                                   add_help_option=False)
    # Display help and exit
    parser.add_option('-h', '--help', action='store_true')
    # Write out MARC XML references to the specified file
    parser.add_option('-o', '--out', dest='xmlfile')
    # Handle verbosity
    parser.add_option('-v', '--verbose', type=int, dest='verbosity', default=0)
    # Specify a different journals database
    parser.add_option('--kb-journals', dest='kb_journals')

    return parser.parse_args()

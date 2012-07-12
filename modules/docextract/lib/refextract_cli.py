# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""This is file handles the command line interface

    * We parse the options for both daemon and standalone usage
    * When using using the standalone mode, we use the function "main"
      defined here to begin the extraction of references
"""

__revision__ = "$Id$"

import traceback
import optparse
import sys

from invenio.docextract_utils import write_message, setup_loggers
from invenio.bibtask import task_update_progress

# Is refextract running standalone? (Default = yes)
RUNNING_INDEPENDENTLY = False

DESCRIPTION = ""

# Help message, used by bibtask's 'task_init()' and 'usage()'
HELP_MESSAGE = """
  -i, --inspire        Output journal standard reference form in the INSPIRE
                       recognised format: [series]volume,page.
  --kb-journals        Manually specify the location of a journal title
                       knowledge-base file.
  --kb-journals-re     Manually specify the location of a journal title regexps
                       knowledge-base file.
  --kb-report-numbers  Manually specify the location of a report number
                       knowledge-base file.
  --kb-authors         Manually specify the location of an author
                       knowledge-base file.
  --kb-books           Manually specify the location of a book
                       knowledge-base file.
  --no-overwrite       Do not touch record if it already has references

  Standalone Refextract options:
  -o, --out            Write the extracted references, in xml form, to a file
                       rather than standard output.
  --dictfile           Write statistics about all matched title abbreviations
                       (i.e. LHS terms in the titles knowledge base) to a file.
  --output-raw-refs    Output raw references, as extracted from the document.
                       No MARC XML mark-up - just each extracted line, prefixed
                       by the recid of the document that it came from.
  --raw-references     Treat the input file as pure references. i.e. skip the
                       stage of trying to locate the reference section within a
                       document and instead move to the stage of recognition
                       and standardisation of citations within lines.
"""

USAGE_MESSAGE = """Usage: docextract [options] file1 [file2 ...]
Command options: %s
Examples:
    docextract -o /home/chayward/refs.xml /home/chayward/thesis.pdf
""" % HELP_MESSAGE


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
    # Display version and exit
    parser.add_option('-V', '--version', action='store_true')
    # Output recognised journal titles in the Inspire compatible format
    parser.add_option('-i', '--inspire', action='store_true')
    # The location of the report number kb requested to override
    # a 'configuration file'-specified kb
    parser.add_option('--kb-report-numbers', dest='kb_report_numbers')
    # The location of the journal title kb requested to override
    # a 'configuration file'-specified kb, holding
    # 'seek---replace' terms, used when matching titles in references
    parser.add_option('--kb-journals', dest='kb_journals')
    parser.add_option('--kb-journals-re', dest='kb_journals_re')
    # The location of the author kb requested to override
    parser.add_option('--kb-authors', dest='kb_authors')
    # The location of the author kb requested to override
    parser.add_option('--kb-books', dest='kb_books')
    # The location of the author kb requested to override
    parser.add_option('--kb-conferences', dest='kb_conferences')
    # Write out the statistics of all titles matched during the
    # extraction job to the specified file
    parser.add_option('--dictfile')
    # Write out MARC XML references to the specified file
    parser.add_option('-o', '--out', dest='xmlfile')
    # Handle verbosity
    parser.add_option('-v', '--verbose', type=int, dest='verbosity', default=0)
    # Output a raw list of refs
    parser.add_option('--output-raw-refs', action='store_true',
                        dest='output_raw')
    # Treat input as pure reference lines:
    # (bypass the reference section lookup)
    parser.add_option('--raw-references', action='store_true',
                        dest='treat_as_reference_section')
    return parser.parse_args()


def halt(err=StandardError, msg=None, exit_code=1):
    """ Stop extraction, and deal with the error in the appropriate
    manner, based on whether Refextract is running in standalone or
    bibsched mode.
    @param err: (exception) The exception raised from an error, if any
    @param msg: (string) The brief error message, either displayed
    on the bibsched interface, or written to stderr.
    @param exit_code: (integer) Either 0 or 1, depending on the cause
    of the halting. This is only used when running standalone."""
    # If refextract is running independently, exit.
    # 'RUNNING_INDEPENDENTLY' is a global variable
    if RUNNING_INDEPENDENTLY:
        if msg:
            write_message(msg, stream=sys.stderr, verbose=0)
        sys.exit(exit_code)
    # Else, raise an exception so Bibsched will flag this task.
    else:
        if msg:
            # Update the status of refextract inside the Bibsched UI
            task_update_progress(msg.strip())
        raise err(msg)


def usage(wmsg=None, err_code=0):
    """Display a usage message for refextract on the standard error stream and
       then exit.
       @param wmsg: (string) some kind of brief warning message for the user.
       @param err_code: (integer) an error code to be passed to halt,
        which is called after the usage message has been printed.
       @return: None.
    """
    if wmsg:
        wmsg = wmsg.strip()

    # Display the help information and the warning in the stderr stream
    # 'help_message' is global
    print >> sys.stderr, USAGE_MESSAGE
    # Output error message, either to the stderr stream also or
    # on the interface. Stop the extraction procedure
    halt(msg=wmsg, exit_code=err_code)


def main(config, args, run):
    """Main wrapper function for begin_extraction, and is
    always accessed in a standalone/independent way. (i.e. calling main
    will cause refextract to run in an independent mode)"""
    # Flag as running out of bibtask
    global RUNNING_INDEPENDENTLY
    RUNNING_INDEPENDENTLY = True

    if config.verbosity not in range(0, 10):
        usage("Error: Verbosity must be an integer between 0 and 10")

    setup_loggers(config.verbosity)

    if config.version:
        # version message and exit
        write_message(__revision__, verbose=0)
        halt(exit_code=0)

    if config.help:
        usage()

    if not args:
        # no files provided for reference extraction - error message
        usage("Error: No valid input file specified (file1 [file2 ...])")

    try:
        run(config, args)
        write_message("Extraction complete", verbose=2)
    except StandardError, e:
        # Remove extra '\n'
        write_message(traceback.format_exc()[:-1], verbose=9)
        write_message("Error: %s" % e, verbose=0)
        halt(exit_code=1)

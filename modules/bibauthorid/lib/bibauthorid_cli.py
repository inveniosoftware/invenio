# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""
bibauthorid_cli
    This module provides a command-line interface for BibAuthorID.
"""

import getopt
import sys
import time
import os.path as osp

import bibauthorid_config as bconfig


def main():
    """Main function """
    arguments = sys.argv

    if len(arguments) <= 1:
        bconfig.LOGGER.error("Please provide parameters!")
        _display_help()

    try:
        import bibauthorid_daemon as daemon
    except ImportError:
        bconfig.LOGGER.error("Hmm...No Daemon process running.")
        return

    daemon.bibauthorid_daemon()


def _display_help():
    """Prints the help message for this module."""
    print """Usage: bibauthorid [OPTIONS]

Runs the author disambiguation and identity matching algorithm.

General options:
  -h, --help                Display this help and exit
  -V, --version             Output version information and exit
  -v, --verbose=LEVEL       Number between 1 and 50. The higher the number,
                            the higher the level of importance. Everything
                            below the number will be ignored. Equal and above
                            will be shovn. Debugging=10, Info=20, Bibauthorid
                            default log=25, Warnings=30, Errors=40]

Daemon mode options:
 Commands:
      --repair-personid     Deletes untouched person entities to then
                            re-create and updated these entities.
      --fast-update-personid    Updates personid adding not yet assigned papers to the system,
                            in a fast, best effort basis. -r to specify records.
      --personid-gc        Runs the gc on personid. -r to specify records.

 Options:
  -r, --record-ids=NUM      Specifies a list of record ids. To use as on option
                            for --update-universe to limit the update to the
                            selected records. Must be space less CSVs.
  --all-records             To use as on option for --update-universe to
                            perform the update an all existing record ids. Be
                            WARNED that this will empty and re-fill all aid*
                            tables in the process!

Examples:
  - Process all records that hold an author with last name 'Ellis':
      $ bibauthorid -u admin --lastname "Ellis"
  - Process all records and regard all authors:
      $ bibauthorid -u admin --process-all
  - To update all information from newly entered and modified records:
      $ bibauthorid -u admin -U
  - Prepare job packages in folder 'gridfiles' with the sub directories
    prefixed with 'task' and a maximum number of 2000 records per package:
      $ bibauthorid -u admin --prepare-grid -d gridfiles -p task -m 2000
"""
    sys.exit(1)


def _display_version():
    """Display Bibauthorid version and exit."""
    try:
        from invenio.config import CFG_VERSION
        print "\nInvenio/%s bibauthorid v%s\n" % (CFG_VERSION, bconfig.VERSION)
    except ImportError:
        print "\nInvenio bibauthorid (standalone) v%s\n" % (bconfig.VERSION)
    sys.exit(1)


def _read_options(options_string):
    """Reads the options, test if the specified values are consistent and
    populates the options dictionary."""
    options = {
        "record_ids" : None,
        "all_records": False,
        "repair_pid": False,
        "fast_update_personid": False,
        "personid_gc": False
    }

    try:
        short_flags = "hVv:r:"
        long_flags = ["verbose=", "help", "version", "record-ids=", "all-records",
                      "repair-personid", "fast-update-personid", "personid-gc"]
        opts, args = getopt.gnu_getopt(options_string, short_flags, long_flags)
    except getopt.GetoptError, err1:
        print >> sys.stderr, "Parameter problem: %s" % err1
        _display_help()

    # 2 dictionaries containing the option linked to its destination in the
    # options dictionary.
    with_argument = {
        "--record-ids": "record_ids",
        "-r": "record_ids"
    }

    without_argument = {
        "--all-records": "all_records",
        "--repair-personid": "repair_pid",
        "--fast-update-personid":"fast_update_personid",
        "--personid-gc":"personid_gc"
    }

    for option, argument in opts:
        if option in ("-h", "--help"):
            _display_help()
        elif option in ("-V", "--version"):
            _display_version()
        elif option in ("-v", "--verbose"):
            bconfig.LOG_LEVEL = int(argument)
        elif option in with_argument:
            options[with_argument[option]] = argument
        elif option in without_argument:
            options[without_argument[option]] = True
        else:
            # This shouldn't happen as gnu_getopt should already handle
            # that case.
            bconfig.LOGGER.error("option unrecognized -- %s" % option)


    # Collect the text inputs.
    options["text_files"] = args

    return options


if __name__ == '__main__':
    main()

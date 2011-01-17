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
import bibauthorid as engine
import bibauthorid_structs as dat

from bibauthorid_file_utils import populate_structs_from_files
from bibauthorid_file_utils import write_mem_cache_to_files
from bibauthorid_file_utils import make_directory

#log = bconfig.get_logger("bibauthor.cli")


def main():
    """Main function """
    arguments = sys.argv

    if len(arguments) <= 1:
        bconfig.LOGGER.error("Please provide parameters!")
        _display_help()

    run_daemon = True
    standalone_option = ("-S", "--standalone", "-j", "--job-dir")

    for option in standalone_option:
        for arg in arguments:
            if arg.startswith(option):
                run_daemon = False

    if run_daemon:
        daemon = None
        try:
            import bibauthorid_daemon as daemon
        except ImportError:
            bconfig.LOGGER.error("Hmm...No Daemon process running.")

        if daemon:
            daemon.bibauthorid_daemon()
    else:
        options = _read_options(arguments)

        if options["job_dir"]:
            job_dir = options["job_dir"]

            if job_dir.endswith("/"):
                job_dir = job_dir[0:-1]

            log_name = osp.abspath(job_dir).split("/")
            logfile = "%s/%s.log" % (job_dir, log_name[-1])

            start = time.time()

            bconfig.init_logger(logfile)
            populate_structs_from_files(job_dir)

            bconfig.LOGGER.debug("| Loaded %s records."
                                 % len(dat.RELEVANT_RECORDS))

            engine.start_computation(process_doclist=True,
                             process_orphans=True,
                             print_stats=True)

            result_path = "%s/results/" % (job_dir,)

            if make_directory(result_path):
                write_mem_cache_to_files(result_path, is_result=True)
            else:
                bconfig.LOGGER.error("Cannot write to destination: "
                                     "Cannot create directory")

            end = time.time() - start

            bconfig.LOGGER.log(25, "Finish! The computation finished in %.2fs"
                               % (end))
            bconfig.stop_and_close_logger()
        else:
            bconfig.LOGGER.error("Standalone mode without parameters "
                                 "does not do anything helpful. Please"
                                 "consult -h help message for usage")


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
  -S, --standalone          Switches on stand alone mode. This is required
                            for jobs that should run on a set of files rather
                            than on the database (e.g. this is needed on the
                            grid). Without this switch no standalone job will
                            start or perform.

Daemon mode options:
 Commands:
  NOTE: Options -n, -a, -U, -G and -R are mutually exclusive (XOR)!
  -n, --lastname=STRING     Process only authors with this last name.
  -a, --process-all         The option for cleaning all authors.
  -U, --update-universe     Update bibauthorid universe. Find modified and
                            newly entered records and process all the authors
                            on these records.
  -G, --prepare-grid        Prepares a set of files that supply the
                            pre-clustered data needed for stand alone job to
                            run (e.g. needed on the grid). The behavior of
                            this export can be controlled with the
                            options -d (required), -p and -m (both optional).
  -R, --load-grid-results   Loads the results from the grid jobs
                            and writes them to the database. The behavior of
                            this import can be controlled with the
                            options -d (required).
      --update-cache        Updates caches to the newly introduced changes
                            (new and modified documents).
                            This should be called daily or better more then
                            once per day, to ensure the correct operation of
                            the frontend (and the backend).
      --clean-cache         Clean the cache from out of date contents
                            (deleted documents).

 Options:
  -d, --data-dir=DIRNAME    Specifies the data directory, in which the data for
                            the grid preparation will be stored to or loaded
                            from. It requires the -G or -R switch.
  -p, --prefix=STRING       Specifies the prefix of the directories created
                            under the --data-dir directory. Optional.
                            Defaults to 'job'. It requires the -G switch.
  -m, --max-records         Specifies the number of records that
                            shall be stored per job package. Optional.
                            Defaults to 4000 and requires -G switch.

Standalone mode options:
  -j, --job-dir=DIRECTORY   Run the job on the files found under the path
                            specified here. Supplying a directory is mandatory.
                            The results of the process will be stored in a
                            sub directory of --job-dir named 'results'. These
                            results can be loaded into the db with the -R
                            option of this command line tool.

Examples (daemon mode):
  - Process all records that hold an author with last name 'Ellis':
      $ bibauthorid -u admin --lastname "Ellis"
  - Process all records and regard all authors:
      $ bibauthorid -u admin --process-all
  - To update all information from newly entered and modified records:
      $ bibauthorid -u admin -U
  - Prepare job packages in folder 'gridfiles' with the sub directories
    prefixed with 'task' and a maximum number of 2000 records per package:
      $ bibauthorid -u admin --prepare-grid -d gridfiles -p task -m 2000

Examples (standalone mode):
  - Process the job package stored in folder 'grid_data/job0'
      $ bibauthorid -S --job-dir=grid_data/job0
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
        "lastname": "None,",
        "do_all": False,
        "output_limit": 20,
        "prepare_grid": False,
        "prefix": "job",
        "data_dir": "data_dir",
        "standalone": False,
        "job_dir": False,
        "max_records": 4000,
        "load_grid_results": False,
        "update": False,
        "update_cache": False,
        "clean_cache": False
    }

    try:
        short_flags = "n:v:i:d:p:j:m:USGRahV"
        long_flags = ["lastname=", "verbose=", "recid=",
            "process-all", "help", "version", "prepare-grid", "prefix=",
            "data-dir=", "standalone", "job-dir=", "max-records=",
            "load-grid-results", "update-universe", "update-cache", "clean-cache"]
        opts, args = getopt.gnu_getopt(options_string, short_flags, long_flags)
    except getopt.GetoptError, err1:
        print >> sys.stderr, "Parameter problem: %s" % err1
        _display_help()

    # 2 dictionaries containing the option linked to its destination in the
    # options dictionary.
    with_argument = {
        "-n": "lastname",
        "--lastname": "lastname",
        "-d": "data_dir",
        "--data-dir": "data_dir",
        "-p": "prefix",
        "--prefix": "prefix",
        "-j": "job_dir",
        "--job-dir": "job_dir",
        "-m": "max_records",
        "--max-records": "max_records"
    }

    without_argument = {
        "-a": "do_all",
        "--process-all": "do_all",
        "-U": "update",
        "--update-universe": "update",
        "-G": "prepare_grid",
        "--prepare-grid": "prepare_grid",
        "-S": "standalone",
        "--standalone": "standalone",
        "-R": "load_grid_results",
        "--load-grid-results": "load_grid_results",
        "--update-cache" : "update_cache",
        "--clean-cache" : "clean_cache"
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

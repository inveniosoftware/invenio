## -*- mode: python; coding: utf-8; -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012 CERN.
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
Usage: bibsort [options]

BibSort tool

Options:
  -h, --help            show this help message and exit
  -l, --load-config     Loads the configuration from bibsort.cfg into the
                        database
  -d, --dump-config     Outputs a database dump in form of a config file
  -p, --print-sorting-methods
                        Prints the available sorting methods
  -R, --rebalance       Runs the sorting methods given in '--metods'and
                        rebalances all the buckets.
                        If no method is specified, the rebalance will be done
                        for all the methods in the config file.
  -S, --update-sorting  Runs the sorting methods given in '--methods' for the
                        recids given in '--id'.
                        If no method is specified, the update will be done for
                        all the methods in the config file.
                        If no recids are specified, the update will be done
                        for all the records that have been
                        modified/inserted from the last run of the sorting.
                        If you want to run the sorting for all records, you
                        should use the '-B' option
  -M, --methods=METHODS Specify the sorting methods for which the
                        update_sorting or rebalancing will run
                        (ex: --methods=method1,method2,method3).
  -i, --id=RECIDS       Specify the records for which the update_sorting will
                        run (ex: --id=1,2-56,72)
"""

__revision__ = "$Id$"

import sys
import optparse
import time
import ConfigParser
from invenio.dbquery import run_sql, Error
from invenio.config import CFG_ETCDIR
from invenio.bibsort_engine import run_bibsort_update, \
                            run_bibsort_rebalance
from invenio.bibtask import task_init, write_message, \
    task_set_option, task_get_option


def load_configuration():
    """Loads the configuration for the bibsort.cfg file into the database"""
    config_file = CFG_ETCDIR + "/bibsort/bibsort.cfg"
    write_message('Reading config data from: %s' %config_file)
    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open(config_file))
    except StandardError, err:
        write_message("Cannot find configuration file: %s" \
                      %config_file, stream=sys.stderr)
        return False
    to_insert = []
    for section in config.sections():
        try:
            name = config.get(section, "name")
            definition = config.get(section, "definition")
            washer = config.get(section, "washer")
        except (ConfigParser.NoOptionError, StandardError), err:
            write_message("For each sort_field you need to define at least \
                          the name, the washer and the definition. \
                          [error: %s]" %err, stream=sys.stderr)
            return False
        to_insert.append((name, definition, washer))
    # all the values were correctly read from the config file
    run_sql("TRUNCATE TABLE bsrMETHOD")
    write_message('Old data has been deleted from bsrMETHOD table', verbose=5)
    for row in to_insert:
        run_sql("INSERT INTO bsrMETHOD(name, definition, washer) \
                VALUES (%s, %s, %s)", (row[0], row[1], row[2]))
        write_message('Method %s has been inserted into bsrMETHOD table' \
                      %row[0], verbose=5)
    return True


def dump_configuration():
    """Creates a dump of the data existing in the bibsort tables"""
    try:
        results = run_sql("SELECT id, name, definition, washer FROM bsrMETHOD")
    except Error, err:
        write_message("The error: [%s] occured while trying to get \
                      the bibsort data from the database." %err, sys.stderr)
        return False
    write_message('The bibsort data has been read from the database.', verbose=5)
    if results:
        config = ConfigParser.ConfigParser()
        for item in results:
            section = "sort_field_%s" % item[0]
            config.add_section(section)
            config.set(section, "name", item[1])
            config.set(section, "definition", item[2])
            config.set(section, "washer", item[3])
        output_file_name = CFG_ETCDIR + '/bibsort/bibsort_db_dump_%s.cfg' % \
                           time.strftime("%d%m%Y%H%M%S", time.localtime())
        write_message('Opening the output file %s' %output_file_name)
        try:
            output_file = open(output_file_name, 'w')
            config.write(output_file)
            output_file.close()
        except Error, err:
            write_message('Can not operate on the configuration file %s [%s].' \
                          %(output_file_name, err), stream=sys.stderr)
            return False
        write_message('Configuration data dumped to file.')
    else:
        write_message("The bsrMETHOD table does not contain any data.")
    return True


def update_sorting(methods, recids):
    """Runs the updating of the sorting tables for methods and recids
    Recids is a list of integer numbers(record ids)
    but can also contain intervals"""
    method_list = []
    if methods:
        method_list = methods.strip().split(',')

    recid_list = []
    if recids:
        cli_recid_list = recids.strip().split(',')
        for recid in cli_recid_list:
            if recid.find('-') > 0:
                rec_range = recid.split('-')
                try:
                    recid_min = int(rec_range[0])
                    recid_max = int(rec_range[1])
                    for rec in range(recid_min, recid_max + 1):
                        recid_list.append(rec)
                except Error, err:
                    write_message("Error: [%s] occured while trying \
                          to parse the recids argument." %err, sys.stderr)
                    return False
            else:
                recid_list.append(int(recid))
    return run_bibsort_update(recid_list, method_list)


def rebalance(methods):
    """Runs the complete sorting and rebalancing of buckets for
    the methods specified in 'methods' argument"""
    method_list = []
    if methods:
        method_list = methods.strip().split(',')
    return run_bibsort_rebalance(method_list)


def print_sorting_methods():
    """Outputs the available sorting methods from the DB"""
    try:
        results = run_sql("SELECT name FROM bsrMETHOD")
    except Error, err:
        write_message("The error: [%s] occured while trying to \
              get the bibsort data from the database." %err)
        return False
    if results:
        methods = []
        for result in results:
            methods.append(result[0])
        if len(methods) > 0:
            write_message('Methods: %s' %methods)
    else:
        write_message("There are no sorting methods configured.")
    return True


# main with option parser
# to be used in case the connection with bibsched is not wanted
def main_op():
    """Runs program and handles command line options"""
    option_parser = optparse.OptionParser(description="""BibSort tool""")
    option_parser.add_option('-L', '--load-config', action = 'store_true', \
        help = 'Loads the configuration from bibsort.conf into the database')
    option_parser.add_option('-D', '--dump-config', action = 'store_true', \
        help = 'Outputs a database dump in form of a config file')
    option_parser.add_option('-P', '--print-sorting-methods',
        action = 'store_true', \
        help = "Prints the available sorting methods")
    option_parser.add_option('-R', '--rebalance', action = 'store_true', \
        help = "Runs the sorting methods given in '--metods'and rebalances all the buckets. If no method is specified, the rebalance will be done for all the methods in the config file.")
    option_parser.add_option('-S', '--update-sorting', action = 'store_true', \
        help = "Runs the sorting methods given in '--methods' for the recids given in '--id'. If no method is specified, the update will be done for all the methods in the config file. If no recids are specified, the update will be done for all the records that have been modified/inserted from the last run of the sorting. If you want to run the sorting for all records, you should use the '-R' option")
    option_parser.add_option('--methods', action = 'store', dest = 'methods', \
        metavar = 'METHODS', \
        help = "Specify the sorting methods for which the update_sorting or rebalancing will run (ex: --methods=method1,method2,method3).")
    option_parser.add_option('--id', action = 'store', dest = 'recids', \
        metavar = 'RECIDS', \
        help = "Specify the records for which the update_sorting will run (ex: --id=1,2-56,72) ")
    options, dummy = option_parser.parse_args()

    if options.load_config and options.dump_config:
        option_parser.error('.. conflicting options, please add only one')
    elif options.rebalance and options.update_sorting:
        option_parser.error('..conflicting options, please add only one')
    elif (options.load_config or options.dump_config) and \
        (options.rebalance or options.update_sorting):
        option_parser.error('..conflicting options, please add only one')

    if options.load_config:
        load_configuration()
    elif options.dump_config:
        dump_configuration()
    elif options.update_sorting:
        update_sorting(options.methods, options.recids)
    elif options.rebalance:
        rebalance(options.methods)
    elif options.print_sorting_methods:
        print_sorting_methods()
    else:
        option_parser.print_help()


def main():
    """Main function that constructs the bibtask"""
    task_init(authorization_action='runbibsort',
              authorization_msg="BibSort Task Submission",
              description = "",
              help_specific_usage="""
 Specific options:
  -l, --load-config     Loads the configuration from bibsort.conf into the
                        database
  -d, --dump-config     Outputs a database dump in form of a config file
  -p, --print-sorting-methods
                        Prints the available sorting methods
  -R, --rebalance       Runs the sorting methods given in '--metods'and
                        rebalances all the buckets. If no method is
                        specified, the rebalance will be done for all
                        the methods in the config file.
  -S, --update-sorting  Runs the sorting methods given in '--methods' for the
                        recids given in '--id'. If no method is
                        specified, the update will be done for all the
                        methods in the config file. If no recids are
                        specified, the update will be done for all the records
                        that have been modified/inserted from the last
                        run of the sorting. If you want to run the
                        sorting for all records, you should use the '-B'
                        option
  -M, --methods=METHODS Specify the sorting methods for which the
                        update_sorting or rebalancing will run (ex:
                        --methods=method1,method2,method3).
  -i, --id=RECIDS       Specify the records for which the update_sorting will
                        run (ex: --id=1,2-56,72)
""",
              version=__revision__,
              specific_params=("ldpRSM:i:",
                               ["load-config",
                                "dump-config",
                                "print-sorting-methods",
                                "rebalance",
                                "update-sorting",
                                "methods=",
                                "id="]),
              task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
              task_run_fnc=task_run_core)


def task_submit_elaborate_specific_parameter(key, value, opts, dummy_args):
    """Given the string key it checks it's meaning, eventually using the
    value. Usually it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key."""

    #Load configuration
    if key in ('-l', '--load-config'):
        task_set_option('cmd', 'load')
        if ('-d', '') in opts or ('--dump-conf', '') in opts:
            raise StandardError(".. conflicting options, please add only one")

    #Dump configuration
    elif key in ('-d', '--dump_conf'):
        task_set_option('cmd', 'dump')

    #Print sorting methods
    elif key in ('-p', '--print-sorting-methods'):
        task_set_option('cmd', 'print')

    #Rebalance
    elif key in ('-R', '--rebalance'):
        task_set_option('cmd', 'rebalance')
        if ('-S', '') in opts or ('--update-sorting', '') in opts:
            raise StandardError(".. conflicting options, please add only one")

    #Update sorting
    elif key in ('-S', '--update-sorting'):
        task_set_option('cmd', 'sort')

    #Define methods
    elif key in ('-M', '--methods'):
        task_set_option('methods', value)

    #Define records
    elif key in ('-i', '--id'):
        task_set_option('recids', value)

    else:
        return False

    return True


def task_run_core():
    """Reimplement to add the body of the task"""
    write_message("bibsort starting..")

    cmd = task_get_option('cmd')
    methods = task_get_option('methods')
    recids = task_get_option('recids')
    write_message("Task parameters: command=%s ; methods=%s ; recids=%s" \
                  % (cmd, methods, recids), verbose=2)

    executed_correctly = False

    # if no command is defined, run sorting
    if not cmd:
        cmd = 'sort'

    if cmd == 'load':
        write_message('Starting loading the configuration \
                      from the cfg file to the db.', verbose=5)
        executed_correctly = load_configuration()
        if executed_correctly:
            write_message('Loading completed.', verbose=5)
    elif cmd == 'dump':
        write_message('Starting dumping the configuration \
                      from the db into the cfg file.', verbose=5)
        executed_correctly = dump_configuration()
        if executed_correctly:
            write_message('Dumping completed.', verbose=5)
    elif cmd == 'print':
        executed_correctly = print_sorting_methods()
    elif cmd == 'sort':
        write_message('Starting sorting.', verbose=5)
        executed_correctly = update_sorting(methods, recids)
        if executed_correctly:
            write_message('Sorting completed.', verbose=5)
    elif cmd == 'rebalance':
        write_message('Starting rebalancing the sorting buckets.', verbose=5)
        executed_correctly = rebalance(methods)
        if executed_correctly:
            write_message('Rebalancing completed.', verbose=5)
    else:
        write_message("This action is not possible. \
        See the --help for available actions.", sys.stderr)

    write_message('bibsort exiting..')
    return executed_correctly

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2012 CERN.
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
Invenio DB dumper.

Usage: /opt/invenio/bin/dbdump [options]

Command options:
  -o, --output=DIR      Output directory. [default=/opt/invenio/var/log]
  -n, --number=NUM      Keep up to NUM previous dump files. [default=5]
  --params=PARAMS       Specify your own mysqldump parameters. Optional.
  --compress            Compress dump directly into gzip.
  --slave=HOST          Perform the dump from a slave, if no host use CFG_DATABASE_SLAVE.
  --ignore=TABLES       Specify the tables to ignore (comma seperated)

Scheduling options:
  -u, --user=USER User name to submit the task as, password needed.
  -t, --runtime=TIME Time to execute the task (now), e.g. +15s, 5m, 3h, 2002-10-27 13:57:26.
  -s, --sleeptime=SLEEP Sleeping frequency after which to repeat task (no), e.g.: 30m, 2h, 1d.
  -L  --limit=LIMIT Time limit when it is allowed to execute the task, e.g. Sunday 01:00-05:00.
                    The time limit syntax is [Wee[kday]] [hh[:mm][-hh[:mm]]].
  -P, --priority=PRI Task priority (0=default, 1=higher, etc).
  -N, --name=NAME Task specific name (advanced option).

General options:
  -h, --help  Print this help.
  -V, --version  Print version information.
  -v, --verbose=LEVEL Verbose level (0=min, 1=default, 9=max).
      --profile=STATS Print profile information. STATS is a comma-separated
   list of desired output stats (calls, cumulative,
   file, line, module, name, nfl, pcalls, stdname, time).
"""

__revision__ = "$Id$"

import os
import re

from invenio.config import CFG_LOGDIR, CFG_PATH_MYSQL, CFG_PATH_GZIP
from invenio.dbquery import CFG_DATABASE_HOST, \
                            CFG_DATABASE_USER, \
                            CFG_DATABASE_PASS, \
                            CFG_DATABASE_NAME, \
                            CFG_DATABASE_PORT, \
                            CFG_DATABASE_SLAVE
from invenio.bibtask import task_init, \
                            write_message, \
                            task_set_option, \
                            task_get_option, \
                            task_update_progress, \
                            task_get_task_param
from invenio.shellutils import run_shell_command, \
                               escape_shell_arg


def _delete_old_dumps(dirname, filename, number_to_keep):
    """
    Look for files in DIRNAME directory starting with FILENAME
    pattern.  Delete up to NUMBER_TO_KEEP files (when sorted
    alphabetically, which is equal to sorted by date).  Useful to
    prune old dump files.
    """
    files = [x for x in os.listdir(dirname) if x.startswith(filename)]
    files.sort()
    for afile in files[:-number_to_keep]:
        write_message("... deleting %s" % dirname + os.sep + afile)
        os.remove(dirname + os.sep + afile)


def dump_database(dump_path, host=CFG_DATABASE_HOST, port=CFG_DATABASE_PORT, \
                  user=CFG_DATABASE_USER, passw=CFG_DATABASE_PASS, \
                  name=CFG_DATABASE_NAME, params=None, compress=False, \
                  ignore=None):
    """
    Dump Invenio database into SQL file located at DUMP_PATH.

    Will perform the command to mysqldump with the given host configuration
    and user credentials.

    Optional mysqldump parameters can also be passed. Otherwise, a default
    set of parameters will be used.

    @param dump_path: path on the filesystem to save the dump to.
    @type dump_path: string

    @param host: hostname of mysql database node to connect to.
    @type host: string

    @param port: port of mysql database node to connect to
    @type port: string

    @param user: username to connect with
    @type user: string

    @param passw: password to connect to with
    @type passw: string

    @param name: name of mysql database node to dump
    @type name: string

    @param params: command line parameters to pass to mysqldump. Optional.
    @type params: string

    @param compress: should the dump be compressed through gzip?
    @type compress: bool

    @param ignore: list of tables to ignore in the dump
    @type ignore: string
    """
    write_message("... writing %s" % (dump_path,))

    # Is mysqldump installed or in the right path?
    cmd_prefix = CFG_PATH_MYSQL + 'dump'
    if not os.path.exists(cmd_prefix):
        raise StandardError("%s is not installed." % (cmd_prefix))

    if not params:
        # No parameters set, lets use the default ones.
        params = " --skip-opt --add-drop-table --add-locks --create-options" \
                 " --quick --extended-insert --set-charset --disable-keys" \
                 " --lock-tables=false "

    if ignore:
        params += " ".join(["--ignore-table=%s.%s" % (CFG_DATABASE_NAME, table) for table in ignore])

    dump_cmd = "%s %s " \
               " --host=%s --port=%s --user=%s --password=%s %s" % \
               (cmd_prefix, \
                params, \
                re.escape(host), \
                re.escape(str(port)), \
                re.escape(user), \
                re.escape(passw), \
                re.escape(name))

    if compress:
        dump_cmd = "%s | %s -cf; exit ${PIPESTATUS[0]}" % \
                   (dump_cmd, \
                    CFG_PATH_GZIP)
        dump_cmd = "bash -c %s" % (escape_shell_arg(dump_cmd),)

    exit_code, stdout, stderr = run_shell_command(dump_cmd, None, dump_path)

    if exit_code:
        raise StandardError("ERROR: mysqldump exit code is %s. stderr: %s stdout: %s" % \
                            (repr(exit_code), \
                             repr(stderr), \
                             repr(stdout)))

    write_message("... completed writing %s" % (dump_path,))


def dump_slave_database(dump_path, host, params=None, ignore=None):
    """
    Performs a dump of a defined slave database, making sure
    to halt slave replication until the dump has completed.

    @param dump_path: path on the filesystem to save the dump to.
    @type dump_path: string

    @param host: hostname or IP of DB slave to dump from.
    @type host: string

    @param params: command line parameters to pass to mysqldump. Optional.
    @type params: string

    @param ignore: list of tables to ignore in the dump
    @type ignore: string
    """
    # We need to stop slave replication before performing the dump
    write_message("... stopping slave")

    # Is mysqladmin installed or in the right path?
    admin_cmd = CFG_PATH_MYSQL + 'admin'
    if not os.path.exists(admin_cmd):
        raise StandardError("%s is not installed." % (admin_cmd))

    slave_cmd = "%s -e 'STOP SLAVE SQL_THREAD;' " \
                " --host=%s --port=%s --user=%s --password=%s" \
                % (CFG_PATH_MYSQL,
                   escape_shell_arg(host),
                   escape_shell_arg(CFG_DATABASE_PORT),
                   escape_shell_arg(CFG_DATABASE_USER),
                   escape_shell_arg(CFG_DATABASE_PASS))

    exit_code, dummy1, stderr = run_shell_command(slave_cmd)
    if exit_code:
        raise StandardError("ERROR: Stopping slave failed: %s" % (stderr,))

    write_message("... slave stopped")

    dump_database(dump_path, \
                  host=host, \
                  params=params, \
                  ignore=ignore)

    write_message("... starting slave.")
    admin_cmd += " start-slave " \
                 " --host=%s --port=%s --user=%s --password=%s " % \
                 (escape_shell_arg(host),
                  escape_shell_arg(CFG_DATABASE_PORT),
                  escape_shell_arg(CFG_DATABASE_USER),
                  escape_shell_arg(CFG_DATABASE_PASS),)

    exit_code, dummy1, stderr = run_shell_command(admin_cmd)
    if exit_code:
        raise StandardError("ERROR: Starting slave failed: %s" % (stderr,))
    write_message("... slave started")


def _dbdump_elaborate_submit_param(key, value, dummyopts, dummyargs):
    """
    Elaborate task submission parameter.  See bibtask's
    task_submit_elaborate_specific_parameter_fnc for help.
    """
    if key in ('-n', '--number'):
        try:
            task_set_option('number', int(value))
        except ValueError:
            raise StandardError("ERROR: Number '%s' is not integer." % (value,))
    elif key in ('-o', '--output'):
        if os.path.isdir(value):
            task_set_option('output', value)
        else:
            raise StandardError("ERROR: Output '%s' is not a directory." % \
                  (value,))
    elif key in ('--params'):
        task_set_option('params', value)
    elif key in ('--compress'):
        if not CFG_PATH_GZIP or (CFG_PATH_GZIP and not os.path.exists(CFG_PATH_GZIP)):
            raise StandardError("ERROR: No valid gzip path is defined.")
        task_set_option('compress', True)
    elif key in ('--slave'):
        if value:
            task_set_option('slave', value)
        else:
            if not CFG_DATABASE_SLAVE:
                raise StandardError("ERROR: No slave defined.")
            task_set_option('slave', CFG_DATABASE_SLAVE)
    elif key in ('--ignore'):
        task_set_option('ignore', value)
    else:
        return False
    return True


def _dbdump_run_task_core():
    """
    Run DB dumper core stuff.

    Note: do not use task_can_sleep() stuff here because we don't want
    other tasks to interrupt us while we are dumping the DB content.
    """
    # read params:
    task_update_progress("Reading parameters")
    write_message("Reading parameters started")
    output_dir = task_get_option('output', CFG_LOGDIR)
    output_num = task_get_option('number', 5)
    params = task_get_option('params', None)
    compress = task_get_option('compress', False)
    slave = task_get_option('slave', False)
    ignore = task_get_option('ignore', None)

    output_file_suffix = task_get_task_param('task_starting_time').replace(' ', '_') + '.sql'
    if compress:
        output_file_suffix = "%s.gz" % (output_file_suffix,)
    write_message("Reading parameters ended")

    if ignore:
        ignore = [table.strip() for table in ignore.split(',')]

    # make dump:
    task_update_progress("Dumping database")
    write_message("Database dump started")

    if slave:
        output_file_prefix = 'slave-%s-dbdump-' % (CFG_DATABASE_NAME,)
        output_file = output_file_prefix + output_file_suffix
        dump_path = output_dir + os.sep + output_file
        dump_slave_database(dump_path, slave, params, ignore)
    else:
        output_file_prefix = '%s-dbdump-' % (CFG_DATABASE_NAME,)
        output_file = output_file_prefix + output_file_suffix
        dump_path = output_dir + os.sep + output_file
        dump_database(dump_path, params=params, ignore=ignore)

    write_message("Database dump ended")
    # prune old dump files:
    task_update_progress("Pruning old dump files")
    write_message("Pruning old dump files started")
    _delete_old_dumps(output_dir, output_file_prefix, output_num)
    write_message("Pruning old dump files ended")
    # we are done:
    task_update_progress("Done.")
    return True


def main():
    """Main that construct all the bibtask."""
    task_init(authorization_action='rundbdump',
              authorization_msg="DB Dump Task Submission",
              help_specific_usage="""\
  -o, --output=DIR      Output directory. [default=%s]
  -n, --number=NUM      Keep up to NUM previous dump files. [default=5]
  --params=PARAMS       Specify your own mysqldump parameters. Optional.
  --compress            Compress dump directly into gzip.
  --slave=HOST          Perform the dump from a slave, if no host use CFG_DATABASE_SLAVE.
  --ignore=TABLES       Specify the tables to ignore (comma seperated)
""" % CFG_LOGDIR,
              version=__revision__,
              specific_params=("n:o:p:",
                               ["number=", "output=", "params=", "slave=", "compress", 'ignore=']),
              task_submit_elaborate_specific_parameter_fnc=_dbdump_elaborate_submit_param,
              task_run_fnc=_dbdump_run_task_core)

if __name__ == '__main__':
    main()

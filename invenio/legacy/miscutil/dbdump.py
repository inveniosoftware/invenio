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
import sys
from invenio.config import CFG_LOGDIR, CFG_PATH_MYSQL, CFG_PATH_GZIP
from invenio.legacy.dbquery import CFG_DATABASE_HOST, \
                            CFG_DATABASE_USER, \
                            CFG_DATABASE_PASS, \
                            CFG_DATABASE_NAME
from invenio.bibtask import task_init, write_message, task_set_option, \
                            task_get_option, task_update_progress, \
                            task_get_task_param
from invenio.shellutils import run_shell_command, escape_shell_arg


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


def _dump_database(dirname, filename):
    """
    Dump Invenio database into SQL file called FILENAME living in
    DIRNAME.
    """
    write_message("... writing %s" % dirname + os.sep + filename)
    cmd = CFG_PATH_MYSQL + 'dump'
    if not os.path.exists(cmd):
        msg = "ERROR: cannot find %s." % cmd
        write_message(msg, stream=sys.stderr)
        raise StandardError(msg)

    cmd += " --skip-opt --add-drop-table --add-locks --create-options " \
           " --quick --extended-insert --set-charset --disable-keys " \
           " --host=%s --user=%s --password=%s %s | %s -c " % \
           (escape_shell_arg(CFG_DATABASE_HOST),
            escape_shell_arg(CFG_DATABASE_USER),
            escape_shell_arg(CFG_DATABASE_PASS),
            escape_shell_arg(CFG_DATABASE_NAME),
            CFG_PATH_GZIP)
    dummy1, dummy2, dummy3 = run_shell_command(cmd, None, dirname + os.sep + filename)
    if dummy1:
        msg = "ERROR: mysqldump exit code is %s." % repr(dummy1)
        write_message(msg, stream=sys.stderr)
        raise StandardError(msg)
    if dummy2:
        msg = "ERROR: mysqldump stdout is %s." % repr(dummy1)
        write_message(msg, stream=sys.stderr)
        raise StandardError(msg)
    if dummy3:
        msg = "ERROR: mysqldump stderr is %s." % repr(dummy1)
        write_message(msg, stream=sys.stderr)
        raise StandardError(msg)


def _dbdump_elaborate_submit_param(key, value, dummyopts, dummyargs):
    """
    Elaborate task submission parameter.  See bibtask's
    task_submit_elaborate_specific_parameter_fnc for help.
    """
    if key in ('-n', '--number'):
        try:
            task_set_option('number', int(value))
        except ValueError:
            raise StandardError("ERROR: Number '%s' is not integer." % value)
    elif key in ('-o', '--output'):
        if os.path.isdir(value):
            task_set_option('output', value)
        else:
            raise StandardError("ERROR: Output '%s' is not a directory." % \
                  value)
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
    output_fil_prefix = CFG_DATABASE_NAME + '-dbdump-'
    output_fil_suffix = task_get_task_param('task_starting_time').replace(' ', '_') + '.sql.gz'
    output_fil = output_fil_prefix + output_fil_suffix
    write_message("Reading parameters ended")
    # make dump:
    task_update_progress("Dumping database")
    write_message("Database dump started")
    _dump_database(output_dir, output_fil)
    write_message("Database dump ended")
    # prune old dump files:
    task_update_progress("Pruning old dump files")
    write_message("Pruning old dump files started")
    _delete_old_dumps(output_dir, output_fil_prefix, output_num)
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
""" % CFG_LOGDIR,
              version=__revision__,
              specific_params=("n:o:",
                               ["number=", "output="]),
              task_submit_elaborate_specific_parameter_fnc=_dbdump_elaborate_submit_param,
              task_run_fnc=_dbdump_run_task_core)


if __name__ == '__main__':
    main()

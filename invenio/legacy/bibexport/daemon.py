# -*- mode: python; coding: utf-8; -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011 CERN.
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
BibExport daemon.

Usage: %s [options]

 Scheduling options:
 -u, --user=USER           user name to store task, password needed
 -s, --sleeptime=SLEEP     time after which to repeat tasks (no)
                            e.g.: 1s, 30m, 24h, 7d
 -t, --time=TIME           moment for the task to be active (now)
                            e.g.: +15s, 5m, 3h , 2002-10-27 13:57:26
 General options:
 -h, --help                print this help and exit
 -V, --version             print version and exit
 -v, --verbose=LEVEL       verbose level (from 0 to 9, default 1)
"""

__revision__ = "$Id$"

import os
import sys
from ConfigParser import ConfigParser

from invenio.config import CFG_ETCDIR
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibsched.bibtask import task_init, write_message, task_set_option, \
       task_get_option, task_has_option, task_get_task_param

from .registry import configurations

def _detect_jobs_to_run(string_of_jobnames=None):
    """Detect which jobs to run from optional string of jobs.
       If not passed, run all jobs.
       Return list of jobnames to run."""
    if string_of_jobnames:
        jobnames = string_of_jobnames.split(',')
    else:
        jobnames = []
        # FIXME: pay attention to periodicity; extract only jobs needed to run
        res = run_sql("SELECT jobname FROM expJOB")
        for row in res:
            jobnames.append(row[0])
    return jobnames

def _detect_export_method(jobname):
    """Detect export method of JOBNAME.  Basically, parse JOBNAME.cfg
       and return export_method.  Return None if problem found."""
    jobconf = ConfigParser()
    jobconffile = configurations.get(jobname, '')
    if not os.path.exists(jobconffile):
        write_message("ERROR: cannot find config file %s." % jobconffile, sys.stderr)
        return None
    jobconf.read(jobconffile)
    export_method = jobconf.get('export_job', 'export_method')
    return export_method

def _update_job_lastrun_time(jobname):
    """Update expJOB table and set lastrun time of JOBNAME to the task
    starting time."""
    run_sql("UPDATE expJOB SET lastrun=%s WHERE jobname=%s",
            (task_get_task_param('task_starting_time'), jobname,))

def task_run_core():
    """
    Runs the task by fetching arguments from the BibSched task queue.  This is
    what BibSched will be invoking via daemon call.
    """
    errors_encountered_p = False
    jobnames = _detect_jobs_to_run(task_get_option('wjob'))
    for jobname in jobnames:
        jobname_export_method = _detect_export_method(jobname)
        if not jobname_export_method:
            write_message("ERROR: cannot detect export method for job %s." % jobname, sys.stderr)
            errors_encountered_p = True
        else:
            try:
                # every bibexport method must define run_export_job() that will do the job
                exec "from invenio.bibexport_method_%s import run_export_method" % jobname_export_method
                write_message("started export job " + jobname, verbose=3)
                # pylint: disable=E0602
                # The import is done via the exec command 2 lines above.
                run_export_method(jobname)
                # pylint: enable=E0602
                _update_job_lastrun_time(jobname)
                write_message("finished export job " + jobname, verbose=3)
            except Exception as msg:
                write_message("ERROR: cannot run export job %s: %s." % (jobname, msg), sys.stderr)
                errors_encountered_p = True
    return not errors_encountered_p

def task_submit_check_options():
    """Check that options are valid."""
    if task_has_option('wjob'):
        jobnames = task_get_option('wjob')
        if jobnames:
            jobnames = jobnames.split(',')
            for jobname in jobnames:
                res = run_sql("SELECT COUNT(*) FROM expJOB WHERE jobname=%s", (jobname,))
                if res and res[0][0]:
                    # okay, jobname exists
                    pass
                else:
                    write_message("Sorry, job name %s is not known. Exiting." % jobname)
                    return False
    return True

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """Usual 'elaboration' of task specific parameters adapted to the bibexport task."""
    if key in ("-w", "--wjob"):
        task_set_option("wjob", value)
    else:
        return False
    return True

def force_recrawling():
    """
    This function touches a simple file whose modification is going to be
    used by the sitemap generator in order to know what minimum modification
    date to export to crawlers. (useful e.g. in case of major update of
    the interface).
    """
    from invenio.legacy.bibexport.sitemap import _CFG_FORCE_RECRAWLING_TIMESTAMP_PATH
    open(_CFG_FORCE_RECRAWLING_TIMESTAMP_PATH, "w").write("DUMMY")

def main():
    """Main function that constructs full bibtask."""
    if '--force-recrawling' in sys.argv:
        force_recrawling()
        print "Recrawling forced"
        sys.exit(1)
    task_init(authorization_action='runbibexport',
              authorization_msg="BibExport Task Submission",
              help_specific_usage="""Export options:
  -w,  --wjob=j1[,j2]\tRun specific exporting jobs j1, j2, etc (e.g. 'sitemap').
  --force-recrawling\tWhen using the sitemap export will force all the timestamp
                    \tthere included to refer to correspond at least to now. In
                    \tthis way crawlers are going to crawl all the content again.
                    \tThis is useful in case of a major update in the detailed
                    \tview of records.
""",
              version=__revision__,
              specific_params=("w:", ["wjob="]),
              task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
              task_submit_check_options_fnc=task_submit_check_options,
              task_run_fnc=task_run_core)

if __name__ == "__main__":
    _detect_export_method("sitemap")
    main()

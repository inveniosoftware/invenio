# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDS Invenio Bibliographic Task Class.

BibTask class.
"""

__revision__ = "$Id$"

import sys
from invenio.dbquery import run_sql
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_PREFIX
import getopt
import getpass
import marshal
import signal
import re
import time
import traceback
import os

_task_self = None

class BibTask:
    def __init__(self, header, task_name, action, description, output=sys.stdout):
        """ Construct a BibTask.
        @param header is the header to print in logs.
        @param task_name is the name of the task
        @param action is the action name connected with this task and checked
        by acc_authorize_action
        @param description will be printed in the help page.
        @param output is the stream to which to output log strings.
        #"""
        self.options = {} # global variable to hold task options
        self.output = output
        self.header = header
        self.task_name = task_name
        self.action = action
        self.description = description
        self._check_command_line()

    def flush_cache(self):
        """ Reimplement to flush cashes to STOP."""
        pass

    def close_tables(self):
        """ Reimplement to close tables to STOP. """
        pass

    def get_specific_usage(self):
        """ Reimplement to return the string for this task specific CLI params
        e.g. "  -n, --number      \t\t Fibonacci number to reach.\n"
        """
        return ""

    def get_specific_parameters(self):
        """ Reimplement to return a touple containing the short string form of
        additional CLI parameters and the long list form, with the syntax understood
        by getopt: e.g. ('n:', ['number='])
        """
        return ("", [])

    def elaborate_specific_parameter(self, key, value):
        """ Given the string key it checks it's meaning, eventually using the value.
        Usually it fills some key in the options dict.
        It must return True if it has elaborated the key, False, if it doesn't
        know that key.
        eg:
        if key in ['-n', '--number']:
            self.options['number'] = value
            return True
        return False
        """
        return False

    def task_core(self):
        """ Reimplement to add the body of the task."""
        pass

    def _authenticate(self, user):
        """Authenticate the user against the user database.
        Check for its password, if it exists.
        Check for action access rights.
        Return user name upon authorization success,
        do system exit upon authorization failure.
        """
        print self.header
        print "=" * len(self.header)
        if user == "":
            print >> sys.stdout, "\rUsername: ",
            user = sys.stdin.readline().lower().strip()
        else:
            print >> sys.stdout, "\rUsername:", user
        ## first check user pw:
        res = run_sql("select id,password from user where email=%s", (user,), 1) + \
            run_sql("select id,password from user where nickname=%s", (user,), 1)
        if not res:
            print "Sorry, %s does not exist." % user
            sys.exit(1)
        else:
            (uid_db, password_db) = res[0]
            if password_db:
                password_entered = getpass.getpass()
                if password_db == password_entered:
                    pass
                else:
                    print "Sorry, wrong credentials for %s." % user
                    sys.exit(1)
            ## secondly check authorization for the action:
            (auth_code, auth_message) = acc_authorize_action(uid_db, self.action)
            if auth_code != 0:
                print auth_message
                sys.exit(1)
        return user

    def _task_submit(self):
        """Submits task to the BibSched task queue.  This is what people will be invoking via command line."""
        ## sanity check: remove eventual "task" option:
        if self.options.has_key("task"):
            del self.options["task"]
        ## authenticate user:
        self.user = self._authenticate(self.options.get("user", ""))
        ## submit task:
        if self.options["verbose"] >= 9:
            print ""
            write_message("storing task options %s\n" % self.options)
        self.task_id = run_sql("""INSERT INTO schTASK (id,proc,user,runtime,sleeptime,status,arguments)
                            VALUES (NULL,%s,%s,%s,%s,'WAITING',%s)""",
                        (self.task_name, self.user, self.options["runtime"], self.options["sleeptime"], marshal.dumps(self.options)))
        ## update task number:
        self.options["task"] = self.task_id
        run_sql("""UPDATE schTASK SET arguments=%s WHERE id=%s""", (marshal.dumps(self.options), self.task_id))
        write_message("Task #%d submitted." % self.task_id)
        return self.task_id

    def task_update_progress(self, msg):
        """Updates progress information in the BibSched task table."""
        if self.options["verbose"] >= 9:
            write_message("Updating task progress to %s." % msg)
        return run_sql("UPDATE schTASK SET progress=%s where id=%s", (msg, self.options["task"]))

    def task_update_status(self, val):
        """Updates status information in the BibSched task table."""
        if self.options["verbose"] >= 9:
            write_message("Updating task status to %s." % val)
        return run_sql("UPDATE schTASK SET status=%s where id=%s", (val, self.options["task"]))

    def task_read_status(self):
        """Read status information in the BibSched task table."""
        res = run_sql("SELECT status FROM schTASK where id=%s", (self.task_id,), 1)
        try:
            out = res[0][0]
        except:
            out = 'UNKNOWN'
        return out

    def task_get_options(self):
        """Returns options for the task 'id' read from the BibSched task queue table."""
        out = {}
        res = run_sql("SELECT arguments FROM schTASK WHERE id=%s AND proc=%s", (self.task_id, self.task_name))
        try:
            out = marshal.loads(res[0][0])
        except:
            write_message("Error: %s task %d does not seem to exist." \
                % (self.task_name, self.task_id), sys.stderr)
            sys.exit(1)
        return out

    def _task_run(self):
        """Runs the task by fetching arguments from the BibSched task queue.  This is what BibSched will be invoking via daemon call.
        The task prints Fibonacci numbers for up to NUM on the stdout, and some messages on stderr.
        Return 1 in case of success and 0 in case of failure."""
        global _task_self
        assert(_task_self is None)
        ## We prepare the pid file inside /prefix/var/run/taskname_id.pid
        pidfile_name = os.path.join(CFG_PREFIX, 'var', 'run', '%s_%d.pid' % (self.task_name, self.task_id))
        pidfile = open(pidfile_name, 'w')
        pidfile.write(str(os.getpid()))
        pidfile.close()
        self.options = self.task_get_options() # get options from BibSched task table
        ## check task id:
        if not self.options.has_key("task"):
            write_message("Error: The task #%d does not seem to be a %s task." \
                % (self.task_id, self.task_name), sys.stderr)
            return 0
        ## check task status:
        task_status = self.task_read_status()
        if task_status != "WAITING":
            write_message("Error: The task #%d is %s.  I expected WAITING." % (self.task_id, task_status), sys.stderr)
            return 0
        ## we can run the task now:
        if self.options["verbose"]:
            write_message("Task #%d started." % self.task_id)
        self.task_update_status("RUNNING")
        _task_self = self
        ## initialize signal handler:
        signal.signal(signal.SIGUSR1, _task_sig_sleep)
        signal.signal(signal.SIGTERM, _task_sig_stop)
        signal.signal(signal.SIGABRT, _task_sig_suicide)
        signal.signal(signal.SIGCONT, _task_sig_wakeup)
        signal.signal(signal.SIGINT, _task_sig_unknown)
        ## run the task:
        self.task_core()
        ## we are done:
        self.task_update_status("DONE")
        if self.options["verbose"]:
            write_message("Task #%d finished." % self.task_id)
        ## Removing the pid
        os.remove(pidfile_name)
        return 1

    def usage(self, exitcode=1, msg=""):
        """Prints usage info."""
        if msg:
            sys.stderr.write("Error: %s.\n" % msg)
        sys.stderr.write("Usage: %s [options]\n" % sys.argv[0])
        specific_usage = self.get_specific_usage()
        if specific_usage:
            sys.stderr.write("Command options:\n")
            sys.stderr.write(specific_usage)
        sys.stderr.write("Scheduling options:\n")
        sys.stderr.write("  -u, --user=USER \t User name to submit the task as, password needed.\n")
        sys.stderr.write("  -t, --runtime=TIME \t Time to execute the task (now), e.g.: +15s, 5m, 3h, 2002-10-27 13:57:26\n")
        sys.stderr.write("  -s, --sleeptime=SLEEP \t Sleeping frequency after which to repeat task (no), e.g.: 30m, 2h, 1d\n")
        sys.stderr.write("General options:\n")
        sys.stderr.write("  -h, --help      \t\t Print this help.\n")
        sys.stderr.write("  -V, --version   \t\t Print version information.\n")
        sys.stderr.write("  -v, --verbose=LEVEL \t Verbose level (0=min, 1=default, 9=max).\n")
        if self.description:
            sys.stderr.write(self.description)
        sys.exit(exitcode)

    def _check_command_line(self):
        """Main function that analyzes command line input and calls whatever is appropriate.
        Useful for learning on how to write BibSched tasks."""
        ## parse command line:
        # set default values:
        self.options = {}
        self.options["runtime"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.options["sleeptime"] = ""
        self.options["verbose"] = 1
        if len(sys.argv) == 2 and sys.argv[1].isdigit():
            ## A - run the task
            self.task_id = int(sys.argv[1])
            self.options["task"] = self.task_id
            try:
                if not self._task_run():
                    write_message("Error occurred.  Exiting.", sys.stderr)
            except StandardError, e:
                write_message("Unexpected error occurred: %s." % e, sys.stderr)
                write_message("Traceback is:", sys.stderr)
                traceback.print_tb(sys.exc_info()[2])
                write_message("Exiting.", sys.stderr)
                self.task_update_status("ERROR")
        else:
            ## B - submit the task
            # set user-defined options:
            try:
                (short_params, long_params) = self.get_specific_parameters()
                opts, args = getopt.getopt(sys.argv[1:], "hVv:n:u:s:t:"+short_params, ["help", "version", "verbose=", "number=", "user=", "sleep=", "time="]+long_params)
            except getopt.GetoptError, err:
                self.usage(1, err)
            try:
                for opt in opts:
                    if opt[0] in ["-h", "--help"]:
                        self.usage(0)
                    elif opt[0] in ["-V", "--version"]:
                        print __revision__
                        sys.exit(0)
                    elif opt[0] in [ "-u", "--user"]:
                        self.options["user"] = opt[1]
                    elif opt[0] in ["-v", "--verbose"]:
                        self.options["verbose"] = int(opt[1])
                    elif opt[0] in [ "-s", "--sleeptime" ]:
                        get_datetime(opt[1]) # see if it is a valid shift
                        self.options["sleeptime"] = opt[1]
                    elif opt[0] in [ "-t", "--runtime" ]:
                        self.options["runtime"] = get_datetime(opt[1])
                    elif self.elaborate_specific_parameter(opt[0], opt.get(1, None)):
                        pass
                    else:
                        self.usage(1)
            except StandardError, e:
                self.usage(e)
            self._task_submit()
        return

def write_messages(msgs, stream=sys.stdout):
    for msg in msgs.split('\n'):
        write_message(msg, stream)

def write_message(msg, stream=sys.stdout):
    """Write message and flush output stream (may be sys.stdout or sys.stderr).  Useful for debugging stuff."""
    if msg:
        if stream == sys.stdout or stream == sys.stderr:
            stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
            try:
                stream.write("%s\n" % msg)
            except UnicodeEncodeError:
                stream.write("%s\n" % msg.encode('ascii', 'backslashreplace'))
            stream.flush()
        else:
            sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)

def _task_sig_sleep(sig, frame):
    """Signal handler for the 'sleep' signal sent by BibSched."""
    task_self = frame.f_globals._task_self
    if task_self.options["verbose"] >= 9:
        write_message("task_sig_sleep(), got signal %s frame %s" % (sig, frame))
    write_message("sleeping...")
    task_self.task_update_status("SLEEPING")
    signal.pause() # wait for wake-up signal

def _task_sig_wakeup(sig, frame):
    """Signal handler for the 'wakeup' signal sent by BibSched."""
    task_self = frame.f_globals._task_self
    if task_self.options["verbose"] >= 9:
        write_message("task_sig_wakeup(), got signal %s frame %s" % (sig, frame))
    write_message("continuing...")
    task_self.task_update_status("CONTINUING")

def _task_sig_stop(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    task_self = frame.f_globals._task_self
    if task_self.options["verbose"] >= 9:
        write_message("task_sig_stop(), got signal %s frame %s" % (sig, frame))
    write_message("stopping...")
    task_self.task_update_status("STOPPING")
    if callable(task_self.flush_cache):
        write_message("flushing cache or whatever...")
        task_self.flush_cache()
        time.sleep(3)
    if callable(task_self.close_tables):
        write_message("closing tables or whatever...")
        task_self.close_tables()
        time.sleep(1)
    write_message("stopped")
    task_self.task_update_status("STOPPED")
    sys.exit(0)

def _task_sig_suicide(sig, frame):
    """Signal handler for the 'suicide' signal sent by BibSched."""
    task_self = frame.f_globals._task_self
    if task_self.options["verbose"] >= 9:
        write_message("task_sig_suicide(), got signal %s frame %s" % (sig, frame))
    write_message("suiciding myself now...")
    task_self.task_update_status("SUICIDING")
    write_message("suicided")
    task_self.task_update_status("SUICIDED")
    sys.exit(0)

def _task_sig_unknown(sig, frame):
    """Signal handler for the other unknown signals sent by shell or user."""
    # do nothing for unknown signals:
    task_self = frame.f_globals._task_self
    write_message("unknown signal %d (frame %s) ignored" % (sig, frame))

def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    date = time.time()
    shift_re = re.compile("([-\+]{0,1})([\d]+)([dhms])")
    factors = {"d":24*3600, "h":3600, "m":60, "s":1}
    m = shift_re.match(var)
    if m:
        sign = m.groups()[0] == "-" and -1 or 1
        factor = factors[m.groups()[2]]
        value = float(m.groups()[1])
        date = time.localtime(date + sign * factor * value)
        date = time.strftime(format_string, date)
    else:
        date = time.strptime(var, format_string)
        date = time.strftime(format_string, date)
    return date


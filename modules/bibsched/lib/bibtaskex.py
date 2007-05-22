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

"""CDS Invenio Bibliographic Task Example.

Demonstrates BibTask <-> BibSched connectivity, signal handling,
error handling, etc.
"""

__revision__ = "$Id$"

import sys
from invenio.dbquery import run_sql
from invenio.access_control_engine import acc_authorize_action
import getopt
import getpass
import marshal
import signal
import re
import string
import time
import traceback

options = {} # global variable to hold task options

cfg_n_default = 30 # how many Fibonacci numbers to calculate if none submitted?

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

def write_message(msg, stream=sys.stdout):
    """Write message and flush output stream (may be sys.stdout or sys.stderr).  Useful for debugging stuff."""
    if stream == sys.stdout or stream == sys.stderr:
        stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
        try:
            stream.write("%s\n" % msg)
        except UnicodeEncodeError:
            stream.write("%s\n" % msg.encode('ascii', 'backslashreplace'))
        stream.flush()
    else:
        sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)
    return

def task_sig_sleep(sig, frame):
    """Signal handler for the 'sleep' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_sleep(), got signal %s frame %s" % (sig, frame))
    write_message("sleeping...")
    task_update_status("SLEEPING")
    signal.pause() # wait for wake-up signal

def task_sig_wakeup(sig, frame):
    """Signal handler for the 'wakeup' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_wakeup(), got signal %s frame %s" % (sig, frame))
    write_message("continuing...")
    task_update_status("CONTINUING")

def task_sig_stop(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_stop(), got signal %s frame %s" % (sig, frame))
    write_message("stopping...")
    task_update_status("STOPPING")
    write_message("flushing cache or whatever...")
    time.sleep(3)
    write_message("closing tables or whatever...")
    time.sleep(1)
    write_message("stopped")
    task_update_status("STOPPED")
    sys.exit(0)
    
def task_sig_suicide(sig, frame):
    """Signal handler for the 'suicide' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_suicide(), got signal %s frame %s" % (sig, frame))
    write_message("suiciding myself now...")
    task_update_status("SUICIDING")
    write_message("suicided")
    task_update_status("SUICIDED")
    sys.exit(0)

def task_sig_unknown(sig, frame):
    """Signal handler for the other unknown signals sent by shell or user."""
    # do nothing for unknown signals:
    write_message("unknown signal %d (frame %s) ignored" % (sig, frame)) 

def fib(n):
    """Returns Fibonacci number for 'n'."""
    out = 1
    if n >= 2:
        out = fib(n-2) + fib(n-1)
    return out

def authenticate(user, header="BibTaskEx Task Submission", action="runbibtaskex"):
    """Authenticate the user against the user database.
       Check for its password, if it exists.
       Check for action access rights.
       Return user name upon authorization success,
       do system exit upon authorization failure.
       """
    print header
    print "=" * len(header)
    if user == "":
        print >> sys.stdout, "\rUsername: ",
        user = string.strip(string.lower(sys.stdin.readline()))
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
        (auth_code, auth_message) = acc_authorize_action(uid_db, action)
        if auth_code != 0:
            print auth_message
            sys.exit(1)
    return user

def task_submit():
    """Submits task to the BibSched task queue.  This is what people will be invoking via command line."""
    global options
    ## sanity check: remove eventual "task" option:
    if options.has_key("task"):
        del options["task"]
    ## authenticate user:
    user = authenticate(options.get("user", ""))
    ## submit task:
    if options["verbose"] >= 9:
        print ""
        write_message("storing task options %s\n" % options)
    task_id = run_sql("""INSERT INTO schTASK (id,proc,user,runtime,sleeptime,status,arguments)
                         VALUES (NULL,'bibtaskex',%s,%s,%s,'WAITING',%s)""",
                      (user, options["runtime"], options["sleeptime"], marshal.dumps(options)))
    ## update task number: 
    options["task"] = task_id
    run_sql("""UPDATE schTASK SET arguments=%s WHERE id=%s""", (marshal.dumps(options), task_id))
    write_message("Task #%d submitted." % task_id)    
    return task_id

def task_update_progress(msg):
    """Updates progress information in the BibSched task table."""
    global options
    if options["verbose"] >= 9:
        write_message("Updating task progress to %s." % msg)
    return run_sql("UPDATE schTASK SET progress=%s where id=%s", (msg, options["task"]))

def task_update_status(val):
    """Updates status information in the BibSched task table."""
    global options
    if options["verbose"] >= 9:
        write_message("Updating task status to %s." % val)
    return run_sql("UPDATE schTASK SET status=%s where id=%s", (val, options["task"]))    

def task_read_status(task_id):
    """Read status information in the BibSched task table."""
    res = run_sql("SELECT status FROM schTASK where id=%s", (task_id,), 1)
    try:
        out = res[0][0]
    except:
        out = 'UNKNOWN'
    return out

def task_get_options(id):
    """Returns options for the task 'id' read from the BibSched task queue table."""
    out = {}
    res = run_sql("SELECT arguments FROM schTASK WHERE id=%s AND proc='bibtaskex'", (id,))
    try:
        out = marshal.loads(res[0][0])
    except:
        write_message("Error: BibTaskEx task %d does not seem to exist." % id, sys.stderr)
        sys.exit(1)
    return out

def task_run(task_id):
    """Runs the task by fetching arguments from the BibSched task queue.  This is what BibSched will be invoking via daemon call.
       The task prints Fibonacci numbers for up to NUM on the stdout, and some messages on stderr.
       Return 1 in case of success and 0 in case of failure."""
    global options
    options = task_get_options(task_id) # get options from BibSched task table
    ## check task id:
    if not options.has_key("task"):
        write_message("Error: The task #%d does not seem to be a BibTaskEx task." % task_id, sys.stderr)
        return 0
    ## check task status:
    task_status = task_read_status(task_id)
    if task_status != "WAITING":
        write_message("Error: The task #%d is %s.  I expected WAITING." % (task_id, task_status), sys.stderr)
        return 0
    ## we can run the task now:
    if options["verbose"]:
        write_message("Task #%d started." % task_id)
    task_update_status("RUNNING")
    ## initialize signal handler:
    signal.signal(signal.SIGUSR1, task_sig_sleep)
    signal.signal(signal.SIGTERM, task_sig_stop)
    signal.signal(signal.SIGABRT, task_sig_suicide)
    signal.signal(signal.SIGCONT, task_sig_wakeup)
    signal.signal(signal.SIGINT, task_sig_unknown)
    ## run the task:
    if options.has_key("number"):
        n = options["number"]
    else:
        n = cfg_n_default
    if options["verbose"] >= 9:
        write_message("Printing %d Fibonacci numbers." % n)
    for i in range(0, n):
        if i > 0 and i % 4 == 0:
            if options["verbose"] >= 3:
                write_message("Error: water in the CPU.  Ignoring and continuing.", sys.stderr)
        elif i > 0 and i % 5 == 0:
            if options["verbose"]:
                write_message("Error: floppy drive dropped on the floor.  Ignoring and continuing.", sys.stderr)
        if options["verbose"]:
            write_message("fib(%d)=%d" % (i, fib(i)))
        task_update_progress("Done %d out of %d." % (i, n))
        time.sleep(1)
    ## we are done:
    task_update_progress("Done %d out of %d." % (n, n))
    task_update_status("DONE")
    if options["verbose"]:
        write_message("Task #%d finished." % task_id)
    return 1

def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s [options]\n" % sys.argv[0])
    sys.stderr.write("Command options:\n")
    sys.stderr.write("  -n, --number=NUM\t Print Fibonacci numbers for up to NUM.  [default=%d]\n" % cfg_n_default)
    sys.stderr.write("Scheduling options:\n")
    sys.stderr.write("  -u, --user=USER \t User name to submit the task as, password needed.\n")
    sys.stderr.write("  -t, --runtime=TIME \t Time to execute the task (now), e.g.: +15s, 5m, 3h, 2002-10-27 13:57:26\n")
    sys.stderr.write("  -s, --sleeptime=SLEEP \t Sleeping frequency after which to repeat task (no), e.g.: 30m, 2h, 1d\n")
    sys.stderr.write("General options:\n")
    sys.stderr.write("  -h, --help      \t\t Print this help.\n")
    sys.stderr.write("  -V, --version   \t\t Print version information.\n")
    sys.stderr.write("  -v, --verbose=LEVEL \t Verbose level (0=min, 1=default, 9=max).\n")
    sys.exit(exitcode)

def main():
    """Main function that analyzes command line input and calls whatever is appropriate.
       Useful for learning on how to write BibSched tasks."""
    global options
    ## parse command line:
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        ## A - run the task
        task_id = int(sys.argv[1])
        try:
            if not task_run(task_id):
                write_message("Error occurred.  Exiting.", sys.stderr)
        except StandardError, e:
            write_message("Unexpected error occurred: %s." % e, sys.stderr)
            write_message("Traceback is:", sys.stderr)
            traceback.print_tb(sys.exc_info()[2])
            write_message("Exiting.", sys.stderr)
            task_update_status("ERROR")                                   
    else:
        ## B - submit the task
        # set default values:
        options = {}
        options["runtime"] = time.strftime("%Y-%m-%d %H:%M:%S") 
        options["sleeptime"] = ""
        options["verbose"] = 1
        # set user-defined options:
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hVv:n:u:s:t:", ["help", "version", "verbose=", "number=", "user=", "sleep=", "time="])
        except getopt.GetoptError, err:
            usage(1, err)
        try:
            for opt in opts:
                if opt[0] in ["-h", "--help"]:
                    usage(0)
                elif opt[0] in ["-V", "--version"]:
                    print __revision__
                    sys.exit(0)
                elif opt[0] in [ "-u", "--user"]:
                    options["user"] = opt[1]
                elif opt[0] in ["-v", "--verbose"]:
                    options["verbose"] = int(opt[1])
                elif opt[0] in ["-n", "--number"]:
                    options["number"] = int(opt[1])
                elif opt[0] in [ "-s", "--sleeptime" ]:
                    get_datetime(opt[1]) # see if it is a valid shift
                    options["sleeptime"] = opt[1]
                elif opt[0] in [ "-t", "--runtime" ]:
                    options["runtime"] = get_datetime(opt[1])
                else:
                    usage(1)
        except StandardError, e:
            usage(e)        
        task_submit()
    return

### okay, here we go:
if __name__ == '__main__':
    main()

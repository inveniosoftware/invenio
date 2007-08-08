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
from invenio.dbquery import run_sql, _db_login, _db_logout
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
from invenio.access_control_config import CFG_EXTERNAL_AUTH_USING_SSO, \
    CFG_EXTERNAL_AUTHENTICATION
from invenio.webuser import get_user_preferences, get_email

# Which tasks don't need to ask the user for authorization?
cfg_valid_processes_no_auth_needed = ("bibupload")

# Global variables
_options = {'verbose' : 1, 'name' : ''}
_task_params = {}


def task_init(
    authorization_action="",
    authorization_msg="",
    description="",
    help_specific_usage="",
    version=__revision__,
    specific_params=("", []),
    task_stop_helper_fnc=None,
    task_submit_elaborate_specific_parameter_fnc=None,
    task_submit_check_options_fnc=None,
    task_run_fnc=None):
    """ Initialize a BibTask.
    @param authorization_action is the name of the authorization action
    connected with this task;
    @param authorization_msg is the header printed when asking for an
    authorization password;
    @param description is the generic description printed in the usage page;
    @param help_specific_usage is the specific parameter help
    @param task_stop_fnc is a function that will be called
    whenever the task is stopped
    @param task_submit_elaborate_specific_parameter_fnc will be called passing
    a key and a value, for parsing specific cli parameters. Must return True if
    it has recognized the parameter. Must eventually update the options with
    bibtask_set_option;
    @param task_submit_check_options must check the validity of options (via
    bibtask_get_option) once all the options where parsed;
    @param task_run_fnc will be called as the main core function. Must return
    False in case of errors.
    """
    _options["runtime"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _options["sleeptime"] = ""
    _options["verbose"] = 1
    _options["version"] = version
    _task_params["task_name"] = os.path.basename(sys.argv[0])
    _task_params["task_stop_helper_fnc"] = task_stop_helper_fnc
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        ## A - run the task
        _task_params['task_id'] = int(sys.argv[1])
        _options["task"] = _task_params['task_id']
        try:
            if not _task_run(task_run_fnc):
                write_message("Error occurred.  Exiting.", sys.stderr)
        except StandardError, e:
            write_message("Unexpected error occurred: %s." % e, sys.stderr)
            write_message("Traceback is:", sys.stderr)
            traceback.print_tb(sys.exc_info()[2])
            write_message("Exiting.", sys.stderr)
            task_update_status("ERROR")
    else:
        ## B - submit the task
        # set user-defined options:
        try:
            (short_params, long_params) = specific_params
            opts, args = getopt.getopt(sys.argv[1:], "hVv:u:s:t:" +
                short_params, [
                    "help",
                    "version",
                    "verbose=",
                    "user=",
                    "sleep=",
                    "time="
                ] + long_params)
        except getopt.GetoptError, err:
            _usage(1, err, help_specific_usage=help_specific_usage, description=description)
        try:
            for opt in opts:
                if opt[0] in ["-h", "--help"]:
                    _usage(0, help_specific_usage=help_specific_usage, description=description)
                elif opt[0] in ["-V", "--version"]:
                    print _options["version"]
                    sys.exit(0)
                elif opt[0] in [ "-u", "--user"]:
                    _options["user"] = opt[1]
                elif opt[0] in ["-v", "--verbose"]:
                    _options["verbose"] = int(opt[1])
                elif opt[0] in [ "-s", "--sleeptime" ]:
                    get_datetime(opt[1]) # see if it is a valid shift
                    _options["sleeptime"] = opt[1]
                elif opt[0] in [ "-t", "--runtime" ]:
                    _options["runtime"] = get_datetime(opt[1])
                elif not callable(task_submit_elaborate_specific_parameter_fnc) or \
                    not task_submit_elaborate_specific_parameter_fnc(opt[0],
                        opt[1], opts, args):
                    _usage(1, help_specific_usage=help_specific_usage, description=description)
        except StandardError, e:
            _usage(e, help_specific_usage=help_specific_usage, description=description)
        if callable(task_submit_check_options_fnc):
            if not task_submit_check_options_fnc():
                _usage(1, help_specific_usage=help_specific_usage, description=description)
        _task_submit(authorization_action, authorization_msg)

def task_set_option(key, value):
    """Set an value to key in the option dictionary of the task"""
    _options[key] = value

def task_get_option(key, default=None):
    """Returns the value corresponding to key in the option dictionary of the task"""
    return _options.get(key, default)

def task_has_option(key):
    """Map the has_key query to _options"""
    return _options.has_key(key)

def task_get_task_param(key):
    """Returns the value corresponding to the particular task param"""
    return _task_params.get(key)

def task_update_progress(msg):
    """Updates progress information in the BibSched task table."""
    if _options["verbose"] >= 9:
        write_message("Updating task progress to %s." % msg)
    return run_sql("UPDATE schTASK SET progress=%s where id=%s",
        (msg, _options["task"]))

def task_update_status(val):
    """Updates status information in the BibSched task table."""
    if _options["verbose"] >= 9:
        write_message("Updating task status to %s." % val)
    return run_sql("UPDATE schTASK SET status=%s where id=%s",
        (val, _options["task"]))

def task_read_status():
    """Read status information in the BibSched task table."""
    res = run_sql("SELECT status FROM schTASK where id=%s",
        (_task_params['task_id'],), 1)
    try:
        out = res[0][0]
    except:
        out = 'UNKNOWN'
    return out


def write_messages(msgs, stream=sys.stdout, verbose=1):
    """Write many messages through write_message"""
    for msg in msgs.split('\n'):
        write_message(msg, stream, verbose)

def write_message(msg, stream=sys.stdout, verbose=1):
    """Write message and flush output stream (may be sys.stdout or sys.stderr).
    Useful for debugging stuff."""
    if msg and _options['verbose'] >= verbose:
        if stream == sys.stdout or stream == sys.stderr:
            stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ",
                time.localtime()))
            try:
                stream.write("%s\n" % msg)
            except UnicodeEncodeError:
                stream.write("%s\n" % msg.encode('ascii', 'backslashreplace'))
            stream.flush()
        else:
            sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)

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

def authenticate(user, authorization_action, authorization_msg=""):
    """Authenticate the user against the user database.
    Check for its password, if it exists.
    Check for authorization_action access rights.
    Return user name upon authorization success,
    do system exit upon authorization failure.
    """
    # With SSO it's impossible to check for pwd
    if CFG_EXTERNAL_AUTH_USING_SSO or \
            _task_params['task_name'] in cfg_valid_processes_no_auth_needed:
        return user
    if authorization_msg:
        print authorization_msg
        print "=" * len(authorization_msg)
    if user == "":
        print >> sys.stdout, "\rUsername: ",
        user = sys.stdin.readline().lower().strip()
    else:
        print >> sys.stdout, "\rUsername:", user
    ## first check user:
    # p_un passed may be an email or a nickname:
    res = run_sql("select id from user where email=%s", (user,), 1) + \
        run_sql("select id from user where nickname=%s", (user,), 1)
    if not res:
        print "Sorry, %s does not exist." % user
        sys.exit(1)
    else:
        uid = res[0][0]
        ok = False
        login_method = get_user_preferences(uid)['login_method']
        if not CFG_EXTERNAL_AUTHENTICATION[login_method][0]:
            #Local authentication, let's see if we want passwords.
            res = run_sql("select id from user where id=%s "
                    "and password=AES_ENCRYPT(email,'')",
            (uid,), 1)
            if res:
                ok = True
        if not ok:
            password_entered = getpass.getpass()
            if not CFG_EXTERNAL_AUTHENTICATION[login_method][0]:
                res = run_sql("select id from user where id=%s "
                        "and password=AES_ENCRYPT(email, %s)",
                (uid, password_entered), 1)
                if res:
                    ok = True
            else:
                if CFG_EXTERNAL_AUTHENTICATION[login_method][0].auth_user(get_email(uid), password_entered):
                    ok = True
        if not ok:
            print "Sorry, wrong credentials for %s." % user
            sys.exit(1)
        else:
            ## secondly check authorization for the authorization_action:
            (auth_code, auth_message) = acc_authorize_action(uid, authorization_action)
            if auth_code != 0:
                print auth_message
                sys.exit(1)
            return user

def _task_submit(authorization_action, authorization_msg):
    """Submits task to the BibSched task queue.  This is what people will
        be invoking via command line."""
    ## sanity check: remove eventual "task" option:
    if _options.has_key("task"):
        del _options["task"]

    ## authenticate user:
    _options['user'] = authenticate(_options.get("user", ""), authorization_action, authorization_msg)

    ## submit task:
    if _options["verbose"] >= 9:
        print ""
        write_message("storing task options %s\n" % _options)
    _task_params['task_id'] = run_sql("""INSERT INTO schTASK
        (id,proc,user,runtime,sleeptime,status,arguments)
        VALUES (NULL,%s,%s,%s,%s,'WAITING',%s)""",
        (_task_params['task_name'], _options['user'], _options["runtime"],
        _options["sleeptime"],
        marshal.dumps(_options)))

    ## update task number:
    _options["task"] = _task_params['task_id']
    run_sql("""UPDATE schTASK SET arguments=%s WHERE id=%s""",
        (marshal.dumps(_options), _task_params['task_id']))
    write_message("Task #%d submitted." % _task_params['task_id'])
    return _task_params['task_id']


def _task_get_options():
    """Returns options for the task 'id' read from the BibSched task
    queue table."""
    out = {}
    res = run_sql("SELECT arguments FROM schTASK WHERE id=%s AND proc=%s",
        (_task_params['task_id'], _task_params['task_name']))
    try:
        out = marshal.loads(res[0][0])
    except:
        write_message("Error: %s task %d does not seem to exist." \
            % (_task_params['task_name'], _task_params['task_id']), sys.stderr)
        sys.exit(1)
    write_message('Options retrieved: %s' % out, verbose=9)
    return out

def _task_run(task_run_fnc=None):
    """Runs the task by fetching arguments from the BibSched task queue.
    This is what BibSched will be invoking via daemon call.
    The task prints Fibonacci numbers for up to NUM on the stdout, and some
    messages on stderr.
    @param task_run_fnc will be called as the main core function. Must return
    False in case of errors.
    Return 1 in case of success and 0 in case of failure."""

    ## We prepare the pid file inside /prefix/var/run/taskname_id.pid
    global _options
    pidfile_name = os.path.join(CFG_PREFIX, 'var', 'run',
        'bibsched_task_%d.pid' % _task_params['task_id'])
    pidfile = open(pidfile_name, 'w')
    pidfile.write(str(os.getpid()))
    pidfile.close()

    _options = _task_get_options() # get options from BibSched task table
    ## check task id:
    if not _options.has_key("task"):
        write_message("Error: The task #%d does not seem to be a %s task."
            % (_task_params['task_id'], _task_params['task_name']), sys.stderr)
        return False
    ## check task status:
    task_status = task_read_status()
    if task_status != "WAITING":
        write_message("Error: The task #%d is %s.  I expected WAITING." %
            (_task_params['task_id'], task_status), sys.stderr)
        return False
    ## we can run the task now:
    if _options["verbose"]:
        write_message("Task #%d started." % _task_params['task_id'])
    task_update_status("RUNNING")
    ## initialize signal handler:
    signal.signal(signal.SIGUSR1, _task_sig_sleep)
    signal.signal(signal.SIGTERM, _task_sig_stop)
    signal.signal(signal.SIGABRT, _task_sig_suicide)
    signal.signal(signal.SIGCONT, _task_sig_wakeup)
    signal.signal(signal.SIGINT, _task_sig_unknown)
    ## run the task:
    _task_params['task_starting_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if callable(task_run_fnc) and task_run_fnc():
        task_update_status("DONE")
    else:
        task_update_status("DONE WITH ERRORS")

    ## we are done:
    if _options["verbose"]:
        write_message("Task #%d finished." % _task_params['task_id'])
    ## Removing the pid
    os.remove(pidfile_name)
    return True

def _usage(exitcode=1, msg="", help_specific_usage="", description=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s [options]\n" % sys.argv[0])
    if help_specific_usage:
        sys.stderr.write("Command options:\n")
        sys.stderr.write(help_specific_usage)
    sys.stderr.write("Scheduling options:\n")
    sys.stderr.write("  -u, --user=USER \t User name to submit the"
        " task as, password needed.\n")
    sys.stderr.write("  -t, --runtime=TIME \t Time to execute the"
        " task (now), e.g.: +15s, 5m, 3h, 2002-10-27 13:57:26\n")
    sys.stderr.write("  -s, --sleeptime=SLEEP \t Sleeping frequency after"
        " which to repeat task (no), e.g.: 30m, 2h, 1d\n")
    sys.stderr.write("General options:\n")
    sys.stderr.write("  -h, --help      \t\t Print this help.\n")
    sys.stderr.write("  -V, --version   \t\t Print version information.\n")
    sys.stderr.write("  -v, --verbose=LEVEL \t Verbose level (0=min,"
        " 1=default, 9=max).\n")
    if description:
        sys.stderr.write(description)
    sys.exit(exitcode)


def _task_sig_sleep(sig, frame):
    """Signal handler for the 'sleep' signal sent by BibSched."""
    write_message("task_sig_sleep(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    # _db_logout() #FIXME Not sure this can do more evil than good things.
    write_message("sleeping...")
    task_update_status("SLEEPING")
    signal.pause() # wait for wake-up signal

def _task_sig_wakeup(sig, frame):
    """Signal handler for the 'wakeup' signal sent by BibSched."""
    write_message("task_sig_wakeup(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    # _db_login(1) #FIXME Not sure this can do more evil than good things.
    write_message("continuing...")
    task_update_status("CONTINUING")

def _task_sig_stop(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    write_message("task_sig_stop(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("stopping...")
    task_update_status("STOPPING")
    if callable(_task_params['task_stop_helper_fnc']):
        try:
            write_message("flushing cache or whatever...")
            _task_params['task_stop_helper_fnc']()
            time.sleep(3)
        except StandardError, err:
            write_message("Error during stopping! %e" % err)
            task_update_status("STOPPINGFAILED")
            sys.exit(1)
    # _db_logout() #FIXME Not sure this can do more evil than good things.
    write_message("stopped")
    task_update_status("STOPPED")
    sys.exit(0)

def _task_sig_suicide(sig, frame):
    """Signal handler for the 'suicide' signal sent by BibSched."""
    write_message("task_sig_suicide(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("suiciding myself now...")
    task_update_status("SUICIDING")
    _db_logout()
    write_message("suicided")
    task_update_status("SUICIDED")
    sys.exit(0)

def _task_sig_unknown(sig, frame):
    """Signal handler for the other unknown signals sent by shell or user."""
    # do nothing for unknown signals:
    write_message("unknown signal %d (frame %s) ignored" % (sig, frame))


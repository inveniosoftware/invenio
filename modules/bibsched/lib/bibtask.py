# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

A BibTask is an executable under CFG_BINDIR, whose name is stored in
bibtask_config.CFG_BIBTASK_VALID_TASKS.
A valid task must call the task_init function with the proper parameters.
Generic task related parameters (user, sleeptime, runtime, task_id, task_name
verbose)
go to _task_params global dictionary accessible through task_get_task_param.
Option specific to the particular BibTask go to _options global dictionary
and are accessible via task_get_option/task_set_option.

In order to log something properly, just use write_message(s) with the desired
verbose level.

task_update_status and task_update_progress can be used to update the status
of the task (DONE, FAILED, DONE WITH ERRORS...) and it's progress
(1 out 100..) within the bibsched monitor.

It is possible to enqueue a BibTask via API call by means of
task_low_level_submission.
"""

__revision__ = "$Id$"

import getopt
import getpass
import marshal
import os
import pwd
import re
import signal
import sys
import time
import datetime
import popen2
import traceback
import logging
import logging.handlers

from invenio.dbquery import run_sql, _db_login
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_PREFIX, CFG_BINDIR, CFG_LOGDIR, \
    CFG_BIBSCHED_PROCESS_USER
from invenio.errorlib import register_exception

from invenio.access_control_config import CFG_EXTERNAL_AUTH_USING_SSO, \
    CFG_EXTERNAL_AUTHENTICATION
from invenio.webuser import get_user_preferences, get_email
from invenio.bibtask_config import CFG_BIBTASK_VALID_TASKS, \
    CFG_BIBTASK_DEFAULT_TASK_SETTINGS

# Which tasks don't need to ask the user for authorization?
CFG_VALID_PROCESSES_NO_AUTH_NEEDED = ("bibupload", )
CFG_TASK_IS_NOT_A_DEAMON = ("bibupload", )

def fix_argv_paths(paths, argv=None):
    """Given the argv vector of cli parameters, and a list of path that
    can be relative and may have been specified within argv,
    it substitute all the occurencies of these paths in argv.
    argv is changed in place and returned.
    """
    if argv is None:
        argv = sys.argv
    for path in paths:
        for count in xrange(len(argv)):
            if path == argv[count]:
                argv[count] = os.path.realpath(path)
    return argv

def task_low_level_submission(name, user, *argv):
    """Let special lowlevel enqueuing of a task on the bibsche queue.
    @param name is the name of the bibtask. It must be a valid executable under
                CFG_BINDIR.
    @param user is a string that will appear as the "user" submitting the task.
                Since task are submitted via API it make sense to set the
                user to the name of the module/function that called
                task_low_level_submission.
    @param argv will be merged with the default setting of the given task as
                they can be found in bibtask_config. In order to know which
                variable are valid and which is the semantic, please have
                a glimpse at bibtask_config and to the source of the
                task_submit_elaborate_specific_parameter function of the
                desired bibtask.
    @return the task_id when the task is correctly enqueued.
    Use with care!
    Please use absolute paths in argv!
    """
    def get_priority(argv):
        """Try to get the priority by analysing the arguments."""
        priority = 0
        try:
            stripped_argv = [arg for arg in argv if not arg.startswith('-') or arg.startswith('-P') or arg.startswith('--priority')]
            opts, args = getopt.gnu_getopt(stripped_argv, 'P:', ['priority='])
            for opt in opts:
                if opt[0] in ('-P', '--priority'):
                    priority = opt[1]
        except:
            pass
        return priority

    task_id = None
    try:
        if not name in CFG_BIBTASK_VALID_TASKS:
            raise StandardError('%s is not a valid task name' % name)

        priority = get_priority(argv)
        argv = tuple([os.path.join(CFG_BINDIR, name)] + list(argv))

        ## submit task:
        task_id = run_sql("""INSERT INTO schTASK (proc,user,
            runtime,sleeptime,status,progress,arguments,priority)
            VALUES (%s,%s,NOW(),'','WAITING','',%s,%s)""",
            (name, user, marshal.dumps(argv), priority))

    except Exception:
        register_exception()
        if task_id:
            run_sql("""DELETE FROM schTASK WHERE id=%s""", (task_id, ))
        raise
    return task_id

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
    global _task_params, _options
    _task_params = {
        "version" : version,
        "task_stop_helper_fnc" : task_stop_helper_fnc,
        "task_name" : os.path.basename(sys.argv[0]),
        "task_specific_name" : '',
        "user" : '',
        "verbose" : 1,
        "sleeptime" : '',
        "runtime" : time.strftime("%Y-%m-%d %H:%M:%S"),
        "priority" : 0,
        "runtime_limit" : None
    }
    to_be_submitted = True
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        _task_params['task_id'] = int(sys.argv[1])
        argv = _task_get_options(_task_params['task_id'], _task_params['task_name'])
        to_be_submitted = False
    else:
        argv = sys.argv

    if type(argv) is dict:
        # FIXME: REMOVE AFTER MAJOR RELEASE 1.0
        # This is needed for old task submitted before CLI parameters
        # where stored in DB and _options dictionary was stored instead.
        _options = argv
    else:
        _task_build_params(_task_params['task_name'], argv, description,
            help_specific_usage, version, specific_params,
            task_submit_elaborate_specific_parameter_fnc,
            task_submit_check_options_fnc)

    write_message('argv=%s' % (argv, ), verbose=9)
    write_message('_options=%s' % (_options, ), verbose=9)
    write_message('_task_params=%s' % (_task_params, ), verbose=9)

    if to_be_submitted:
        _task_submit(argv, authorization_action, authorization_msg)
    else:
        try:
            if not _task_run(task_run_fnc):
                write_message("Error occurred.  Exiting.", sys.stderr)
        except Exception, e:
            write_message("Unexpected error occurred: %s." % e, sys.stderr)
            write_message("Traceback is:", sys.stderr)
            traceback.print_tb(sys.exc_info()[2])
            write_message("Exiting.", sys.stderr)
            task_update_status("ERROR")

def _task_build_params(
    task_name,
    argv,
    description="",
    help_specific_usage="",
    version=__revision__,
    specific_params=("", []),
    task_submit_elaborate_specific_parameter_fnc=None,
    task_submit_check_options_fnc=None):
    """ Build the BibTask params.
    @param argv a list of string as in sys.argv
    @param description is the generic description printed in the usage page;
    @param help_specific_usage is the specific parameter help
    @param task_submit_elaborate_specific_parameter_fnc will be called passing
    a key and a value, for parsing specific cli parameters. Must return True if
    it has recognized the parameter. Must eventually update the options with
    bibtask_set_option;
    @param task_submit_check_options must check the validity of options (via
    bibtask_get_option) once all the options where parsed;
    """
    global _task_params, _options
    _options = {}

    if task_name in CFG_BIBTASK_DEFAULT_TASK_SETTINGS:
        _options.update(CFG_BIBTASK_DEFAULT_TASK_SETTINGS[task_name])

    # set user-defined options:
    try:
        (short_params, long_params) = specific_params
        opts, args = getopt.gnu_getopt(argv[1:], "hVv:u:s:t:P:N:L:" +
            short_params, [
                "help",
                "version",
                "verbose=",
                "user=",
                "sleep=",
                "time=",
                "priority=",
                "task-specific-name=",
                "runtime-limit="
            ] + long_params)
    except getopt.GetoptError, err:
        _usage(1, err, help_specific_usage=help_specific_usage, description=description)
    try:
        for opt in opts:
            if opt[0] in ("-h", "--help"):
                _usage(0, help_specific_usage=help_specific_usage, description=description)
            elif opt[0] in ("-V", "--version"):
                print _task_params["version"]
                sys.exit(0)
            elif opt[0] in ("-u", "--user"):
                _task_params["user"] = opt[1]
            elif opt[0] in ("-v", "--verbose"):
                _task_params["verbose"] = int(opt[1])
            elif opt[0] in ("-s", "--sleeptime"):
                if task_name not in CFG_TASK_IS_NOT_A_DEAMON:
                    get_datetime(opt[1]) # see if it is a valid shift
                    _task_params["sleeptime"] = opt[1]
            elif opt[0] in ("-t", "--runtime"):
                _task_params["runtime"] = get_datetime(opt[1])
            elif opt[0] in ("-P", "--priority"):
                _task_params["priority"] = int(opt[1])
            elif opt[0] in ("-N", "--task-specific-name"):
                _task_params["task_specific_name"] = opt[1]
            elif opt[0] in ("-L", "--runtime-limit"):
                _task_params["runtime_limit"] = parse_runtime_limit(opt[1])
            elif not callable(task_submit_elaborate_specific_parameter_fnc) or \
                not task_submit_elaborate_specific_parameter_fnc(opt[0],
                    opt[1], opts, args):
                _usage(1, help_specific_usage=help_specific_usage, description=description)
    except StandardError, e:
        _usage(e, help_specific_usage=help_specific_usage, description=description)
    if callable(task_submit_check_options_fnc):
        if not task_submit_check_options_fnc():
            _usage(1, help_specific_usage=help_specific_usage, description=description)

def task_set_option(key, value):
    """Set an value to key in the option dictionary of the task"""
    global _options
    try:
        _options[key] = value
    except NameError:
        _options = {key : value}

def task_get_option(key, default=None):
    """Returns the value corresponding to key in the option dictionary of the task"""
    try:
        return _options.get(key, default)
    except NameError:
        return default

def task_has_option(key):
    """Map the has_key query to _options"""
    try:
        return _options.has_key(key)
    except NameError:
        return False

def task_get_task_param(key, default=None):
    """Returns the value corresponding to the particular task param"""
    try:
        return _task_params.get(key, default)
    except NameError:
        return default

def task_set_task_param(key, value):
    """Set the value corresponding to the particular task param"""
    global _task_params
    try:
        _task_params[key] = value
    except NameError:
        _task_params = {key : value}

def task_update_progress(msg):
    """Updates progress information in the BibSched task table."""
    write_message("Updating task progress to %s." % msg, verbose=9)
    return run_sql("UPDATE schTASK SET progress=%s where id=%s",
        (msg, _task_params["task_id"]))

def task_update_status(val):
    """Updates status information in the BibSched task table."""
    write_message("Updating task status to %s." % val, verbose=9)
    return run_sql("UPDATE schTASK SET status=%s where id=%s",
        (val, _task_params["task_id"]))

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
    if msg and _task_params['verbose'] >= verbose:
        if stream == sys.stdout:
            print "%s --> %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), msg)
            logging.info(msg)
        elif stream == sys.stderr:
            print >> sys.stderr, "%s --> %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), msg)
            logging.error(msg)
        else:
            sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)

_RE_SHIFT = re.compile("([-\+]{0,1})([\d]+)([dhms])")
def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    date = time.time()
    factors = {"d":24*3600, "h":3600, "m":60, "s":1}
    m = _RE_SHIFT.match(var)
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

_RE_RUNTIMELIMIT_FULL = re.compile(r"(?P<weekday>\w+)(\s+(?P<begin>\d\d?(:\d\d?)?)(-(?P<end>\d\d?(:\d\d?)?))?)?")
_RE_RUNTIMELIMIT_HOUR = re.compile(r'(?P<hour>\d\d?):(?P<minutes>\d\d?)')
def parse_runtime_limit(value):
    """
    Parsing CLI option for runtime limit, supplied as VALUE.
    Value could be something like: Sunday 23:00-05:00, the format being
    Wee[kday][ hh[:mm][-hh:[mm]]].
    The function would return the first range datetime in which now() is
    contained.
    """
    def extract_time(value):
        value = _RE_RUNTIMELIMIT_HOUR.search(value).groupdict()
        hour = int(value['hour']) % 24
        minutes = (value['minutes'] is not None and int(value['minutes']) or 0) % 60
        return hour * 3600 + minutes * 60

    today = datetime.datetime.today()
    try:
        g = _RE_RUNTIMELIMIT_FULL.search(value)
        if not g:
            raise ValueError
        pieces = g.groupdict()
        weekday = {
            'mon' : 0,
            'tue' : 1,
            'wed' : 2,
            'thu' : 3,
            'fri' : 4,
            'sat' : 5,
            'sun' : 6,
        }[pieces['weekday'][:3].lower()]
        today_weekday = today.isoweekday() - 1
        first_occasion_day = -((today_weekday - weekday) % 7) * 24 * 3600
        next_occasion_day = first_occasion_day + 7 * 24 * 3600
        if pieces['begin'] is None:
            pieces['begin'] = '00:00'
        if pieces['end'] is None:
            pieces['end'] = '00:00'
        beginning_time = extract_time(pieces['begin'])
        ending_time = extract_time(pieces['end'])
        if beginning_time >= ending_time:
            ending_time += 24 * 3600
        reference_time = time.mktime(datetime.datetime(today.year, today.month, today.day).timetuple())
        first_range = (
            reference_time + first_occasion_day + beginning_time,
            reference_time + first_occasion_day + ending_time
        )
        second_range = (
            reference_time + next_occasion_day + beginning_time,
            reference_time + next_occasion_day + ending_time
        )
        return first_range, second_range
    except:
        raise ValueError, '"%s" does not seem to be correct format for parse_runtime_limit() (Wee[kday][ hh[:mm][-hh:[mm]]]).' % value

def task_sleep_now_if_required(can_stop_too=False):
    """This function should be called during safe state of BibTask,
    e.g. after flushing caches or outside of run_sql calls.
    """
    write_message('Entering task_sleep_now_if_required with signal_request=%s' % _task_params['signal_request'], verbose=9)
    if _task_params['signal_request'] == 'sleep':
        _task_params['signal_request'] = None
        write_message("sleeping...")
        task_update_status("SLEEPING")
        signal.pause() # wait for wake-up signal
    elif _task_params['signal_request'] == 'ctrlz':
        _task_params['signal_request'] = None
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)
        write_message("sleeping...")
        task_update_status("SLEEPING")
        os.kill(os.getpid(), signal.SIGTSTP)
        time.sleep(1)
    elif _task_params['signal_request'] == 'ctrlc' and can_stop_too:
        _task_params['signal_request'] = None
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        write_message("stopped")
        task_update_status("STOPPED")
        os.kill(os.getpid(), signal.SIGINT)
        time.sleep(1)
    elif _task_params['signal_request'] == 'stop' and can_stop_too:
        _task_params['signal_request'] = None
        write_message("stopped")
        task_update_status("STOPPED")
        sys.exit(0)

def authenticate(user, authorization_action, authorization_msg=""):
    """Authenticate the user against the user database.
    Check for its password, if it exists.
    Check for authorization_action access rights.
    Return user name upon authorization success,
    do system exit upon authorization failure.
    """
    # With SSO it's impossible to check for pwd
    if CFG_EXTERNAL_AUTH_USING_SSO or os.path.basename(sys.argv[0]) in CFG_VALID_PROCESSES_NO_AUTH_NEEDED:
        return user
    if authorization_msg:
        print authorization_msg
        print "=" * len(authorization_msg)
    if user == "":
        print >> sys.stdout, "\rUsername: ",
        try:
            user = sys.stdin.readline().lower().strip()
        except EOFError:
            sys.stderr.write("\n")
            sys.exit(1)
        except KeyboardInterrupt:
            sys.stderr.write("\n")
            sys.exit(1)
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
            try:
                password_entered = getpass.getpass()
            except EOFError:
                sys.stderr.write("\n")
                sys.exit(1)
            except KeyboardInterrupt:
                sys.stderr.write("\n")
                sys.exit(1)
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

def _task_submit(argv, authorization_action, authorization_msg):
    """Submits task to the BibSched task queue.  This is what people will
        be invoking via command line."""

    ## check as whom we want to submit?
    check_running_process_user()

    ## sanity check: remove eventual "task" option:

    ## authenticate user:
    _task_params['user'] = authenticate(_task_params["user"], authorization_action, authorization_msg)

    ## submit task:
    if _task_params['task_specific_name']:
        task_name = '%s:%s' % (_task_params['task_name'], _task_params['task_specific_name'])
    else:
        task_name = _task_params['task_name']
    write_message("storing task options %s\n" % argv, verbose=9)
    _task_params['task_id'] = run_sql("""INSERT INTO schTASK (proc,user,
                                           runtime,sleeptime,status,progress,arguments,priority)
                                         VALUES (%s,%s,%s,%s,'WAITING','',%s, %s)""",
        (task_name, _task_params['user'], _task_params["runtime"],
         _task_params["sleeptime"], marshal.dumps(argv), _task_params['priority']))

    ## update task number:
    write_message("Task #%d submitted." % _task_params['task_id'])
    return _task_params['task_id']


def _task_get_options(task_id, task_name):
    """Returns options for the task 'id' read from the BibSched task
    queue table."""
    out = {}
    res = run_sql("SELECT arguments FROM schTASK WHERE id=%s AND proc LIKE %s",
        (task_id, task_name+'%'))
    try:
        out = marshal.loads(res[0][0])
    except:
        write_message("Error: %s task %d does not seem to exist." \
            % (task_name, task_id), sys.stderr)
        task_update_status('ERROR')
        sys.exit(1)
    write_message('Options retrieved: %s' % (out, ), verbose=9)
    return out

def _task_run(task_run_fnc):
    """Runs the task by fetching arguments from the BibSched task queue.
    This is what BibSched will be invoking via daemon call.
    The task prints Fibonacci numbers for up to NUM on the stdout, and some
    messages on stderr.
    @param task_run_fnc will be called as the main core function. Must return
    False in case of errors.
    Return True in case of success and False in case of failure."""

    ## We prepare the pid file inside /prefix/var/run/taskname_id.pid
    check_running_process_user()
    try:
        pidfile_name = os.path.join(CFG_PREFIX, 'var', 'run',
            'bibsched_task_%d.pid' % _task_params['task_id'])
        pidfile = open(pidfile_name, 'w')
        pidfile.write(str(os.getpid()))
        pidfile.close()
    except OSError:
        register_exception(alert_admin=True)
        task_update_status("ERROR")
        return False

    ## Setting up the logging system
    logger = logging.getLogger()
    stderr_logger = logging.handlers.RotatingFileHandler(os.path.join(CFG_LOGDIR, 'bibsched_task_%d.err' % _task_params['task_id']), 'a', 1*1024*1024, 10)
    stdout_logger = logging.handlers.RotatingFileHandler(os.path.join(CFG_LOGDIR, 'bibsched_task_%d.log' % _task_params['task_id']), 'a', 1*1024*1024, 10)
    formatter = logging.Formatter('%(asctime)s --> %(message)s', '%Y-%m-%d %H:%M:%S')
    stderr_logger.setFormatter(formatter)
    stdout_logger.setFormatter(formatter)
    logger.addHandler(stderr_logger)
    logger.addHandler(stdout_logger)
    logger.setLevel(logging.INFO)

    ## check task status:
    task_status = task_read_status()
    if task_status not in ("WAITING", "SCHEDULED"):
        write_message("Error: The task #%d is %s.  I expected WAITING or SCHEDULED." %
            (_task_params['task_id'], task_status), sys.stderr)
        return False

    if _task_params['runtime_limit'] is not None:
        if not _task_params['runtime_limit'][0][0] <= time.time() <= _task_params['runtime_limit'][0][1]:
            new_runtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(_task_params['runtime_limit'][1][0]))
            progress = run_sql("SELECT progress FROM schTASK WHERE id=%s", (_task_params['task_id'], ))
            if progress:
                progress = progress[0][0]
            else:
                progress = ''
            g =  re.match(r'Postponed \d+ time\(s\)', progress)
            if g:
                postponed_times = int(g.group(1))
            else:
                postponed_times = 0
            run_sql("UPDATE schTASK SET runtime=%s, status='WAITING', progress=%s WHERE id=%s", (new_runtime, 'Postponed %d time(s)' % (postponed_times + 1), _task_params['task_id']))
            write_message("Task #%d postponed because outside of runtime limit" % _task_params['task_id'])
            return True

    ## initialize signal handler:
    _task_params['signal_request'] = None
    signal.signal(signal.SIGUSR1, _task_sig_sleep)
    signal.signal(signal.SIGUSR2, signal.SIG_IGN)
    signal.signal(signal.SIGTSTP, _task_sig_ctrlz)
    signal.signal(signal.SIGTERM, _task_sig_stop)
    signal.signal(signal.SIGQUIT, _task_sig_stop)
    signal.signal(signal.SIGABRT, _task_sig_suicide)
    signal.signal(signal.SIGCONT, _task_sig_wakeup)
    signal.signal(signal.SIGINT, _task_sig_ctrlc)
    ## we can run the task now:
    write_message("Task #%d started." % _task_params['task_id'])
    task_update_status("RUNNING")
    ## run the task:
    _task_params['task_starting_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    sleeptime = _task_params['sleeptime']
    try:
        try:
            if callable(task_run_fnc) and task_run_fnc():
                task_update_status("DONE")
            else:
                task_update_status("DONE WITH ERRORS")
        except SystemExit:
            pass
        except:
            register_exception(alert_admin=True)
            task_update_status("ERROR")
    finally:
        task_status = task_read_status()
        if sleeptime:
            new_runtime = get_datetime(sleeptime)
            ## The task is a daemon. We resubmit it
            if task_status == 'DONE':
                ## It has finished in a good way. We recycle the database row
                run_sql("UPDATE schTASK SET runtime=%s, status='WAITING', progress='' WHERE id=%s", (new_runtime, _task_params['task_id']))
                write_message("Task #%d finished and resubmitted." % _task_params['task_id'])
            else:
                ## We keep the bad result and we resubmit with another id.
                #res = run_sql('SELECT proc,user,sleeptime,arguments,priority FROM schTASK WHERE id=%s', (_task_params['task_id'], ))
                #proc, user, sleeptime, arguments, priority = res[0]
                #run_sql("""INSERT INTO schTASK (proc,user,
                            #runtime,sleeptime,status,arguments,priority)
                            #VALUES (%s,%s,%s,%s,'WAITING',%s, %s)""",
                            #(proc, user, new_runtime, sleeptime, arguments, priority))
                write_message("Task #%d finished but not resubmitted. [%s]" % (_task_params['task_id'], task_status))

        else:
            ## we are done:
            write_message("Task #%d finished. [%s]" % (_task_params['task_id'], task_status))
        ## Removing the pid
        os.remove(pidfile_name)
        try:
            # Let's signal bibsched that we have finished.
            from invenio.bibsched import pidfile
            os.kill(int(open(pidfile).read()), signal.SIGUSR2)
        except:
            pass
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
    sys.stderr.write("  -u, --user=USER\tUser name to submit the"
        " task as, password needed.\n")
    sys.stderr.write("  -t, --runtime=TIME\tTime to execute the"
        " task (now), e.g. +15s, 5m, 3h, 2002-10-27 13:57:26\n")
    sys.stderr.write("  -s, --sleeptime=SLEEP\tSleeping frequency after"
        " which to repeat task (no), e.g.: 30m, 2h, 1d\n")
    sys.stderr.write("  -L  --runtime-limit=LIMIT\tTime limit when it is"
        " allowed to execute the task, e.g. Sunday 01:00-05:00\n"
        "\t\t\t\twith the syntax Wee[kday][ hh[:mm][-hh:[mm]]]\n")
    sys.stderr.write("  -P, --priority=PRIORITY\tPriority level (an integer, 0 is default)\n")
    sys.stderr.write("  -N, --task-specific-name=TASK_SPECIFIC_NAME\tAdvanced option\n")
    sys.stderr.write("General options:\n")
    sys.stderr.write("  -h, --help\t\tPrint this help.\n")
    sys.stderr.write("  -V, --version\t\tPrint version information.\n")
    sys.stderr.write("  -v, --verbose=LEVEL\tVerbose level (0=min,"
        " 1=default, 9=max).\n")
    if description:
        sys.stderr.write(description)
    sys.exit(exitcode)

def _task_sig_sleep(sig, frame):
    """Signal handler for the 'sleep' signal sent by BibSched."""
    write_message("task_sig_sleep(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("sleeping as soon as possible...")
    _task_params['signal_request'] = 'sleep'
    _db_login(1)
    task_update_status("ABOUT TO SLEEP")

def _task_sig_ctrlz(sig, frame):
    """Signal handler for the 'ctrlz' signal sent by BibSched."""
    write_message("task_sig_ctrlz(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("sleeping as soon as possible...")
    _task_params['signal_request'] = 'ctrlz'
    _db_login(1)
    task_update_status("ABOUT TO STOP")

def _task_sig_wakeup(sig, frame):
    """Signal handler for the 'wakeup' signal sent by BibSched."""
    signal.signal(signal.SIGTSTP, _task_sig_ctrlz)
    write_message("task_sig_wakeup(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("continuing...")
    _task_params['signal_request'] = None
    _db_login(1)
    task_update_status("CONTINUING")

def _task_sig_ctrlc(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    write_message("task_sig_ctrlc(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("stopping as soon as possible...")
    _db_login(1) # To avoid concurrency with an interrupted run_sql call
    task_update_status("STOPPING")
    _task_params['signal_request'] = 'ctrlc'

def _task_sig_stop(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    write_message("task_sig_stop(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("stopping as soon as possible...")
    _db_login(1) # To avoid concurrency with an interrupted run_sql call
    task_update_status("STOPPING")
    _task_params['signal_request'] = 'stop'

def _task_sig_suicide(sig, frame):
    """Signal handler for the 'suicide' signal sent by BibSched."""
    write_message("task_sig_suicide(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("suiciding myself now...")
    task_update_status("SUICIDING")
    write_message("suicided")
    _db_login(1)
    task_update_status("SUICIDED")
    sys.exit(0)

def _task_sig_unknown(sig, frame):
    """Signal handler for the other unknown signals sent by shell or user."""
    # do nothing for unknown signals:
    write_message("unknown signal %d (frame %s) ignored" % (sig, frame))

_RE_PSLINE = re.compile('^\s*(.+?)\s+(.+?)\s*$')
def guess_apache_process_user_from_ps():
    """Guess Apache process user by parsing the list of running processes."""
    apache_users = []
    try:
        # Tested on Linux, Sun and MacOS X
        for line in os.popen('ps -A -o user,comm').readlines():
            g = _RE_PSLINE.match(line)
            if g:
                username = g.group(2)
                process = os.path.basename(g.group(1))
                if process in ('apache', 'apache2', 'httpd') :
                    if username not in apache_users and username != 'root':
                        apache_users.append(username)
    except Exception, e:
        print >> sys.stderr, "WARNING: %s" % e
    return tuple(apache_users)

def guess_apache_process_user():
    """
    Return the possible name of the user running the Apache server process.
    (Look at running OS processes or look at OS users defined in /etc/passwd.)
    """
    apache_users = guess_apache_process_user_from_ps() + ('apache2', 'apache', 'www-data')
    for username in apache_users:
        try:
            userline = pwd.getpwnam(username)
            return userline[0]
        except KeyError:
            pass
    print >> sys.stderr, "ERROR: Cannot detect Apache server process user. Please set the correct value in CFG_BIBSCHED_PROCESS_USER."
    sys.exit(1)

def check_running_process_user():
    """
    Check that the user running this program is the same as the user
    configured in CFG_BIBSCHED_PROCESS_USER or as the user running the
    Apache webserver process.
    """
    running_as_user = pwd.getpwuid(os.getuid())[0]
    if CFG_BIBSCHED_PROCESS_USER and running_as_user != CFG_BIBSCHED_PROCESS_USER:
        print >> sys.stderr, """ERROR: You must run "%(x_proc)s" as the user set up in your
       CFG_BIBSCHED_PROCESS_USER (seems to be "%(x_user)s").

       You may want to do "sudo -u %(x_user)s %(x_proc)s ..." to do so.

       If you think this is not right, please set CFG_BIBSCHED_PROCESS_USER
       appropriately and rerun "inveniocfg --update-config-py".""" % \
        {'x_proc': os.path.basename(sys.argv[0]), 'x_user': CFG_BIBSCHED_PROCESS_USER}
        sys.exit(1)
    elif running_as_user != guess_apache_process_user():
        print >> sys.stderr, """ERROR: You must run "%(x_proc)s" as the same user that runs your Apache server
       process (seems to be "%(x_user)s").

       You may want to do "sudo -u %(x_user)s %(x_proc)s ..." to do so.

       If you think this is not right, please set CFG_BIBSCHED_PROCESS_USER
       appropriately and rerun "inveniocfg --update-config-py".""" % \
        {'x_proc': os.path.basename(sys.argv[0]), 'x_user': guess_apache_process_user()}
        sys.exit(1)
    return

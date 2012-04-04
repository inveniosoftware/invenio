# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

"""Invenio Bibliographic Task Class.

BibTask class.

A BibTask is an executable under CFG_BINDIR, whose name is stored in
bibtask_config.CFG_BIBTASK_VALID_TASKS.
A valid task must call the task_init function with the proper parameters.
Generic task related parameters (user, sleeptime, runtime, task_id, task_name
verbose)
go to _TASK_PARAMS global dictionary accessible through task_get_task_param.
Option specific to the particular BibTask go to _OPTIONS global dictionary
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
import traceback
import logging
import logging.handlers
import random

from invenio.dbquery import run_sql, _db_login
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_PREFIX, CFG_BINDIR, CFG_LOGDIR, \
    CFG_BIBSCHED_PROCESS_USER, CFG_TMPDIR
from invenio.errorlib import register_exception

from invenio.access_control_config import CFG_EXTERNAL_AUTH_USING_SSO, \
    CFG_EXTERNAL_AUTHENTICATION
from invenio.webuser import get_user_preferences, get_email
from invenio.bibtask_config import CFG_BIBTASK_VALID_TASKS, \
    CFG_BIBTASK_DEFAULT_TASK_SETTINGS, CFG_BIBTASK_FIXEDTIMETASKS
from invenio.dateutils import parse_runtime_limit
from invenio.shellutils import escape_shell_arg

# Global _TASK_PARAMS dictionary.
_TASK_PARAMS = {
        'version': '',
        'task_stop_helper_fnc': None,
        'task_name': os.path.basename(sys.argv[0]),
        'task_specific_name': '',
        'task_id': 0,
        'user': '',
        # If the task is not initialized (usually a developer debugging
        # a single method), output all messages.
        'verbose': 9,
        'sleeptime': '',
        'runtime': time.strftime("%Y-%m-%d %H:%M:%S"),
        'priority': 0,
        'runtime_limit': None,
        'profile': [],
        'post-process': [],
        'sequence-id':None,
        'stop_queue_on_error': False,
        'fixed_time': False,
        }

# Global _OPTIONS dictionary.
_OPTIONS = {}

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
                argv[count] = os.path.abspath(path)
    return argv

def task_low_level_submission(name, user, *argv):
    """Let special lowlevel enqueuing of a task on the bibsche queue.
    @param name: is the name of the bibtask. It must be a valid executable under
        C{CFG_BINDIR}.
    @type name: string
    @param user: is a string that will appear as the "user" submitting the task.
        Since task are submitted via API it make sense to set the
        user to the name of the module/function that called
        task_low_level_submission.
    @type user: string
    @param argv: are all the additional CLI parameters that would have been
        passed on the CLI (one parameter per variable).
        e.g.:
        >>> task_low_level_submission('bibupload', 'admin', '-a', '/tmp/z.xml')
    @type: strings
    @return: the task identifier when the task is correctly enqueued.
    @rtype: int
    @note: use absolute paths in argv
    """
    def get_priority(argv):
        """Try to get the priority by analysing the arguments."""
        priority = 0
        argv = list(argv)
        while True:
            try:
                opts, args = getopt.gnu_getopt(argv, 'P:', ['priority='])
            except getopt.GetoptError, err:
                ## We remove one by one all the non recognized parameters
                if len(err.opt) > 1:
                    argv = [arg for arg in argv if arg != '--%s' % err.opt and not arg.startswith('--%s=' % err.opt)]
                else:
                    argv = [arg for arg in argv if not arg.startswith('-%s' % err.opt)]
            else:
                break
        for opt in opts:
            if opt[0] in ('-P', '--priority'):
                try:
                    priority = int(opt[1])
                except ValueError:
                    pass
        return priority

    def get_special_name(argv):
        """Try to get the special name by analysing the arguments."""
        special_name = ''
        argv = list(argv)
        while True:
            try:
                opts, args = getopt.gnu_getopt(argv, 'N:', ['name='])
            except getopt.GetoptError, err:
                ## We remove one by one all the non recognized parameters
                if len(err.opt) > 1:
                    argv = [arg for arg in argv if arg != '--%s' % err.opt and not arg.startswith('--%s=' % err.opt)]
                else:
                    argv = [arg for arg in argv if not arg.startswith('-%s' % err.opt)]
            else:
                break
        for opt in opts:
            if opt[0] in ('-N', '--name'):
                special_name = opt[1]
        return special_name

    def get_runtime(argv):
        """Try to get the runtime by analysing the arguments."""
        runtime = time.strftime("%Y-%m-%d %H:%M:%S")
        argv = list(argv)
        while True:
            try:
                opts, args = getopt.gnu_getopt(argv, 't:', ['runtime='])
            except getopt.GetoptError, err:
                ## We remove one by one all the non recognized parameters
                if len(err.opt) > 1:
                    argv = [arg for arg in argv if arg != '--%s' % err.opt and not arg.startswith('--%s=' % err.opt)]
                else:
                    argv = [arg for arg in argv if not arg.startswith('-%s' % err.opt)]
            else:
                break
        for opt in opts:
            if opt[0] in ('-t', '--runtime'):
                try:
                    runtime = get_datetime(opt[1])
                except ValueError:
                    pass
        return runtime

    def get_sleeptime(argv):
        """Try to get the runtime by analysing the arguments."""
        sleeptime = ""
        argv = list(argv)
        while True:
            try:
                opts, args = getopt.gnu_getopt(argv, 's:', ['sleeptime='])
            except getopt.GetoptError, err:
                ## We remove one by one all the non recognized parameters
                if len(err.opt) > 1:
                    argv = [arg for arg in argv if arg != '--%s' % err.opt and not arg.startswith('--%s=' % err.opt)]
                else:
                    argv = [arg for arg in argv if not arg.startswith('-%s' % err.opt)]
            else:
                break
        for opt in opts:
            if opt[0] in ('-s', '--sleeptime'):
                try:
                    sleeptime = opt[1]
                except ValueError:
                    pass
        return sleeptime

    task_id = None
    try:
        if not name in CFG_BIBTASK_VALID_TASKS:
            raise StandardError('%s is not a valid task name' % name)

        new_argv = []
        for arg in argv:
            if isinstance(arg, unicode):
                arg = arg.encode('utf8')
            new_argv.append(arg)
        argv = new_argv
        priority = get_priority(argv)
        special_name = get_special_name(argv)
        runtime = get_runtime(argv)
        sleeptime = get_sleeptime(argv)
        argv = tuple([os.path.join(CFG_BINDIR, name)] + list(argv))

        if special_name:
            name = '%s:%s' % (name, special_name)

        verbose_argv = 'Will execute: %s' % ' '.join([escape_shell_arg(str(arg)) for arg in argv])

        ## submit task:
        task_id = run_sql("""INSERT INTO schTASK (proc,user,
            runtime,sleeptime,status,progress,arguments,priority)
            VALUES (%s,%s,%s,%s,'WAITING',%s,%s,%s)""",
            (name, user, runtime, sleeptime, verbose_argv, marshal.dumps(argv), priority))

    except Exception:
        register_exception(alert_admin=True)
        if task_id:
            run_sql("""DELETE FROM schTASK WHERE id=%s""", (task_id, ))
        raise
    return task_id


def bibtask_allocate_sequenceid(curdir=None):
    """
    Returns an almost unique number to be used a task sequence ID.

    In WebSubmit functions, set C{curdir} to the curdir (!) to read
    the shared sequence ID for all functions of this submission (reading
    "access number").

    @param curdir: in WebSubmit functions (ONLY) the value retrieved
                   from the curdir parameter of the function
    @return: an integer for the sequence ID. 0 is returned if the
             sequence ID could not be allocated
    @rtype: int
    """
    if curdir:
        try:
            fd = file(os.path.join(curdir, 'access'), "r")
            access = fd.readline().strip()
            fd.close()
            return access.replace("_", "")[-9:]
        except:
            return 0
    else:
        return random.randrange(1, 4294967296)


def setup_loggers(task_id=None):
    """Sets up the logging system."""
    logger = logging.getLogger()
    for handler in logger.handlers:
        ## Let's clean the handlers in case some piece of code has already
        ## fired any write_message, i.e. any call to debug, info, etc.
        ## which triggered a call to logging.basicConfig()
        logger.removeHandler(handler)
    formatter = logging.Formatter('%(asctime)s --> %(message)s', '%Y-%m-%d %H:%M:%S')
    if task_id is not None:
        err_logger = logging.handlers.RotatingFileHandler(os.path.join(CFG_LOGDIR, 'bibsched_task_%d.err' % _TASK_PARAMS['task_id']), 'a', 1*1024*1024, 10)
        log_logger = logging.handlers.RotatingFileHandler(os.path.join(CFG_LOGDIR, 'bibsched_task_%d.log' % _TASK_PARAMS['task_id']), 'a', 1*1024*1024, 10)
        log_logger.setFormatter(formatter)
        log_logger.setLevel(logging.DEBUG)
        err_logger.setFormatter(formatter)
        err_logger.setLevel(logging.WARNING)
        logger.addHandler(err_logger)
        logger.addHandler(log_logger)
    stdout_logger = logging.StreamHandler(sys.stdout)
    stdout_logger.setFormatter(formatter)
    stdout_logger.setLevel(logging.DEBUG)
    stderr_logger = logging.StreamHandler(sys.stderr)
    stderr_logger.setFormatter(formatter)
    stderr_logger.setLevel(logging.WARNING)
    logger.addHandler(stderr_logger)
    logger.addHandler(stdout_logger)
    logger.setLevel(logging.INFO)
    return logger


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
    @param authorization_action: is the name of the authorization action
    connected with this task;
    @param authorization_msg: is the header printed when asking for an
    authorization password;
    @param description: is the generic description printed in the usage page;
    @param help_specific_usage: is the specific parameter help
    @param task_stop_fnc: is a function that will be called
    whenever the task is stopped
    @param task_submit_elaborate_specific_parameter_fnc: will be called passing
    a key and a value, for parsing specific cli parameters. Must return True if
    it has recognized the parameter. Must eventually update the options with
    bibtask_set_option;
    @param task_submit_check_options: must check the validity of options (via
    bibtask_get_option) once all the options where parsed;
    @param task_run_fnc: will be called as the main core function. Must return
    False in case of errors.
    """
    global _TASK_PARAMS, _OPTIONS
    _TASK_PARAMS = {
        "version" : version,
        "task_stop_helper_fnc" : task_stop_helper_fnc,
        "task_name" : os.path.basename(sys.argv[0]),
        "task_specific_name" : '',
        "user" : '',
        "verbose" : 1,
        "sleeptime" : '',
        "runtime" : time.strftime("%Y-%m-%d %H:%M:%S"),
        "priority" : 0,
        "runtime_limit" : None,
        "profile" : [],
        "post-process": [],
        "sequence-id": None,
        "stop_queue_on_error": False,
        "fixed_time": False,
    }
    to_be_submitted = True
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        _TASK_PARAMS['task_id'] = int(sys.argv[1])
        argv = _task_get_options(_TASK_PARAMS['task_id'], _TASK_PARAMS['task_name'])
        to_be_submitted = False
    else:
        argv = sys.argv

    setup_loggers(_TASK_PARAMS.get('task_id'))

    task_name = os.path.basename(sys.argv[0])
    if task_name not in CFG_BIBTASK_VALID_TASKS or os.path.realpath(os.path.join(CFG_BINDIR, task_name)) != os.path.realpath(sys.argv[0]):
        raise OSError("%s is not in the allowed modules" % sys.argv[0])

    if type(argv) is dict:
        # FIXME: REMOVE AFTER MAJOR RELEASE 1.0
        # This is needed for old task submitted before CLI parameters
        # where stored in DB and _OPTIONS dictionary was stored instead.
        _OPTIONS = argv
    else:
        try:
            _task_build_params(_TASK_PARAMS['task_name'], argv, description,
                help_specific_usage, version, specific_params,
                task_submit_elaborate_specific_parameter_fnc,
                task_submit_check_options_fnc)
        except (SystemExit, Exception), err:
            if not to_be_submitted:
                register_exception(alert_admin=True)
                write_message("Error in parsing the parameters: %s." % err, sys.stderr)
                write_message("Exiting.", sys.stderr)
                task_update_status("ERROR")
            raise

    write_message('argv=%s' % (argv, ), verbose=9)
    write_message('_OPTIONS=%s' % (_OPTIONS, ), verbose=9)
    write_message('_TASK_PARAMS=%s' % (_TASK_PARAMS, ), verbose=9)

    if to_be_submitted:
        _task_submit(argv, authorization_action, authorization_msg)
    else:
        try:
            if task_get_task_param('profile'):
                try:
                    from cStringIO import StringIO
                    import pstats
                    filename = os.path.join(CFG_TMPDIR, 'bibsched_task_%s.pyprof' % _TASK_PARAMS['task_id'])
                    existing_sorts = pstats.Stats.sort_arg_dict_default.keys()
                    required_sorts = []
                    profile_dump = []
                    for sort in task_get_task_param('profile'):
                        if sort not in existing_sorts:
                            sort = 'cumulative'
                        if sort not in required_sorts:
                            required_sorts.append(sort)
                    if sys.hexversion < 0x02050000:
                        import hotshot
                        import hotshot.stats
                        pr = hotshot.Profile(filename)
                        ret = pr.runcall(_task_run, task_run_fnc)
                        for sort_type in required_sorts:
                            tmp_out = sys.stdout
                            sys.stdout = StringIO()
                            hotshot.stats.load(filename).strip_dirs().sort_stats(sort_type).print_stats()
                            # pylint: disable=E1103
                            # This is a hack. sys.stdout is a StringIO in this case.
                            profile_dump.append(sys.stdout.getvalue())
                            # pylint: enable=E1103
                            sys.stdout = tmp_out
                    else:
                        import cProfile
                        pr = cProfile.Profile()
                        ret = pr.runcall(_task_run, task_run_fnc)
                        pr.dump_stats(filename)
                        for sort_type in required_sorts:
                            strstream = StringIO()
                            pstats.Stats(filename, stream=strstream).strip_dirs().sort_stats(sort_type).print_stats()
                            profile_dump.append(strstream.getvalue())
                    profile_dump = '\n'.join(profile_dump)
                    profile_dump += '\nYou can use profile=%s' % existing_sorts
                    open(os.path.join(CFG_LOGDIR, 'bibsched_task_%d.log' % _TASK_PARAMS['task_id']), 'a').write("%s" % profile_dump)
                    os.remove(filename)
                except ImportError:
                    ret = _task_run(task_run_fnc)
                    write_message("ERROR: The Python Profiler is not installed!", stream=sys.stderr)
            else:
                ret = _task_run(task_run_fnc)
            if not ret:
                write_message("Error occurred.  Exiting.", sys.stderr)
        except Exception, e:
            register_exception(alert_admin=True)
            write_message("Unexpected error occurred: %s." % e, sys.stderr)
            write_message("Traceback is:", sys.stderr)
            write_messages(''.join(traceback.format_tb(sys.exc_info()[2])), sys.stderr)
            write_message("Exiting.", sys.stderr)
            task_update_status("ERROR")
        logging.shutdown()

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
    @param argv: a list of string as in sys.argv
    @param description: is the generic description printed in the usage page;
    @param help_specific_usage: is the specific parameter help
    @param task_submit_elaborate_specific_parameter_fnc: will be called passing
    a key and a value, for parsing specific cli parameters. Must return True if
    it has recognized the parameter. Must eventually update the options with
    bibtask_set_option;
    @param task_submit_check_options: must check the validity of options (via
    bibtask_get_option) once all the options where parsed;
    """
    global _OPTIONS
    _OPTIONS = {}

    if task_name in CFG_BIBTASK_DEFAULT_TASK_SETTINGS:
        _OPTIONS.update(CFG_BIBTASK_DEFAULT_TASK_SETTINGS[task_name])

    # set user-defined options:
    try:
        (short_params, long_params) = specific_params
        opts, args = getopt.gnu_getopt(argv[1:], "hVv:u:s:t:P:N:L:I:" +
            short_params, [
                "help",
                "version",
                "verbose=",
                "user=",
                "sleep=",
                "runtime=",
                "priority=",
                "name=",
                "limit=",
                "profile=",
                "post-process=",
                "sequence-id=",
                "stop-on-error",
                "continue-on-error",
                "fixed-time",
            ] + long_params)
    except getopt.GetoptError, err:
        _usage(1, err, help_specific_usage=help_specific_usage, description=description)
    try:
        for opt in opts:
            if opt[0] in ("-h", "--help"):
                _usage(0, help_specific_usage=help_specific_usage, description=description)
            elif opt[0] in ("-V", "--version"):
                print _TASK_PARAMS["version"]
                sys.exit(0)
            elif opt[0] in ("-u", "--user"):
                _TASK_PARAMS["user"] = opt[1]
            elif opt[0] in ("-v", "--verbose"):
                _TASK_PARAMS["verbose"] = int(opt[1])
            elif opt[0] in ("-s", "--sleeptime"):
                if task_name not in CFG_TASK_IS_NOT_A_DEAMON:
                    get_datetime(opt[1]) # see if it is a valid shift
                    _TASK_PARAMS["sleeptime"] = opt[1]
            elif opt[0] in ("-t", "--runtime"):
                _TASK_PARAMS["runtime"] = get_datetime(opt[1])
            elif opt[0] in ("-P", "--priority"):
                _TASK_PARAMS["priority"] = int(opt[1])
            elif opt[0] in ("-N", "--name"):
                _TASK_PARAMS["task_specific_name"] = opt[1]
            elif opt[0] in ("-L", "--limit"):
                _TASK_PARAMS["runtime_limit"] = parse_runtime_limit(opt[1])
            elif opt[0] in ("--profile", ):
                _TASK_PARAMS["profile"] += opt[1].split(',')
            elif opt[0] in ("--post-process", ):
                _TASK_PARAMS["post-process"] += [opt[1]];
            elif opt[0] in ("-I","--sequence-id"):
                _TASK_PARAMS["sequence-id"] = opt[1]
            elif opt[0] in ("--stop-on-error", ):
                _TASK_PARAMS["stop_queue_on_error"] = True
            elif opt[0] in ("--continue-on-error", ):
                _TASK_PARAMS["stop_queue_on_error"] = False
            elif opt[0] in ("--fixed-time", ):
                _TASK_PARAMS["fixed_time"] = True
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
    global _OPTIONS
    try:
        _OPTIONS[key] = value
    except NameError:
        _OPTIONS = {key : value}

def task_get_option(key, default=None):
    """Returns the value corresponding to key in the option dictionary of the task"""
    try:
        return _OPTIONS.get(key, default)
    except NameError:
        return default

def task_has_option(key):
    """Map the has_key query to _OPTIONS"""
    try:
        return _OPTIONS.has_key(key)
    except NameError:
        return False

def task_get_task_param(key, default=None):
    """Returns the value corresponding to the particular task param"""
    try:
        return _TASK_PARAMS.get(key, default)
    except NameError:
        return default

def task_set_task_param(key, value):
    """Set the value corresponding to the particular task param"""
    global _TASK_PARAMS
    try:
        _TASK_PARAMS[key] = value
    except NameError:
        _TASK_PARAMS = {key : value}

def task_update_progress(msg):
    """Updates progress information in the BibSched task table."""
    write_message("Updating task progress to %s." % msg, verbose=9)
    if "task_id" in _TASK_PARAMS:
        return run_sql("UPDATE schTASK SET progress=%s where id=%s",
            (msg, _TASK_PARAMS["task_id"]))

def task_update_status(val):
    """Updates status information in the BibSched task table."""
    write_message("Updating task status to %s." % val, verbose=9)
    if "task_id" in _TASK_PARAMS:
        return run_sql("UPDATE schTASK SET status=%s where id=%s",
            (val, _TASK_PARAMS["task_id"]))

def task_read_status():
    """Read status information in the BibSched task table."""
    res = run_sql("SELECT status FROM schTASK where id=%s",
        (_TASK_PARAMS['task_id'],), 1)
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
    if msg and _TASK_PARAMS['verbose'] >= verbose:
        if stream == sys.stdout:
            logging.info(msg)
        elif stream == sys.stderr:
            logging.error(msg)
        else:
            sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)
    else:
        logging.debug(msg)

_RE_SHIFT = re.compile("([-\+]{0,1})([\d]+)([dhms])")
def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S", now=None):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    date = now or datetime.datetime.now()

    factors = {"d": 24 * 3600, "h": 3600, "m": 60, "s": 1}
    m = _RE_SHIFT.match(var)
    if m:
        sign = m.groups()[0] == "-" and -1 or 1
        factor = factors[m.groups()[2]]
        value = float(m.groups()[1])
        delta = sign * factor * value
        while delta > 0 and date < datetime.datetime.now():
            date = date + datetime.timedelta(seconds=delta)
        date = date.strftime(format_string)
    else:
        date = time.strptime(var, format_string)
        date = time.strftime(format_string, date)
    return date


def task_sleep_now_if_required(can_stop_too=False):
    """This function should be called during safe state of BibTask,
    e.g. after flushing caches or outside of run_sql calls.
    """
    status = task_read_status()
    write_message('Entering task_sleep_now_if_required with status=%s' % status, verbose=9)
    if status == 'ABOUT TO SLEEP':
        write_message("sleeping...")
        task_update_status("SLEEPING")
        signal.signal(signal.SIGTSTP, _task_sig_dumb)
        os.kill(os.getpid(), signal.SIGSTOP)
        time.sleep(1)
        if task_read_status() == 'NOW STOP':
            if can_stop_too:
                write_message("stopped")
                task_update_status("STOPPED")
                sys.exit(0)
            else:
                write_message("stopping as soon as possible...")
                task_update_status('ABOUT TO STOP')
        else:
            write_message("... continuing...")
            task_update_status("CONTINUING")
        signal.signal(signal.SIGTSTP, _task_sig_sleep)
    elif status == 'ABOUT TO STOP' and can_stop_too:
        write_message("stopped")
        task_update_status("STOPPED")
        sys.exit(0)
    if can_stop_too:
        runtime_limit = task_get_option("limit")
        if runtime_limit is not None:
            if not (runtime_limit[0] <= time.time() <= runtime_limit[1]):
                write_message("stopped (outside runtime limit)")
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
        if not CFG_EXTERNAL_AUTHENTICATION[login_method]:
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
            if not CFG_EXTERNAL_AUTHENTICATION[login_method]:
                res = run_sql("select id from user where id=%s "
                        "and password=AES_ENCRYPT(email, %s)",
                (uid, password_entered), 1)
                if res:
                    ok = True
            else:
                if CFG_EXTERNAL_AUTHENTICATION[login_method].auth_user(get_email(uid), password_entered):
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
    _TASK_PARAMS['user'] = authenticate(_TASK_PARAMS["user"], authorization_action, authorization_msg)

    ## submit task:
    if _TASK_PARAMS['task_specific_name']:
        task_name = '%s:%s' % (_TASK_PARAMS['task_name'], _TASK_PARAMS['task_specific_name'])
    else:
        task_name = _TASK_PARAMS['task_name']
    write_message("storing task options %s\n" % argv, verbose=9)
    verbose_argv = 'Will execute: %s' % ' '.join([escape_shell_arg(str(arg)) for arg in argv])
    _TASK_PARAMS['task_id'] = run_sql("""INSERT INTO schTASK (proc,user,
                                           runtime,sleeptime,status,progress,arguments,priority,sequenceid)
                                         VALUES (%s,%s,%s,%s,'WAITING',%s,%s,%s,%s)""",
        (task_name, _TASK_PARAMS['user'], _TASK_PARAMS["runtime"],
         _TASK_PARAMS["sleeptime"], verbose_argv, marshal.dumps(argv), _TASK_PARAMS['priority'], _TASK_PARAMS['sequence-id']))

    ## update task number:
    write_message("Task #%d submitted." % _TASK_PARAMS['task_id'])
    return _TASK_PARAMS['task_id']


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
    @param task_run_fnc: will be called as the main core function. Must return
    False in case of errors.
    Return True in case of success and False in case of failure."""

    from invenio.bibtasklet import _TASKLETS
    ## We prepare the pid file inside /prefix/var/run/taskname_id.pid
    check_running_process_user()
    try:
        pidfile_name = os.path.join(CFG_PREFIX, 'var', 'run',
            'bibsched_task_%d.pid' % _TASK_PARAMS['task_id'])
        pidfile = open(pidfile_name, 'w')
        pidfile.write(str(os.getpid()))
        pidfile.close()
    except OSError:
        register_exception(alert_admin=True)
        task_update_status("ERROR")
        return False

    ## check task status:
    task_status = task_read_status()
    if task_status not in ("WAITING", "SCHEDULED"):
        write_message("Error: The task #%d is %s.  I expected WAITING or SCHEDULED." %
            (_TASK_PARAMS['task_id'], task_status), sys.stderr)
        return False

    time_now = time.time()
    if _TASK_PARAMS['runtime_limit'] is not None and os.environ.get('BIBSCHED_MODE', 'manual') != 'manual':
        if not _TASK_PARAMS['runtime_limit'][0][0] <= time_now <= _TASK_PARAMS['runtime_limit'][0][1]:
            if time_now <= _TASK_PARAMS['runtime_limit'][0][0]:
                new_runtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(_TASK_PARAMS['runtime_limit'][0][0]))
            else:
                new_runtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(_TASK_PARAMS['runtime_limit'][1][0]))
            progress = run_sql("SELECT progress FROM schTASK WHERE id=%s", (_TASK_PARAMS['task_id'], ))
            if progress:
                progress = progress[0][0]
            else:
                progress = ''
            g =  re.match(r'Postponed (\d+) time\(s\)', progress)
            if g:
                postponed_times = int(g.group(1))
            else:
                postponed_times = 0
            run_sql("UPDATE schTASK SET runtime=%s, status='WAITING', progress=%s, host='' WHERE id=%s", (new_runtime, 'Postponed %d time(s)' % (postponed_times + 1), _TASK_PARAMS['task_id']))
            write_message("Task #%d postponed because outside of runtime limit" % _TASK_PARAMS['task_id'])
            return True

    ## initialize signal handler:
    signal.signal(signal.SIGUSR2, signal.SIG_IGN)
    signal.signal(signal.SIGTSTP, _task_sig_sleep)
    signal.signal(signal.SIGTERM, _task_sig_stop)
    signal.signal(signal.SIGQUIT, _task_sig_stop)
    signal.signal(signal.SIGABRT, _task_sig_suicide)
    signal.signal(signal.SIGINT, _task_sig_stop)
    ## we can run the task now:
    write_message("Task #%d started." % _TASK_PARAMS['task_id'])
    task_update_status("RUNNING")
    ## run the task:
    _TASK_PARAMS['task_starting_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    sleeptime = _TASK_PARAMS['sleeptime']
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
            if task_get_task_param('stop_queue_on_error'):
                task_update_status("ERROR")
            else:
                task_update_status("CERROR")
    finally:
        task_status = task_read_status()
        if sleeptime:
            argv = _task_get_options(_TASK_PARAMS['task_id'], _TASK_PARAMS['task_name'])
            verbose_argv = 'Will execute: %s' % ' '.join([escape_shell_arg(str(arg)) for arg in argv])

            # Here we check if the task can shift away of has to be run at
            # a fixed time
            old_runtime = run_sql("SELECT runtime FROM schTASK WHERE id=%s", (_TASK_PARAMS['task_id'], ))[0][0]
            if not task_get_task_param('fixed_time') or _TASK_PARAMS['task_name'] not in CFG_BIBTASK_FIXEDTIMETASKS:
                old_runtime = None
            new_runtime = get_datetime(sleeptime, now=old_runtime)

            ## The task is a daemon. We resubmit it
            if task_status == 'DONE':
                ## It has finished in a good way. We recycle the database row
                run_sql("UPDATE schTASK SET runtime=%s, status='WAITING', progress=%s, host='' WHERE id=%s", (new_runtime, verbose_argv, _TASK_PARAMS['task_id']))
                write_message("Task #%d finished and resubmitted." % _TASK_PARAMS['task_id'])
            elif task_status == 'STOPPED':
                run_sql("UPDATE schTASK SET status='WAITING', progress=%s, host='' WHERE id=%s", (verbose_argv, _TASK_PARAMS['task_id'], ))
                write_message("Task #%d stopped and resubmitted." % _TASK_PARAMS['task_id'])
            else:
                ## We keep the bad result and we resubmit with another id.
                #res = run_sql('SELECT proc,user,sleeptime,arguments,priority FROM schTASK WHERE id=%s', (_TASK_PARAMS['task_id'], ))
                #proc, user, sleeptime, arguments, priority = res[0]
                #run_sql("""INSERT INTO schTASK (proc,user,
                            #runtime,sleeptime,status,arguments,priority)
                            #VALUES (%s,%s,%s,%s,'WAITING',%s, %s)""",
                            #(proc, user, new_runtime, sleeptime, arguments, priority))
                write_message("Task #%d finished but not resubmitted. [%s]" % (_TASK_PARAMS['task_id'], task_status))

        else:
            ## we are done:
            write_message("Task #%d finished. [%s]" % (_TASK_PARAMS['task_id'], task_status))
        ## Removing the pid
        os.remove(pidfile_name)

    #Lets call the post-process tasklets
    if task_get_task_param("post-process"):

        split = re.compile(r"(bst_.*)\[(.*)\]")
        for tasklet in task_get_task_param("post-process"):
            if not split.match(tasklet): # wrong syntax
                _usage(1, "There is an error in the post processing option "
                        "for this task.")

            aux_tasklet = split.match(tasklet)
            _TASKLETS[aux_tasklet.group(1)](**eval("dict(%s)" % (aux_tasklet.group(2))))
    return True

def _usage(exitcode=1, msg="", help_specific_usage="", description=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s [options]\n" % sys.argv[0])
    if help_specific_usage:
        sys.stderr.write("Command options:\n")
        sys.stderr.write(help_specific_usage)
    sys.stderr.write("  Scheduling options:\n")
    sys.stderr.write("  -u, --user=USER\tUser name under which to submit this"
        " task.\n")
    sys.stderr.write("  -t, --runtime=TIME\tTime to execute the task. [default=now]\n"
        "\t\t\tExamples: +15s, 5m, 3h, 2002-10-27 13:57:26.\n")
    sys.stderr.write("  -s, --sleeptime=SLEEP\tSleeping frequency after"
        " which to repeat the task.\n"
        "\t\t\tExamples: 30m, 2h, 1d. [default=no]\n")
    sys.stderr.write("  --fixed-time\t\tAvoid drifting of execution time when using --sleeptime\n")
    sys.stderr.write("  -I, --sequence-id=SEQUENCE-ID\tSequence Id of the current process\n")
    sys.stderr.write("  -L  --limit=LIMIT\tTime limit when it is"
        " allowed to execute the task.\n"
        "\t\t\tExamples: 22:00-03:00, Sunday 01:00-05:00.\n"
        "\t\t\tSyntax: [Wee[kday]] [hh[:mm][-hh[:mm]]].\n")
    sys.stderr.write("  -P, --priority=PRI\tTask priority (0=default, 1=higher, etc).\n")
    sys.stderr.write("  -N, --name=NAME\tTask specific name (advanced option).\n\n")
    sys.stderr.write("  General options:\n")
    sys.stderr.write("  -h, --help\t\tPrint this help.\n")
    sys.stderr.write("  -V, --version\t\tPrint version information.\n")
    sys.stderr.write("  -v, --verbose=LEVEL\tVerbose level (0=min,"
        " 1=default, 9=max).\n")
    sys.stderr.write("  --profile=STATS\tPrint profile information. STATS is a comma-separated\n\t\t\tlist of desired output stats (calls, cumulative,\n\t\t\tfile, line, module, name, nfl, pcalls, stdname, time).\n")
    sys.stderr.write("  --stop-on-error\tIn case of unrecoverable error stop the bibsched queue.\n")
    sys.stderr.write("  --continue-on-error\tIn case of unrecoverable error don't stop the bibsched queue.\n")
    sys.stderr.write("  --post-process=BIB_TASKLET_NAME[parameters]\tPostprocesses the specified\n\t\t\tbibtasklet with the given parameters between square\n\t\t\tbrackets.\n")
    sys.stderr.write("\t\t\tExample:--post-process \"bst_send_email[fromaddr=\n\t\t\t'foo@xxx.com', toaddr='bar@xxx.com', subject='hello',\n\t\t\tcontent='help']\"\n")
    if description:
        sys.stderr.write(description)
    sys.exit(exitcode)

def _task_sig_sleep(sig, frame):
    """Signal handler for the 'sleep' signal sent by BibSched."""
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    write_message("task_sig_sleep(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("sleeping as soon as possible...")
    _db_login(1)
    task_update_status("ABOUT TO SLEEP")

def _task_sig_stop(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    write_message("task_sig_stop(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("stopping as soon as possible...")
    _db_login(1) # To avoid concurrency with an interrupted run_sql call
    task_update_status("ABOUT TO STOP")

def _task_sig_suicide(sig, frame):
    """Signal handler for the 'suicide' signal sent by BibSched."""
    write_message("task_sig_suicide(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("suiciding myself now...")
    task_update_status("SUICIDING")
    write_message("suicided")
    _db_login(1)
    task_update_status("SUICIDED")
    sys.exit(1)

def _task_sig_dumb(sig, frame):
    """Dumb signal handler."""
    pass

_RE_PSLINE = re.compile('^\s*(\w+)\s+(\w+)')
def guess_apache_process_user_from_ps():
    """Guess Apache process user by parsing the list of running processes."""
    apache_users = []
    try:
        # Tested on Linux, Sun and MacOS X
        for line in os.popen('ps -A -o user,comm').readlines():
            g = _RE_PSLINE.match(line)
            if g:
                username = g.group(1)
                process = os.path.basename(g.group(2))
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
    if CFG_BIBSCHED_PROCESS_USER:
        # We have the expected bibsched process user defined in config,
        # so check against her, not against Apache.
        if running_as_user != CFG_BIBSCHED_PROCESS_USER:
            print >> sys.stderr, """ERROR: You must run "%(x_proc)s" as the user set up in your
CFG_BIBSCHED_PROCESS_USER (seems to be "%(x_user)s").

You may want to do "sudo -u %(x_user)s %(x_proc)s ..." to do so.

If you think this is not right, please set CFG_BIBSCHED_PROCESS_USER
appropriately and rerun "inveniocfg --update-config-py".""" % \
            {'x_proc': os.path.basename(sys.argv[0]), 'x_user': CFG_BIBSCHED_PROCESS_USER}
            sys.exit(1)
    elif running_as_user != guess_apache_process_user(): # not defined in config, check against Apache
        print >> sys.stderr, """ERROR: You must run "%(x_proc)s" as the same user that runs your Apache server
process (seems to be "%(x_user)s").

You may want to do "sudo -u %(x_user)s %(x_proc)s ..." to do so.

If you think this is not right, please set CFG_BIBSCHED_PROCESS_USER
appropriately and rerun "inveniocfg --update-config-py".""" % \
        {'x_proc': os.path.basename(sys.argv[0]), 'x_user': guess_apache_process_user()}
        sys.exit(1)
    return

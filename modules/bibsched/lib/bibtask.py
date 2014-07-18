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

from socket import gethostname

from invenio.dbquery import run_sql, _db_login
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_PREFIX, \
                           CFG_BINDIR, \
                           CFG_BIBSCHED_PROCESS_USER, \
                           CFG_TMPDIR, \
                           CFG_SITE_SUPPORT_EMAIL, \
                           CFG_VERSION, \
                           CFG_BIBSCHED_FLUSH_LOGS
from invenio.errorlib import register_exception

from invenio.access_control_config import CFG_EXTERNAL_AUTH_USING_SSO, \
                                          CFG_EXTERNAL_AUTHENTICATION
from invenio.webuser import get_user_preferences, get_email
from invenio.bibtask_config import (CFG_BIBTASK_VALID_TASKS,
                                    CFG_BIBTASK_DEFAULT_TASK_SETTINGS,
                                    CFG_BIBTASK_FIXEDTIMETASKS,
                                    CFG_BIBTASK_DEFAULT_GLOBAL_TASK_SETTINGS,
                                    CFG_BIBSCHED_LOGDIR,
                                    CFG_BIBTASK_LOG_FORMAT)
from invenio.dateutils import parse_runtime_limit
from invenio.shellutils import escape_shell_arg
from invenio.mailutils import send_email
from invenio.bibsched import bibsched_set_host, \
                             bibsched_get_host
from invenio.intbitset import intbitset


# Global _TASK_PARAMS dictionary.
_TASK_PARAMS = dict(CFG_BIBTASK_DEFAULT_GLOBAL_TASK_SETTINGS)

# Global _OPTIONS dictionary.
_OPTIONS = {}

# Which tasks don't need to ask the user for authorization?
CFG_VALID_PROCESSES_NO_AUTH_NEEDED = ("bibupload", )
CFG_TASK_IS_NOT_A_DEAMON = ("bibupload", )


class RecoverableError(StandardError):
    pass

class InvalidParams(StandardError):
    def __init__(self, err=None):
        self.err = err
        StandardError.__init__(self)

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


def get_sleeptime(argv):
    """Try to get the runtime by analysing the arguments."""
    sleeptime = ""
    argv = list(argv)
    while True:
        try:
            opts, dummy_args = getopt.gnu_getopt(argv, 's:', ['sleeptime='])
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
                opts, dummy_args = getopt.gnu_getopt(argv, 'P:', ['priority='])
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
                opts, dummy_args = getopt.gnu_getopt(argv, 'N:', ['name='])
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
                opts, dummy_args = getopt.gnu_getopt(argv, 't:', ['runtime='])
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

    def get_sequenceid(argv):
        """Try to get the sequenceid by analysing the arguments."""
        sequenceid = None
        argv = list(argv)
        while True:
            try:
                opts, dummy_args = getopt.gnu_getopt(argv, 'I:', ['sequence-id='])
            except getopt.GetoptError, err:
                ## We remove one by one all the non recognized parameters
                if len(err.opt) > 1:
                    argv = [arg for arg in argv if arg != '--%s' % err.opt and not arg.startswith('--%s=' % err.opt)]
                else:
                    argv = [arg for arg in argv if not arg.startswith('-%s' % err.opt)]
            else:
                break
        for opt in opts:
            if opt[0] in ('-I', '--sequence-id'):
                try:
                    sequenceid = opt[1]
                except ValueError:
                    pass
        return sequenceid

    def get_host(argv):
        """Try to get the sequenceid by analysing the arguments."""
        host = ''
        argv = list(argv)
        while True:
            try:
                opts, dummy_args = getopt.gnu_getopt(argv, '', ['host='])
            except getopt.GetoptError, err:
                ## We remove one by one all the non recognized parameters
                if len(err.opt) > 1:
                    argv = [arg for arg in argv if arg != '--%s' % err.opt and not arg.startswith('--%s=' % err.opt)]
                else:
                    argv = [arg for arg in argv if not arg.startswith('-%s' % err.opt)]
            else:
                break
        for opt in opts:
            if opt[0] in ('--host',):
                try:
                    host = opt[1]
                except ValueError:
                    pass
        return host

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
        sequenceid = get_sequenceid(argv)
        host = get_host(argv)
        argv = tuple([os.path.join(CFG_BINDIR, name)] + list(argv))

        if special_name:
            name = '%s:%s' % (name, special_name)

        verbose_argv = 'Will execute: %s' % ' '.join([escape_shell_arg(str(arg)) for arg in argv])

        ## submit task:
        task_id = run_sql("""INSERT INTO schTASK (proc,host,user,
            runtime,sleeptime,status,progress,arguments,priority,sequenceid)
            VALUES (%s,%s,%s,%s,%s,'WAITING',%s,%s,%s,%s)""",
            (name, host, user, runtime, sleeptime, verbose_argv,
             marshal.dumps(argv), priority, sequenceid))

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
        except (IOError, OSError):
            return 0
    else:
        return random.randrange(1, 4294967296)


def task_log_path(task_id, log_type):
    """Returns the path to the log files of given task

    Args:
     - task_id
     - log_type: either 'log' or 'err' to indiciate which type of log we want
    """
    sub_dir = str(task_id / 10000)
    dest_dir = os.path.join(CFG_BIBSCHED_LOGDIR, sub_dir)

    return os.path.join(dest_dir, 'bibsched_task_%d.%s' % (task_id, log_type))


def get_and_create_task_log_path(task_id, log_type):
    """Returns and creates the path to the log files of given task

    @see task_log_path
    """
    log_dest = task_log_path(task_id, log_type)

    # log_dest and err_dest are in the same folder
    dest_dir = os.path.dirname(log_dest)
    try:
        os.makedirs(dest_dir)
    except OSError, e:
        # If directory already exists, ignore error
        if e.errno != 17:
            raise

    return log_dest


def create_logfiles_handlers(task_id, formatter):
    """Create log handlers to write into tasks log files

    Args:
     - task_id
     - Formatter is an instance of logging.Formatter
    Returns:
     - log handler for standard log
     - log handler for error log
    """
    std_dest = get_and_create_task_log_path(task_id, 'log')
    err_dest = get_and_create_task_log_path(task_id, 'err')

    std_logger = logging.handlers.RotatingFileHandler(std_dest, 'a', 5*1024*1024, 10)
    err_logger = logging.handlers.RotatingFileHandler(err_dest, 'a', 5*1024*1024, 10)

    std_logger.setFormatter(formatter)
    err_logger.setFormatter(formatter)

    std_logger.setLevel(logging.DEBUG)
    err_logger.setLevel(logging.WARNING)

    return std_logger, err_logger


def create_streams_handlers(formatter):
    """Create log handlers to print to stdout/stderr

    Args:
     - Formatter is an instance of logging.Formatter
    Returns:
     - log handler for standard log
     - log handler for error log
    """
    stdout_logger = logging.StreamHandler(sys.stdout)
    stdout_logger.setFormatter(formatter)
    stdout_logger.setLevel(logging.DEBUG)

    stderr_logger = logging.StreamHandler(sys.stderr)
    stderr_logger.setFormatter(formatter)
    stderr_logger.setLevel(logging.WARNING)

    return stdout_logger, stderr_logger


def setup_loggers(task_id=None):
    """Sets up the logging system."""
    logger = logging.getLogger()

    # Let's clean the handlers in case some piece of code has already
    # fired any write_message, i.e. any call to debug, info, etc.
    # which triggered a call to logging.basicConfig()
    for handler in logger.handlers:
        logger.removeHandler(handler)

    formatter = logging.Formatter(*CFG_BIBTASK_LOG_FORMAT)

    # Log files
    if task_id is not None:
        log_logger, err_logger = create_logfiles_handlers(task_id, formatter)
        logger.addHandler(err_logger)
        logger.addHandler(log_logger)

    # Stream handlers
    stdout_logger, stderr_logger = create_streams_handlers(formatter)
    logger.addHandler(stdout_logger)
    logger.addHandler(stderr_logger)

    # Default log level
    logger.setLevel(logging.INFO)
    return logger


def task_init(authorization_action="",
              authorization_msg="",
              description="",
              help_specific_usage="",
              version=CFG_VERSION,
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
        "host": '',
    }
    to_be_submitted = True
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        _TASK_PARAMS['task_id'] = int(sys.argv[1])
        argv = task_get_options(_TASK_PARAMS['task_id'], _TASK_PARAMS['task_name'])
        to_be_submitted = False
    else:
        argv = sys.argv

    setup_loggers(_TASK_PARAMS.get('task_id'))

    task_name = os.path.basename(sys.argv[0])
    if task_name not in CFG_BIBTASK_VALID_TASKS or os.path.realpath(os.path.join(CFG_BINDIR, task_name)) != os.path.realpath(sys.argv[0]):
        raise OSError("%s is not in the allowed modules" % sys.argv[0])

    from invenio.errorlib import wrap_warn
    wrap_warn()

    if type(argv) is dict:
        # FIXME: REMOVE AFTER MAJOR RELEASE 1.0
        # This is needed for old task submitted before CLI parameters
        # where stored in DB and _OPTIONS dictionary was stored instead.
        _OPTIONS = argv
    else:
        _OPTIONS = {}
        if task_name in CFG_BIBTASK_DEFAULT_TASK_SETTINGS:
            _OPTIONS.update(CFG_BIBTASK_DEFAULT_TASK_SETTINGS[task_name])

        try:
            params = _task_build_params(_TASK_PARAMS['task_name'],
                                argv, specific_params,
                                task_submit_elaborate_specific_parameter_fnc,
                                task_submit_check_options_fnc)
        except InvalidParams, e:
            if e.err:
                err_msg = str(e.err)
            else:
                err_msg = ""
            _usage(1, err_msg,
                   help_specific_usage=help_specific_usage,
                   description=description)
        except (SystemExit, Exception), err:
            if not to_be_submitted:
                register_exception(alert_admin=True)
                write_message("Error in parsing the parameters: %s." % err, sys.stderr)
                write_message("Exiting.", sys.stderr)
                task_update_status("ERROR")
            raise

        _TASK_PARAMS.update(params)

    write_message('argv=%s' % (argv, ), verbose=9)
    write_message('_OPTIONS=%s' % (_OPTIONS, ), verbose=9)
    write_message('_TASK_PARAMS=%s' % (_TASK_PARAMS, ), verbose=9)

    if params.get('display_help'):
        _usage(0, help_specific_usage=help_specific_usage, description=description)

    if params.get('display_version'):
        print _TASK_PARAMS["version"]
        sys.exit(0)


    if to_be_submitted:
        _task_submit(argv, authorization_action, authorization_msg)
    else:
        ## BibTasks typically are going to work on several records
        ## and recreating data. Caching is typically done at the
        ## Python level, so there's no point in having a not
        ## exploited SQL cache.
        try:
            run_sql("SET SESSION query_cache_type = OFF;")
        except Exception:
            ## Very likely query_cache_type is already disabled globally.
            ## See: http://bugs.mysql.com/bug.php?id=69396
            pass
        try:
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
                        open(os.path.join(CFG_BIBSCHED_LOGDIR, 'bibsched_task_%d.log' % _TASK_PARAMS['task_id']), 'a').write("%s" % profile_dump)
                        os.remove(filename)
                    except ImportError:
                        ret = _task_run(task_run_fnc)
                        write_message("ERROR: The Python Profiler is not installed!", stream=sys.stderr)
                else:
                    ret = _task_run(task_run_fnc)
                if not ret:
                    write_message("Error occurred.  Exiting.", sys.stderr)
            except Exception, e:  # pylint: disable-msg=W0703
                # We want to catch all exceptions here because:
                # We set the task status to error and we want to display
                # an error traceback
                if isinstance(e, SystemExit) and e.code == 0:
                    raise
                register_exception(alert_admin=True)
                write_message("Unexpected error occurred: %s." % e, sys.stderr)
                write_message("Traceback is:", sys.stderr)
                from invenio.errorlib import get_pretty_traceback
                write_messages(get_pretty_traceback(), sys.stderr)
                write_message("Exiting.", sys.stderr)
                if task_get_task_param('stop_queue_on_error'):
                    task_update_status("ERROR")
                elif isinstance(e, RecoverableError) and task_get_task_param('email_logs_to'):
                    task_update_status("ERRORS REPORTED")
                else:
                    task_update_status("CERROR")
        finally:
            _task_email_logs()
            logging.shutdown()

def _task_build_params(task_name,
                       argv,
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
    params = {}

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
                "email-logs-to=",
                "host=",
            ] + long_params)
    except getopt.GetoptError, err:
        raise InvalidParams(err)
    try:
        for opt in opts:
            if opt[0] in ("-h", "--help"):
                params["display_help"] = True
                break
            elif opt[0] in ("-V", "--version"):
                params["display_version"] = True
                break
            elif opt[0] in ("-u", "--user"):
                params["user"] = opt[1]
            elif opt[0] in ("-v", "--verbose"):
                params["verbose"] = int(opt[1])
            elif opt[0] in ("-s", "--sleeptime"):
                if task_name not in CFG_TASK_IS_NOT_A_DEAMON:
                    get_datetime(opt[1]) # see if it is a valid shift
                    params["sleeptime"] = opt[1]
            elif opt[0] in ("-t", "--runtime"):
                params["runtime"] = get_datetime(opt[1])
            elif opt[0] in ("-P", "--priority"):
                params["priority"] = int(opt[1])
            elif opt[0] in ("-N", "--name"):
                params["task_specific_name"] = opt[1]
            elif opt[0] in ("-L", "--limit"):
                params["runtime_limit"] = parse_runtime_limit(opt[1])
            elif opt[0] in ("--profile", ):
                params.setdefault("profile", []).extend(opt[1].split(','))
            elif opt[0] in ("--post-process", ):
                params.setdefault("post-process", []).append(opt[1])
            elif opt[0] in ("-I", "--sequence-id"):
                params["sequence-id"] = opt[1]
            elif opt[0] in ("--stop-on-error", ):
                params["stop_queue_on_error"] = True
            elif opt[0] in ("--continue-on-error", ):
                params["stop_queue_on_error"] = False
            elif opt[0] in ("--fixed-time", ):
                params["fixed_time"] = True
            elif opt[0] in ("--email-logs-to",):
                params["email_logs_to"] = opt[1].split(',')
            elif opt[0] in ("--host",):
                params["host"] = opt[1]
            elif not callable(task_submit_elaborate_specific_parameter_fnc) or \
                not task_submit_elaborate_specific_parameter_fnc(opt[0],
                                                                 opt[1],
                                                                 opts,
                                                                 args):
                raise InvalidParams()
    except StandardError, e:
        raise InvalidParams(e)

    if callable(task_submit_check_options_fnc):
        if not task_submit_check_options_fnc():
            raise InvalidParams()

    return params

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
        return key in _OPTIONS
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
            (msg[:255], _TASK_PARAMS["task_id"]))

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
    except IndexError:
        out = 'UNKNOWN'
    return out

def write_messages(msgs, stream=None, verbose=1):
    """Write many messages through write_message"""
    if stream is None:
        stream = sys.stdout
    for msg in msgs.split('\n'):
        write_message(msg, stream, verbose)

def write_message(msg, stream=None, verbose=1):
    """Write message and flush output stream (may be sys.stdout or sys.stderr).
    Useful for debugging stuff.

    @note: msg could be a callable with no parameters. In this case it is
    been called in order to obtain the string to be printed.
    """
    if stream is None:
        stream = sys.stdout
    if msg and _TASK_PARAMS['verbose'] >= verbose:
        if callable(msg):
            msg = msg()
        if stream == sys.stdout:
            logging.info(msg)
        elif stream == sys.stderr:
            logging.error(msg)
        else:
            sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)
    else:
        logging.debug(msg)

    if CFG_BIBSCHED_FLUSH_LOGS:
        for handler in logging.root.handlers:
            handler.flush()

_RE_SHIFT = re.compile(r"([-\+]{0,1})([\d]+)([dhms])")
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
        signal.signal(signal.SIGTSTP, cb_task_sig_dumb)
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
        signal.signal(signal.SIGTSTP, cb_task_sig_sleep)
    elif status == 'ABOUT TO STOP':
        if can_stop_too:
            write_message("stopped")
            task_update_status("STOPPED")
            sys.exit(0)

    if can_stop_too:
        runtime_limit = task_get_option("limit")
        if runtime_limit is not None:
            if not (runtime_limit[0] <= datetime.datetime.now() <= runtime_limit[1]):
                write_message("stopped (outside runtime limit)")
                task_update_status("STOPPED")
                sys.exit(0)

def get_modified_records_since(modification_date):
    """
    Return the set of modified record since the given
    modification_date.
    @param modification_date: Return records modified after this date
    @type modification_date datetime
    """
    results = run_sql("SELECT id FROM bibrec WHERE modification_date >= %s",
                      (modification_date,))
    return intbitset(results)

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
                                           runtime,sleeptime,status,progress,arguments,priority,sequenceid,host)
                                         VALUES (%s,%s,%s,%s,'WAITING',%s,%s,%s,%s,%s)""",
        (task_name, _TASK_PARAMS['user'], _TASK_PARAMS["runtime"],
         _TASK_PARAMS["sleeptime"], verbose_argv[:255], marshal.dumps(argv),
         _TASK_PARAMS['priority'], _TASK_PARAMS['sequence-id'],
         _TASK_PARAMS['host']))

    ## update task number:
    write_message("Task #%d submitted." % _TASK_PARAMS['task_id'])
    return _TASK_PARAMS['task_id']


def task_get_options(task_id, task_name):
    """Returns options for the task 'id' read from the BibSched task
    queue table."""
    out = {}
    res = run_sql("SELECT arguments FROM schTASK WHERE id=%s AND proc LIKE %s",
        (task_id, task_name+'%'))
    try:
        out = marshal.loads(res[0][0])
    except ValueError:
        write_message("Error: %s task %d does not seem to exist."
            % (task_name, task_id), sys.stderr)
        task_update_status('ERROR')
        sys.exit(1)
    write_message('Options retrieved: %s' % (out, ), verbose=9)
    return out

def _task_email_logs():
    """
    In case this was requested, emails the logs.
    """
    email_logs_to = task_get_task_param('email_logs_to')

    if not email_logs_to:
        return

    status = task_read_status()
    task_name = task_get_task_param('task_name')
    task_specific_name = task_get_task_param('task_specific_name')
    if task_specific_name:
        task_name += '%s:%s' % (task_name, task_specific_name)
    runtime = task_get_task_param('runtime')

    title = "Execution of %s: %s" % (task_name, status)
    body = """
Attached you can find the stdout and stderr logs of the execution of
name: %s
id: %s
runtime: %s
options: %s
status: %s
""" % (task_name, _TASK_PARAMS['task_id'], runtime, _OPTIONS, status)
    log_file = task_log_path(_TASK_PARAMS['task_id'], 'log')
    err_file = task_log_path(_TASK_PARAMS['task_id'], 'err')
    return send_email(CFG_SITE_SUPPORT_EMAIL, email_logs_to, title, body,
                      attachments=[(log_file, 'text/plain'), (err_file, 'text/plain')])


def get_task_old_runtime(task_params):
    """Fetch from the database the last time this task ran

    Here we check if the task can shift away or has to be run at a fixed time.
    """
    if task_params['fixed_time'] or \
                        task_params['task_name'] in CFG_BIBTASK_FIXEDTIMETASKS:
        sql = "SELECT runtime FROM schTASK WHERE id=%s"
        old_runtime = run_sql(sql, (task_params['task_id'], ))[0][0]
    else:
        old_runtime = None
    return old_runtime


def get_task_new_runtime(task_params):
    """Compute the next time this task should run"""
    return get_datetime(task_params['sleeptime'],
                        now=get_task_old_runtime(task_params))


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

    time_now = datetime.datetime.now()
    if _TASK_PARAMS['runtime_limit'] is not None:
        if not _TASK_PARAMS['runtime_limit'][0][0] <= time_now <= _TASK_PARAMS['runtime_limit'][0][1]:
            if task_get_option('fixed_time'):
                new_runtime = get_task_new_runtime(_TASK_PARAMS)
            elif time_now <= _TASK_PARAMS['runtime_limit'][0][0]:
                new_runtime = _TASK_PARAMS['runtime_limit'][0][0].strftime("%Y-%m-%d %H:%M:%S")
            else:
                new_runtime = _TASK_PARAMS['runtime_limit'][1][0].strftime("%Y-%m-%d %H:%M:%S")
            progress = run_sql("SELECT progress FROM schTASK WHERE id=%s", (_TASK_PARAMS['task_id'], ))
            if progress:
                progress = progress[0][0]
            else:
                progress = ''
            g = re.match(r'Postponed (\d+) time\(s\)', progress)
            if g:
                postponed_times = int(g.group(1))
            else:
                postponed_times = 0
            if _TASK_PARAMS['sequence-id']:
                ## Also postponing other dependent tasks.
                run_sql("UPDATE schTASK SET runtime=%s, progress=%s WHERE sequenceid=%s AND status='WAITING'", (new_runtime, 'Postponed as task %s' % _TASK_PARAMS['task_id'], _TASK_PARAMS['sequence-id'])) # kwalitee: disable=sql
            run_sql("UPDATE schTASK SET runtime=%s, status='WAITING', progress=%s, host='' WHERE id=%s", (new_runtime, 'Postponed %d time(s)' % (postponed_times + 1), _TASK_PARAMS['task_id'])) # kwalitee: disable=sql
            write_message("Task #%d postponed because outside of runtime limit" % _TASK_PARAMS['task_id'])
            return True

    # Make sure the host field is updated
    # It will not be updated properly when we run
    # a task from the cli (without using the bibsched monitor)
    host = bibsched_get_host(_TASK_PARAMS['task_id'])
    if host and host != gethostname():
        write_message("Error: The task #%d is bound to %s." %
            (_TASK_PARAMS['task_id'], host), sys.stderr)
        return False
    else:
        bibsched_set_host(_TASK_PARAMS['task_id'], gethostname())

    ## initialize signal handler:
    signal.signal(signal.SIGUSR2, cb_task_sig_debug)
    signal.signal(signal.SIGTSTP, cb_task_sig_sleep)
    signal.signal(signal.SIGTERM, cb_task_sig_stop)
    signal.signal(signal.SIGQUIT, cb_task_sig_stop)
    signal.signal(signal.SIGABRT, cb_task_sig_suicide)
    signal.signal(signal.SIGINT, cb_task_sig_stop)
    ## we can run the task now:
    write_message("Task #%d started." % _TASK_PARAMS['task_id'])
    task_update_status("RUNNING")
    ## run the task:
    _TASK_PARAMS['task_starting_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    sleeptime = _TASK_PARAMS['sleeptime']
    try:
        if callable(task_run_fnc) and task_run_fnc():
            task_update_status("DONE")
        elif task_get_task_param('email_logs_to'):
            task_update_status("ERRORS REPORTED")
        else:
            task_update_status("DONE WITH ERRORS")
    finally:
        task_status = task_read_status()
        if sleeptime:
            argv = task_get_options(_TASK_PARAMS['task_id'], _TASK_PARAMS['task_name'])
            verbose_argv = 'Will execute: %s' % ' '.join([escape_shell_arg(str(arg)) for arg in argv])

            new_runtime = get_task_new_runtime(_TASK_PARAMS)

            ## The task is a daemon. We resubmit it
            if task_status == 'DONE':
                ## It has finished in a good way. We recycle the database row
                run_sql("UPDATE schTASK SET runtime=%s, status='WAITING', progress=%s, host=%s WHERE id=%s", (new_runtime, verbose_argv, _TASK_PARAMS['host'], _TASK_PARAMS['task_id']))
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
    sys.stderr.write("  --email-logs-to=EMAILS Sends an email with the results of the execution\n\t\t\tof the task, and attached the logs (EMAILS could be a comma-\n\t\t\tseparated lists of email addresses)\n")
    sys.stderr.write("  --host=HOSTNAME Bind the task to the specified host, it will only ever run on that host.\n")
    if description:
        sys.stderr.write(description)
    sys.exit(exitcode)

def cb_task_sig_sleep(sig, frame):
    """Signal handler for the 'sleep' signal sent by BibSched."""
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    write_message("task_sig_sleep(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("sleeping as soon as possible...")
    _db_login(relogin=1)
    task_update_status("ABOUT TO SLEEP")

def cb_task_sig_stop(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    write_message("task_sig_stop(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("stopping as soon as possible...")
    _db_login(relogin=1) # To avoid concurrency with an interrupted run_sql call
    task_update_status("ABOUT TO STOP")

def cb_task_sig_suicide(sig, frame):
    """Signal handler for the 'suicide' signal sent by BibSched."""
    write_message("task_sig_suicide(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    write_message("suiciding myself now...")
    task_update_status("SUICIDING")
    write_message("suicided")
    _db_login(relogin=1)
    task_update_status("SUICIDED")
    sys.exit(1)

def cb_task_sig_debug(sig, frame):
    """Signal handler for the 'debug' signal sent by BibSched.

    This spawn a remote console server we can connect to to check
    the task behavior at runtime."""
    write_message("task_sig_debug(), got signal %s frame %s"
            % (sig, frame), verbose=9)
    from rfoo.utils import rconsole
    rconsole.spawn_server()

def cb_task_sig_dumb(sig, frame):
    """Dumb signal handler."""
    pass

_RE_PSLINE = re.compile(r'^\s*(\w+)\s+(\w+)')
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
                if process in ('apache', 'apache2', 'httpd'):
                    if username not in apache_users and username != 'root':
                        apache_users.append(username)
    except OSError, e:
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

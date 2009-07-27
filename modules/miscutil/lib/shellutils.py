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

"""
The shellutils module contains helper functions useful for interacting
with the operating system shell.

The main API functions are:
   - run_shell_command()
"""

import os
import tempfile
import time
import signal

try:
    import subprocess
    from invenio.asyncproc import Timeout, with_timeout, Process
    CFG_HAS_SUBPROCESS = True
except ImportError:
    CFG_HAS_SUBPROCESS = False

from invenio.config import CFG_MISCUTIL_DEFAULT_PROCESS_TIMEOUT

__all__ = ['run_shell_command', 'run_process_with_timeout', 'Timeout']

"""
This module implements two functions:
    - L{run_shell_command}
    - L{run_process_with_timeout}

L{run_shell_command} will run a command through a shell, capturing its
standard output and standard error.

L{run_process_with_timeout} will run a process on its own allowing to
specify a input file, capturing the standard output and standard error and
killing the process after a given timeout.
"""

def run_shell_command(cmd, args=None, filename_out=None, filename_err=None):
    """Run operating system command cmd with arguments from the args
    tuple in a sub-shell and return tuple (exit status code, stdout
    info, stderr info).

    @param cmd: Command to execute in a shell; may contain %s
        placeholders for arguments that will be expanded from the args
        tuple. Example: cmd='echo %s', args = ('hello',).
    @type cmd: string

    @param args: Arguments to be escaped and substituted for %s
        placeholders in cmd.
    @type args: tuple of strings

    @param filename_out: Desired filename for stdout output
        (optional; see below).
    @type filename_out: string

    @param filename_err: Desired filename for stderr output
        (optional; see below).
    @type filename_err: string

    @return: Tuple (exit code, string containing stdout output buffer,
        string containing stderr output buffer).

        However, if either filename_out or filename_err are defined,
        then the output buffers are not passed back but rather written
        into filename_out/filename_err pathnames.  This is useful for
        commands that produce big files, for which it is not practical
        to pass results back to the callers in a Python text buffer.
        Note that it is the client's responsibility to name these
        files in the proper fashion (e.g. to be unique) and to close
        these files after use.
    @rtype: (number, string, string)

    @raise TypeError: if the number of args does not correspond to the
       number of placeholders in cmd.

    @note: Uses temporary files to store out/err output, not pipes due
        to potential pipe race condition on some systems.  If either
        filename_out or filename_err are defined, then do not create
        temporary files, but store stdout or stderr output directly in
        these files instead, and do not delete them after execution.
    """
    # wash args value:
    if args:
        args = tuple(args)
    else:
        args = ()
    # construct command with argument substitution:
    try:
        cmd = cmd % tuple([escape_shell_arg(x) for x in args])
    except TypeError:
        # there were problems with %s and args substitution, so raise an error:
        raise
    cmd_out = ''
    cmd_err = ''
    # create files:
    if filename_out:
        cmd_out_fd = os.open(filename_out, os.O_CREAT, 0644)
        file_cmd_out = filename_out
    else:
        cmd_out_fd, file_cmd_out = \
                    tempfile.mkstemp("invenio-shellutils-cmd-out")
    if filename_err:
        cmd_err_fd = os.open(filename_err, os.O_CREAT, 0644)
        file_cmd_err = filename_err
    else:
        cmd_err_fd, file_cmd_err = \
                    tempfile.mkstemp("invenio-shellutils-cmd-err")
    # run command:
    cmd_exit_code = os.system("%s > %s 2> %s" % (cmd,
                                                 file_cmd_out,
                                                 file_cmd_err))
    # delete temporary files: (if applicable)
    if not filename_out:
        if os.path.exists(file_cmd_out):
            cmd_out_fo = open(file_cmd_out)
            cmd_out = cmd_out_fo.read()
            cmd_out_fo.close()
            os.remove(file_cmd_out)
    if not filename_err:
        if os.path.exists(file_cmd_err):
            cmd_err_fo = open(file_cmd_err)
            cmd_err = cmd_err_fo.read()
            cmd_err_fo.close()
            os.remove(file_cmd_err)
    os.close(cmd_out_fd)
    os.close(cmd_err_fd)
    # return results:
    return cmd_exit_code, cmd_out, cmd_err

def run_process_with_timeout(args, filename_in=None, filename_out=None, filename_err=None, cwd=None, timeout=CFG_MISCUTIL_DEFAULT_PROCESS_TIMEOUT):
    """
    Run a process capturing its output and killing it after a given timeout.

    @param args: should be a string, or a sequence of program arguments. The
        program to execute is the first item in the args sequence or the string
        if a string is given.
    @type args: string/sequence
    @param filename_in: the path of a file to be used as standard input to
        the process. If None, the process will receive no standard input.
    @type filename_in: string
    @param filename_out: the path of a file to be used as standard output from
        the process. If None, the process standard output will still be
        captured and returned.
    @type filename_out: string
    @param filename_err: the path of a file to be used as standard error from
        the process. If None, the process standard error will still be
        captured and returned.
    @type filename_err: string
    @param timeout: the number of seconds after which the process is killed.
    @type timeout: int
    @param cwd: the current working directory where to execute the process.
    @type cwd: string
    @return: a tuple containing with the exit status, the captured output and
        the captured error.
    @rtype: tuple
    @raise Timeout: in case the process is still in execution after the
        specified timeout.
    @note: that if C{Timeout} exception is raised and cmd_out_file/cmd_err_file
        have  been specified, they will be probably partially filled.
    @warning: in case Python 2.3 is used and the subprocess module is not
        available this function will try to fallback on L{run_shell_command},
        provided that no C{cmd_in_file} parameter is filled.
    """
    def call_the_process(the_process, stdout, stderr):
        cmd_out = ''
        cmd_err = ''
        while True:
            time.sleep(1)
            poll = the_process.wait(os.WNOHANG)
            tmp_cmd_out, tmp_cmd_err = the_process.readboth()
            if stdout:
                stdout.write(tmp_cmd_out)
            if stderr:
                stderr.write(tmp_cmd_err)
            cmd_out += tmp_cmd_out
            cmd_err += tmp_cmd_err
            if poll != None:
                break
        return poll, cmd_out, cmd_err

    if not CFG_HAS_SUBPROCESS:
        ## Let's fall back on run_shell_command.
        if filename_in is not None:
            raise ImportError, "Failed to import subprocess module and " \
            "run_process_with_timeout with cmd_in_file set, thus can not " \
            "fall back on run_shell_command."
        if cwd:
            cwd_str = "cd %s; " % escape_shell_arg(cwd)
        else:
            cwd_str = ''
        return run_shell_command(cwd_str + ('%s ' * len(args))[:-1], args, filename_out=filename_out, filename_err=filename_err)

    if filename_in is not None:
        stdin = open(filename_in)
    else:
        stdin = None
    if filename_out is not None:
        stdout = open(filename_out, 'w')
    else:
        stdout = None
    if filename_err is not None:
        stderr = open(filename_err, 'w')
    else:
        stderr = None
    the_process = Process(args, stdin=stdin, cwd=cwd)
    try:
        return with_timeout(timeout, call_the_process, the_process, stdout, stderr)
    except Timeout:
        ## the_process.terminate()
        ## FIXME: the_process.terminate() would rather be a better
        ## solution, but apparently it does not work. When signal.SIGTERM
        ## is sent to the process the wait operation down there does
        ## not respect any timeout and will wait until the very end
        ## of the process. So the afterwards SIGKILL will not find any
        ## process... So let's send SIGTERM/SIGKILL directly here without
        ## waiting anything. Anyway we are not interested in the outcome
        ## of a timeouted process, we just want to kill it!!
        the_process.kill(signal.SIGTERM)
        time.sleep(1)
        the_process.kill(signal.SIGKILL)
        raise

def escape_shell_arg(shell_arg):
    """Escape shell argument shell_arg by placing it within
    single-quotes.  Any single quotes found within the shell argument
    string will be escaped.

    @param shell_arg: The shell argument to be escaped.
    @type shell_arg: string
    @return: The single-quote-escaped value of the shell argument.
    @rtype: string
    @raise TypeError: if shell_arg is not a string.
    @see: U{http://mail.python.org/pipermail/python-list/2005-October/346957.html}
    """
    if type(shell_arg) is not str:
        msg = "ERROR: escape_shell_arg() expected string argument but " \
              "got '%s' of type '%s'." % (repr(shell_arg), type(shell_arg))
        raise TypeError(msg)

    return "'%s'" % shell_arg.replace("'", r"'\''")

# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011 CERN.
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
The shellutils module contains helper functions useful for interacting
with the operating system shell.

The main API functions are:
   - run_shell_command()
"""

import os
import fcntl
import sys
import tempfile
import time
import signal
import select
from cStringIO import StringIO
import subprocess

from invenio.config import CFG_MISCUTIL_DEFAULT_PROCESS_TIMEOUT

__all__ = ['run_shell_command', 'run_process_with_timeout', 'Timeout', 'SmarterPopen']

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

class Timeout(Exception):
    """Exception raised by with_timeout() when the operation takes too long.
    """
    pass

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
    stdin = subprocess.PIPE
    stdout = stderr = None
    if filename_in:
        stdin = open(filename_in)
    if filename_out:
        stdout = open(filename_out, 'w')
    if filename_err:
        stderr = open(filename_err, 'w')
    tmp_stdout = StringIO()
    tmp_stderr = StringIO()
    s("filename_in: %s, filename_out: %s, filename_err: %s, stdin: %s, stdout: %s, stderr: %s, tmp_stdout: %s, tmp_stderr: %s" % (filename_in, filename_out, filename_err, stdin, stdout, stderr, tmp_stdout, tmp_stderr))
    ## See: <http://stackoverflow.com/questions/3876886/timeout-a-subprocess>
    process = subprocess.Popen(args, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, cwd=cwd, preexec_fn=os.setpgrp)
    s("process: %s, pid: %s, args: %s, cwd: %s" % (process, process.pid, args, cwd))

    ## See: <http://stackoverflow.com/questions/375427/non-blocking-read-on-a-stream-in-python>
    fd = process.stdout.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    fd = process.stderr.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    poller = select.poll()
    poller.register(process.stdout)
    poller.register(process.stderr)
    t1 = time.time()
    try:
        while process.poll() is None:
            s("polling")
            if time.time() - t1 >= timeout:
                process.stdin.close()
                time.sleep(1)
                if process.poll() is None:
                    ## See: <http://stackoverflow.com/questions/3876886/timeout-a-subprocess>
                    os.killpg(process.pid, signal.SIGTERM)
                    time.sleep(1)
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                try:
                    os.waitpid(process.pid, 0)
                except OSError:
                    pass
                raise Timeout()
            for fd, event in poller.poll(500):
                if fd == process.stdout.fileno():
                    buf = process.stdout.read(65536)
                    tmp_stdout.write(buf)
                    if stdout is not None:
                        stdout.write(buf)
                elif fd == process.stderr.fileno():
                    buf = process.stderr.read(65536)
                    tmp_stderr.write(buf)
                    if stderr is not None:
                        stderr.write(buf)
                else:
                    raise OSError("fd %s is not a valid file descriptor" % fd)
    finally:
        while True:
            ## Let's just read what is remaining to read.
            s("flushing")
            for fd, event in poller.poll(500):
                if fd == process.stdout.fileno():
                    buf = process.stdout.read(65536)
                    tmp_stdout.write(buf)
                    if stdout is not None:
                        stdout.write(buf)
                elif fd == process.stderr.fileno():
                    buf = process.stderr.read(65536)
                    tmp_stderr.write(buf)
                    if stderr is not None:
                        stderr.write(buf)
                else:
                    raise OSError("fd %s is not a valid file descriptor" % fd)
            else:
                break
    return process.poll(), tmp_stdout.getvalue(), tmp_stderr.getvalue()

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

def s(t):
    ## De-comment this to have lots of debugging information
    #print time.time(), t
    pass

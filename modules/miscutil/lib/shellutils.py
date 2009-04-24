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

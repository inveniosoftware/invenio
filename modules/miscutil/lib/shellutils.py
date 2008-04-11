## $Id$
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

"""Helper functions that could be useful when interacting with the shell.
"""

__revision__ = "$Id$"


def escape_shell_arg(shell_arg):
    """Escape a shell argument by placing it within single-quotes. Any single-
       quotes within it the shell_arg string will be escaped.
       E.g.:
          hello         ---> 'hello'
          hello'world   ---> 'hello'\''world'
       @param shell_arg: (string) - the item to be quoted.
       @return: (string) - the single-quoted string.
       @Exceptions raised: (TypeError) - the function expects that shell_arg be
        a string. If not, a TypeError will be raised.
       Details of this were found here:
       <http://mail.python.org/pipermail/python-list/2005-October/346957.html>
    """
    if type(shell_arg) is not str:
        msg = "ERROR: \"escape_shell_arg\" function expected parameter of " \
              "string type. Got: %s." % type(shell_arg)
        raise TypeError(msg)

    return "'%s'" % shell_arg.replace("'", r"'\''")

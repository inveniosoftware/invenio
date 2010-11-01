# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
Some common utilities for BibClassify.
"""

import sys
import time

# Verbose levels are as such:
# 0: No verbose.
# 1: Error messages.
# 2: Warning messages.
# 3 (and more): Info messages.

# By default, output error messages.
VERBOSE_LEVEL = 1

def set_verbose_level(level):
    """Sets the verbose level."""
    global VERBOSE_LEVEL
    VERBOSE_LEVEL = int(level)

def write_message(msg, stream=sys.stdout, verbose=1):
    """Write message and flush output stream (may be sys.stdout or sys.stderr).
    Useful for debugging stuff. Copied and adapted from bibtask.py."""
    if msg and verbose <= VERBOSE_LEVEL:
        if stream == sys.stdout or stream == sys.stderr:
            stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ",
                time.localtime()))
            try:
                stream.write("%s\n" % msg)
            except UnicodeEncodeError:
                stream.write("%s\n" % msg.encode('ascii', 'backslashreplace'))
                stream.flush()
        else:
            sys.stderr.write("Unknown stream %s. [must be sys.stdout or "
                "sys.stderr]\n" % stream)

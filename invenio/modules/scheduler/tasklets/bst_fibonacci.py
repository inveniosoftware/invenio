# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Invenio Bibliographic Tasklet Example.

Demonstrates BibTaskLet <-> BibTask <-> BibSched connectivity
"""

import sys
import time
from invenio.legacy.bibsched.bibtask import write_message, task_set_option, \
        task_get_option, task_update_progress, task_has_option, \
        task_get_task_param, task_sleep_now_if_required

def fib(n):
    """Returns Fibonacci number for 'n'."""
    out = 1
    if n >= 2:
        out = fib(n-2) + fib(n-1)
    return out

def bst_fibonacci(n=30):
    """
    Small tasklets that prints the the Fibonacci sequence for n.
    @param n: how many Fibonacci numbers to print.
    @type n: int
    """
    ## Since it's tasklet, the parameter might be passed as a string.
    ## it should then be converted to an int.
    n = int(n)
    write_message("Printing %d Fibonacci numbers." % n, verbose=9)
    for i in range(0, n):
        if i > 0 and i % 4 == 0:
            write_message("Error: water in the CPU.  Ignoring and continuing.", sys.stderr, verbose=3)
        elif i > 0 and i % 5 == 0:
            write_message("Error: floppy drive dropped on the floor.  Ignoring and continuing.", sys.stderr)
        write_message("fib(%d)=%d" % (i, fib(i)))
        task_update_progress("Done %d out of %d." % (i, n))
        task_sleep_now_if_required(can_stop_too=True)
        time.sleep(1)
    task_update_progress("Done %d out of %d." % (n, n))
    return 1


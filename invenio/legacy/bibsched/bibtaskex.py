# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Invenio Bibliographic Task Example.

Demonstrates BibTask <-> BibSched connectivity, signal handling,
error handling, etc.
"""

__revision__ = "$Id$"

import sys
import time

from invenio.legacy.bibsched.bibtask import task_init, write_message, task_set_option, \
        task_get_option, task_update_progress, task_has_option, \
        task_get_task_param, task_sleep_now_if_required

def fib(n):
    """Returns Fibonacci number for 'n'."""
    out = 1
    if n >= 2:
        out = fib(n-2) + fib(n-1)
    return out

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """ Given the string key it checks it's meaning, eventually using the
    value. Usually it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    eg:
    if key in ('-n', '--number'):
        task_set_option('number', value)
        return True
    return False
    """
    if key in ('-n', '--number'):
        task_set_option('number', value)
        return True
    elif key in ('-e', '--error'):
        task_set_option('error', True)
        return True
    return False

def task_run_core():
    """Runs the task by fetching arguments from the BibSched task queue.  This is
    what BibSched will be invoking via daemon call.
    The task prints Fibonacci numbers for up to NUM on the stdout, and some
    messages on stderr.
    Return 1 in case of success and 0 in case of failure."""
    n = int(task_get_option('number'))
    write_message("Printing %d Fibonacci numbers." % n, verbose=9)
    for i in range(0, n):
        if i > 0 and i % 4 == 0:
            write_message("Error: water in the CPU.  Ignoring and continuing.", sys.stderr, verbose=3)
        elif i > 0 and i % 5 == 0:
            write_message("Error: floppy drive dropped on the floor.  Ignoring and continuing.", sys.stderr)
            if task_get_option('error'):
                1 / 0
        write_message("fib(%d)=%d" % (i, fib(i)))
        task_update_progress("Done %d out of %d." % (i, n))
        task_sleep_now_if_required(can_stop_too=True)
        time.sleep(1)
    task_update_progress("Done %d out of %d." % (n, n))
    return 1


def main():
    """Main that construct all the bibtask."""
    task_init(authorization_action='runbibtaskex',
            authorization_msg="BibTaskEx Task Submission",
            help_specific_usage="""\
-n,  --number         Print Fibonacci numbers for up to NUM. [default=30]
-e,  --error          Raise an error from time to time
""",
            version=__revision__,
            specific_params=("n:e",
                ["number=", "error"]),
            task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
            task_run_fnc=task_run_core)

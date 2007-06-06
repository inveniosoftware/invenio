# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""CDS Invenio Bibliographic Task Example.

Demonstrates BibTask <-> BibSched connectivity, signal handling,
error handling, etc.
"""

__revision__ = "$Id$"

import sys
from invenio.bibtask import BibTask, write_message
import getopt
import getpass
import marshal
import signal
import time
import traceback

cfg_n_default = 30 # how many Fibonacci numbers to calculate if none submitted?

def fib(n):
    """Returns Fibonacci number for 'n'."""
    out = 1
    if n >= 2:
        out = fib(n-2) + fib(n-1)
    return out


class BibTaskExBibTask(BibTask):
    """Abstract class for implementing a Bibliographic task."""
    def __init__(self):
        BibTask.__init__(self, authorization_action='runbibtaskex', authorization_msg="BibTaskEx Task Submission",
            description="", help_specific_usage="  -n, --number=NUM       Print Fibonacci numbers for up to NUM.  [default=30]",
            specific_params=("n:", ["number="]))

    def task_submit_elaborate_specific_parameter(self, key, value):
        """ Given the string key it checks it's meaning, eventually using the
        value. Usually it fills some key in the options dict.
        It must return True if it has elaborated the key, False, if it doesn't
        know that key.
        eg:
        if key in ('-n', '--number'):
            self.options['number'] = value
            return True
        return False
        """
        if key in ('-n', '--number'):
            self.options['number'] = value
            return True
        return False

    def task_run_core(self):
        """Runs the task by fetching arguments from the BibSched task queue.  This is
        what BibSched will be invoking via daemon call.
        The task prints Fibonacci numbers for up to NUM on the stdout, and some
        messages on stderr.
        Return 1 in case of success and 0 in case of failure."""
        if self.options.has_key("number"):
            n = self.options["number"]
        else:
            n = cfg_n_default
        if self.options["verbose"] >= 9:
            write_message("Printing %d Fibonacci numbers." % n)
        for i in range(0, n):
            if i > 0 and i % 4 == 0:
                if self.options["verbose"] >= 3:
                    write_message("Error: water in the CPU.  Ignoring and continuing.", sys.stderr)
            elif i > 0 and i % 5 == 0:
                if self.options["verbose"]:
                    write_message("Error: floppy drive dropped on the floor.  Ignoring and continuing.", sys.stderr)
            if self.options["verbose"]:
                write_message("fib(%d)=%d" % (i, fib(i)))
            self.task_update_progress("Done %d out of %d." % (i, n))
            time.sleep(1)
        self.task_update_progress("Done %d out of %d." % (n, n))
        if self.options["verbose"]:
            write_message("Task #%d finished." % self.task_id)
        return 1

def main():
    task = BibTaskExBibTask()
    task.main()

### okay, here we go:
if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""Unit tests for the inveniomanage script."""

import sys
import StringIO
from invenio.testutils import make_test_suite, run_test_suite, InvenioTestCase


class Catcher(object):
    """Helper decorator to test raw_input."""
    ## see: http://stackoverflow.com/questions/13480632/python-stringio-selectively-place-data-into-stdin

    def __init__(self, handler):
        self.handler = handler
        self.inputs = []

    def __enter__(self):
        self.__stdin = sys.stdin
        self.__stdout = sys.stdout
        sys.stdin = self
        sys.stdout = self

    def __exit__(self, type, value, traceback):
        sys.stdin = self.__stdin
        sys.stdout = self.__stdout

    def write(self, value):
        self.__stdout.write(value)
        result = self.handler(value)
        if result is not None:
            self.inputs.append(result)

    def readline(self):
        return self.inputs.pop()

    def getvalue(self):
        return self.__stdout.getvalue()

    def truncate(self, pos):
        return self.__stdout.truncate(pos)


def run(command_line, manager_run, capture_stderr=False):
    """Returns tuple of standard output and exit code."""

    sys_stderr_orig = sys.stderr
    sys_stdout_orig = sys.stdout
    sys.stdout = StringIO.StringIO()

    if capture_stderr:
        sys.stderr = StringIO.StringIO()

    sys.argv = command_line.split()
    exit_code = None
    try:
        manager_run()
    except SystemExit as e:
        exit_code = e.code
    finally:
        out = sys.stdout.getvalue()
        # clear the standard output buffer
        sys.stdout.truncate(0)
        assert len(sys.stdout.getvalue()) == 0
        if capture_stderr:
            out += sys.stderr.getvalue()
        sys.stderr = sys_stderr_orig
        sys.stdout = sys_stdout_orig

    return out, exit_code


class InveniomanageTest(InvenioTestCase):

    def test_upgrade_show_applied_cmd(self):
        """ Test `upgrade show applied` command. """
        from invenio.upgrade_manager import main
        out, dummy_exit_code = run('upgrade show applied', main)

        expected = ['>>> Following upgrade(s) have been applied:',
                    '>>> No upgrades have been applied.']
        self.assertTrue(expected[0] in out.split('\n'),
                        "%s was not found in output %s" % (expected, out))

    def test_upgrade_show_pending_cmd(self):
        """ Test `upgrade show pending` command. """
        from invenio.upgrade_manager import main
        out, dummy_exit_code = run('upgrade show pending', main)

        lines = out.split('\n')
        expected = ['>>> Following upgrade(s) are ready to be applied:',
                    '>>> All upgrades have been applied.']
        self.assertTrue(expected[0] in lines or expected[1] in lines,
                        "%s was not found in output %s" % (expected, lines))


TEST_SUITE = make_test_suite(InveniomanageTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

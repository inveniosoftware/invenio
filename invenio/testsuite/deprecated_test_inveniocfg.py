# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2013 CERN.
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

"""Unit tests for the inveniocfg script."""


import sys
import StringIO
import logging

from invenio.legacy.inveniocfg import main
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class InveniocfgTest(InvenioTestCase):
    """
    Test suite for inveniocfg
    """

    def setUp(self):
        """ Save original stdout/err so they can be set back. """
        self.default_stdout = sys.stdout
        self.default_stderr = sys.stderr
        self.output = None
        self.error = None

    def tearDown(self):
        """ Ensure that stdout/err capturing is stopped. """
        self.stop_capture()

    def stop_capture(self):
        """ Helper method to *stop* capture stdout and stderr """
        sys.stdout = self.default_stdout
        sys.stderr = self.default_stderr

        # Inveniocfg sets up some loggers
        # At shutdown, they try to close their stream so we close them here
        # in order to not leave them which a closed stream they will fail to
        # close
        try:
            logging.shutdown()
        except:
            # No loggers are open?
            pass

        if self.output:
            self.output.close()
        if self.error:
            self.error.close()

    def capture(self):
        """ Helper method to *start* capture stdout and stderr """
        if self.output:
            self.output.close()
        if self.error:
            self.error.close()
        self.output = StringIO.StringIO()
        self.error = StringIO.StringIO()
        sys.stdout = self.output
        sys.stderr = self.error

    def assertExitValue(self, exit_val, func, *args, **kwargs):
        """ Assert method to ensure a specific system exit value is called. """
        try:
            func(*args, **kwargs)
            self.fail()
        except SystemExit, e:
            self.assertEqual(exit_val, e.code)

    #
    # Tests
    #
    def test_invalid_cmd(self):
        """ Test exit value for non-existing option. """
        from invenio.config import CFG_PREFIX
        self.capture()
        self.assertExitValue(2, main, '--conf-dir', "%s/etc/" % CFG_PREFIX,
                             '--some-invalid-option-which-does-not-exists')
        self.stop_capture()

    def test_cmd_get(self):
        """ Test --get cmd """
        # New way of calling get
        from invenio.config import CFG_PREFIX
        self.capture()
        main('--conf-dir', '%s/etc/' % CFG_PREFIX, '--get=CFG_PREFIX')
        self.assertEqual('%s\n' % CFG_PREFIX, self.output.getvalue())

        # Old way of calling get
        self.capture()
        main('--conf-dir=%s/etc/' % CFG_PREFIX, '--get', 'CFG_PREFIX')
        self.assertEqual("%s\n" % CFG_PREFIX, self.output.getvalue())

        # Missing option value
        self.capture()
        self.assertExitValue(2, main, '--conf-dir', "%s/etc/" % CFG_PREFIX,
                             '--get')
        self.stop_capture()


TEST_SUITE = make_test_suite(InveniocfgTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

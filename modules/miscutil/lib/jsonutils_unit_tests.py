# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

"""Unit tests for jsonutils library."""

import unittest

from invenio.jsonutils import wash_for_js
from invenio.testutils import make_test_suite, run_test_suite

class JSStringEscapeTest(unittest.TestCase):
    """ Test functions related to escaping of JavaScript strings. """

    def test_newline(self):
        """jsonutils - test if newlines are properly escaped. """
        test_str = "a string with a \n line break in it"
        self.assertEqual(wash_for_js(test_str), "\"a string with a \\n line break in it\"")
        test_str = "a string with a \r\n line break in it"
        self.assertEqual(wash_for_js(test_str), "\"a string with a \\r\\n line break in it\"")
        test_str = """a string with a \r\n line break and "quote" in it"""
        self.assertEqual(wash_for_js(test_str), '''"a string with a \\r\\n line break and \\"quote\\" in it"''')
        
    def test_newline_nojson(self):
        """jsonutils - test if newlines are properly escaped without JSON module. """
        # Trick jsonutils into thinking json module is not available.
        import invenio.jsonutils
        invenio.jsonutils.CFG_JSON_AVAILABLE = False
        self.test_newline()


TEST_SUITE = make_test_suite(JSStringEscapeTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

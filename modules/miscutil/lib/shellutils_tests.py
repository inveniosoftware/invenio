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

"""Unit tests for shellutils library."""

__revision__ = "$Id$"

import unittest

from invenio.shellutils import escape_shell_arg
from invenio.testutils import make_test_suite, run_test_suite

class EscapeShellArgTest(unittest.TestCase):
    """Testing escaping of shell arguments."""

    def test_escape_simple_strings(self):
        """shellutils - escaping simple strings"""
        self.assertEqual("'hello'",
                         escape_shell_arg("hello"))

    def test_escape_backtick_strings(self):
        """shellutils - escaping strings containing backticks"""
        self.assertEqual(r"'hello `world`'",
                         escape_shell_arg(r'hello `world`'))

    def test_escape_quoted_strings(self):
        """shellutils - escaping strings containing single quotes"""
        self.assertEqual("'hello'\\''world'",
                         escape_shell_arg("hello'world"))

    def test_escape_double_quoted_strings(self):
        """shellutils - escaping strings containing double-quotes"""
        self.assertEqual("""'"hello world"'""",
                         escape_shell_arg('"hello world"'))

    def test_escape_complex_quoted_strings(self):
        """shellutils - escaping strings containing complex quoting"""
        self.assertEqual(r"""'"Who is this `Eve'\'', Bob?", asked Alice.'""",
             escape_shell_arg(r""""Who is this `Eve', Bob?", asked Alice."""))

    def test_escape_windows_style_path(self):
        """shellutils - escaping strings containing windows-style file paths"""
        self.assertEqual(r"'C:\Users\Test User\My Documents\funny file name (for testing).pdf'",
                         escape_shell_arg(r'C:\Users\Test User\My Documents\funny file name (for testing).pdf'))

    def test_escape_unix_style_path(self):
        """shellutils - escaping strings containing unix-style file paths"""
        self.assertEqual(r"'/tmp/z_temp.txt'",
                         escape_shell_arg(r'/tmp/z_temp.txt'))

    def test_escape_number_sign(self):
        """shellutils - escaping strings containing the number sign"""
        self.assertEqual(r"'Python comments start with #.'",
                         escape_shell_arg(r'Python comments start with #.'))

    def test_escape_ampersand_string(self):
        """shellutils - escaping strings containing ampersand"""
        self.assertEqual(r"'Today the weather is hot & sunny'",
                         escape_shell_arg(r'Today the weather is hot & sunny'))

    def test_escape_greater_that_strings(self):
        """shellutils - escaping strings containing the greater-than sign"""
        self.assertEqual(r"'10 > 5'",
                         escape_shell_arg(r'10 > 5'))

    def test_escape_less_that_strings(self):
        """shellutils - escaping strings containing the less-than sign"""
        self.assertEqual(r"'5 < 10'",
                         escape_shell_arg(r'5 < 10'))


TEST_SUITE = make_test_suite(EscapeShellArgTest,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

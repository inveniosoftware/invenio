# -*- coding: utf-8 -*-
##
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

"""Unit tests for the textutils library."""

__revision__ = "$Id$"

import unittest

from invenio.textutils import wrap_text_in_a_box, guess_minimum_encoding
from invenio.testutils import make_test_suite, run_test_suite

class GuessMinimumEncodingTest(unittest.TestCase):
    """Test functions related to guess_minimum_encoding function."""
    def test_guess_minimum_encoding(self):
        """textutils - guess_minimum_encoding."""
        self.assertEqual(guess_minimum_encoding('patata'), ('patata', 'ascii'))
        self.assertEqual(guess_minimum_encoding('àèéìòù'), ('\xe0\xe8\xe9\xec\xf2\xf9', 'latin1'))
        self.assertEqual(guess_minimum_encoding('Ιθάκη'), ('Ιθάκη', 'utf8'))

class WrapTextInABoxTest(unittest.TestCase):
    """Test functions related to wrap_text_in_a_box function."""

    def test_plain_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box plain."""
        result = """
**********************************************
** foo bar                                  **
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box('foo bar'), result)

    def test_empty_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box empty."""
        result = """
**********************************************
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box(), result)

    def test_with_title_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box with title."""
        result = """
**********************************************
** a Title!                                 **
** **************************************** **
** foo bar                                  **
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box('foo bar', title='a Title!'), result)

    def test_multiline_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box multiline."""
        result = """
**********************************************
** foo bar                                  **
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box('foo\n bar'), result)

    def test_real_multiline_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box real multiline."""
        result = """
**********************************************
** foo                                      **
** bar                                      **
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box('foo\n\nbar'), result)

    def test_real_no_width_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box no width."""
        result = """
************
** foobar **
************
"""
        self.assertEqual(wrap_text_in_a_box('foobar', min_col=0), result)

    def test_real_nothing_at_all_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box nothing at all."""
        result = """
******
******
"""
        self.assertEqual(wrap_text_in_a_box(min_col=0), result)

    def test_real_squared_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box squared style."""
        result = """
+--------+
| foobar |
+--------+
"""
        self.assertEqual(wrap_text_in_a_box('foobar', style='squared', min_col=0), result)

    def test_indented_text_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box indented text."""
        text = """
    def test_real_squared_wrap_text_in_a_box(self):\n
        \"""wrap_text_in_a_box - squared style.\"""\n
        result = \"""\n
+--------+\n
| foobar |\n
+--------+
\"""
"""
        result = """
******************************
**     def test_real_square **
**     d_wrap_text_in_a_box **
**     (self):              **
**         \"""wrap_text_in_ **
**         a_box - squared  **
**         style.\"""        **
**         result = \"""     **
** +--------+               **
** | foobar |               **
** +--------+\"""            **
******************************
"""
        self.assertEqual(wrap_text_in_a_box(text, min_col=0, max_col=30, break_long=True), result)

    def test_single_new_line_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box single new line."""
        result = """
**********************************************
** ciao come và?                            **
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box("ciao\ncome và?"), result)


    def test_indented_box_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box indented box."""
        result = """
    **********************************************
    ** foobar                                   **
    **********************************************
"""
        self.assertEqual(wrap_text_in_a_box('foobar', tab_num=1), result)

    def test_real_conclusion_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box conclusion."""
        result = """----------------------------------------
foobar                                  \n"""
        self.assertEqual(wrap_text_in_a_box('foobar', style='conclusion'), result)

    def test_real_longtext_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box long text."""
        text = """CDS Invenio (formerly CDSware), the integrated digital library system, is a suite of applications which provides the framework and tools for building and managing an autonomous digital library server. The software is readily available to anyone, as it is free software, licensed under the GNU General Public Licence (GPL). The technology offered by the software covers all aspects of digital library management. It complies with the Open Archives Initiative metadata harvesting protocol (OAI-PMH) and uses MARC 21 as its underlying bibliographic standard. Its flexibility and performance make it a comprehensive solution for the management of document repositories of moderate to large size.

CDS Invenio is developed by, maintained by, and used at, the CERN Document Server. At CERN, CDS Invenio manages over 500 collections of data, consisting of over 800,000 bibliographic records, covering preprints, articles, books, journals, photographs, and more. Besides CERN, CDS Invenio is currently installed and in use by over a dozen scientific institutions worldwide (see the Demo page for details)

If you would like to try it out yourself, please feel free to download our latest version. If you have any questions about the product or our support service, do not hesitate to check out CDS Invenio mailing list archives or to contact us."""

        result = """
************************************************************************
** CDS Invenio (formerly CDSware), the integrated digital library     **
** system, is a suite of applications which provides the framework    **
** and tools for building and managing an autonomous digital library  **
** server. The software is readily available to anyone, as it is free **
** software, licensed under the GNU General Public Licence (GPL). The **
** technology offered by the software covers all aspects of digital   **
** library management. It complies with the Open Archives Initiative  **
** metadata harvesting protocol (OAI-PMH) and uses MARC 21 as its     **
** underlying bibliographic standard. Its flexibility and performance **
** make it a comprehensive solution for the management of document    **
** repositories of moderate to large size.                            **
** CDS Invenio is developed by, maintained by, and used at, the CERN  **
** Document Server. At CERN, CDS Invenio manages over 500 collections **
** of data, consisting of over 800,000 bibliographic records,         **
** covering preprints, articles, books, journals, photographs, and    **
** more. Besides CERN, CDS Invenio is currently installed and in use  **
** by over a dozen scientific institutions worldwide (see the Demo    **
** page for details)                                                  **
** If you would like to try it out yourself, please feel free to      **
** download our latest version. If you have any questions about the   **
** product or our support service, do not hesitate to check out CDS   **
** Invenio mailing list archives or to contact us.                    **
************************************************************************
"""
        self.assertEqual(wrap_text_in_a_box(text), result)

TEST_SUITE = make_test_suite(WrapTextInABoxTest, GuessMinimumEncodingTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)


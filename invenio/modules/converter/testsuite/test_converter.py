# -*- coding: utf-8 -*-
# Invenio bibconvert unit tests.

# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

"""Unit tests for the bibconvert."""

__revision__ = "$Id$"

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
bibconvert = lazy_import('invenio.legacy.bibconvert.api')


class TestFormattingFunctions(InvenioTestCase):
    """Test bibconvert formatting functions."""

    def test_ff(self):
        """bibconvert - formatting functions"""

        self.assertEqual("Hello world!", bibconvert.FormatField("ello world", "ADD(H,!)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world", "ABR(11,!)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("xHello world!x", "CUT(x,x)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("He11o wor1d!", "REP(1,l)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "SUP(NUM)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "LIM(12,R)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "WORDS(2)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "MINL(5)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "MAXL(12)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world! @", "EXP(@,1)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "IF(Hello world!,ORIG,)"))
        self.assertEqual("", bibconvert.FormatField("Hello world!", "NUM()"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!   ", "SHAPE()"))
        self.assertEqual("HELLO WORLD!", bibconvert.FormatField("Hello world!", "UP()"))
        self.assertEqual("hello world!", bibconvert.FormatField("Hello world!", "DOWN()"))
        self.assertEqual("Hello World!", bibconvert.FormatField("Hello world!", "CAP()"))

    def test_ff_regex(self):
        """bibconvert - formatting functions with regular expression"""
        self.assertEqual("Hello world!",
                bibconvert.FormatField("Hellx wyrld!", "REP(//[xy]//,o)"))
        self.assertEqual("Hello world!",
                bibconvert.FormatField("Hello world!", "REP(//[abc]//,o)"))
        self.assertEqual("Hello world!",
                bibconvert.FormatField("Hello world! @", "EXP(//[@_]//,1)"))
        self.assertEqual("Hello world!",
                bibconvert.FormatField("Hello world! abc", "EXP(//[oz]+//,0)"))
        self.assertEqual("Hello world!",
                bibconvert.FormatField("Hello world!", "EXP(//[abc]+//,1)"))
        self.assertEqual("lala",
                bibconvert.FormatField("Hello world!", "IF(//^Hello .*!$//,lala,lolo)"))
        self.assertEqual("lolo",
                bibconvert.FormatField("Hello world!", "IF(//^Hello .*x$//,lala,lolo)"))


class TestGlobalFormattingFunctions(InvenioTestCase):
    """Test bibconvert global formatting functions."""

    def test_gff(self):
        """bibconvert - global formatting functions"""

        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!","DEFP()"))

class TestGenerateValues(InvenioTestCase):
    """Test bibconvert value generation."""

    def test_gv(self):
        """bibconvert - value generation"""

        self.assertEqual("Hello world!", bibconvert.generate("VALUE(Hello world!)"))

class TestParseData(InvenioTestCase):
    """Test bibconvert input data parsing."""

    def test_idp(self):
        """bibconvert - input data parsing"""

        self.assertEqual(['A','B','C','D'], bibconvert.parse_field_definition("A---B---C---D"))

class TestRegExp(InvenioTestCase):
    """Test bibconvert regular expressions"""

    def test_regexp(self):
        """bibconvert - regular expressions"""

        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "RE([A-Z][a-z].*!)"))

class TestLim(InvenioTestCase):
    """Test bibconvert LIM() function."""

    def test_lim_default(self):
        """bibconvert - LIM(0,)"""
        test_input = "ab cd xx 12 34"
        self.assertEqual(test_input,
                         bibconvert.FormatField(test_input, "LIM(0,)"))

    def test_lim_left(self):
        """bibconvert - LIM(n,L)"""
        test_input = "ab cd xx 12 34"
        self.assertEqual("2 34",
                         bibconvert.FormatField(test_input, "LIM(4,L)"))
        test_input = "sep_1999"
        self.assertEqual("1999",
                         bibconvert.FormatField(test_input, "LIM(4,L)"))

    def test_lim_right(self):
        """bibconvert - LIM(n,R)"""
        test_input = "ab cd xx 12 34"
        self.assertEqual("ab c",
                         bibconvert.FormatField(test_input, "LIM(4,R)"))
        test_input = "sep_1999"
        self.assertEqual("sep_",
                         bibconvert.FormatField(test_input, "LIM(4,R)"))

class TestLimw(InvenioTestCase):
    """Test bibconvert LIMW() function."""

    def test_limw_default(self):
        """bibconvert - LIMW(,)"""
        test_input = "ab cd xx 12 34"
        self.assertEqual(test_input,
                         bibconvert.FormatField(test_input, "LIMW(,)"))
        self.assertEqual(test_input,
                         bibconvert.FormatField(test_input, "LIMW(,R)"))

    def test_limw_left(self):
        """bibconvert - LIMW(c,L)"""
        test_input = "ab cd xx 12 34"
        self.assertEqual(" cd xx 12 34",
                         bibconvert.FormatField(test_input, "LIMW( ,L)"))

    def test_limw_left_regex(self):
        """bibconvert - LIMW(c,L) with regular expression"""
        test_input = "ab cd xx 12 34"
        self.assertEqual("ab ",
                bibconvert.FormatField(test_input, "LIMW(//\s//,R)"))
        self.assertEqual(test_input,
                bibconvert.FormatField(test_input, "LIMW(//[!_-]//,R)"))

    def test_limw_right(self):
        """bibconvert - LIMW(c,R)"""
        test_input = "ab cd xx 12 34"
        self.assertEqual("ab ",
                         bibconvert.FormatField(test_input, "LIMW( ,R)"))
        test_input = "sep_1999"
        self.assertEqual("sep_",
                         bibconvert.FormatField(test_input, "LIMW(_,R)"))

    def test_limw_right_regex(self):
        """bibconvert - LIMW(c,R) with regular expression"""
        test_input = "ab cd xx 12 34"
        self.assertEqual("ab ",
                bibconvert.FormatField(test_input, "LIMW(//\s//,R)"))
        self.assertEqual(test_input,
                bibconvert.FormatField(test_input, "LIMW(//[!_-]//,R)"))

        test_input = "sep_1999"
        self.assertEqual("sep_",
                bibconvert.FormatField(test_input, "LIMW(//[!_]//,R)"))
        self.assertEqual(test_input,
                bibconvert.FormatField(test_input, "LIMW(//[!-]//,R)"))


class TestWords(InvenioTestCase):
    """Test bibconvert WORDS() function."""

    def test_words_default(self):
        """bibconvert - WORDS(,)"""
        test_input = "ab cd xx 12 34"
        self.assertEqual(test_input,
                         bibconvert.FormatField(test_input, "WORDS(,)"))

    def test_words_left(self):
        """bibconvert - WORDS(n,L)"""
        test_input = "ab cd xx 12 34"
        self.assertEqual("12 34",
                         bibconvert.FormatField(test_input, "WORDS(2,L)"))
        test_input = "Sep 1999"
        self.assertEqual("1999",
                         bibconvert.FormatField(test_input, "WORDS(1,L)"))

    def test_words_right(self):
        """bibconvert - WORDS(n,R)"""
        test_input = "ab cd xx 12 34"
        self.assertEqual("ab cd",
                         bibconvert.FormatField(test_input, "WORDS(2,R)"))
        test_input = "Sep 1999"
        self.assertEqual("Sep",
                         bibconvert.FormatField(test_input, "WORDS(1,R)"))

    def test_words_exceed_wordcount(self):
        """bibconvert - WORDS(2,R) when less then 2 words in value"""
        test_input = "ab"
        self.assertEqual(test_input,
                         bibconvert.FormatField(test_input, "WORDS(2,R)"))

class TestBCCL(InvenioTestCase):
    """Test bibconvert BCCL compliance"""

    def xtest_bccl_09(self):
        """bibconvert - BCCL v.0.9 compliance"""

        # FIXME: put proper tests here
        self.assertEqual(1, 1)

class TestKnowledgeBase(InvenioTestCase):
    """Test bibconvert knowledge base"""

    def xtest_enc(self):
        """bibconvert - knowledge base"""

        # FIXME: put proper tests here
        self.assertEqual(1, 1)

class TestErrorCodes(InvenioTestCase):
    """Test bibconvert error codes"""

    def xtest_enc(self):
        """bibconvert - error codes"""

        # FIXME: put proper tests here
        self.assertEqual(1, 1)

class TestEncodings(InvenioTestCase):
    """Test bibconvert encodings"""

    def xtest_enc(self):
        """bibconvert - encodings"""

        # FIXME: put proper tests here
        self.assertEqual(1, 1)


TEST_SUITE = make_test_suite(TestFormattingFunctions,
                             TestGlobalFormattingFunctions,
                             TestGenerateValues,
                             TestParseData,
                             TestRegExp,
                             TestLim,
                             TestLimw,
                             TestWords,
                             TestBCCL,
                             TestKnowledgeBase,
                             TestErrorCodes,
                             TestEncodings,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
